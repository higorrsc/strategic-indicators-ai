"""Supported language locale value object for strategic intelligence."""

from __future__ import annotations

from enum import StrEnum


class SupportedLanguage(StrEnum):
    """Enumeration of supported language locales for AI and report generation."""

    PT_BR = "pt-br"
    EN_US = "en-us"

    @classmethod
    def from_string(cls, value: str) -> SupportedLanguage:
        """Parse string to SupportedLanguage case-insensitively.

        Args:
            value: Language code string (e.g. 'pt-br', 'en-us').

        Returns:
            SupportedLanguage: Matching language enum.

        Raises:
            ValueError: If unsupported language code is provided.
        """
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        msg = (
            f"Unsupported language '{value}'. "
            f"Supported options: {', '.join(m.value for m in cls)}."
        )
        raise ValueError(msg)
