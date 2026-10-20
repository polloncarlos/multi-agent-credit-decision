"""Leitura e rótulos do HMDA público (CFPB), dicionário de 2018 em diante."""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# Arquivo grande demais para o repo: fica em LARGE_DATA_DIR (.env) ou em data/raw.
HMDA_DIR = Path(os.getenv("LARGE_DATA_DIR", ROOT / "data" / "raw")) / "hmda"
HMDA_CSV = HMDA_DIR / "hmda_2025_fha.csv"

# Campos usados no Data Understanding: decisão, motivos e o que a norma cita.
COLUMNS = [
    "lei",
    "state_code",
    "action_taken",
    "preapproval",
    "loan_purpose",
    "lien_status",
    "occupancy_type",
    "total_units",
    "loan_amount",
    "loan_to_value_ratio",
    "property_value",
    "income",
    "debt_to_income_ratio",
    "applicant_credit_score_type",
    "aus-1",
    "denial_reason-1",
    "denial_reason-2",
    "denial_reason-3",
    "denial_reason-4",
]

ACTION_TAKEN = {
    "1": "originado",
    "2": "aprovado, não aceito",
    "3": "negado",
    "4": "retirado pelo cliente",
    "5": "fechado por incompletude",
    "6": "comprado de terceiro",
    "7": "pré aprovação negada",
    "8": "pré aprovação aprovada, não aceita",
}

DENIAL_REASON = {
    "1": "DTI",
    "2": "histórico de emprego",
    "3": "histórico de crédito",
    "4": "garantia (imóvel)",
    "5": "recursos insuficientes",
    "6": "informação não verificável",
    "7": "cadastro incompleto",
    "8": "seguro hipotecário negado",
    "9": "outro",
    "10": "não se aplica",
    "1111": "isento (banco dispensado de informar)",
}

LOAN_PURPOSE = {
    "1": "compra",
    "2": "reforma",
    "31": "refinanciamento sem saque",
    "32": "refinanciamento com saque",
    "4": "outro",
    "5": "não se aplica",
}

OCCUPANCY = {"1": "residência principal", "2": "segunda residência", "3": "investimento"}

LIEN = {"1": "primeira hipoteca", "2": "hipoteca subordinada"}

PREAPPROVAL = {"1": "pedida", "2": "não pedida"}

CREDIT_SCORE_TYPE = {
    "1": "Equifax Beacon 5.0",
    "2": "Experian Fair Isaac",
    "3": "FICO Classic 04",
    "4": "FICO Classic 98",
    "5": "VantageScore 2.0",
    "6": "VantageScore 3.0",
    "7": "mais de um modelo",
    "8": "outro modelo",
    "9": "não se aplica",
    "1111": "isento",
}

# Motivos que dependem de dado ausente do HMDA público (saem da avaliação).
DENIAL_INVISIBLE = {"2", "3", "6"}
# Motivos com algum campo correspondente no HMDA (DTI e valor financiado).
DENIAL_VISIBLE = {"1", "4"}

# Ordem das faixas de DTI como o HMDA publica (36 a 49 vêm como valor individual).
DTI_ORDER = (
    ["<20%", "20%-<30%", "30%-<36%"]
    + [str(v) for v in range(36, 50)]
    + ["50%-60%", ">60%", "NA", "Exempt"]
)


def load_hmda(path: Path = HMDA_CSV, nrows: int | None = None) -> pd.DataFrame:
    """Lê o CSV do HMDA só com as colunas de COLUMNS, tudo como texto."""
    return pd.read_csv(path, usecols=COLUMNS, dtype=str, nrows=nrows)


def dti_band(dti: pd.Series) -> pd.Series:
    """Agrupa as faixas publicadas em: até 43, 44 a 49, 50 a 60, acima de 60."""
    numeric = pd.to_numeric(dti, errors="coerce")
    band = pd.Series(pd.NA, index=dti.index, dtype="object")
    band[dti.isin(["<20%", "20%-<30%", "30%-<36%"]) | (numeric <= 43)] = "até 43"
    band[(numeric >= 44) & (numeric <= 49)] = "44 a 49"
    band[dti == "50%-60%"] = "50 a 60"
    band[dti == ">60%"] = "acima de 60"
    return band


def dti_above(dti: pd.Series, limit: int = 43) -> pd.Series:
    """True se a faixa de DTI publicada está inteira acima de `limit` (NA vira NaN)."""
    numeric = pd.to_numeric(dti, errors="coerce")
    above = numeric > limit
    above[dti.isin(["50%-60%", ">60%"])] = True
    above[dti.isin(["<20%", "20%-<30%", "30%-<36%"])] = False
    return above.where(dti.isin(DTI_ORDER[:-2]))
