"""Leitura e rótulos do NSMO Public Use File v70 (FHFA e CFPB)."""

import os
import shutil
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# CSV baixado da FHFA, grande demais para o repo: fica em LARGE_DATA_DIR (.env) ou em
# data/raw, junto da cópia dos Terms of Service salva no download.
NSMO_DIR = Path(os.getenv("LARGE_DATA_DIR", ROOT / "data" / "raw")) / "nsmo"
NSMO_CSV = NSMO_DIR / "nsmo_v70_1324_puf.csv"
NSMO_TERMS_DOWNLOADED = NSMO_DIR / "nsmo_terms_of_service.pdf"

# Recorte com as colunas de COLUMNS, em parquet, versionado no repo. Os termos da FHFA
# exigem a cópia do Agreement junto do dado, por isso ela vai para a mesma pasta.
NSMO_REPO_DIR = ROOT / "data" / "raw" / "nsmo"
NSMO_PARQUET = NSMO_REPO_DIR / "nsmo_v70_1324_puf.parquet"
NSMO_TERMS = NSMO_REPO_DIR / "nsmo_terms_of_service.pdf"

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
    "x33",
    "cashout",
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

# Finalidade declarada na pesquisa (x33) e marca de refinanciamento com saque (cashout,
# 1 = com saque), calculada pela NMDB comparando a dívida nova com a antiga.
X33 = {
    1: "compra",
    2: "refinanciamento",
    3: "inclusão ou retirada de co-tomador",
    4: "construção",
    5: "imóvel quitado",
}
CASHOUT_YES = 1

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


def save_nsmo_parquet(
    csv_path: Path = NSMO_CSV, parquet_path: Path = NSMO_PARQUET
) -> Path:
    """Grava o recorte em parquet e copia os Terms of Service para a mesma pasta."""
    nsmo = pd.read_csv(csv_path, usecols=COLUMNS)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    nsmo.to_parquet(parquet_path, index=False)
    shutil.copyfile(NSMO_TERMS_DOWNLOADED, parquet_path.parent / NSMO_TERMS.name)
    return parquet_path


def load_nsmo(path: Path = NSMO_PARQUET) -> pd.DataFrame:
    """Lê o recorte da NSMO em parquet."""
    return pd.read_parquet(path)
