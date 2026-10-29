"""Regras do Handbook 4000.1 (Update 18) usadas para ler o dado: tetos de CLTV, a
matriz de razões da análise manual (II.A.5.d.viii) e a resposta esperada de cada caso.

A matriz é igual na Update 17 e na Update 18.
"""

import math

SECTION = "II.A.5.d.viii"

# Teto de CLTV por finalidade (loan_purpose do HMDA), com score a partir de 580:
# compra (II.A.2), refinanciamento sem saque e com saque (II.A.8). O Streamline não tem
# teto, e o HMDA não o separa dos outros refinanciamentos sem saque.
CLTV_CAP = {"1": 96.5, "31": 97.75, "32": 80.0}
# Com score de 500 a 579, o LTV fica limitado a 90% em qualquer finalidade
# (II.A.2.b.i). A norma limita o LTV; o HMDA só publica o CLTV, que é maior ou igual.
CLTV_CAP_SCORE_500_579 = 90.0

# Linhas da matriz para score a partir de 580: (PTI máx., DTI máx., exigência).
ROWS_580 = [
    (31, 43, "nenhum fator"),
    (37, 47, "1 fator"),
    (40, 40, "sem dívida discricionária"),
    (40, 50, "2 fatores"),
]
RESERVE_MIN_PAYMENTS = 3  # II.A.5.d.ix(B), imóveis de 1 e 2 unidades
MIN_SCORE = 500  # abaixo disso o cliente não é elegível ao FHA (MDCS)
INELIGIBLE = "inelegível (score abaixo de 500)"


def sem_valor(x: float | None) -> bool:
    """True se o valor está ausente (None ou NaN)."""
    return x is None or math.isnan(x)


def cltv_cap(purpose: str, score: float | None) -> float:
    """Teto de CLTV da finalidade, com o corte por score da II.A.2.b.i.

    `score` ausente (None ou NaN) usa o teto da finalidade sem o corte. No HMDA o score
    não é publicado; tratar a falta assim é decisão do projeto: lacuna da base, não
    pendência do cliente (o banco puxa o relatório de crédito em todo pedido).
    """
    cap = CLTV_CAP[purpose]
    if not sem_valor(score) and score < 580:
        return min(cap, CLTV_CAP_SCORE_500_579)
    return cap


def cabe_na_linha(dti: float, pti: float, max_pti: float, max_dti: float) -> bool:
    """True se o caso respeita os limites da linha. PTI ausente não barra o caso."""
    pti_ok = sem_valor(pti) or pti <= max_pti
    return dti <= max_dti and pti_ok


def manual_requirement(dti: float, pti: float, score: float | None) -> str:
    """Exigência da matriz manual para o caso, 'fora da matriz' ou inelegível.

    `pti` ausente (NaN) é tratado como compatível com qualquer linha, e o DTI decide.
    No HMDA o PTI não é publicado; tratar a falta como compatível é decisão do projeto:
    lacuna da base, não pendência do cliente.

    `score` ausente (None ou NaN) usa a linha "500 a 579 ou sem score" da matriz, a
    mais restritiva. Score abaixo de 500 não é elegível ao FHA.
    """
    if not sem_valor(score) and score < MIN_SCORE:
        return INELIGIBLE
    if sem_valor(score) or score < 580:
        if cabe_na_linha(dti, pti, 31, 43):
            return "nenhum fator"
        return "fora da matriz"
    for max_pti, max_dti, requirement in ROWS_580:
        if cabe_na_linha(dti, pti, max_pti, max_dti):
            return requirement
    return "fora da matriz"


def manual_requirements(dtis, ptis, scores) -> list[str]:
    """Aplica manual_requirement a cada caso, na ordem das listas recebidas."""
    requirements = []
    for dti, pti, score in zip(dtis, ptis, scores):
        requirements.append(manual_requirement(dti, pti, score))
    return requirements


def norm_reading(requirement: str, has_reserve: bool) -> str:
    """O que a norma permite concluir na NSMO, dada a exigência e a reserva.

    Só a reserva pode ser verificada na NSMO; os outros fatores compensatórios não
    estão na base.
    """
    if requirement in ("fora da matriz", INELIGIBLE):
        return "fora da matriz manual"
    if requirement == "sem dívida discricionária":
        return "exigência não informada na base"
    if requirement == "1 fator":
        if has_reserve:
            return "exigência verificada"
        return "fator não verificado"
    if requirement == "2 fatores":
        if has_reserve:
            return "1 de 2 fatores verificado"
        return "nenhum de 2 fatores verificado"
    return "exigência verificada"


# Resposta esperada pela norma em código (o teto de referência da Evaluation).
# Vocabulário fixo, para conferir a resposta do agente sem ler texto livre.
APPROVE = "aprovar"
APPROVE_WITH_FACTOR = "aprovar com fator compensatório"
DENY = "negar"
SUSPEND = "suspender"

PENDING_1_FACTOR = "comprovação de 1 fator compensatório"
PENDING_2_FACTORS = "comprovação de 2 fatores compensatórios"
PENDING_2ND_FACTOR = "comprovação do 2º fator compensatório"
PENDING_SECOND_LIEN = "comprovação do segundo financiamento (II.A.5)"

