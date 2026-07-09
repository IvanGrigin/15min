from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


PLACEHOLDER_RE = re.compile(r"{{\s*([^}]+?)\s*}}")
LEADING_NUMBER_RE = re.compile(r"^\s*\d+\.\s*")


class WorksheetRenderError(ValueError):
    """Понятная ошибка при сборке или рендере листа."""


@dataclass(frozen=True)
class WrappedProblemSlot:
    index: int
    x: int
    y: int
    width: int
    height: int
    separator_y: int
    lines: list[str]


@dataclass(frozen=True)
class WorksheetPlan:
    template: dict[str, Any]
    placeholders: dict[str, str]
    slots: list[WrappedProblemSlot]


@dataclass(frozen=True)
class ProblemSource:
    problems: list[str]
    header: dict[str, str]


def load_worksheet_template(path: str | Path) -> dict[str, Any]:
    template_path = Path(path)
    payload = json.loads(template_path.read_text(encoding="utf-8"))

    if "page" not in payload or "problem_area" not in payload:
        raise WorksheetRenderError(
            f"Шаблон {template_path} не содержит обязательные блоки page/problem_area."
        )

    slots = payload["problem_area"].get("slots", [])
    if not slots:
        raise WorksheetRenderError(f"Шаблон {template_path} не содержит ни одного слота задач.")

    return payload


