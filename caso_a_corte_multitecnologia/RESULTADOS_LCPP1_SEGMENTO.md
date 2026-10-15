# Nível de segmento (GTSP de arcos + PCGLNS, Π de fechamento, t_perf = 0) nas instâncias do LCPP-1 — 282 instâncias com resultado

Todos os valores são FO **honestas** (caminho contíguo; a heurística com os saltos contados; o PCGLNS por peça com as pernas da origem).

| comparação | mediana | média | vitórias do primeiro |
|---|---:|---:|---:|
| nosso segmento × PCGLNS por peça | -0.463% | -0.971% | 282/282 |
| heurística do LCPP (forte, honesta) × PCGLNS por peça | -0.470% | -0.930% | 254/282 |
| **nosso segmento × heurística do LCPP (honesta)** | +0.010% | -0.041% | 132/282 |

| instância | contornos | pares Π | arcos | nosso | heurística honesta | PCGLNS peça | nosso×heur | nosso×peça |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| art_7_hole_sep | 55 | 21 | 225 | 265.24 | 267.51 | 265.61 | -0.85% | -0.14% |
| art_23_hole_sep | 31 | 13 | 128 | 158.79 | 160.11 | 159.40 | -0.82% | -0.38% |
| art_13_hole_sep | 54 | 19 | 219 | 279.26 | 281.45 | 279.40 | -0.78% | -0.05% |
| art_20_hole_sep | 20 | 9 | 78 | 88.79 | 89.41 | 89.26 | -0.70% | -0.53% |
| art_23_hole_pack | 62 | 21 | 266 | 327.82 | 330.05 | 328.89 | -0.68% | -0.33% |
| art_9_hole_sep | 33 | 11 | 135 | 161.33 | 162.40 | 161.89 | -0.66% | -0.34% |
| art_12_hole_pack | 38 | 12 | 152 | 192.50 | 193.70 | 193.16 | -0.62% | -0.34% |
| fu_sep | 12 | 0 | 40 | 26.39 | 26.55 | 27.71 | -0.62% | -4.78% |
| art_24_hole_sep | 53 | 18 | 219 | 278.86 | 280.55 | 279.09 | -0.60% | -0.08% |
| art_22_hole_sep | 36 | 13 | 152 | 177.14 | 178.20 | 177.61 | -0.59% | -0.26% |
| art_17_hole_pack | 43 | 15 | 188 | 216.68 | 217.96 | 217.98 | -0.59% | -0.60% |
| art_14_hole_pack | 47 | 15 | 199 | 256.29 | 257.77 | 257.06 | -0.57% | -0.30% |
| art_12_hole_sep | 60 | 21 | 244 | 327.02 | 328.86 | 327.10 | -0.56% | -0.02% |
| art_18_hole_sep | 47 | 15 | 195 | 241.66 | 243.01 | 242.00 | -0.56% | -0.14% |
| art_3_hole_sep | 18 | 7 | 74 | 82.76 | 83.22 | 83.24 | -0.55% | -0.57% |
| art_14_hole_sep | 57 | 21 | 242 | 289.71 | 291.31 | 290.16 | -0.55% | -0.16% |
| art_10_hole_pack | 26 | 8 | 110 | 140.84 | 141.60 | 141.39 | -0.54% | -0.39% |
| art_8_hole_sep | 59 | 20 | 237 | 304.08 | 305.73 | 304.12 | -0.54% | -0.01% |
| art_24_hole_pack | 26 | 8 | 111 | 137.28 | 138.02 | 138.17 | -0.53% | -0.64% |
| art_2_hole_pack | 35 | 13 | 149 | 164.88 | 165.75 | 165.37 | -0.53% | -0.29% |
| art_8_hole_pack | 57 | 18 | 248 | 309.54 | 311.10 | 310.62 | -0.50% | -0.35% |
| art_1_hole_pack | 43 | 14 | 196 | 228.19 | 229.30 | 229.03 | -0.49% | -0.37% |
| art_1_hole_sep | 59 | 18 | 250 | 329.57 | 331.14 | 329.78 | -0.48% | -0.06% |
| art_4_hole_sep | 43 | 16 | 179 | 223.92 | 224.98 | 223.92 | -0.47% | -0.00% |
| art_11_hole_pack | 18 | 7 | 77 | 83.19 | 83.55 | 83.77 | -0.43% | -0.70% |
