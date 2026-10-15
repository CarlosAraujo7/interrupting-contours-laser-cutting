# TSH-Π (precedência de fechamento) — 84 layouts do CPPLib

Layouts com solução viável encontrada pelo passeio de Fleury com portão: **72/84** (verificadas: contíguo, cada trecho cortado uma vez, Π relaxada com 0 violações). Tentativas (mediana): 8; tempo (mediana): 0.07 s; máx. 120.0 s.

Ar em unidades de distância (Chebyshev). `TSH-Π` tem o MESMO ar do TSH (mesmo multigrafo). Referência de peça: PCGLNS (Π **estrita**, média de 10 sementes). Heurística: modo original e com Π, com os saltos contados.

| comparação (mediana dos gaps de ar) | valor |
|---|---:|
| TSH-Π em relação ao PCGLNS (peça, Π estrita) | -54.2% (média -53.3%) |
| TSH-Π em relação à heurística original honesta (Π relaxada quase satisfeita) | -64.7% |
| TSH-Π em relação à heurística com Π estrita (honesta) | -80.6% |
| PCGLNS em relação ao TSH-Π | +118.3% |

Perfurações do TSH-Π (mediana): 92 contra 50 contornos (piece-level = nº de contornos).

| layout | contornos | ar TSH-Π | ar PCGLNS (peça) | gap | perfurações |
|---|---:|---:|---:|---:|---:|
| p1xe_7 | 5 | 250 | 955 | -74% | 8 |
| p1xe_6 | 6 | 119 | 1260 | -91% | 10 |
| p5xe_1 | 9 | 643 | 1502 | -57% | 17 |
| p3xe_2 | 14 | 773 | 1316 | -41% | 24 |
| p5xj_4 | 14 | 1502 | 2589 | -42% | 27 |
| p1xe_1 | 16 | 1196 | 2245 | -47% | 28 |
| p1xe_2 | 17 | 1291 | 2749 | -53% | 31 |
| p1xe_4 | 21 | 852 | 3031 | -72% | 40 |
| p1xe_5 | 21 | 432 | 1461 | -70% | 38 |
| p3xe_1 | 21 | 831 | 1159 | -28% | 36 |
| p1xj_16 | 22 | 867 | 5434 | -84% | 43 |
| p1xe_3 | 24 | 972 | 2257 | -57% | 43 |
| p5xj_8 | 24 | 1638 | 6408 | -74% | 46 |
| p1xj_8 | 30 | 2490 | 5640 | -56% | 56 |
| p3xj_5 | 31 | 2158 | 6575 | -67% | 58 |
| p5xk_1 | 33 | 3112 | 7025 | -56% | 61 |
| p1xj_17 | 37 | 1813 | 6786 | -73% | 67 |
| p1xj_5 | 39 | 1100 | 3218 | -66% | 75 |
| p1xj_7 | 39 | 730 | 4532 | -84% | 71 |
| p1xj_15 | 40 | 804 | 3475 | -77% | 76 |
| p1xj_6 | 40 | 1888 | 6387 | -70% | 68 |
| p3xj_10 | 40 | 2105 | 4594 | -54% | 73 |
| p5xk_2 | 40 | 3292 | 4937 | -33% | 73 |
| p7xj_2 | 40 | 2243 | 3928 | -43% | 74 |
| p1xj_10 | 41 | 3004 | 9048 | -67% | 73 |
| p5xj_5 | 41 | 1486 | 3081 | -52% | 75 |
| p1xj_3 | 42 | 1823 | 4387 | -58% | 79 |
| p1xj_11 | 43 | 1885 | 4732 | -60% | 75 |
| p5xj_7 | 43 | 2964 | 4395 | -33% | 77 |
| p7xj_3 | 43 | 2507 | 4112 | -39% | 84 |
| p5xj_9 | 44 | 3702 | 5181 | -29% | 80 |
| p1xj_12 | 45 | 1490 | 4392 | -66% | 85 |
| p7xj_7 | 45 | 2810 | 4906 | -43% | 84 |
| p5xj_6 | 46 | 2115 | 4376 | -52% | 90 |
| p1xj_4 | 47 | 1637 | 5295 | -69% | 85 |
| p1xj_9 | 49 | 2520 | 5598 | -55% | 92 |
| p3xj_11 | 50 | 2302 | 4844 | -52% | 95 |
| p5xj_2 | 52 | 3343 | 5238 | -36% | 97 |
| p3xj_1 | 53 | 2264 | 4951 | -54% | 97 |
| p3xj_8 | 53 | 1835 | 5465 | -66% | 102 |

Sem solução viável no limite: ['p1xe_8', 'p1xj_1', 'p1xj_13', 'p1xk_1', 'p1xk_10', 'p1xk_14', 'p1xk_6', 'p3xj_2', 'p3xj_4', 'p3xj_6', 'p3xk_4', 'p3xk_9']
