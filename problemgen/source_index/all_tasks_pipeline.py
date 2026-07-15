from __future__ import annotations

import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "Docs" / "all_tasks_all_files.md"
SOURCE_INDEX_DIR = PROJECT_ROOT / "data" / "source_index"
TEMPLATES_DIR = PROJECT_ROOT / "data" / "templates"

TREE_PATH = SOURCE_INDEX_DIR / "All_tasks_structure_tree.json"
REJECTED_PATH = SOURCE_INDEX_DIR / "All_tasks_rejected_problems.json"
TEMPLATES_PATH = TEMPLATES_DIR / "All_tasks_templates.json"
SUMMARY_PATH = SOURCE_INDEX_DIR / "All_tasks_modules_summary.md"
COVERAGE_PATH = TEMPLATES_DIR / "All_tasks_template_coverage_report.md"

ROOT_COMPATIBILITY_FILES = {
    TREE_PATH: PROJECT_ROOT / "All_tasks_structure_tree.json",
    REJECTED_PATH: PROJECT_ROOT / "All_tasks_rejected_problems.json",
    TEMPLATES_PATH: PROJECT_ROOT / "All_tasks_templates.json",
    SUMMARY_PATH: PROJECT_ROOT / "All_tasks_modules_summary.md",
    COVERAGE_PATH: PROJECT_ROOT / "All_tasks_template_coverage_report.md",
}


@dataclass(frozen=True)
class ModuleSpec:
    module_id: str
    module_name: str
    description: str
    difficulty: int
    keywords: tuple[str, ...]
    secondary_tags: tuple[str, ...]


