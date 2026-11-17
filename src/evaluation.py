"""Ferramentas de medida da avaliação: a regra fixa de DTI e o acerto contra o banco.

Não fazem parte da norma. A regra fixa é o adversário simples do agente, e o acerto mede
em quantos pedidos uma resposta bate com a decisão real do banco.
"""

from src.rules import APPROVE, DENY


def fixed_dti_rule(dti_band: str) -> str:
    """Adversário simples: DTI até 43% aprova, acima nega."""
    if dti_band == "até 43":
        return APPROVE
    return DENY


def agreement(actions, decisions) -> float:
    """Percentual de pedidos em que a ação bate com a decisão do banco.

    `actions` e `decisions` são Series do pandas com o mesmo índice. Só aprovar contra
    "aprovado" e negar contra "negado" contam como acerto.
    """
    aprovou_certo = (actions == APPROVE) & (decisions == "aprovado")
    negou_certo = (actions == DENY) & (decisions == "negado")
    bate = aprovou_certo | negou_certo
    return round(100 * bate.mean(), 1)
