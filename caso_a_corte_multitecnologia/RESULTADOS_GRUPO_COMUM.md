# Linha-base com cortes comuns (grupos de perfuracao): certificado e ponto de equilibrio generalizados (docs/59, Estudo E)

| layout | n | R_min | V | A_P* | A_G* | A* | t_cert^G (s) | t_c^G (s) | rho_G | S_G(0) % | S_G(0,25) % | S_G(1) % | S_cc(1) % | S_total(1) % | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| art_2_regular_pack | 10 | 9 | 42 | 292.3 | 292.3 | 176.4 | 0.290 | 0.05321 | 0.216 | 0.537 | 0.000 | 0.000 | 1.562 | 1.562 | exato |
| dighe1_pack | 16 | 11 | 60 | 449.0 | 366.0 | 223.0 | 0.357 | 0.13000 | 0.368 | 0.361 | 0.000 | 0.000 | 8.490 | 8.490 | exato |
| fu_pack | 12 | 5 | 32 | 104.0 | 65.0 | 47.0 | 0.045 | 0.04500 | 0.220 | 0.163 | 0.000 | 0.000 | 24.994 | 24.994 | exato |
| fu_sep | 12 | 9 | 40 | 116.0 | 103.0 | 65.0 | 0.095 | 0.02375 | 0.196 | 0.343 | 0.000 | 0.000 | 10.659 | 10.659 | exato |
| poly1a_mod_pack | 15 | 13 | 59 | 86.2 | 85.5 | 36.8 | 0.122 | 0.02993 | 0.497 | 0.640 | 0.000 | 0.000 | 5.886 | 5.886 | exato |
| poly1a_mod_sep | 15 | 14 | 60 | 95.6 | 95.6 | 49.8 | 0.115 | 0.02959 | 0.529 | 0.603 | 0.000 | -0.000 | 2.939 | 2.939 | exato |
| poly1a_pack | 15 | 8 | 63 | 81.0 | 75.0 | 30.0 | 0.113 | 0.04000 | 0.394 | 0.571 | 0.000 | 0.000 | 20.215 | 20.215 | exato |
| poly1a_sep | 15 | 13 | 68 | 90.0 | 90.0 | 42.0 | 0.120 | 0.03750 | 0.600 | 0.608 | 0.000 | 0.000 | 5.760 | 5.760 | exato |

Layouts: 8; com ponto de equilibrio exato sobre G: 8.

E-1 (nulo em 0,25 s sobre G): 8 de 8 layouts; previsao: todos: **SUSTENTADA**.
E-2 (t_c^G <= 0,2 s e rho_G mediano em [0,2; 0,8]): maior t_c^G = 0.1300 s; rho_G mediano = 0.381 (min 0.196, max 0.600): **SUSTENTADA**.
E-3 (a 1 s o ganho total do segmento e todo de corte comum: S_G(1) = 0 e S_total(1) = S_cc(1)): 8 layouts com M(1) provado: **SUSTENTADA**.
E-4 (S_cc(1) > 0): minimo 1 s (8 layouts): **SUSTENTADA**.
