"""Baixa o HMDA público (CFPB) de um ano, EUA inteiro, filtrado para pedidos FHA.

Uso, da raiz do projeto: python -m src.download_hmda
Depois, python -m src.raw_parquet grava o recorte em parquet que os notebooks leem.
"""

from pathlib import Path

import requests

from src.hmda import HMDA_CSV

YEAR = 2025
LOAN_TYPE_FHA = 2
URL = "https://ffiec.cfpb.gov/v2/data-browser-api/view/nationwide/csv"
OUT_FILE = HMDA_CSV
OUT_DIR = OUT_FILE.parent


def download(year: int = YEAR) -> Path:
    """Faz o download em streaming e grava em HMDA_DIR (ver src/hmda.py)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUT_FILE.with_suffix(".part")
    params = {"years": year, "loan_types": LOAN_TYPE_FHA}
    with requests.get(URL, params=params, stream=True, timeout=600) as r:
        r.raise_for_status()
        done = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=8 * 1024 * 1024):
                f.write(chunk)
                done += len(chunk)
                print(f"{done / 1e6:,.0f} MB", flush=True)
    tmp.replace(OUT_FILE)
    return OUT_FILE


if __name__ == "__main__":
    path = download()
    print(f"OK: {path} ({path.stat().st_size / 1e6:,.0f} MB)")
