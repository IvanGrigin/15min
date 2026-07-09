"""Полная морфологическая парадигма существительного для русскоязычных шаблонов задач."""
from __future__ import annotations

from dataclasses import dataclass

_VALID_CASES = frozenset({
    "nom", "gen", "dat", "acc", "ins", "pre",
    "nom_pl", "gen_pl", "dat_pl", "acc_pl", "ins_pl", "pre_pl",
})


@dataclass(frozen=True)
class RussianNoun:
    """Полная шестипадежная парадигма русского существительного.

    Все 12 форм задаются явно, без автоматического склонения — это гарантирует
    корректность для слов с нестандартными формами (год→лет, кур→кур, человек→людей).

    Примеры:
        >>> год = RussianNoun("год","года","году","год","годом","годе",
        ...                   "года","лет","годам","годы","годами","годах","m")
        >>> год.get_case("gen_pl")
        'лет'
        >>> год.count_forms()
        ('год', 'года', 'лет')
    """

    # Единственное число (singularis)
    nom: str   # именительный — кот
    gen: str   # родительный — кота
    dat: str   # дательный — коту
    acc: str   # винительный — кота
    ins: str   # творительный — котом
    pre: str   # предложный — коте

    # Множественное число (pluralis)
    nom_pl: str   # именительный — коты
    gen_pl: str   # родительный — котов
    dat_pl: str   # дательный — котам
    acc_pl: str   # винительный — котов
    ins_pl: str   # творительный — котами
    pre_pl: str   # предложный — котах

    # Грамматические свойства
    gender: str   # "m" мужской, "f" женский, "n" средний
    animate: bool = False

    # Переопределение форм счёта для нестандартных слов (мороженое, пальто и др.)
    # Пустая строка означает «использовать стандартную форму».
    count_one: str = ""   # при n=1  (по умолчанию — nom)
    count_few: str = ""   # при n=2–4 (по умолчанию — gen)
    count_many: str = ""  # при n=5+  (по умолчанию — gen_pl)

    def count_forms(self) -> tuple[str, str, str]:
        """Формы для счёта: (1, 2–4, 5+).

        В русском языке числительное управляет падежом существительного:
          1 год  (именительный ед.ч. — nom)
          2 года (родительный ед.ч. — gen)
          5 лет  (родительный мн.ч. — gen_pl)
        Для нестандартных слов используются переопределения count_one/few/many.
        """
        return (
            self.count_one or self.nom,
            self.count_few or self.gen,
            self.count_many or self.gen_pl,
        )

    def get_case(self, case: str) -> str:
        """Вернуть словоформу по названию падежа."""
        if case not in _VALID_CASES:
            raise ValueError(
                f"Неизвестный падеж: '{case}'. "
                f"Допустимые: {sorted(_VALID_CASES)}"
            )
        return getattr(self, case)
