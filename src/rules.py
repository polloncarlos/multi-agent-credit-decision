"""Matriz de razões da análise manual, Handbook 4000.1 II.A.5.d.viii (Update 18).

A matriz é igual na Update 17 e na Update 18 (texto comparado em 2026-09-29).
"""

import math

SECTION = "II.A.5.d.viii"

# Linhas da matriz para score a partir de 580: (PTI máx., DTI máx., exigência).
ROWS_580 = [
    (31, 43, "nenhum fator"),
    (37, 47, "1 fator"),
    (40, 40, "sem dívida discricionária"),
    (40, 50, "2 fatores"),
]
RESERVE_MIN_PAYMENTS = 3  # II.A.5.d.ix(B), imóveis de 1 e 2 unidades


def cabe_na_linha(dti: float, pti: float, max_pti: float, max_dti: float) -> bool:
    """True se o caso respeita os limites da linha. PTI ausente não barra o caso."""
    sem_pti = pti is None or math.isnan(pti)
    pti_ok = sem_pti or pti <= max_pti
    return dti <= max_dti and pti_ok


def manual_requirement(dti: float, pti: float, score: float | None) -> str:
    """Exigência da matriz manual para o caso, ou 'fora da matriz'.

    `pti` ausente (NaN) é tratado como compatível com qualquer linha, e o DTI decide.
    """
    if score is None or score < 580:
        if cabe_na_linha(dti, pti, 31, 43):
            return "nenhum fator"
        return "fora da matriz"
    for max_pti, max_dti, requirement in ROWS_580:
        if cabe_na_linha(dti, pti, max_pti, max_dti):
            return requirement
    return "fora da matriz"
