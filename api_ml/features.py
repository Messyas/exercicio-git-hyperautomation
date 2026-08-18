import re
import unicodedata

FEATURE_ORDER = ("status_raw", "turno", "tem_obs")


def normalizar_status_raw(value: str) -> str:
    """Normaliza o status raw removendo acentos, espaços extras e convertendo para maiúsculas."""
    if not value:
        return ""
    # Converte para maiúsculas e remove acentos
    text = value.strip().upper()
    nfkd_form = unicodedata.normalize("NFKD", text)
    text_without_accents = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Remove múltiplos espaços
    normalized = re.sub(r"\s+", " ", text_without_accents)
    return normalized.strip()
