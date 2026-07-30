"""Проверки реестра вселенных: локации, предметы и их связь с персонажами."""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.russian.characters import COMMON_POOL, characters_by_universe  # noqa: E402
from problemgen.russian.noun_dict import NOUNS  # noqa: E402
from problemgen.russian.universes import (  # noqa: E402
    age_rating_options,
    audience_options,
    load_universes,
    locations_of,
    universe_groups,
    universes_in_group,
    universes_matching,
)
from problemgen.template_studio.runtime import generate_active_template  # noqa: E402

CASES = ("nom", "gen", "dat", "acc", "ins", "pre")


class UniverseRegistryTests(unittest.TestCase):
    def test_every_universe_has_locations_and_items(self) -> None:
        for name, universe in load_universes().items():
            self.assertTrue(universe.locations, f"{name}: нет локаций")
            self.assertGreaterEqual(len(universe.items), 3, f"{name}: слишком мало предметов")

    def test_locations_have_full_paradigm_and_preposition(self) -> None:
        for name, universe in load_universes().items():
            for location in universe.locations:
                for case in CASES:
                    self.assertTrue(location.get_case(case).strip(), f"{location.location_id}: пустой {case}")
                self.assertIn(location.preposition, {"в", "на"}, location.location_id)
                self.assertIn(location.gender, {"m", "f", "n"}, location.location_id)
                self.assertEqual(
                    location.get_case("loc"),
                    f"{location.preposition} {location.pre}",
                    f"{location.location_id}: слот loc обязан склеивать предлог с предложным падежом",
                )
            self.assertEqual(
                len({location.location_id for location in universe.locations}),
                len(universe.locations),
                f"{name}: повторяющиеся location_id",
            )

    def test_items_are_known_and_countable(self) -> None:
        """Предмет вселенной попадает в счётный слот, поэтому «5 мёдов» недопустимо."""
        for name, universe in load_universes().items():
            for item in universe.items:
                self.assertIn(item, NOUNS, f"{name}: {item} нет в словаре существительных")
                self.assertTrue(NOUNS[item].countable, f"{name}: {item} — вещественное, его нельзя считать")

    def test_groups_are_declared_and_non_empty(self) -> None:
        groups = universe_groups()
        self.assertTrue(groups)
        for key in groups:
            self.assertTrue(universes_in_group(key), f"группа {key} пуста")
        for name, universe in load_universes().items():
            self.assertIn(universe.group, groups, f"{name}: неизвестная группа {universe.group}")

    def test_every_described_universe_has_characters(self) -> None:
        """Локации и предметы без персонажей бесполезны — шаблон не соберётся."""
        by_universe = characters_by_universe()
        for name in load_universes():
            self.assertIn(name, by_universe, f"{name}: описана в universes.json, но персонажей нет")
            self.assertGreaterEqual(len(by_universe[name]), 6, f"{name}: меньше шести персонажей")

    def test_every_character_universe_is_described(self) -> None:
        described = set(load_universes())
        for universe in characters_by_universe():
            if universe == COMMON_POOL:
                continue  # обычные имена не привязаны к миру: ни локаций, ни предметов у них нет
            self.assertIn(universe, described, f"{universe}: есть персонажи, но нет локаций и предметов")


class PrepositionSlotTests(unittest.TestCase):
    def test_location_separates_where_from_where_to(self) -> None:
        """«где» и «куда» — разные падежи при одном предлоге."""
        place = locations_of("Гарри Поттер")[0]
        self.assertEqual(place.get_case("loc"), f"{place.preposition} {place.pre}")
        self.assertEqual(place.get_case("dir"), f"{place.preposition} {place.acc}")
        self.assertNotEqual(place.get_case("loc"), place.get_case("dir"))

    def test_unknown_case_is_rejected(self) -> None:
        place = locations_of("Смешарики")[0]
        with self.assertRaises(ValueError):
            place.get_case("nom_pl")

    def test_s_or_so_follows_the_consonant_cluster_rule(self) -> None:
        from problemgen.russian.template_engine import _s_or_so

        for form, expected in (
            ("Свеном", "со"), ("Знайкой", "со"), ("шляпой", "со"), ("Шреком", "со"),
            ("Змеем Горынычем", "со"), ("мной", "со"),
            ("Нюшей", "с"), ("Кристоффом", "с"), ("Симкой", "с"),
            ("зеркалом", "с"), ("жабой", "с"), ("сундуком", "с"),
        ):
            self.assertEqual(_s_or_so(form), expected, form)


