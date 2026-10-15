# Tetos certificados do ganho do nivel de segmento e otimo exato do nivel de contorno (14/10/2026)

Instancias com RPP exato e referencia de contorno: 42 (33 sem precedencia, 9 com furos). Exploratorio: calculado depois dos resultados principais.

## C1. Teto geral c(t) = (T_P(t) - LB(t)) / T_P(t), LB(t) = L/v_c + A*/v_a + t R_min (qualquer layout; T_P = PCGLNS por contorno guardado)

| t (s) | teto mediano | teto maximo | instancias com teto < 0,1% |
|---|---:|---:|---:|
| 0 | 0.725% | 10.70% | 0/42 |
| 0.01 | 0.755% | 10.91% | 0/42 |
| 0.06 | 0.785% | 11.91% | 0/42 |
| 0.25 | 0.778% | 15.36% | 0/42 |
| 1 | 0.706% | 25.11% | 0/42 |
| 0.5 | 0.752% | 19.19% | 0/42 |

Layouts com R_min < n (contornos que se tocam ou compartilham aresta): 17/42.

## C2. Otimo exato do nivel de contorno (Held-Karp) x PCGLNS por contorno guardado

Instancias com <= 18 contornos e mesma instancia abstrata do PCGLNS: 41.

| instancia | contornos | PCGLNS (FO) | DP exato (FO) | PCGLNS / DP - 1 |
|---|---:|---:|---:|---:|
| art_10_irregular_sep | 10 | 74.529 | 74.529 | +0.0000% |
| art_11_hole_pack | 18 | 83.772 | 83.543 | +0.2746% |
| art_11_hole_sep | 16 | 86.220 | 86.175 | +0.0531% |
| art_11_irregular_sep | 12 | 89.108 | 89.108 | +0.0000% |
| art_12_regular_pack | 12 | 69.120 | 69.119 | +0.0009% |
| art_13_irregular_pack | 12 | 88.765 | 88.755 | +0.0106% |
| art_14_regular_sep | 16 | 104.327 | 104.327 | +0.0000% |
| art_15_hole_pack | 17 | 88.719 | 88.604 | +0.1294% |
| art_15_hole_sep | 17 | 99.918 | 99.904 | +0.0140% |
| art_15_regular_sep | 13 | 94.567 | 94.567 | +0.0000% |
| art_16_regular_pack | 16 | 108.859 | 108.794 | +0.0598% |
| art_17_regular_sep | 16 | 105.702 | 105.702 | -0.0000% |
| art_18_regular_pack | 12 | 67.423 | 67.394 | +0.0423% |
| art_18_regular_sep | 12 | 69.186 | 69.186 | -0.0000% |
| art_21_hole_sep | 17 | 91.442 | 91.353 | +0.0970% |
| art_23_irregular_pack | 10 | 72.955 | 72.931 | +0.0327% |
| art_25_hole_pack | 16 | 80.562 | 80.443 | +0.1486% |
| art_2_regular_pack | 10 | 54.008 | 54.008 | +0.0000% |
| art_3_hole_sep | 18 | 83.237 | 82.919 | +0.3838% |
| art_3_regular_pack | 14 | 90.622 | 90.578 | +0.0482% |
| art_4_hole_pack | 15 | 87.820 | 87.820 | +0.0000% |
| art_6_regular_sep | 16 | 115.499 | 115.487 | +0.0105% |
| art_7_irregular_sep | 13 | 92.636 | 92.636 | -0.0000% |
| art_8_regular_sep | 14 | 88.430 | 88.418 | +0.0134% |
| art_9_irregular_sep | 13 | 93.782 | 93.782 | +0.0000% |
| dighe1_mod_pack | 16 | 101.157 | 101.081 | +0.0748% |
| dighe1_mod_sep | 16 | 101.261 | 101.178 | +0.0822% |
| dighe1_pack | 16 | 99.062 | 99.042 | +0.0202% |
| dighe1_sep | 16 | 99.565 | 99.455 | +0.1106% |
| dighe2_mod_pack | 10 | 77.963 | 77.899 | +0.0822% |
| dighe2_mod_sep | 10 | 78.165 | 78.165 | +0.0000% |
| dighe2_pack | 10 | 78.917 | 78.917 | -0.0000% |
| dighe2_sep | 10 | 79.227 | 79.097 | +0.1644% |
| fu_mod_pack | 12 | 32.263 | 32.263 | +0.0000% |
| fu_mod_sep | 12 | 32.276 | 32.276 | +0.0000% |
| fu_pack | 12 | 27.680 | 27.680 | -0.0000% |
| fu_sep | 12 | 27.710 | 27.710 | +0.0000% |
| poly1a_mod_pack | 15 | 19.018 | 19.006 | +0.0635% |
| poly1a_mod_sep | 15 | 19.039 | 19.030 | +0.0503% |
| poly1a_pack | 15 | 19.725 | 19.702 | +0.1142% |
| poly1a_sep | 15 | 19.747 | 19.725 | +0.1141% |