def load_problem_source(path: str | Path) -> ProblemSource:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))

    if isinstance(payload, dict) and isinstance(payload.get("problems"), list):
        raw_items = payload["problems"]
        raw_header = payload.get("header", {})
    elif isinstance(payload, list):
        raw_items = payload
        raw_header = {}
    else:
        raise WorksheetRenderError(
            "Файл задач должен быть либо JSON-списком, либо объектом с полем 'problems'."
        )

    result: list[str] = []
    for item in raw_items:
        if isinstance(item, str):
            result.append(item.strip())
            continue

        if not isinstance(item, dict):
            raise WorksheetRenderError("Каждая задача должна быть строкой или JSON-объектом.")

        for key in ("problem_text", "condition", "text"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                result.append(value.strip())
                break
        else:
            raise WorksheetRenderError(
                "Не удалось извлечь текст задачи: ожидалось поле 'problem_text', 'condition' или 'text'."
            )

    header = {
        "surname": str(raw_header.get("surname", "") or ""),
        "name": str(raw_header.get("name", "") or ""),
        "date": str(raw_header.get("date", "") or ""),
        "logo_path": str(raw_header.get("logo_path", "") or ""),
        "qr_path": str(raw_header.get("qr_path", "") or ""),
    }
    return ProblemSource(problems=result, header=header)


def load_problem_texts(path: str | Path) -> list[str]:
    return load_problem_source(path).problems


def prepare_problem_text(text: str, index: int) -> str:
    cleaned = LEADING_NUMBER_RE.sub("", text.strip())
    return f"{index}. {cleaned}"


def resolve_placeholder_text(text: str, placeholders: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return placeholders.get(key, match.group(0))

    return PLACEHOLDER_RE.sub(replace, text)


def build_placeholder_map(
    problems: list[str],
    *,
    surname: str = "",
    name: str = "",
    date_text: str | None = None,
    logo_path: str = "",
    qr_path: str = "",
) -> dict[str, str]:
    normalized_date = date_text or datetime.now().strftime("%d.%m.%Y")
    placeholders = {
        "surname": surname,
        "name": name,
        "date": normalized_date,
        "logo_path": logo_path,
        "qr_path": qr_path,
    }

    for idx, text in enumerate(problems):
        placeholders[f"problems[{idx}]"] = text

    return placeholders


def wrap_text_to_width(
    text: str,
    *,
    max_width: int,
    measure: Callable[[str], float],
) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        if measure(candidate) <= max_width:
            current = candidate
            continue

        if measure(word) > max_width:
            raise WorksheetRenderError(
                f"Слово '{word}' не помещается в доступную ширину {max_width}."
            )

        lines.append(current)
        current = word

    lines.append(current)
    return lines


def build_worksheet_plan(
    template: dict[str, Any],
    problems: list[str],
    *,
    surname: str = "",
    name: str = "",
    date_text: str | None = None,
    logo_path: str = "",
    qr_path: str = "",
    measure: Callable[[str, int, bool], float],
) -> WorksheetPlan:
    slots = template["problem_area"]["slots"]
    expected_count = len(slots)
    if len(problems) != expected_count:
        raise WorksheetRenderError(
            f"Шаблон ожидает {expected_count} задач, а получено {len(problems)}."
        )

    numbered = [prepare_problem_text(text, idx) for idx, text in enumerate(problems, start=1)]
    placeholders = build_placeholder_map(
        numbered,
        surname=surname,
        name=name,
        date_text=date_text,
        logo_path=logo_path,
        qr_path=qr_path,
    )

    area = template["problem_area"]
    default_font_size = area.get(
        "font_size",
        template.get("styles", {}).get("problem_font_size", 20),
    )
    line_height = area.get(
        "line_height",
        template.get("styles", {}).get("problem_line_height", default_font_size + 6),
    )

    wrapped_slots: list[WrappedProblemSlot] = []
    for slot in slots:
        resolved_text = resolve_placeholder_text(slot["text"], placeholders)
        font_size = slot.get("font_size", default_font_size)
        max_lines = max(1, math.floor(slot["height"] / line_height))
        lines = wrap_text_to_width(
            resolved_text,
            max_width=slot["width"],
            measure=lambda text, fs=font_size: measure(text, fs, False),
        )
        if len(lines) > max_lines:
            raise WorksheetRenderError(
                f"Текст задачи {slot['index']} не помещается в слот: "
                f"{len(lines)} строк при лимите {max_lines}."
            )

        wrapped_slots.append(
            WrappedProblemSlot(
                index=slot["index"],
                x=slot["x"],
                y=slot["y"],
                width=slot["width"],
                height=slot["height"],
                separator_y=slot["separator_y"],
                lines=lines,
            )
        )

    return WorksheetPlan(template=template, placeholders=placeholders, slots=wrapped_slots)


def render_worksheet(
    *,
    template_path: str | Path,
    problems_path: str | Path,
    output_path: str | Path,
    surname: str = "",
    name: str = "",
    date_text: str | None = None,
    logo_path: str = "",
    qr_path: str = "",
) -> Path:
    template = load_worksheet_template(template_path)
    source = load_problem_source(problems_path)
    problems = source.problems
    output = Path(output_path)
    suffix = output.suffix.lower()

    resolved_surname = surname or source.header.get("surname", "")
    resolved_name = name or source.header.get("name", "")
    resolved_date = date_text or source.header.get("date", "") or None
    resolved_logo_path = logo_path or source.header.get("logo_path", "")
    resolved_qr_path = qr_path or source.header.get("qr_path", "")

    if suffix == ".pdf":
        return _render_pdf(
            template=template,
            problems=problems,
            output_path=output,
            surname=resolved_surname,
            name=resolved_name,
            date_text=resolved_date,
            logo_path=resolved_logo_path,
            qr_path=resolved_qr_path,
        )
    if suffix == ".png":
        return _render_png(
            template=template,
            problems=problems,
            output_path=output,
            surname=resolved_surname,
            name=resolved_name,
            date_text=resolved_date,
            logo_path=resolved_logo_path,
            qr_path=resolved_qr_path,
        )

    raise WorksheetRenderError(
        f"Неподдерживаемый формат '{output.suffix}'. Используйте .pdf или .png."
    )


def _resolve_font_paths() -> tuple[Path | None, Path | None]:
    regular_candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
        Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("C:/Windows/Fonts/times.ttf"),
    ]
    bold_candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf"),
        Path("C:/Windows/Fonts/tahomabd.ttf"),
        Path("C:/Windows/Fonts/timesbd.ttf"),
    ]

    regular = next((path for path in regular_candidates if path.exists()), None)
    bold = next((path for path in bold_candidates if path.exists()), regular)
    return regular, bold


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    if len(value) != 6:
        raise WorksheetRenderError(f"Некорректный цвет: {color}")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _render_pdf(
    *,
    template: dict[str, Any],
    problems: list[str],
    output_path: Path,
    surname: str,
    name: str,
    date_text: str | None,
    logo_path: str,
    qr_path: str,
) -> Path:
    try:
        from reportlab.lib.colors import Color
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas
    except ImportError as error:
        raise WorksheetRenderError(
            "Для рендера PDF нужен пакет reportlab. Установите его в окружении."
        ) from error

    regular_font, bold_font = _resolve_font_paths()
    regular_name = "Helvetica"
    bold_name = "Helvetica-Bold"

    if regular_font is not None:
        regular_name = "WorksheetSans"
        pdfmetrics.registerFont(TTFont(regular_name, str(regular_font)))
    if bold_font is not None:
        bold_name = "WorksheetSansBold"
        pdfmetrics.registerFont(TTFont(bold_name, str(bold_font)))

    plan = build_worksheet_plan(
        template,
        problems,
        surname=surname,
        name=name,
        date_text=date_text,
        logo_path=logo_path,
        qr_path=qr_path,
        measure=lambda text, font_size, bold: pdfmetrics.stringWidth(
            text,
            bold_name if bold else regular_name,
            font_size,
        ),
    )

    page = template["page"]
    page_width = page["width"]
    page_height = page["height"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))

    bg_r, bg_g, bg_b = _hex_to_rgb(page.get("background", "#ffffff"))
    sheet.setFillColor(Color(bg_r / 255, bg_g / 255, bg_b / 255))
    sheet.rect(0, 0, page_width, page_height, stroke=0, fill=1)
    sheet.setFillColorRGB(17 / 255, 17 / 255, 17 / 255)

    _draw_pdf_header(sheet, template, plan, page_height, regular_name, bold_name)
    _draw_pdf_problem_slots(sheet, template, plan, page_height, regular_name)
    _draw_pdf_right_panel(
        sheet,
        template,
        plan,
        page_height,
        regular_name,
        ImageReader,
    )

    sheet.showPage()
    sheet.save()
    return output_path


