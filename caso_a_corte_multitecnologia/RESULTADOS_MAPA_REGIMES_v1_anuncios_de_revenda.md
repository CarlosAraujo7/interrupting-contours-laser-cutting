# Mapa de regimes ancorado em fontes (`docs/28`; exploratório; rotas guardadas, sem reotimizar)

60 instâncias. Célula: mediana de T(rota)/T(peça) − 1, em %. Perfis e custos de reinício ancorados em fontes secundárias (ver o cabeçalho de `analise_mapa_regimes.py`).

## Heurística (cega ao reinício)

| perfil de movimento | t = 0 s | t = 0.01 s | t = 0.06 s | t = 0.25 s | t = 1 s |
|---|---:|---:|---:|---:|---:|
| FIBRA_1G | -0.00 | +0.11 | +0.62 | +2.89 | +10.50 |
| FIBRA_1_5G | -0.02 | +0.10 | +0.62 | +2.91 | +10.52 |
| FIBRA_2_9G | +0.00 | +0.09 | +0.64 | +2.90 | +10.51 |
| DEWIL16 | +0.04 | +0.04 | +0.27 | +2.36 | +10.00 |

## Heurística reparada (t = 1)

| perfil de movimento | t = 0 s | t = 0.01 s | t = 0.06 s | t = 0.25 s | t = 1 s |
|---|---:|---:|---:|---:|---:|
| FIBRA_1G | +0.01 | +0.01 | +0.01 | +0.05 | +0.10 |
| FIBRA_1_5G | +0.00 | +0.01 | +0.00 | +0.04 | +0.08 |
| FIBRA_2_9G | +0.00 | +0.01 | +0.01 | +0.05 | +0.06 |
| DEWIL16 | +0.04 | +0.04 | +0.06 | +0.09 | +0.18 |

## Arcos ciente do reinício (t = 0,25)

| perfil de movimento | t = 0 s | t = 0.01 s | t = 0.06 s | t = 0.25 s | t = 1 s |
|---|---:|---:|---:|---:|---:|
| FIBRA_1G | -0.03 | -0.03 | -0.02 | -0.01 | -0.01 |
| FIBRA_1_5G | -0.03 | -0.03 | -0.02 | -0.01 | -0.01 |
| FIBRA_2_9G | -0.02 | -0.02 | -0.01 | -0.01 | -0.01 |
| DEWIL16 | -0.05 | -0.05 | -0.05 | -0.05 | -0.04 |

## Peso do tempo de voo (nível de peça; mediana)

| perfil | ar / tempo total |
|---|---:|
| FIBRA_1G | 1.71% |
| FIBRA_1_5G | 1.42% |
| FIBRA_2_9G | 1.03% |
| DEWIL16 | 4.24% |
