"""Perfil do caso em texto, o que o agente lê sobre o pedido.

HMDA e NSMO saem com os mesmos campos, na mesma ordem e no mesmo formato. Campo que a
base não traz aparece como "não informado". Nunca entram a decisão do banco, o motivo da
negativa, o banco nem o nome da base. Os campos preenchidos ainda mostram de qual base
vem o caso, então o prompt não pode citar as bases (notebook 02, seção 8.1).
"""

import math

from src.hmda import LIEN, LOAN_PURPOSE, OCCUPANCY
from src.nsmo import CASHOUT_YES, X5001

NOT_INFORMED = "não informado"

FIELDS = [
    "Finalidade",
    "Valor do empréstimo",
    "Valor do imóvel",
    "Renda anual",
    "DTI",
    "PTI",
    "CLTV",
    "Score de crédito",
    "Reserva após o fechamento",
    "Ocupação",
    "Posição da hipoteca",
    "Unidades",
]

# Faixas de DTI que o HMDA publica, escritas por extenso.
DTI_BANDS = {
    "<20%": "abaixo de 20%",
    "20%-<30%": "de 20% a 30%",
    "30%-<36%": "de 30% a 36%",
    "50%-60%": "de 50% a 60%",
    ">60%": "acima de 60%",
}


def vazio(value) -> bool:
    """True se o valor está ausente (None, NaN ou texto vazio)."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip() == ""


def dollars(value) -> str:
    """US$ com ponto de milhar, ou 'não informado'."""
    if vazio(value):
        return NOT_INFORMED
    number = round(float(value))
    text = f"{number:,}".replace(",", ".")
    return "US$ " + text


def percent(value) -> str:
    """Percentual com vírgula decimal, ou 'não informado'."""
    if vazio(value):
        return NOT_INFORMED
    number = float(value)
    if number == round(number):
        return f"{number:.0f}%"
    text = f"{number:.2f}".rstrip("0").replace(".", ",")
    return text + "%"


def hmda_dti(published) -> str:
    """DTI do HMDA: valor exato de 36 a 49, faixa por extenso nos outros casos."""
    if vazio(published):
        return NOT_INFORMED
    if published in DTI_BANDS:
        return DTI_BANDS[published]
    return percent(published)


def cltv_text(value, cltv_has_ufmip: bool) -> str:
    """CLTV com o jeito como foi publicado (com ou sem o seguro inicial do FHA).

    O analista real sabe o valor do empréstimo com e sem o seguro; a base não diz, e o
    projeto deduz pelo banco (HMDA) ou pela base (NSMO publica com o seguro).
    """
    text = percent(value)
    if text == NOT_INFORMED:
        return text
    if cltv_has_ufmip:
        return text + " (com o seguro inicial do FHA, quando financiado)"
    return text + " (sem o seguro inicial do FHA)"


def hmda_case(row, cltv_has_ufmip: bool) -> dict:
    """Campos do perfil a partir de uma linha do HMDA (renda em milhares de US$)."""
    income = row["income"]
    if not vazio(income):
        income = float(income) * 1000
    return {
        "Finalidade": LOAN_PURPOSE.get(row["loan_purpose"], NOT_INFORMED),
        "Valor do empréstimo": dollars(row["loan_amount"]),
        "Valor do imóvel": dollars(row["property_value"]),
        "Renda anual": dollars(income),
        "DTI": hmda_dti(row["debt_to_income_ratio"]),
        "PTI": NOT_INFORMED,
        "CLTV": cltv_text(row["loan_to_value_ratio"], cltv_has_ufmip),
        "Score de crédito": NOT_INFORMED,
        "Reserva após o fechamento": NOT_INFORMED,
        "Ocupação": OCCUPANCY.get(row["occupancy_type"], NOT_INFORMED),
        "Posição da hipoteca": LIEN.get(row["lien_status"], NOT_INFORMED),
        "Unidades": NOT_INFORMED if vazio(row["total_units"]) else row["total_units"],
    }


def nsmo_purpose_code(x33, cashout) -> str:
    """Finalidade da NSMO com o código do HMDA ("" quando não há teto na tabela).

    Refinanciamento e troca de co-tomador (x33 2 e 3) viram com ou sem saque pela marca
    `cashout`; construção e imóvel quitado ficam sem código.
    """
    if x33 == 1:
        return "1"
    if x33 in (2, 3) and cashout == CASHOUT_YES:
        return "32"
    if x33 in (2, 3):
        return "31"
    return ""


def nsmo_purpose(x33, cashout) -> str:
    """Finalidade da NSMO no mesmo rótulo do HMDA."""
    code = nsmo_purpose_code(x33, cashout)
    return LOAN_PURPOSE.get(code, NOT_INFORMED)


def nsmo_case(row, score) -> dict:
    """Campos do perfil a partir de uma linha da NSMO; `score` é o menor dos tomadores."""
    reserve = X5001.get(row["x5001"], NOT_INFORMED)
    if reserve != NOT_INFORMED:
        reserve = reserve + " de prestação"
    pti = row["pti"]
    if not vazio(pti) and pti <= 0:
        pti = None
    score_text = NOT_INFORMED
    if not vazio(score):
        score_text = str(int(score))
    return {
        "Finalidade": nsmo_purpose(row["x33"], row["cashout"]),
        "Valor do empréstimo": NOT_INFORMED,
        "Valor do imóvel": NOT_INFORMED,
        "Renda anual": NOT_INFORMED,
        "DTI": percent(row["dti"]),
        "PTI": percent(pti),
        "CLTV": cltv_text(row["cltv"], True),
        "Score de crédito": score_text,
        "Reserva após o fechamento": reserve,
        "Ocupação": NOT_INFORMED,
        "Posição da hipoteca": NOT_INFORMED,
        "Unidades": NOT_INFORMED,
    }


def case_profile(case: dict) -> str:
    """Texto do perfil, um campo por linha, sempre na ordem de FIELDS."""
    lines = []
    for field in FIELDS:
        lines.append(field + ": " + str(case[field]))
    return "\n".join(lines)
