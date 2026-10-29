# Dados

Os notebooks leem os arquivos em parquet desta pasta, então não é preciso baixar nada para
rodá-los. Os CSV originais passam do limite de tamanho do GitHub e ficam fora do repositório.
Cada parquet guarda todas as linhas do CSV de origem, só com as colunas que o projeto usa.

## HMDA (Home Mortgage Disclosure Act)

- Arquivo: `raw/hmda/hmda_2025_fha.parquet` (2.062.934 pedidos, 19 colunas, 14,3 MB).
- Fonte: base pública da CFPB (Consumer Financial Protection Bureau), ano 2025, Estados
  Unidos inteiro, só pedidos FHA (Federal Housing Administration), pela API do HMDA Data
  Browser. Baixada em 29/09/2026.
- CSV original: `hmda_2025_fha.csv`, 768,2 MB, SHA-256
  `cc94236a94f960bbd8a5a5b0710500719252f18af550d0d38fe7c9d01a21e717`.
- Licença: a CFPB declara de domínio público a informação que produz. É proibido tentar
  identificar pessoas a partir do dado.

Para refazer a partir da fonte, rodar da raiz do projeto `python -m src.download_hmda` e
depois `python -m src.raw_parquet`. A CFPB pode revisar a base depois de publicada, e o
SHA-256 acima permite conferir se o CSV baixado é o mesmo usado aqui.

## NSMO (National Survey of Mortgage Originations)

- Arquivo: `raw/nsmo/nsmo_v70_1324_puf.parquet` (62.359 financiamentos, 18 colunas,
  0,9 MB).
- Fonte: Public Use File versão 70 da NSMO, publicado pela FHFA (Federal Housing Finance
  Agency) e pela CFPB em fhfa.gov/data/nsmo/puf. O download exige aceitar os termos de uso
  no site, por isso não há script para ele. Baixado em 29/09/2026.
- CSV original: `nsmo_v70_1324_puf.csv`, 167,3 MB, SHA-256
  `fc3a4038510c921bfdae53aeb3960767e331c38276c9bd226b0d8a0375e96cab`.
- Termos de uso: `raw/nsmo/nsmo_terms_of_service.pdf`. Os termos permitem redistribuir o
  dado desde que essa cópia vá junto, proíbem reidentificar pessoas e exigem o aviso abaixo.

O parquet é um recorte de colunas feito para este projeto e não é um arquivo oficial da
FHFA. Para refazê-lo, salvar o CSV e os termos em `raw/nsmo/` (ou na pasta indicada em
`LARGE_DATA_DIR` no `.env`) e rodar `python -m src.raw_parquet`.

> The opinions and analyses contained herein are solely of the users/authors of any data
> analyses or papers, and the FHFA cannot and does not attest to nor vouch for the quality,
> accuracy, or timeliness of the data, or analyses derived from these data after the data
> has been retrieved from FHFA.gov.

## Aviso

Este projeto é de portfólio e não serve para decisão real de crédito.