REASON_DTI = "DTI"
REASON_COLLATERAL = "garantia"
REASON_OUT_OF_MATRIX = "fora da tabela manual"

# Seguro inicial do FHA (UFMIP). Todo teto de LTV vale antes dele, e o seguro pode ser
# somado à dívida por cima, em qualquer finalidade (II.A.2.iii).
UFMIP = 1.75


def cap_with_ufmip(purpose: str, score: float | None) -> float:
    """Teto de CLTV com o seguro inicial por cima: 98,2 na compra, 81,4 no saque, 99,5 sem
    saque (com score de 580 ou mais)."""
    return round(cltv_cap(purpose, score) * (1 + UFMIP / 100), 1)


def cltv_situation(purpose: str, cltv: float | None, score: float | None) -> str:
    """Situação do CLTV contra o teto da finalidade.

    Devolve "não informado", "dentro do teto", "seguro financiado" (entre o teto e o
    teto com o seguro inicial, lacuna da base), "segundo financiamento a confirmar"
    (compra acima disso, II.A.5) ou "acima do teto" (refinanciamento acima disso).
    Finalidade fora de CLTV_CAP devolve "sem teto na tabela".
    """
    if sem_valor(cltv):
        return "não informado"
    if purpose not in CLTV_CAP:
        return "sem teto na tabela"
    if cltv <= cltv_cap(purpose, score):
        return "dentro do teto"
    if cltv <= cap_with_ufmip(purpose, score):
        return "seguro financiado"
    if purpose == "1":
        return "segundo financiamento a confirmar"
    return "acima do teto"


def combine(action: str, reasons: list[str], pending: list[str]) -> dict:
    """Junta a ação pelo DTI com os motivos e pendências do CLTV, pelo custo assimétrico.

    Negar vence suspender, e suspender vence aprovar: com um motivo de negativa o caso é
    negado; com pendência e sem motivo, suspenso.
    """
    if reasons:
        return {"acao": DENY, "motivos": reasons, "pendencias": []}
    if pending:
        return {"acao": SUSPEND, "motivos": [], "pendencias": pending}
    return {"acao": action, "motivos": [], "pendencias": []}


def expected_hmda(dti_published: str, purpose: str, cltv: float | None) -> dict:
    """Resposta esperada para um pedido do HMDA, que não traz score, PTI nem reserva.

    Score e PTI ausentes são lacuna da base, não pendência do cliente: até 43% de DTI a
    resposta é aprovar. De 44% a 49%, a norma pede fator compensatório, que a base não
    mostra, então a resposta é suspender pedindo a comprovação. A faixa "50%-60%" mistura
    o 50% (permitido com dois fatores) com valores acima do teto manual; aqui ela vale
    como acima do teto, e o pedido sai da nota pela marcação de faixa.
    """
    reasons = []
    pending = []
    action = APPROVE

    if dti_published == ">60%" or dti_published == "50%-60%":
        reasons.append(REASON_DTI)
    elif dti_published in ("<20%", "20%-<30%", "30%-<36%"):
        action = APPROVE
    else:
        dti = int(dti_published)
        if 44 <= dti <= 47:
            pending.append(PENDING_1_FACTOR)
        elif 48 <= dti <= 49:
            pending.append(PENDING_2_FACTORS)

    situation = cltv_situation(purpose, cltv, None)
    if situation == "acima do teto":
        reasons.append(REASON_COLLATERAL)
    if situation == "segundo financiamento a confirmar":
        pending.append(PENDING_SECOND_LIEN)

    return combine(action, reasons, pending)


def expected_nsmo(
    dti: float,
    pti: float | None,
    score: float | None,
    has_reserve: bool,
    purpose: str,
    cltv: float | None,
) -> dict:
    """Resposta esperada para um caso da NSMO, com score, PTI e reserva.

    `purpose` usa os códigos do HMDA ("1", "31", "32"). Fora da tabela manual (PTI ou
    score) a análise manual não aprova, então a resposta é negar; esses casos saem da
    nota pela marcação. A reserva é o único fator compensatório que a NSMO mostra.
    """
    reasons = []
    pending = []
    action = APPROVE

    requirement = manual_requirement(dti, pti, score)
    reading = norm_reading(requirement, has_reserve)
    if reading == "fora da matriz manual":
        reasons.append(REASON_OUT_OF_MATRIX)
    elif reading == "exigência verificada" and requirement != "nenhum fator":
        action = APPROVE_WITH_FACTOR
    elif reading == "fator não verificado":
        pending.append(PENDING_1_FACTOR)
    elif reading == "1 de 2 fatores verificado":
        pending.append(PENDING_2ND_FACTOR)
    elif reading == "nenhum de 2 fatores verificado":
        pending.append(PENDING_2_FACTORS)

    situation = cltv_situation(purpose, cltv, score)
    if situation == "acima do teto":
        reasons.append(REASON_COLLATERAL)
    if situation == "segundo financiamento a confirmar":
        pending.append(PENDING_SECOND_LIEN)

    return combine(action, reasons, pending)
