"""Leitura e rótulos do NSMO Public Use File v70 (FHFA e CFPB)."""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# Fica junto da cópia obrigatória dos Terms of Service da FHFA.
NSMO_DIR = Path(os.getenv("LARGE_DATA_DIR", ROOT / "data" / "raw")) / "nsmo"
NSMO_CSV = NSMO_DIR / "nsmo_v70_1324_puf.csv"
NSMO_TERMS = NSMO_DIR / "nsmo_terms_of_service.pdf"

DISCLAIMER = (
    "The opinions and analyses contained herein are solely of the users/authors of any "
    "data analyses or papers, and the FHFA cannot and does not attest to nor vouch for "
    "the quality, accuracy, or timeliness of the data, or analyses derived from these "
    "data after the data has been retrieved from FHFA.gov."
)

COLUMNS = [
    "nsmoid",
    "survey_wave",
    "open_year",
    "loan_type",
    "dti",
    "pti",
    "ltv",
    "cltv",
    "score_orig_r",
    "score_orig_s",
    "score_orig_o1",
    "score_orig_o2",
    "score_orig_o3",
    "x5001",
    "x36c",
    "x36d",
]

LOAN_TYPE_FHA = 2

# Códigos especiais do codebook (Appendix C).
MISSING_CODES = {-2: "não se aplica", -3: "não perguntado na onda", -4: "ausente"}

X5001 = {
    1: "menos de 1 mês",
    2: "1 a 2 meses",
    3: "3 a 6 meses",
    4: "7 meses ou mais",
}

# Origem do dinheiro da compra, perguntada só a quem comprou (ondas 7 a 46):
# x36c = ajuda ou empréstimo de órgão público ou entidade sem fins lucrativos;
# x36d = segundo financiamento, home equity ou HELOC.
X36 = {1: "usou", 2: "não usou"}


def load_nsmo(path: Path = NSMO_CSV) -> pd.DataFrame:
    """Lê o CSV da NSMO só com as colunas de COLUMNS."""
    return pd.read_csv(path, usecols=COLUMNS)
