"""Testes da matriz manual (II.A.5.d.viii) e da resposta esperada de src/rules.py.

Rodar da raiz do projeto: python -m pytest tests
"""

import math

from src.rules import (
    APPROVE,
    APPROVE_WITH_FACTOR,
    DENY,
    INELIGIBLE,
    PENDING_1_FACTOR,
    PENDING_2_FACTORS,
    PENDING_2ND_FACTOR,
    PENDING_SECOND_LIEN,
    REASON_COLLATERAL,
    REASON_DTI,
    REASON_OUT_OF_MATRIX,
    SUSPEND,
    cltv_situation,
    expected_hmda,
    expected_nsmo,
    manual_requirement,
)

NAN = math.nan


# Matriz manual: um caso por célula.


def test_score_500_a_579_ate_31_43_sem_fator():
    assert manual_requirement(43, 31, 560) == "nenhum fator"


def test_score_500_a_579_acima_de_43_fora():
    assert manual_requirement(44, 30, 560) == "fora da matriz"


def test_score_500_a_579_pti_acima_de_31_fora():
    assert manual_requirement(40, 32, 560) == "fora da matriz"


def test_sem_score_usa_a_linha_mais_restritiva():
    assert manual_requirement(43, 31, NAN) == "nenhum fator"
    assert manual_requirement(44, 30, None) == "fora da matriz"


def test_score_abaixo_de_500_inelegivel():
    assert manual_requirement(30, 20, 499) == INELIGIBLE


def test_580_ate_31_43_sem_fator():
    assert manual_requirement(43, 31, 580) == "nenhum fator"


def test_580_ate_37_47_um_fator():
    assert manual_requirement(47, 37, 650) == "1 fator"


def test_580_ate_40_40_sem_divida_discricionaria():
    assert manual_requirement(40, 39, 650) == "sem dívida discricionária"


def test_580_ate_40_50_dois_fatores():
    assert manual_requirement(50, 40, 650) == "2 fatores"


def test_580_dti_acima_de_50_fora():
    assert manual_requirement(51, 30, 700) == "fora da matriz"


def test_580_pti_acima_de_40_fora():
    assert manual_requirement(45, 41, 700) == "fora da matriz"


def test_pti_ausente_nao_barra():
    assert manual_requirement(46, NAN, 650) == "1 fator"


# Situação do CLTV.


def test_compra_dentro_do_teto():
    assert cltv_situation("1", 96.5, None) == "dentro do teto"


def test_compra_com_seguro_financiado():
    assert cltv_situation("1", 98.19, None) == "seguro financiado"


def test_compra_acima_do_seguro():
    assert cltv_situation("1", 98.3, None) == "segundo financiamento a confirmar"


def test_saque_com_seguro_financiado():
    assert cltv_situation("32", 81.4, None) == "seguro financiado"


def test_sem_saque_com_seguro_financiado():
    assert cltv_situation("31", 99.46, None) == "seguro financiado"


def test_saque_acima_do_seguro():
    assert cltv_situation("32", 85, None) == "acima do teto"


def test_score_baixo_derruba_o_teto_para_90():
    assert cltv_situation("31", 92, 560) == "acima do teto"
    assert cltv_situation("31", 91.5, 560) == "seguro financiado"


def test_cltv_vazio():
    assert cltv_situation("1", NAN, None) == "não informado"


# Resposta esperada no HMDA.


def test_hmda_ate_43_aprova():
    assert expected_hmda("38", "1", 95.0)["acao"] == APPROVE


def test_hmda_44_suspende_pedindo_um_fator():
    resposta = expected_hmda("44", "1", 95.0)
    assert resposta["acao"] == SUSPEND
    assert resposta["pendencias"] == [PENDING_1_FACTOR]


def test_hmda_49_suspende_pedindo_dois_fatores():
    assert expected_hmda("49", "31", 90.0)["pendencias"] == [PENDING_2_FACTORS]


def test_hmda_acima_de_60_nega_por_dti():
    resposta = expected_hmda(">60%", "1", 90.0)
    assert resposta["acao"] == DENY
    assert resposta["motivos"] == [REASON_DTI]


def test_hmda_saque_acima_de_80_nega_por_garantia():
    resposta = expected_hmda("30%-<36%", "32", 85.0)
    assert resposta["acao"] == DENY
    assert resposta["motivos"] == [REASON_COLLATERAL]


def test_hmda_compra_acima_de_98_2_suspende():
    resposta = expected_hmda("<20%", "1", 100.0)
    assert resposta["acao"] == SUSPEND
    assert resposta["pendencias"] == [PENDING_SECOND_LIEN]


def test_hmda_negar_vence_suspender():
    assert expected_hmda(">60%", "1", 100.0)["acao"] == DENY


# Resposta esperada na NSMO.


def test_nsmo_um_fator_com_reserva_aprova_com_fator():
    assert expected_nsmo(46, 35, 650, True, "1", 96.5)["acao"] == APPROVE_WITH_FACTOR


def test_nsmo_um_fator_sem_reserva_suspende():
    resposta = expected_nsmo(46, 35, 650, False, "1", 96.5)
    assert resposta["pendencias"] == [PENDING_1_FACTOR]


def test_nsmo_dois_fatores_com_reserva_pede_o_segundo():
    resposta = expected_nsmo(49, 39, 650, True, "31", 90)
    assert resposta["pendencias"] == [PENDING_2ND_FACTOR]


def test_nsmo_pti_acima_de_40_fora_da_tabela():
    resposta = expected_nsmo(46, 42, 650, True, "1", 96.5)
    assert resposta["motivos"] == [REASON_OUT_OF_MATRIX]