class ExtendedRegistryTests(unittest.TestCase):
    def test_character_ids_are_unique_across_all_pools(self) -> None:
        identifiers = [
            character.character_id
            for characters in characters_by_universe().values()
            for character in characters
        ]
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_indeclinable_characters_really_have_one_form(self) -> None:
        for characters in characters_by_universe().values():
            for character in characters:
                forms = {character.get_case(case) for case in CASES}
                if character.indeclinable:
                    self.assertEqual(len(forms), 1, f"{character.nom}: помечен несклоняемым, но склоняется")
                else:
                    self.assertGreater(len(forms), 1, f"{character.nom}: склоняемый, но все формы совпали")

    def test_same_name_may_live_in_different_universes(self) -> None:
        """Осёл есть и в «Шреке», и у бременских музыкантов — это разные персонажи."""
        by_name: dict[str, set[str]] = {}
        for characters in characters_by_universe().values():
            for character in characters:
                by_name.setdefault(character.nom, set()).add(character.universe)
        shared = {name: universes for name, universes in by_name.items() if len(universes) > 1}
        for name, universes in shared.items():
            self.assertGreaterEqual(len(universes), 2, name)
        self.assertIn("Осёл", shared)


class UniverseSlotIntegrationTests(unittest.TestCase):
    TEMPLATE = {
        "candidate_template_text": (
            "{hero:nom} и {friend:nom} встретились {place:loc}. "
            "{hero:nom} {hero:g,принёс|принесла} {item:count,n}, а {friend:nom} — ещё {k}. "
            "Сколько всего {item:gen_pl} стало?"
        ),
        "parameter_schema": {
            "hero": {"type": "character"},
            "friend": {"type": "character"},
            "place": {"type": "location"},
            "item": {"type": "noun", "from_universe_items": True},
            "n": {"type": "integer", "min": 2, "max": 9},
            "k": {"type": "integer", "min": 2, "max": 9},
        },
        "derived_values": {"total": "n + k"},
        "constraints": [],
        "answer_expression": "total",
        "answer_type": "integer",
    }

    def test_place_characters_and_items_come_from_one_universe(self) -> None:
        by_universe = load_universes()
        for seed in range(40):
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            universe = values["hero"].universe
            self.assertEqual(values["friend"].universe, universe, f"seed {seed}: персонажи из разных миров")
            self.assertEqual(values["place"].universe, universe, f"seed {seed}: локация из чужого мира")
            self.assertIn(values["item"].nom, by_universe[universe].items, f"seed {seed}: предмет из чужого мира")
            self.assertNotEqual(values["hero"].character_id, values["friend"].character_id, f"seed {seed}")

    def test_rendered_text_is_clean(self) -> None:
        for seed in range(40):
            text = generate_active_template(self.TEMPLATE, random.Random(seed))["rendered_problem"]
            self.assertNotIn("{", text, f"seed {seed}")
            self.assertNotIn("  ", text, f"seed {seed}")
            self.assertTrue(text[0].isupper(), f"seed {seed}: {text[:30]}")

    def test_lowercase_names_stay_lowercase_inside_the_sentence(self) -> None:
        """«пёс Шарик» в середине предложения остаётся строчным, в начале — заглавным."""
        seen_inner = False
        for seed in range(120):
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            friend = generated["parameters"]["friend"]
            if not friend.lowercase_start:
                continue
            seen_inner = True
            self.assertIn(f"а {friend.nom} —", generated["rendered_problem"], f"seed {seed}")
        self.assertTrue(seen_inner, "за 120 сидов не встретилось имени со строчной буквы")


if __name__ == "__main__":
    unittest.main()


class ToponymRegistryTests(unittest.TestCase):
    """Города: падежи, предлоги и часовые пояса."""

    def test_every_toponym_has_full_paradigm(self) -> None:
        from problemgen.russian.toponyms import load_toponyms

        for toponym in load_toponyms():
            for case in CASES:
                self.assertTrue(toponym.get_case(case).strip(), f"{toponym.toponym_id}: {case}")
            self.assertIn(toponym.preposition, {"в", "на"}, toponym.toponym_id)
            self.assertIn(toponym.gender, {"m", "f", "n"}, toponym.toponym_id)

    def test_no_y_after_velars_and_hushing(self) -> None:
        """После к, г, х, ж, ш, ч, щ пишется -и: «с Камчатки», а не «с Камчаткы»."""
        from problemgen.russian.toponyms import load_toponyms

        for toponym in load_toponyms():
            for case in ("nom", "gen"):
                value = toponym.get_case(case)
                if len(value) > 1 and value.endswith("ы"):
                    self.assertNotIn(
                        value[-2], "кгхжшчщ",
                        f"{toponym.toponym_id}.{case}={value!r}: после {value[-2]!r} пишется -и",
                    )

    def test_paired_preposition_is_derived_not_stored(self) -> None:
        """«в» даёт «из», «на» даёт «с» — правило без исключений."""
        from problemgen.russian.toponyms import load_toponyms

        for toponym in load_toponyms():
            expected = "из" if toponym.preposition == "в" else "с"
            self.assertTrue(
                toponym.get_case("from").startswith(expected),
                f"{toponym.toponym_id}: {toponym.get_case('from')}",
            )

    def test_v_or_vo_follows_the_consonant_cluster(self) -> None:
        from problemgen.russian.toponyms import load_toponyms

        by_name = {toponym.nom: toponym for toponym in load_toponyms()}
        self.assertEqual(by_name["Владивосток"].get_case("dir"), "во Владивосток")
        self.assertEqual(by_name["Воронеж"].get_case("dir"), "в Воронеж")

    def test_time_zones_are_real(self) -> None:
        """Разница поясов берётся из данных, поэтому задача не врёт о географии."""
        from problemgen.russian.toponyms import hours_between, load_toponyms

        by_name = {toponym.nom: toponym for toponym in load_toponyms()}
        self.assertEqual(hours_between(by_name["Москва"], by_name["Хабаровск"]), 7)
        self.assertEqual(hours_between(by_name["Хабаровск"], by_name["Москва"]), -7)
        self.assertEqual(hours_between(by_name["Калининград"], by_name["Камчатка"]), 10)


