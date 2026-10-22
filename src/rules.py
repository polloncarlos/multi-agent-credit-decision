"""Regras do Handbook 4000.1 (Update 18) usadas para ler o dado: tetos de CLTV e a
matriz de razões da análise manual (II.A.5.d.viii).

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
