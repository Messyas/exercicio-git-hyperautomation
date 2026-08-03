"""Page Objects da automação web."""

from src.pages.playwright_pages import (
    PlaywrightFormPage,
    PlaywrightLoginPage,
    RegistrationRejectedError,
)

__all__ = [
    "PlaywrightFormPage",
    "PlaywrightLoginPage",
    "RegistrationRejectedError",
]
