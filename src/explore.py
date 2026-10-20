"""Exploração do HMDA: campos numéricos em faixas e busca de pares que separam grupos."""

import itertools

import pandas as pd

VALUE_BINS = (
    [-1, 100e3, 200e3, 300e3, 400e3, 500e3, 1e12],
    ["<=100k", "100-200k", "200-300k", "300-400k", "400-500k", ">500k"],
)
BINS = {
    "loan_to_value_ratio": (
        [-1, 80, 90, 96.5, 100, 1e9],
        ["<=80", "80-90", "90-96,5", "96,5-100", ">100"],
    ),
    "loan_amount": VALUE_BINS,
    "property_value": VALUE_BINS,
    "income": (
        [-1e9, 0, 40, 60, 80, 100, 150, 1e9],
        ["<=0", "0-40k", "40-60k", "60-80k", "80-100k", "100-150k", ">150k"],
    ),
}


def binned(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    """Copia `fields` com os numéricos em faixas e todo valor ausente como 'vazio'."""
    out = df[fields].copy()
    for col in fields:
        if col in BINS:
            num = pd.to_numeric(out[col], errors="coerce")
            out[col] = pd.cut(num, bins=BINS[col][0], labels=BINS[col][1]).astype(str)
            out.loc[num.isna(), col] = "vazio"
        else:
            out[col] = out[col].fillna("vazio")
    return out


def contar_por_grupo(data: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    """Conta os pedidos de cada grupo em cada valor de `colunas`."""
    return data.groupby(colunas + ["grupo"]).size().unstack(fill_value=0)


def lift_por_grupo(
    contagem: pd.DataFrame, alvos: list[str], n: pd.Series
) -> pd.DataFrame:
    """Quantas vezes cada valor aparece mais no grupo negado do que no 'originado'.

    É a proporção do valor dentro do grupo negado dividida pela proporção dele dentro
    dos originados.
    """
    taxa_negados = contagem[alvos] / n[alvos]
    taxa_originados = contagem["originado"] / n["originado"]
    return taxa_negados.div(taxa_originados, axis=0)


def pair_scan(
    df: pd.DataFrame,
    fields: list[str],
    group: pd.Series,
    labels: dict[str, str],
    min_n: int = 300,
    min_frac: float = 0.01,
) -> pd.DataFrame:
    """Lift de cada combinação de dois campos, por grupo, contra o grupo 'originado'.

    `group` traz 'originado' ou o código do grupo comparado. O ganho é o lift do par
    dividido pelo maior lift dos dois valores sozinhos: acima de 1, a combinação separa
    mais do que qualquer um dos campos isolados.
    """
    data = df[fields].assign(grupo=group.values)
    n = data["grupo"].value_counts()
    alvos = [g for g in n.index if g != "originado"]

    # 1. Lift de cada campo sozinho, usado depois para medir o ganho do par
    lift_sozinho = {}
    for campo in fields:
        contagem = contar_por_grupo(data, [campo])
        lift_sozinho[campo] = lift_por_grupo(contagem, alvos, n)

    # 2. Lift de cada par de campos, guardando só as combinações com casos suficientes
    rows = []
    for a, b in itertools.combinations(fields, 2):
        contagem = contar_por_grupo(data, [a, b])
        lift_par = lift_por_grupo(contagem, alvos, n)
        for g in alvos:
            suficiente = (contagem[g] >= min_n) & (contagem[g] >= min_frac * n[g])
            for (va, vb), negados in contagem.loc[suficiente, g].items():
                lift = lift_par.loc[(va, vb), g]
                lift_a = lift_sozinho[a].loc[va, g]
                lift_b = lift_sozinho[b].loc[vb, g]
                melhor_sozinho = max(lift_a, lift_b)
                rows.append({
                    "motivo": labels.get(g, g),
                    "combinação": f"{a} = {va} E {b} = {vb}",
                    "negados": int(negados),
                    "originados": int(contagem.loc[(va, vb), "originado"]),
                    "lift": round(lift, 1),
                    "ganho": round(lift / melhor_sozinho, 1),
                })
    return pd.DataFrame(rows)