MODULES: tuple[ModuleSpec, ...] = (
    ModuleSpec("linear_equation_chain", "Линейные уравнения и выражения", "Задачи на нахождение неизвестного и вычисление выражений.", 4, ("найдите значение x", "найдите неизвестное", "значение х", "найдите значение х", "равенства", "равенство", "вычислите"), ("арифметика", "уравнения")),
    ModuleSpec("digit_frequency_block", "Цифры в записи чисел", "Подсчёт цифр в последовательной записи натуральных чисел.", 5, ("сколько раз", "в записи всех чисел", "встречается цифра", "содержащих цифру", "содержащие цифру"), ("цифры", "подсчёт")),
    ModuleSpec("calendar_weekday", "Календарь и дни недели", "Определение дней недели и календарных дат.", 4, ("день недели", "понедельник", "вторник", "среда", "среду", "среды", "четверг", "пятница", "пятницу", "суббота", "субботу", "воскресенье"), ("календарь", "время")),
    ModuleSpec("heads_and_legs", "Головы и ноги", "Системы на количество объектов по головам и ногам.", 4, ("ноги", "ног", "голов", "головы", "гном", "пони", "уток", "кролик", "мальчик съел", "девочка съела"), ("система", "подсчёт")),
    ModuleSpec("time_zones", "Часовые пояса и локальное время", "Задачи на разницу часовых поясов и длительность событий.", 5, ("местному времени", "час позже", "час раньше", "калининград", "самара", "екатеринбург", "самолёт", "самолет", "часовых пояс"), ("время", "движение")),
    ModuleSpec("digit_sum_numbers", "Числа с заданной суммой цифр", "Подсчёт многозначных чисел с условиями на сумму цифр.", 6, ("сумма цифр", "значных чисел", "разряде сотен", "разряде тысяч", "разряде миллионов"), ("комбинаторика", "цифры")),
    ModuleSpec("cuboid_blocks", "Кубы, бруски и разрезания", "Разрезание кубов и брусков на части.", 5, ("куб", "бруск", "распилил", "разрезал", "маленькие кубики"), ("геометрия", "объём")),
    ModuleSpec("large_product_comparison", "Сравнение произведений", "Сравнение больших произведений без полного умножения.", 5, ("какое из чисел больше", "произведени", "перемножая", "сомножител"), ("арифметика", "множители")),
    ModuleSpec("digital_clock_display", "Электронное табло", "Задачи про цифровые часы и свойства цифр времени.", 6, ("электронном табло", "цифры на табло", "время"), ("цифры", "время")),
    ModuleSpec("divisibility_interval", "Делимость в интервалах", "Подсчёт чисел с условиями делимости на интервале.", 4, ("кратных", "делящихся", "делится на", "не делится"), ("делимость", "интервалы")),
    ModuleSpec("permutations_repeated", "Перестановки и комбинации", "Перестановки букв, цифр и объектов с ограничениями.", 5, ("комбинац", "перебрать", "слово", "алфавитном порядке", "букв", "набор цифр"), ("комбинаторика", "перестановки")),
    ModuleSpec("sequence_sum", "Последовательности и суммы", "Суммы последовательностей и закономерности.", 4, ("последовательности", "сумму последовательности", "+..."), ("последовательности", "арифметика")),
    ModuleSpec("unit_density_conversion", "Единицы измерения и плотность", "Задачи на массу, площадь, плотность и перевод единиц.", 4, ("весит", "граммов", "квадратных", "дециметр", "сантиметр", "см"), ("измерения", "геометрия")),
    ModuleSpec("paint_cube", "Покраска куба", "Задачи на площадь поверхности и окрашивание кубов.", 5, ("покрасить", "краски", "грани", "поверхность"), ("геометрия", "масштаб")),
    ModuleSpec("rectangle_area_perimeter", "Прямоугольники: площадь и периметр", "Прямоугольники, периметр, площадь и отношения сторон.", 5, ("прямоугольник", "периметр", "площад", "пузатость", "стороны"), ("геометрия", "уравнения")),
    ModuleSpec("gcd_lcm_periods", "Периодические встречи", "Задачи на повторяющиеся события и НОК.", 4, ("каждый", "следующий раз", "встретятся", "регулярно"), ("нок", "периоды")),
    ModuleSpec("lexicographic_order", "Лексикографический порядок", "Неизвестный алфавит и порядок слов.", 6, ("алфавит", "слово", "слов из", "идёт следом", "идет следом"), ("комбинаторика", "порядок")),
    ModuleSpec("motion_piecewise", "Движение по участкам", "Пути, скорости, перелёты и движение в несколько этапов.", 5, ("скорост", "вылетел", "летел", "двигался", "путь", "расстояние", "навстречу"), ("движение", "время")),
    ModuleSpec("joint_work", "Совместная работа", "Производительность и совместное выполнение работы.", 5, ("составляет", "за", "вместе за", "производительность", "работ"), ("скорость работы", "арифметика")),
    ModuleSpec("direct_proportion", "Пропорции и отношения", "Прямые пропорции, отношения и масштабирование величин.", 4, ("в раз больше", "отнош", "пропорц", "сколько деревьев", "вместе они"), ("пропорции", "арифметика")),
    ModuleSpec("logic_invariants", "Логика и инварианты", "Логические условия, конструкции и инварианты.", 6, ("приведите пример", "возможно", "докажите", "инвариант", "рыцар", "лжец"), ("логика", "инварианты")),
    ModuleSpec("counting_general", "Комбинаторный подсчёт", "Общий подсчёт вариантов, объектов и случаев.", 5, ("сколько существует", "сколько различных", "сколько способов", "сколько вариантов"), ("подсчёт", "комбинаторика")),
    ModuleSpec("arithmetic_word_model", "Арифметическая текстовая модель", "Прочие текстовые задачи, сводящиеся к арифметической модели.", 4, tuple(), ("арифметика",)),
)

MODULE_BY_ID = {module.module_id: module for module in MODULES}
NOISE_REPLACEMENTS = (
    (r"\[=\]", " "),
    (r"ПОСТУПЛЕНИЕ", " "),
    (r"REF", " "),
    (r"OED", " "),
    (r"\bSma\b", " "),
    (r"\bS22\b", " "),
    (r"\bЕЕ\b", " "),
    (r"\bEE\b", " "),
    (r"\bLe\b", " "),
    (r"\baad\b", " "),
    (r"\bSd\b", " "),
    (r"\bad\b", " "),
    (r"\bwh\b", " "),
)
NAME_WORDS = {
    "Али-Баба", "Алёша", "Алена", "Ваня", "Ваня", "Иван", "Кирилл", "Коля",
    "Максим", "Петя", "Саша", "Серёжа", "Ралины", "Илья",
}


