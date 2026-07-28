"""Машинные проверки падежей в реестрах персонажей, локаций и топонимов.

Правила ниже выполняются в русском языке без исключений, поэтому нарушение —
всегда ошибка в данных. Проверки появились после того, как наполнение реестра
скриптом дало «в Централ-Ситие», «в Крепосту одиночества» и «на рыноке
Забвения»: формы прошли все прежние тесты, потому что те не смотрят на язык.

Полностью заменить чтение выдачи глазами эти правила не могут — они закрывают
ровно те классы ошибок, которые уже случались.
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CASES = ("nom", "gen", "dat", "acc", "ins", "pre")
SPLIT = re.compile(r"[ \-]")
DATA = PROJECT_ROOT / "data" / "entities"
# Гласные, на которые в русском кончаются только несклоняемые слова.
INDECLINABLE_ENDINGS = "иуюэ"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def entries() -> list[tuple[str, str, dict, str | None]]:
    """Все записи с падежной парадигмой: (источник, id, формы, род)."""
    result: list[tuple[str, str, dict, str | None]] = []
    universes = load(DATA / "universes.json")
    for universe in universes["universes"]:
        for location in universe["locations"]:
            result.append(("локация", location["location_id"],
                           location["cases"], location.get("gender")))
    for name in ("approved_characters.json", "extended_characters.json", "common_names.json"):
        path = DATA / "characters" / name
        if not path.exists():
            continue
        payload = load(path)
        for person in payload.get("characters", payload.get("names", [])):
            result.append(("персонаж", person["character_id"],
                           person["cases"], person.get("gender")))
    toponyms = load(DATA / "toponyms.json")
    for toponym in toponyms["toponyms"]:
        result.append(("топоним", toponym["toponym_id"],
                       toponym["cases"], toponym.get("gender")))
    return result


class RegistryDeclensionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entries = entries()

    def test_registries_are_not_empty(self) -> None:
        self.assertGreater(len(self.entries), 500, "реестры не загрузились")

    def test_all_six_cases_present_and_trimmed(self) -> None:
        for source, key, cases, _ in self.entries:
            for case in CASES:
                self.assertIn(case, cases, f"{source} {key}: нет формы {case}")
                value = cases[case]
                self.assertTrue(str(value).strip(), f"{source} {key}: пустая форма {case}")
                self.assertEqual(value, value.strip(), f"{source} {key}: пробелы в {case}")

    def test_tail_on_indeclinable_vowel_never_changes(self) -> None:
        """Слово на -и, -у, -ю, -э не склоняется: «в Централ-Ситие» невозможно.

        Смотреть надо на последнюю часть: в «Ник Фьюри» склоняется имя,
        а фамилия остаётся, и это верно. Дефис разделяет так же, как пробел, —
        иначе «Ростов-на-Дону» попадёт под правило из-за хвоста «Дону».
        """
        for source, key, cases, _ in self.entries:
            forms = {cases[case] for case in CASES}
            if len(forms) == 1:
                continue  # несклоняемое целиком — проверять нечего
            tails = {SPLIT.split(cases[case])[-1] for case in CASES}
            head = SPLIT.split(cases["nom"])[-1]
            if head[-1] in INDECLINABLE_ENDINGS:
                self.assertEqual(
                    len(tails), 1,
                    f"{source} {key}: «{cases['nom']}» кончается на несклоняемую гласную, "
                    f"но формы различаются: {sorted(tails)}",
                )

    def test_third_declension_instrumental(self) -> None:
        """Женский род на -ь даёт творительный на -ью: «Крепостью», не «Крепостом».

        Правило про хвост имени, поэтому неизменяемый хвост под него не попадает:
        в «матушке Готель» склоняется только первое слово.
        """
        for source, key, cases, gender in self.entries:
            forms = {cases[case] for case in CASES}
            tails = {SPLIT.split(cases[case])[-1] for case in CASES}
            if gender != "f" or len(forms) == 1 or len(tails) == 1:
                continue
            if SPLIT.split(cases["nom"])[-1].endswith("ь"):
                self.assertTrue(
                    SPLIT.split(cases["ins"])[-1].endswith("ью"),
                    f"{source} {key}: творительный «{cases['ins']}» при именительном "
                    f"«{cases['nom']}» — третье склонение требует -ью",
                )

    def test_fleeting_vowel_in_ok_endings(self) -> None:
        """Многосложные слова на -ок теряют гласную: замок -> замка.

        Ловит «в замоке Данброх» и «в Полицейском участоке»: механическое
        приписывание окончания к основе даёт лишний слог.

        Только -ок: в -ек гласная беглая не всегда, и «Дровосека» с «человека»
        правило записало бы в ошибки. Список исключений держит слова, где
        и -ок не беглое.
        """
        # Сравнение по концу слова, а не по равенству: «Владивосток» тоже «восток».
        keep = ("поток", "виток", "исток", "восток", "ток", "сок", "бок", "рок", "срок")
        for source, key, cases, _ in self.entries:
            for index, part in enumerate(SPLIT.split(cases["nom"])):
                lowered = part.lower()
                if not lowered.endswith("ок") or lowered.endswith(keep):
                    continue
                if len(re.findall(r"[аеёиоуыэюя]", lowered)) < 2:
                    continue
                genitive = SPLIT.split(cases["gen"])
                if index >= len(genitive):
                    continue
                self.assertNotEqual(
                    genitive[index], part + "а",
                    f"{source} {key}: «{cases['gen']}» — у слова «{part}» "
                    "гласная беглая, родительный кончается на -ка",
                )

    def test_soft_adjective_prepositional(self) -> None:
        """Мягкое прилагательное на -нее даёт предложный на -нем: в Дальнем болоте."""
        for source, key, cases, _ in self.entries:
            parts = SPLIT.split(cases["nom"])
            prepositional = SPLIT.split(cases["pre"])
            for index, part in enumerate(parts):
                if not part.lower().endswith("нее") or index >= len(prepositional):
                    continue
                self.assertFalse(
                    prepositional[index].lower().endswith("ном"),
                    f"{source} {key}: «{cases['pre']}» — «{part}» мягкое, "
                    "предложный кончается на -нем",
                )

    def test_no_part_of_a_name_grows_implausibly(self) -> None:
        """Ни одна часть имени не удлиняется больше чем на три буквы.

        Русское окончание короткое: «Робин» -> «Робином» это плюс два. Правило
        считается по частям, а не по строке целиком: у «Кристофера Робина»
        растут обе половины, и суммарный прирост ничего не означает.
        """
        for source, key, cases, _ in self.entries:
            base = [len(part) for part in SPLIT.split(cases["nom"])]
            for case in CASES:
                parts = SPLIT.split(cases[case])
                if len(parts) != len(base):
                    continue  # состав имени по падежам не меняется — это ловит другой тест
                for was, part in zip(base, parts):
                    self.assertLessEqual(
                        len(part) - was, 3,
                        f"{source} {key}: в форме {case} часть «{part}» неправдоподобно "
                        f"длиннее исходной ({was} букв) — «{cases['nom']}»",
                    )


if __name__ == "__main__":
    unittest.main()