def _draw_pdf_header(sheet: Any, template: dict[str, Any], plan: WorksheetPlan, page_height: int, regular_name: str, bold_name: str) -> None:
    header = template.get("header", {})
    styles = template.get("styles", {})

    for line_key in ("top_line", "bottom_line"):
        line = header.get(line_key)
        if line:
            _draw_pdf_line(sheet, line, page_height)

    for field in header.get("fields", []):
        font_size = field.get("font_size", styles.get("header_font_size", 18))
        font_name = bold_name if field.get("bold") else regular_name
        sheet.setFont(font_name, font_size)
        resolved_value = resolve_placeholder_text(field.get("value", ""), plan.placeholders).strip()
        display_value = resolved_value or field.get("blank_value", "")
        if field.get("label"):
            text = f"{field['label']}: {display_value}"
        else:
            text = display_value
        sheet.drawString(field["x"], page_height - field["y"] - font_size, text)


def _draw_pdf_problem_slots(sheet: Any, template: dict[str, Any], plan: WorksheetPlan, page_height: int, regular_name: str) -> None:
    area = template["problem_area"]
    styles = template.get("styles", {})
    separator_style = area.get("separator", {})
    font_size = area.get("font_size", styles.get("problem_font_size", 20))
    line_height = area.get("line_height", styles.get("problem_line_height", font_size + 6))

    sheet.setFont(regular_name, font_size)
    for slot in plan.slots:
        for line_idx, line in enumerate(slot.lines):
            y = slot.y + line_idx * line_height
            sheet.drawString(slot.x, page_height - y - font_size, line)

        _draw_pdf_line(
            sheet,
            {
                "x1": slot.x,
                "y1": slot.separator_y,
                "x2": slot.x + slot.width,
                "y2": slot.separator_y,
                "stroke": separator_style.get("stroke", "#000000"),
                "width": separator_style.get("width", 1),
            },
            page_height,
        )


