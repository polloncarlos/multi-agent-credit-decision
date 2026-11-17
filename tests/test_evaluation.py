"""Testes da regra fixa de DTI e do acerto de src/evaluation.py.

Rodar da raiz do projeto: python -m pytest tests
"""

import pandas as pd

from src.evaluation import agreement, fixed_dti_rule
from src.rules import APPROVE, DENY, SUSPEND


def test_regra_fixa_aprova_ate_43():
    assert fixed_dti_rule("até 43") == APPROVE


def test_regra_fixa_nega_acima_de_43():
    assert fixed_dti_rule("44 a 49") == DENY
    assert fixed_dti_rule("acima de 60") == DENY


def test_acerto_conta_aprovar_e_negar_certos():
    acoes = pd.Series([APPROVE, DENY, APPROVE, DENY])
    decisoes = pd.Series(["aprovado", "negado", "negado", "aprovado"])
    assert agreement(acoes, decisoes) == 50.0


def test_acerto_nao_conta_suspender():
    acoes = pd.Series([SUSPEND, APPROVE])
    decisoes = pd.Series(["aprovado", "aprovado"])
    assert agreement(acoes, decisoes) == 50.0
