"""Acesso ao texto do HUD Handbook 4000.1 (PDF oficial, domínio público)."""

import difflib
import json
import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

HANDBOOK_DIR = Path(os.getenv("LARGE_DATA_DIR", ROOT / "data" / "raw")) / "handbook"
HANDBOOK = {
    # Versões antigas, do arquivo histórico do HUD (período dos empréstimos da NSMO).
    # A de 12/2016 vigorou até 03/2019; o arquivo não tem versões de 2017 e 2018.
    "2016_12": HANDBOOK_DIR / "HB-4000-1-2016-12-30.pdf",
    "2019_03":HANDBOOK_DIR / "HB-4000-1-2019-03-27.pdf",
    "2019_07": HANDBOOK_DIR / "HB-4000-1-2019-07-10.pdf",
    "2019_08": HANDBOOK_DIR / "HB-4000-1-2019-08-14.pdf",
    "2019_10": HANDBOOK_DIR / "HB-4000-1-2019-10-24.pdf",
    "2019_12": HANDBOOK_DIR / "HB-4000-1-2019-12-16.pdf",
    "2020_11": HANDBOOK_DIR / "HB-4000-1-2020-11-18.pdf",
    "update_17": HANDBOOK_DIR / "40001-hsgh-Update-17.pdf",  # publicado 2025-11-26
    "update_18": HANDBOOK_DIR / "40001-hsgh-Update-18.pdf",  # publicado 2026-08-12
}

# Cabeçalho de página das versões de 2016 a 2020, que _body não remove.
OLD_HEADER = r"II\. ORIGINATION THROUGH .*? specific sections’ effective dates "


@lru_cache(maxsize=9)
def pages(version: str = "update_18") -> tuple[str, ...]:
    """Texto de todas as páginas do PDF, na ordem (lido do cache em disco se existir)."""
    cache_file = HANDBOOK[version].with_suffix(".pages.json")
    if cache_file.exists():
        texts = json.loads(cache_file.read_text(encoding="utf-8"))
        return tuple(texts)

    reader = PdfReader(HANDBOOK[version])
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    cache_file.write_text(json.dumps(texts), encoding="utf-8")
    return tuple(texts)


def _body(text: str) -> str:
    """Remove o cabeçalho repetido da página (até a linha 'Last Revised')."""
    lines = text.splitlines()
    for i, line in enumerate(lines[:10]):
        if line.startswith("Last Revised"):
            return "\n".join(lines[i + 1 :])
    return text


def find_section(heading: str, version: str = "update_18") -> tuple[int, str]:
    """Página (1-based) onde `heading` abre uma linha, com o texto dela e da seguinte."""
    all_pages = pages(version)
    for n, text in enumerate(all_pages, start=1):
        for line in text.splitlines():
            if line.strip().startswith(heading):
                following = all_pages[n] if n < len(all_pages) else ""
                return n, _body(text) + "\n" + _body(following)
    raise ValueError(f"seção não encontrada: {heading}")


def excerpt(text: str, start: str, end: str | None = None) -> str:
    """Trecho de `text` entre as linhas que começam com `start` e `end`."""
    i = text.index(start)
    j = text.index(end, i) if end else len(text)
    return text[i:j].strip()


def section_text(version: str, start: str, end: str) -> str:
    """Trecho entre `start` e `end` numa linha só, em minúsculas e sem formatação."""
    full = "\n".join(_body(p) for p in pages(version))
    i = full.index(start)
    j = full.index(end, i)
    text = re.sub(r"\s+", " ", full[i:j])
    text = re.sub(OLD_HEADER, "", text)  # cabeçalho das versões antigas
    text = re.sub(r"\([A-F]\) ", "", text)  # letras que só as versões novas usam
    text = text.replace("V A", "VA")  # artefato da extração do PDF
    return text.lower().strip()


def changed_sentences(old: str, new: str, start: str, end: str) -> list[str]:
    """Frases do trecho que mudaram entre duas versões ('-' antiga, '+' nova)."""
    old_sentences = re.split(r"(?<=[.;:])\s+", section_text(old, start, end))
    new_sentences = re.split(r"(?<=[.;:])\s+", section_text(new, start, end))
    changed = []
    for line in difflib.unified_diff(old_sentences, new_sentences, lineterm="", n=0):
        is_file_header = line.startswith("---") or line.startswith("+++")
        if line[:1] in "+-" and not is_file_header:
            changed.append(line)
    return changed