def _draw_pdf_right_panel(
    sheet: Any,
    template: dict[str, Any],
    plan: WorksheetPlan,
    page_height: int,
    regular_name: str,
    image_reader_cls: Any,
) -> None:
    panel = template.get("right_panel", {})
    separator = panel.get("left_separator")
    if separator:
        _draw_pdf_line(sheet, separator, page_height)

    for element in panel.get("elements", []):
        if element.get("type") != "image":
            continue
        source = resolve_placeholder_text(element.get("source", ""), plan.placeholders).strip()
        rect_y = page_height - element["y"] - element["height"]
        if source and Path(source).exists():
            sheet.drawImage(
                image_reader_cls(source),
                element["x"],
                rect_y,
                width=element["width"],
                height=element["height"],
                preserveAspectRatio=True,
                mask="auto",
            )
        else:
            sheet.rect(element["x"], rect_y, element["width"], element["height"], stroke=1, fill=0)
            sheet.setFont(regular_name, 12)
            sheet.drawCentredString(
                element["x"] + element["width"] / 2,
                rect_y + element["height"] / 2 - 6,
                element.get("placeholder_label", element.get("name", "IMAGE")).upper(),
            )


def _draw_pdf_line(sheet: Any, line: dict[str, Any], page_height: int) -> None:
    r, g, b = _hex_to_rgb(line.get("stroke", "#000000"))
    sheet.setStrokeColorRGB(r / 255, g / 255, b / 255)
    sheet.setLineWidth(line.get("width", 1))
    sheet.line(
        line["x1"],
        page_height - line["y1"],
        line["x2"],
        page_height - line["y2"],
    )


