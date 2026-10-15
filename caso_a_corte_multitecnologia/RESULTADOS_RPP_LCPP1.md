# Distância ao ótimo (RPP exato sem Π) nas instâncias pequenas do LCPP-1 — 42 resolvidas

Para Π = ∅ (regular, irregular, ESICUP) o RPP exato é o **ótimo** do problema do LCPP-1; para `hole` é **limite inferior**. Tempo de ar em segundos (Chebyshev/v_ar; ar do nível de peça = FO − corte/v_corte).

## Π = ∅ (ótimo) — n = 33

| método | gap do **ar** ao ótimo (mediana) | máx. | no ótimo (≤ 0,01%) | gap da **FO** (mediana) |
|---|---:|---:|---:|---:|
| heurística do LCPP (formal) | +0.61% | +84.62% | 14/33 | +0.003% |
| GTSP de arcos + PCGLNS (2 rodadas) | +0.00% | +24.92% | 17/33 | +0.000% |
| PCGLNS por peça | +126.60% | +2521.28% | 0/33 | +0.745% |

## hole (limite inferior) — n = 9

| método | gap do **ar** ao ótimo (mediana) | máx. | no ótimo (≤ 0,01%) | gap da **FO** (mediana) |
|---|---:|---:|---:|---:|
| heurística do LCPP (formal) | +9.66% | +44.79% | 0/9 | +0.128% |
| GTSP de arcos + PCGLNS (2 rodadas) | +12.34% | +22.54% | 1/9 | +0.107% |
| PCGLNS por peça | +56.56% | +158.67% | 0/9 | +0.726% |

## todas — n = 42

| método | gap do **ar** ao ótimo (mediana) | máx. | no ótimo (≤ 0,01%) | gap da **FO** (mediana) |
|---|---:|---:|---:|---:|
| heurística do LCPP (formal) | +6.64% | +84.62% | 14/42 | +0.048% |
| GTSP de arcos + PCGLNS (2 rodadas) | +2.20% | +24.92% | 18/42 | +0.014% |
| PCGLNS por peça | +111.43% | +2521.28% | 0/42 | +0.731% |

## Por instância (Π = ∅)
| instância | vértices | ar ótimo (s) | heurística | GTSP | peça | tempo MILP (s) |
|---|---:|---:|---:|---:|---:|---:|
| fu_pack | 32 | 0.117 | 0.137 | 0.117 | 3.080 | 0.1 |
| fu_sep | 40 | 0.163 | 0.300 | 0.165 | 1.490 | 8.0 |
| art_2_regular_pack | 42 | 0.441 | 0.441 | 0.441 | 0.731 | 8.3 |
| dighe2_pack | 45 | 0.260 | 0.260 | 0.260 | 1.637 | 0.2 |
| dighe2_sep | 47 | 0.472 | 0.555 | 0.472 | 1.347 | 1.3 |
| art_18_regular_pack | 54 | 0.212 | 0.212 | 0.212 | 0.800 | 9.6 |
| poly1a_mod_pack | 59 | 0.092 | 0.121 | 0.102 | 0.227 | 36.0 |
| art_12_regular_pack | 60 | 0.181 | 0.181 | 0.181 | 0.973 | 22.2 |
| dighe1_pack | 60 | 0.557 | 0.693 | 0.557 | 5.703 | 17.1 |
| poly1a_mod_sep | 60 | 0.124 | 0.142 | 0.140 | 0.249 | 78.8 |
| dighe1_sep | 63 | 0.723 | 1.013 | 0.723 | 1.645 | 54.4 |
| poly1a_pack | 63 | 0.075 | 0.085 | 0.075 | 0.225 | 27.3 |
| fu_mod_pack | 64 | 0.208 | 0.235 | 0.208 | 0.359 | 127.7 |
| fu_mod_sep | 64 | 0.231 | 0.231 | 0.231 | 0.372 | 114.8 |
| dighe2_mod_pack | 66 | 0.292 | 0.292 | 0.292 | 0.930 | 20.3 |
| dighe2_mod_sep | 66 | 0.555 | 0.555 | 0.693 | 1.133 | 36.2 |
| art_18_regular_sep | 68 | 0.678 | 0.678 | 0.762 | 1.228 | 55.3 |
| poly1a_sep | 68 | 0.105 | 0.148 | 0.105 | 0.247 | 79.8 |
| art_15_regular_sep | 70 | 0.690 | 0.690 | 0.690 | 1.563 | 97.7 |
| art_16_regular_pack | 75 | 0.522 | 0.522 | 0.522 | 1.491 | 85.0 |
| art_3_regular_pack | 77 | 0.248 | 0.248 | 0.302 | 1.183 | 18.0 |
| art_10_irregular_sep | 81 | 0.614 | 0.614 | 0.616 | 1.173 | 144.4 |
| art_23_irregular_pack | 81 | 0.340 | 0.365 | 0.355 | 0.842 | 120.6 |
| art_14_regular_sep | 84 | 0.834 | 0.839 | 0.834 | 1.660 | 437.2 |
| art_17_regular_sep | 84 | 1.007 | 1.010 | 1.139 | 1.667 | 390.7 |
| dighe1_mod_pack | 85 | 0.662 | 0.781 | 0.698 | 1.217 | 420.6 |
| dighe1_mod_sep | 85 | 0.847 | 0.983 | 0.876 | 1.322 | 637.1 |
| art_8_regular_sep | 92 | 0.638 | 0.669 | 0.789 | 1.253 | 747.2 |
| art_11_irregular_sep | 96 | 0.533 | 0.739 | 0.533 | 1.180 | 502.4 |
| art_13_irregular_pack | 97 | 0.432 | 0.435 | 0.433 | 1.046 | 375.6 |
| art_6_regular_sep | 105 | 0.950 | 0.950 | 1.184 | 1.725 | 877.3 |
| art_7_irregular_sep | 105 | 0.848 | 0.848 | 0.928 | 1.381 | 410.0 |
| art_9_irregular_sep | 105 | 0.753 | 0.753 | 0.922 | 1.411 | 431.5 |
