"""Page Objects da automação web."""

from src.pages.formulario_lotes_page import PlaywrightFormularioLotesPage
from src.pages.playwright_pages import (
    PlaywrightFormPage,
    PlaywrightLoginPage,
    RegistrationRejectedError,
)

__all__ = [
    "PlaywrightFormPage",
    "PlaywrightFormularioLotesPage",
    "PlaywrightLoginPage",
    "RegistrationRejectedError",
]