Mediana +0.0140%, maximo +0.3838%, minimo -0.0000%; PCGLNS igual ao otimo (|dif| <= 0,005%) em 17/41; PCGLNS abaixo do DP em 0.

## C3. Layouts de contornos disjuntos: ponto de equilibrio certificado t_cert = (A_P* - A*) / v_a

Qualquer plano tem R >= n corridas; com R = n o plano e de nivel de contorno (ar >= A_P*, o otimo exato do DP); com R >= n + 1, ar >= A* (RPP exato). Logo T(t) >= L/v_c + min(A_P*/v_a + t n, A*/v_a + t (n+1)); para t >= t_cert o otimo de nivel de contorno e o otimo de TODOS os planos, e para t < t_cert nenhum plano economiza mais que t_cert - t segundos.

| instancia | contornos | A* (RPP) | A_P* (DP) | t_cert (s) |
|---|---:|---:|---:|---:|
| art_10_irregular_sep | 10 | 245.6 | 469.3 | 0.559 |
| art_11_hole_sep | 16 | 412.4 | 534.3 | 0.305 |
| art_11_irregular_sep | 12 | 213.2 | 471.9 | 0.647 |
| art_13_irregular_pack | 12 | 172.8 | 414.5 | 0.604 |
| art_14_regular_sep | 16 | 333.5 | 664.0 | 0.826 |
| art_15_hole_sep | 17 | 448.6 | 647.1 | 0.496 |
| art_15_regular_sep | 13 | 275.9 | 625.1 | 0.873 |
| art_17_regular_sep | 16 | 402.8 | 667.0 | 0.661 |
| art_18_regular_sep | 12 | 271.2 | 491.0 | 0.550 |
| art_21_hole_sep | 17 | 369.3 | 528.1 | 0.397 |
| art_23_irregular_pack | 10 | 135.9 | 327.4 | 0.479 |
| art_3_hole_sep | 18 | 428.2 | 543.1 | 0.287 |
| art_6_regular_sep | 16 | 379.9 | 685.3 | 0.764 |
| art_7_irregular_sep | 13 | 339.1 | 552.3 | 0.533 |
| art_8_regular_sep | 14 | 255.1 | 496.6 | 0.604 |
| art_9_irregular_sep | 13 | 301.4 | 564.2 | 0.657 |
| dighe1_mod_pack | 16 | 264.7 | 456.7 | 0.480 |
| dighe1_mod_sep | 16 | 338.9 | 495.6 | 0.392 |
| dighe1_sep | 16 | 289.0 | 614.0 | 0.812 |
| dighe2_mod_pack | 10 | 116.9 | 346.5 | 0.574 |
| dighe2_mod_sep | 10 | 221.9 | 453.0 | 0.578 |
| dighe2_sep | 10 | 189.0 | 487.0 | 0.745 |
| fu_mod_pack | 12 | 83.3 | 143.7 | 0.151 |
| fu_mod_sep | 12 | 92.2 | 148.9 | 0.142 |

Layouts disjuntos: 24 (mediana de t_cert 0.566 s; minimo 0.142; maximo 0.873).

| t (s) | economia maxima, mediana | economia maxima, maxima | layouts em que o nivel de contorno e certificadamente otimo |
|---|---:|---:|---:|
| 0 | 0.671% | 0.942% | 0/24 |
| 0.01 | 0.660% | 0.928% | 0/24 |
| 0.06 | 0.606% | 0.859% | 0/24 |
| 0.25 | 0.385% | 0.637% | 2/24 |
| 0.5 | 0.082% | 0.369% | 9/24 |
| 1 | 0.000% | 0.000% | 24/24 |

Verificado: em todos os layouts disjuntos e em todo t, LB2(t) <= heuristica do LCPP e <= rota de arcos de t = 0 avaliada em t.

## C4. Solucoes cientes do reinicio (V3) contra o teto, nos layouts disjuntos em comum

| instancia | t (s) | economia da melhor solucao ciente do reinicio | economia maxima certificada |
|---|---:|---:|---:|
| art_15_regular_sep | 0.25 | -0.000% | 0.637% |
| art_15_regular_sep | 1.0 | -0.000% | 0.000% |
| art_21_hole_sep | 0.25 | 0.082% | 0.154% |
| art_21_hole_sep | 1.0 | 0.072% | 0.000% |
| art_6_regular_sep | 0.25 | 0.010% | 0.430% |
| art_6_regular_sep | 1.0 | 0.009% | 0.000% |
| art_7_irregular_sep | 0.25 | 0.000% | 0.295% |
| art_7_irregular_sep | 1.0 | 0.000% | 0.000% |
| dighe1_mod_pack | 0.25 | 0.072% | 0.219% |
| dighe1_mod_pack | 1.0 | 0.065% | 0.000% |
| dighe1_sep | 0.25 | 0.106% | 0.544% |
| dighe1_sep | 1.0 | 0.095% | 0.000% |
