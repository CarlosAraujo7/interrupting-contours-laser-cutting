# Ponto de equilibrio exato por iteracao de Newton (Proposicao 3)

| layout | n | R de partida | MILPs novos | t_c (s) | t_cert (s) | t_c / t_cert | intervalo guardado (s) | rho_c | status |
|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| art_10_irregular_sep | 10 | 15 | 0 | -- | 0.559 | -- | [0.0954, 0.25] | -- | sem_prova |
| art_15_regular_sep | 13 | 24 | 0 | -- | 0.873 | -- | [0.0768, 0.25] | -- | sem_prova |
| art_18_regular_sep | 12 | 14 | 2 | 0.12137 | 0.550 | 0.22 | [0.1115, 0.25] | 0.514 | exato |
| art_23_irregular_pack | 10 | 11 | 0 | -- | 0.479 | -- | [0.1567, 0.25] | -- | sem_prova |
| dighe1_sep | 16 | 24 | 0 | -- | 0.812 | -- | [0.0900, 0.25] | -- | sem_prova |
| dighe2_mod_pack | 10 | 18 | 2 | 0.09511 | 0.574 | 0.17 | [0.0708, 0.1] | 0.296 | exato |
| dighe2_mod_sep | 10 | 16 | 2 | 0.09426 | 0.578 | 0.16 | [0.0803, 0.1] | 0.294 | exato |
| fu_mod_pack | 12 | 14 | 2 | 0.05194 | 0.151 | 0.34 | [0.0418, 0.06] | 0.469 | exato |
| fu_mod_sep | 12 | 13 | 1 | 0.05194 | 0.142 | 0.37 | [0.0519, 0.06] | 0.469 | exato |

Layouts com t_c exato: 5 de 9. Mediana de t_c = 0.0943 s (min 0.0519, max 0.1214); mediana de t_c/t_cert = 0.22;
rho_c: mediana 0.469, max 0.514.

Previsao H-N5 (empirica, docs/52): mediana de t_c entre 0,04 e 0,15 s: SUSTENTADA; rho_c <= 1 em todos: SUSTENTADA.
