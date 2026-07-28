"""Page Objects de Playwright e Selenium."""

from .playwright_pages import PlaywrightFormPage, PlaywrightLoginPage
from .selenium_pages import SeleniumFormPage, SeleniumLoginPage

__all__ = [
    "PlaywrightFormPage",
    "PlaywrightLoginPage",
    "SeleniumFormPage",
    "SeleniumLoginPage",
]