class ValuablesAndCurrencyTests(unittest.TestCase):
    """Ценности и деньги мира: пираты делят дублоны, а не шоколадки."""

    def test_every_universe_has_currency_and_valuables(self) -> None:
        for name, universe in load_universes().items():
            self.assertTrue(universe.currency, f"{name}: не задана валюта")
            self.assertTrue(universe.valuables, f"{name}: не заданы ценности")

    def test_all_are_known_and_countable(self) -> None:
        for name, universe in load_universes().items():
            for word in universe.currency + universe.valuables:
                self.assertIn(word, NOUNS, f"{name}: {word} нет в словаре")
                self.assertTrue(NOUNS[word].countable, f"{name}: {word} вещественное, его не делят")

    def test_distinctive_worlds_have_their_own_money(self) -> None:
        """Смысл слоя: у мира со своей валютой она и должна использоваться."""
        from problemgen.russian.universes import currency_of

        self.assertIn("дублон", currency_of("Пираты Карибского моря"))
        self.assertIn("кредит", currency_of("Звёздные войны"))
        self.assertIn("галлеон", currency_of("Гарри Поттер"))
        self.assertIn("изумруд", currency_of("Волшебник Изумрудного города / Страна Оз"))

    def test_money_template_uses_the_money_of_its_world(self) -> None:
        from scripts.seed_worksheet_templates import load_library
        from problemgen.russian.universes import currency_of

        template = {item["template_id"]: item for item in load_library()}["money_equalize_pair"]
        for seed in range(60):
            generated = generate_active_template(template, random.Random(seed))
            universe = generated["parameters"]["giver"].universe
            self.assertIn(
                generated["parameters"]["coin"].nom, currency_of(universe),
                f"seed {seed}: {universe}",
            )


class AgeRatingAndAudienceTests(unittest.TestCase):
    """Сеттинг: возрастной рейтинг и мягкое предпочтение по вкусу.

    Оба поля обязательны для загрузки (см. load_universes), но здесь это
    проверяется отдельно и по существу: рейтинг из объявленной шкалы,
    «Обычные имена» — низший рейтинг и нейтральная аудитория, потому что
    на этом держится рассуждение в runtime.py о том, что суженный сеттинг
    почти никогда не остаётся без единой подходящей вселенной.
    """

    def test_every_universe_has_a_valid_rating_and_audience(self) -> None:
        ratings = set(age_rating_options())
        audiences = set(audience_options())
        for name, universe in load_universes().items():
            self.assertIn(universe.age_rating, ratings, name)
            self.assertIn(universe.audience, audiences, name)

    def test_ordinary_names_are_the_universal_fallback(self) -> None:
        """0+ и «любая аудитория»: любой сеттинг обязан её пропускать."""
        registry = load_universes()
        self.assertEqual(registry["Обычные имена"].age_rating, "0+")
        self.assertEqual(registry["Обычные имена"].audience, "any")

    def test_rating_ceiling_is_cumulative(self) -> None:
        """Вселенные 0+ — подмножество 6+, а те — подмножество 12+."""
        rating_0 = set(universes_matching(max_age_rating="0+"))
        rating_6 = set(universes_matching(max_age_rating="6+"))
        rating_12 = set(universes_matching(max_age_rating="12+"))
        self.assertTrue(rating_0)
        self.assertTrue(rating_0 <= rating_6 <= rating_12)
        self.assertEqual(rating_12, set(load_universes()), "12+ должен покрывать все вселенные")

    def test_audience_filter_always_includes_neutral_worlds(self) -> None:
        """«Только девочкам» — это girls плюс any, а не только girls."""
        neutral = {name for name, universe in load_universes().items() if universe.audience == "any"}
        girls_filtered = set(universes_matching(audience="girls"))
        self.assertTrue(neutral <= girls_filtered)
        self.assertTrue(girls_filtered - neutral, "girls-вселенные не найдены вовсе")

    def test_unknown_values_are_rejected(self) -> None:
        from problemgen.russian.universes import UniverseRegistryError

        with self.assertRaises(UniverseRegistryError):
            universes_matching(max_age_rating="взрослый")
        with self.assertRaises(UniverseRegistryError):
            universes_matching(audience="кто угодно")