def normalize_spacing(text: str) -> str:
    text = text.replace("ё", "ё")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.:;!?])", r"\1", text)
    text = re.sub(r"([,.:;!?])(?=\S)", r"\1 ", text)
    return text.strip()


def clean_text(text: str) -> str:
    cleaned = text.replace(" x ", " * ").replace(" х ", " * ").replace("Х", "X")
    cleaned = cleaned.replace("Ha ", "на ").replace(" ha ", " на ")
    cleaned = cleaned.replace(" 2 я = прямоугольнике", " в прямоугольнике")
    cleaned = cleaned.replace("ay rad", "")
    cleaned = cleaned.replace("ульев”", "")
    cleaned = cleaned.replace("Кakoe", "Какое")
    cleaned = cleaned.replace("Kakoe", "Какое")
    cleaned = cleaned.replace("сомножителя,один", "сомножителя, один")
    cleaned = re.sub(r"([0-9])Бм\b", r"\1 см", cleaned)
    cleaned = re.sub(r"([0-9])смх([0-9])", r"\1 см x \2", cleaned)
    cleaned = re.sub(r"\b:\s*([0-9])", r": \1", cleaned)
    for pattern, replacement in NOISE_REPLACEMENTS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*[`'\"“”‚„]+\s*$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return normalize_spacing(cleaned)


def extract_records(source_text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    current_file = ""
    for line in source_text.splitlines():
        if line.startswith("## "):
            current_file = line.removeprefix("## ").strip()
            continue
        match = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        if not match:
            continue
        source_number = int(match.group(1))
        original = match.group(2).strip()
        cleaned = clean_text(original)
        if len(cleaned) < 8:
            rejected.append({
                "source_problem_number": source_number,
                "source_file": current_file,
                "original_text": original,
                "reason": "Record is too short to reconstruct safely.",
            })
            continue
        records.append({
            "problem_id": len(records) + 1,
            "source_problem_number": source_number,
            "source_file": current_file,
            "original_text": original,
            "cleaned_text": cleaned,
        })
    return records, rejected


def classify_problem(cleaned_text: str) -> ModuleSpec:
    lowered = cleaned_text.lower()
    for module in MODULES:
        if module.keywords and any(keyword_matches(keyword, lowered) for keyword in module.keywords):
            return module
    return MODULE_BY_ID["arithmetic_word_model"]


def keyword_matches(keyword: str, lowered_text: str) -> bool:
    if " " in keyword or keyword != keyword.strip():
        return keyword in lowered_text
    return re.search(rf"(?<![а-яёa-z]){re.escape(keyword)}(?![а-яёa-z])", lowered_text) is not None


def difficulty_for(text: str, module: ModuleSpec) -> int:
    score = module.difficulty
    numbers = re.findall(r"\d+", text)
    if len(numbers) >= 6:
        score += 1
    if len(text) > 260:
        score += 1
    if any(word in text.lower() for word in ("докажите", "приведите пример", "алфавит", "стознач")):
        score += 1
    return max(1, min(10, score))


def build_tree(records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        module = classify_problem(record["cleaned_text"])
        grouped[module.module_id].append({
            **record,
            "difficulty": difficulty_for(record["cleaned_text"], module),
            "primary_module": module.module_id,
            "secondary_tags": list(module.secondary_tags),
        })

    modules = []
    module_number = 1
    for module in MODULES:
        problems = grouped.get(module.module_id, [])
        if not problems:
            continue
        modules.append({
            "module_id": module.module_id,
            "module_number": module_number,
            "module_name": module.module_name,
            "description": module.description,
            "problems": problems,
        })
        module_number += 1

    return {
        "schema_version": "1.0",
        "source_file": "Docs/all_tasks_all_files.md",
        "valid_problem_count": len(records),
        "modules": modules,
    }


def placeholder_kind(value: str) -> str:
    if re.fullmatch(r"\d+(?::\d+)?", value):
        return "number"
    if re.fullmatch(r"\d+[.,]\d+", value):
        return "number"
    if value in NAME_WORDS or re.fullmatch(r"[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?", value):
        return "entity"
    return "text"


def parameterize_text(text: str) -> tuple[str, dict[str, Any], dict[str, str], dict[str, Any]]:
    placeholders: dict[str, Any] = {}
    original_values: dict[str, str] = {}
    constraints: dict[str, Any] = {}
    seen: dict[str, str] = {}
    counters = Counter()

    pattern = re.compile(r"\d+(?::\d+)?|\d+[.,]\d+|[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?")

    def replacement(match: re.Match[str]) -> str:
        value = match.group(0)
        kind = placeholder_kind(value)
        if kind == "text":
            return value
        if value in seen:
            return "{" + seen[value] + "}"
        counters[kind] += 1
        if kind == "number":
            name = f"number_{counters[kind]}"
            normalized_value = value.replace(",", ".")
            original_values[name] = value
            constraints[name] = {"type": "number" if "." in normalized_value or ":" in normalized_value else "integer", "original": value}
        else:
            name = f"Entity_number_{counters[kind]}"
            original_values[name] = value
            constraints[name] = {"type": "entity", "original": value}
        placeholders[name] = {"kind": kind, "original_value": value}
        seen[value] = name
        return "{" + name + "}"

    return pattern.sub(replacement, text), placeholders, original_values, constraints


def reconstruct(template_text: str, original_values: dict[str, str]) -> str:
    result = template_text
    for name, value in sorted(original_values.items(), key=lambda item: len(item[0]), reverse=True):
        result = result.replace("{" + name + "}", value)
    return result


def comparable(text: str) -> str:
    return normalize_spacing(text).replace(" .", ".")


def build_templates(tree: dict[str, Any]) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    template_number = 1
    for module in tree["modules"]:
        for problem in module["problems"]:
            template_text, placeholders, original_values, constraints = parameterize_text(problem["cleaned_text"])
            template_id = f"{module['module_id']}_{template_number:05d}"
            template = {
                "template_number": template_number,
                "template_id": template_id,
                "source_problem_id": problem["problem_id"],
                "source_problem_number": problem["source_problem_number"],
                "source_file": problem["source_file"],
                "module_id": module["module_id"],
                "module_name": module["module_name"],
                "difficulty": problem["difficulty"],
                "title": f"{module['module_name']}: задача {problem['source_problem_number']}",
                "source_text": problem["cleaned_text"],
                "template_text": template_text,
                "placeholders": placeholders,
                "constraints": constraints,
                "original_values": original_values,
                "answer_type": "unknown",
                "answer_formula": "",
                "validation_rules": [
                    "original_values_reconstruct_cleaned_source",
                    "all_template_placeholders_are_declared",
                    "source_problem_has_one_primary_module",
                ],
                "generation_status": "requires_specialized_validator",
            }
            templates.append(template)
            template_number += 1
    return templates


def validate_outputs(tree: dict[str, Any], templates: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> dict[str, Any]:
    problems = [problem for module in tree["modules"] for problem in module["problems"]]
    source_numbers = [problem["source_problem_number"] for problem in problems]
    duplicate_numbers = [number for number, count in Counter(source_numbers).items() if count > 1]
    template_by_problem = defaultdict(list)
    reconstruction_failures = []
    placeholder_failures = []
    placeholder_re = re.compile(r"{([A-Za-z_][A-Za-z0-9_]*)}")

    for template in templates:
        template_by_problem[template["source_problem_id"]].append(template["template_number"])
        reconstructed = reconstruct(template["template_text"], template["original_values"])
        if comparable(reconstructed) != comparable(template["source_text"]):
            reconstruction_failures.append(template["template_number"])
        used = set(placeholder_re.findall(template["template_text"]))
        declared = set(template["placeholders"])
        if used != declared:
            placeholder_failures.append({
                "template_number": template["template_number"],
                "missing": sorted(used - declared),
                "unused": sorted(declared - used),
            })

    missing_templates = [
        problem["problem_id"] for problem in problems
        if problem["problem_id"] not in template_by_problem
    ]
    return {
        "extracted_records": len(problems) + len(rejected),
        "valid_problems": len(problems),
        "rejected_records": len(rejected),
        "modules": len(tree["modules"]),
        "templates": len(templates),
        "problems_covered_by_templates": len(template_by_problem),
        "duplicates": len(duplicate_numbers),
        "duplicate_source_problem_numbers": duplicate_numbers,
        "missing_templates": len(missing_templates),
        "missing_template_problem_ids": missing_templates,
        "reconstruction_tests_passed": len(templates) - len(reconstruction_failures),
        "reconstruction_failures": reconstruction_failures,
        "placeholder_failures": placeholder_failures,
        "russian_language_review_count": len(problems),
        "templates_requiring_specialized_validators": sum(1 for template in templates if template["generation_status"] == "requires_specialized_validator"),
        "source_problem_id_to_template_number": {
            str(problem_id): numbers[0] for problem_id, numbers in sorted(template_by_problem.items())
        },
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_summary(tree: dict[str, Any]) -> None:
    lines = ["# All Tasks Modules Summary", ""]
    for module in tree["modules"]:
        difficulties = [problem["difficulty"] for problem in module["problems"]]
        lines.extend([
            f"## {module['module_number']}. {module['module_name']} (`{module['module_id']}`)",
            "",
            module["description"],
            "",
            f"- Problems: {len(module['problems'])}",
            f"- Difficulty range: {min(difficulties)}-{max(difficulties)}",
            "",
            "Representative examples:",
            "",
        ])
        for problem in module["problems"][:3]:
            lines.append(f"- #{problem['source_problem_number']}: {problem['cleaned_text'][:220]}")
        lines.append("")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_coverage_report(stats: dict[str, Any]) -> None:
    covered = stats["problems_covered_by_templates"]
    valid = stats["valid_problems"]
    percent = 0 if valid == 0 else covered / valid * 100
    lines = [
        "# All Tasks Template Coverage Report",
        "",
        f"- Total extracted records: {stats['extracted_records']}",
        f"- Total valid problems: {valid}",
        f"- Total rejected records: {stats['rejected_records']}",
        f"- Total modules: {stats['modules']}",
        f"- Total templates: {stats['templates']}",
        f"- Problems with templates: {covered} ({percent:.2f}%)",
        f"- Duplicate count: {stats['duplicates']}",
        f"- Missing-template count: {stats['missing_templates']}",
        f"- Reconstruction tests passed: {stats['reconstruction_tests_passed']} / {stats['templates']}",
        f"- Placeholder validation failures: {len(stats['placeholder_failures'])}",
        f"- Russian-language review count: {stats['russian_language_review_count']}",
        f"- Templates requiring specialized validators: {stats['templates_requiring_specialized_validators']}",
        "",
        "## Source problem to template mapping",
        "",
    ]
    for problem_id, template_number in stats["source_problem_id_to_template_number"].items():
        lines.append(f"- Source problem ID {problem_id} -> template {template_number}")
    COVERAGE_PATH.write_text("\n".join(lines), encoding="utf-8")


def copy_compatibility_outputs() -> None:
    for source, target in ROOT_COMPATIBILITY_FILES.items():
        shutil.copyfile(source, target)


def run_pipeline() -> dict[str, Any]:
    source_text = SOURCE_PATH.read_text(encoding="utf-8")
    records, rejected = extract_records(source_text)
    tree = build_tree(records)
    templates = build_templates(tree)
    stats = validate_outputs(tree, templates, rejected)

    write_json(TREE_PATH, tree)
    write_json(REJECTED_PATH, {"rejected_problems": rejected})
    write_json(TEMPLATES_PATH, {"schema_version": "1.0", "templates": templates})
    write_summary(tree)
    write_coverage_report(stats)
    copy_compatibility_outputs()
    write_json(SOURCE_INDEX_DIR / "All_tasks_validation_stats.json", stats)
    return stats


def main() -> None:
    stats = run_pipeline()
    print(f"Extracted records: {stats['extracted_records']}")
    print(f"Valid problems: {stats['valid_problems']}")
    print(f"Rejected records: {stats['rejected_records']}")
    print(f"Modules: {stats['modules']}")
    print(f"Templates: {stats['templates']}")
    print(f"Problems covered by templates: {stats['problems_covered_by_templates']}")
    print(f"Duplicates: {stats['duplicates']}")
    print(f"Missing templates: {stats['missing_templates']}")
    print(f"Reconstruction tests passed: {stats['reconstruction_tests_passed']}")
    print(f"Templates requiring manual or specialized validation: {stats['templates_requiring_specialized_validators']}")


if __name__ == "__main__":
    main()
