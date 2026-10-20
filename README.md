# Apoio multi-agente à análise de crédito imobiliário FHA

Sistema multi-agente que recomendaria a decisão de um pedido de financiamento imobiliário FHA
(Federal Housing Administration) em análise manual, citando a seção do HUD Handbook 4000.1 que
sustenta cada recomendação.

> Projeto de portfólio em construção. O entendimento dos dados terminou, e a próxima fase é a
> preparação. Não serve para decisão real de crédito.

## O problema

Nos Estados Unidos, o FHA é o órgão do governo que dá seguro a financiamentos imobiliários
concedidos por bancos. Para ter esse seguro, o banco precisa seguir o HUD Handbook 4000.1, um
manual de centenas de páginas alterado várias vezes por ano pelas Mortgagee Letters.

A maior parte dos pedidos é decidida por um sistema automático. Os que ele não resolve vão para
um analista de crédito (underwriter), que lê o caso, consulta o manual e escolhe uma de quatro
ações: aprovar, aprovar com fatores compensatórios, negar ou suspender até chegar a documentação
que falta. Um fator compensatório é algo a favor do cliente que permite passar do limite padrão,
como ter guardado o equivalente a três prestações.

Os erros têm custos diferentes. Se o banco aprova fora da regra e o cliente não paga, o HUD pode
cobrar dele o prejuízo, estimado em dezenas de milhares de dólares por empréstimo. Negar quem
devia ser aprovado custa a receita do empréstimo. Por isso, na dúvida, o agente suspende em vez
de aprovar.

## O que o agente entregaria

Para cada pedido, um memorando com a recomendação, as regras aplicadas com a seção do Handbook
citada, a situação do cliente contra cada limite (dentro, fora ou não informado) e a lista do
que falta para decidir. O agente recomenda e o analista decide.

## Como vai ser avaliado

O gabarito é a decisão real do banco, registrada no HMDA. Ela é só uma aproximação da decisão
correta, porque o banco também olha score e histórico de crédito, que a base pública não traz.
Os resultados serão reportados por faixa de DTI (Debt to Income, a parte da renda comprometida
com dívidas), já que cada faixa tem informação diferente disponível para decidir. A faixa de
50% a 60% fica fora do resultado principal e é reportada à parte. Ela passa do teto da análise
manual, que é 50%, então um pedido aprovado ali só pode ter passado pelo sistema automático.

Nos casos em que a norma só permite aprovar mediante uma comprovação que a base não mostra,
como um fator compensatório, a resposta esperada é suspender pedindo a comprovação, e o agente
é avaliado contra a norma, não contra o banco.

No HMDA, o agente precisa vencer dois adversários simples, aprovar sempre e uma regra fixa em
código que aprova com DTI até 43% e nega acima disso. Na NSMO, que só tem pedidos aprovados,
aprovar sempre acertaria tudo, então ali o agente é avaliado contra a norma aplicada em código.
As regras do Handbook implementadas em código servem de teto. Também serão medidos:

- o motivo da negativa, comparado ao motivo registrado pelo banco;
- o tempo de resposta por caso, com referência de 60 segundos;
- 20 memorandos conferidos à mão, checando se a seção citada existe e diz o que o memorando
  afirma;
- uma demonstração com uma Mortgagee Letter real, em que o agente acompanharia a mudança da
  norma sem alteração no código.

Os pedidos são divididos uma única vez, com semente fixa, em um grupo de ajuste, onde o prompt
pode ser mexido à vontade, e um grupo da nota final, rodado uma vez só no fim. O sorteio mantém
a proporção de cada finalidade do pedido (compra, refinanciamento com ou sem saque), porque a
chance de negativa muda muito entre elas. Se a regra fixa empatar com o agente ou vencê-lo, esse
será o resultado reportado.

## Dados e norma

Só entram fontes reais, oficiais e que permitem publicação.

| Fonte | O que traz | Papel no projeto | Uso |
|---|---|---|---|
| HMDA (Home Mortgage Disclosure Act), publicado pelo CFPB | Pedidos de financiamento de todos os bancos dos EUA, com a decisão e o motivo da negativa. Não tem score nem reserva | Teste principal, só pedidos FHA de 2025 | Domínio público |
| NSMO (National Survey of Mortgage Originations) Public Use File, da FHFA e do CFPB | Financiamentos aprovados, com DTI, VantageScore 3.0 e reserva após o fechamento | Segundo teste, na faixa de DTI de 44% a 50% | Terms of Service da FHFA |
| HUD Handbook 4000.1 e Mortgagee Letters | Regras do FHA para análise de crédito | Norma consultada pelo agente | Domínio público |

## Metodologia

O projeto segue as fases do CRISP-DM.

- [x] Entendimento do negócio: decisão, ações, custo de errar e métrica definidos antes de abrir
  os dados.
- [x] Entendimento dos dados ([notebook 01](notebooks/01_data_understanding.ipynb)): o DTI
  publicado no HMDA só separa com clareza negados e aprovados acima de 60%. Abaixo disso, a
  decisão depende de campos que a base não traz, como score, reserva e histórico de crédito. Por
  isso a avaliação é reportada por faixa.
- [ ] Preparação dos dados: seleção dos pedidos, separação dos dois grupos, divisão do Handbook
  por seção e geração dos embeddings.
- [ ] Modelagem: arquitetura multi-agente com tool-use. O framework de orquestração (LangGraph ou
  CrewAI) será escolhido nessa fase.
- [ ] Avaliação.
- [ ] Implantação: API em FastAPI e interface em Streamlit.

Stack prevista: Python 3.10, pandas, pypdf para ler o Handbook, Chroma ou FAISS como base
vetorial, LLM via Groq, FastAPI e Streamlit.

## Estrutura do repositório

```
src/        funções reutilizáveis (leitura das bases, regras do Handbook em código)
notebooks/  notebooks numerados por fase
data/       dados brutos e processados
api/        API em FastAPI (a construir)
app/        interface em Streamlit (a construir)
reports/    relatórios e figuras
```

## Aviso

Projeto de estudo, sem vínculo com FHA, HUD, CFPB ou FHFA. As recomendações do agente não devem
ser usadas para decidir crédito de verdade. Nenhuma tentativa de identificar pessoas é feita com
os dados.

Aviso exigido pela FHFA para o uso da NSMO:

> The opinions and analyses contained herein are solely of the users/authors of any data
> analyses or papers, and the FHFA cannot and does not attest to nor vouch for the quality,
> accuracy, or timeliness of the data, or analyses derived from these data after the data has
> been retrieved from FHFA.gov.