def _render_png(
    *,
    template: dict[str, Any],
    problems: list[str],
    output_path: Path,
    surname: str,
    name: str,
    date_text: str | None,
    logo_path: str,
    qr_path: str,
) -> Path:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as error:
        raise WorksheetRenderError(
            "Для рендера PNG нужен пакет Pillow. Установите его в окружении."
        ) from error

    regular_font_path, bold_font_path = _resolve_font_paths()
    if regular_font_path is None:
        raise WorksheetRenderError("Не найден системный TTF-шрифт для PNG-рендера.")

    def load_font(size: int, bold: bool) -> Any:
        path = bold_font_path if bold and bold_font_path is not None else regular_font_path
        return ImageFont.truetype(str(path), size=size)

    font_cache: dict[tuple[int, bool], Any] = {}

    def get_font(size: int, bold: bool) -> Any:
        key = (size, bold)
        if key not in font_cache:
            font_cache[key] = load_font(size, bold)
        return font_cache[key]

    def measure(text: str, font_size: int, bold: bool) -> float:
        font = get_font(font_size, bold)
        bbox = font.getbbox(text)
        return float(bbox[2] - bbox[0])

    plan = build_worksheet_plan(
        template,
        problems,
        surname=surname,
        name=name,
        date_text=date_text,
        logo_path=logo_path,
        qr_path=qr_path,
        measure=measure,
    )

    page = template["page"]
    image = Image.new("RGB", (page["width"], page["height"]), _hex_to_rgb(page.get("background", "#ffffff")))
    draw = ImageDraw.Draw(image)

    _draw_png_header(draw, template, plan, get_font)
    _draw_png_problem_slots(draw, template, plan, get_font)
    _draw_png_right_panel(image, draw, template, plan, get_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path


def _draw_png_header(draw: Any, template: dict[str, Any], plan: WorksheetPlan, get_font: Callable[[int, bool], Any]) -> None:
    header = template.get("header", {})
    styles = template.get("styles", {})

    for line_key in ("top_line", "bottom_line"):
        line = header.get(line_key)
        if line:
            _draw_png_line(draw, line)

    for field in header.get("fields", []):
        font_size = field.get("font_size", styles.get("header_font_size", 18))
        font = get_font(font_size, bool(field.get("bold")))
        resolved_value = resolve_placeholder_text(field.get("value", ""), plan.placeholders).strip()
        display_value = resolved_value or field.get("blank_value", "")
        text = f"{field['label']}: {display_value}" if field.get("label") else display_value
        draw.text((field["x"], field["y"]), text, fill=_hex_to_rgb("#111111"), font=font)


def _draw_png_problem_slots(draw: Any, template: dict[str, Any], plan: WorksheetPlan, get_font: Callable[[int, bool], Any]) -> None:
    area = template["problem_area"]
    styles = template.get("styles", {})
    separator_style = area.get("separator", {})
    font_size = area.get("font_size", styles.get("problem_font_size", 20))
    line_height = area.get("line_height", styles.get("problem_line_height", font_size + 6))
    font = get_font(font_size, False)

    for slot in plan.slots:
        for line_idx, line in enumerate(slot.lines):
            draw.text((slot.x, slot.y + line_idx * line_height), line, fill=_hex_to_rgb("#111111"), font=font)

        _draw_png_line(
            draw,
            {
                "x1": slot.x,
                "y1": slot.separator_y,
                "x2": slot.x + slot.width,
                "y2": slot.separator_y,
                "stroke": separator_style.get("stroke", "#000000"),
                "width": separator_style.get("width", 1),
            },
        )


def _draw_png_right_panel(
    image: Any,
    draw: Any,
    template: dict[str, Any],
    plan: WorksheetPlan,
    get_font: Callable[[int, bool], Any],
) -> None:
    try:
        from PIL import Image
    except ImportError:
        raise WorksheetRenderError("Для PNG-рендера не удалось загрузить Pillow Image.")

    panel = template.get("right_panel", {})
    separator = panel.get("left_separator")
    if separator:
        _draw_png_line(draw, separator)

    for element in panel.get("elements", []):
        if element.get("type") != "image":
            continue
        source = resolve_placeholder_text(element.get("source", ""), plan.placeholders).strip()
        box = (
            element["x"],
            element["y"],
            element["x"] + element["width"],
            element["y"] + element["height"],
        )
        if source and Path(source).exists():
            with Image.open(source) as src:
                prepared = src.convert("RGB")
                prepared.thumbnail((element["width"], element["height"]))
                paste_x = element["x"] + (element["width"] - prepared.width) // 2
                paste_y = element["y"] + (element["height"] - prepared.height) // 2
                image.paste(prepared, (paste_x, paste_y))
            draw.rectangle(box, outline=_hex_to_rgb("#000000"), width=1)
        else:
            draw.rectangle(box, outline=_hex_to_rgb("#000000"), width=1)
            font = get_font(12, False)
            label = element.get("placeholder_label", element.get("name", "IMAGE")).upper()
            bbox = font.getbbox(label)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            text_x = element["x"] + (element["width"] - text_w) / 2
            text_y = element["y"] + (element["height"] - text_h) / 2
            draw.text((text_x, text_y), label, fill=_hex_to_rgb("#111111"), font=font)


def _draw_png_line(draw: Any, line: dict[str, Any]) -> None:
    draw.line(
        (line["x1"], line["y1"], line["x2"], line["y2"]),
        fill=_hex_to_rgb(line.get("stroke", "#000000")),
        width=line.get("width", 1),
    )
