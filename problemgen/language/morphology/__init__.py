"""Morphology blueprint.

Do not remove this docstring without replacing it with a stricter contract.
This package should resolve cases, gender, number and lexical forms.
"""

from .reviewed_characters import character_form, character_gender, personal_pronoun, supports_cases

__all__ = ["character_form", "character_gender", "personal_pronoun", "supports_cases"]
