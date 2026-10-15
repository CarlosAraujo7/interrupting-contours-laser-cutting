# Mapa de regimes ancorado em fontes (`docs/28`; exploratório; rotas guardadas, sem reotimizar)

60 instâncias. Célula: mediana de T(rota)/T(peça) − 1, em %. Perfis ancorados em páginas de fabricantes conferidas em 14/10/2026 e custos de reinício na literatura e em materiais de fabricantes (ver o cabeçalho de `analise_mapa_regimes.py`; a versão 1, com anúncios de revenda, está em `RESULTADOS_MAPA_REGIMES_v1_anuncios_de_revenda.md`).

## Heurística (cega ao reinício)

| perfil de movimento | t = 0 s | t = 0.01 s | t = 0.06 s | t = 0.25 s | t = 1 s |
|---|---:|---:|---:|---:|---:|
| FIBRA_1G | -0.00 | +0.11 | +0.62 | +2.89 | +10.50 |
| V170_1_4G | +0.03 | +0.11 | +0.62 | +2.91 | +10.52 |
| BLM_2G | -0.00 | +0.10 | +0.63 | +2.92 | +10.52 |
| SALV_5G | -0.02 | +0.09 | +0.68 | +2.91 | +10.50 |
| DEWIL16 | +0.04 | +0.04 | +0.27 | +2.36 | +10.00 |

## Heurística reparada (t = 1)

| perfil de movimento | t = 0 s | t = 0.01 s | t = 0.06 s | t = 0.25 s | t = 1 s |
|---|---:|---:|---:|---:|---:|
| FIBRA_1G | +0.01 | +0.01 | +0.01 | +0.05 | +0.10 |
| V170_1_4G | +0.02 | +0.02 | +0.03 | +0.07 | +0.09 |
| BLM_2G | +0.00 | +0.01 | +0.01 | +0.05 | +0.07 |
| SALV_5G | -0.00 | +0.00 | +0.00 | +0.04 | +0.05 |
| DEWIL16 | +0.04 | +0.04 | +0.06 | +0.09 | +0.18 |

## Arcos ciente do reinício (t = 0,25)

| perfil de movimento | t = 0 s | t = 0.01 s | t = 0.06 s | t = 0.25 s | t = 1 s |
|---|---:|---:|---:|---:|---:|
| FIBRA_1G | -0.03 | -0.03 | -0.02 | -0.01 | -0.01 |
| V170_1_4G | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 |
| BLM_2G | -0.02 | -0.02 | -0.01 | -0.01 | -0.01 |
| SALV_5G | -0.02 | -0.02 | -0.01 | -0.01 | -0.01 |
| DEWIL16 | -0.05 | -0.05 | -0.05 | -0.05 | -0.04 |

## Peso do tempo de voo (nível de peça; mediana)

| perfil | ar / tempo total |
|---|---:|
| FIBRA_1G | 1.71% |
| V170_1_4G | 1.46% |
| BLM_2G | 1.22% |
| SALV_5G | 0.78% |
| DEWIL16 | 4.24% |
