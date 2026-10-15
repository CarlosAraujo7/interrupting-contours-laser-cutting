# E-A0 completo -- analise pre-registrada (docs/11_protocolo_E-A0.md); T = 30 s, >= 10 sementes

Instancias com >= 2 pecas: 84; com todos os metodos estocasticos completos: 84; usadas na comparacao (mesmo problema e construcao viavel): **73**. Fora por nao serem do mesmo problema: p1xj_4, p1xj_9, p1xk_9, p3xj_3, p3xk_5, p7xj_1, p7xj_4, p7xj_6, p7xj_7, p7xj_8, p7xk_1. Incompletas (rodada em andamento?): 0.

## Hipoteses

| hipotese | mediana de G [IC 95%] | instancias pior / melhor que o PCGLNS | p | p (Holm) | leitura |
|---|---|---|---:|---:|---|
| H-A0.1 construcao > PCGLNS (unilateral) | +0.87% [+0.74%; +0.90%] | 73 / 0 | 0.0000 | 0.0000 | rejeita H0 |
| H-A0.3 VNS-Pi != PCGLNS (bilateral) | +0.02% [+0.01%; +0.04%] | 61 / 0 | 0.0000 | 0.0000 | rejeita H0 |
| H-A0.2 heuristica + busca local: IC superior <= 0,5% | +0.25% [+0.21%; +0.29%] | -- | -- | -- | equivalencia pratica |
| H-A0.2 heuristica + VNS: IC superior <= 0,5% | +0.04% [+0.01%; +0.09%] | -- | -- | -- | equivalencia pratica |

H-A0.5 (escala): Spearman entre o nº de pecas e G(construcao) = +0.32, p unilateral = 0.0027. H-A0.6: razao mediana de tempo construcao/PCGLNS = 0.031. H-A0.4: instancias com violacao de Pi por metodo = {'pcglns': 0, 'vns_pi': 0, 'heur_pi': 0, 'heur_ls': 0, 'heur_vns': 0, 'mastri': 73, 'heur_orig': 84}.

## Exploratorio: hibridos e VNS-Pi

Friedman sobre ['heur_ls', 'heur_vns', 'vns_pi', 'pcglns']: chi2 = 183.08, p = 1.907e-39. Wilcoxon bilateral com Holm (gap mediano do primeiro sobre o segundo):

| par | gap mediano | p | p (Holm) |
|---|---:|---:|---:|
| heur_ls x heur_vns | +0.14% | 0.0000 | 0.0000 |
| heur_ls x vns_pi | +0.18% | 0.0000 | 0.0000 |
| heur_vns x vns_pi | +0.01% | 0.0000 | 0.0000 |
| heur_ls x pcglns | +0.25% | 0.0000 | 0.0000 |
| heur_vns x pcglns | +0.04% | 0.0000 | 0.0000 |
| vns_pi x pcglns | +0.02% | 0.0000 | 0.0000 |

## Gap por metodo sobre o PCGLNS (instancias usadas)

| metodo | mediana | media | melhor / pior que o PCGLNS | tempo medio de parede (s) |
|---|---:|---:|---:|---:|
| VNS-Pi | +0.02% | +0.04% | 0 / 61 | 29.5 |
| Heuristic (construction) | +0.87% | +0.84% | 0 / 73 | 0.6 |
| Heuristic + local search | +0.25% | +0.23% | 0 / 70 | 1.3 |
| Heuristic + VNS | +0.04% | +0.07% | 0 / 62 | 30.6 |
