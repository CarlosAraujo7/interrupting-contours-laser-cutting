# Esforco de busca do PCGLNS no nivel de segmento (`-mode=slow`, teto de 600 s por rodada, sementes 0 e 1) nos 4 layouts aninhados, t = 1 s

Economia conservadora (% do tempo total) sobre a referencia de contorno de V2 (`causa_aninhados_v2.economia`). Original = V2 guardado (fechamento) e `causa_aninhados_v2.py` (estrita), modo `default` com `min(120, 20 + E/4)` s por rodada; 600 s default = parte C (`causa_aninhados_orcamento.py`); slow = esta extensao (docs/55_desvios.md D1). Tempos: total das duas rodadas, em s.

| layout | n | semantica | original | 600 s default | slow | dFO slow | tempo default (s) | tempo slow (s) |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| ck1x_3__ck1x_3 | 27 | fechamento | +0.165% | +0.165% | +0.165% | +0.000% | 44 | 214 |
| ck1x_3__ck1x_3 | 27 | estrita | +0.090% | +0.090% | +0.090% | -0.000% | 50 | 266 |
| cj1x_2__cj1x_2 | 11 | fechamento | +0.328% | +0.328% | +0.328% | +0.000% | 21 | 46 |
| cj1x_2__cj1x_2 | 11 | estrita | -0.003% | -0.003% | -0.003% | +0.000% | 21 | 45 |
| cj3x_1__cj3x_1 | 46 | fechamento | +0.120% | +0.128% | +0.128% | -0.008% | 505 | 1216 |
| cj3x_1__cj3x_1 | 46 | estrita | +0.004% | +0.037% | +0.034% | +0.000% | 633 | 1215 |
| snce_5__snce_5 | 20 | fechamento | +0.153% | +0.153% | +0.153% | -0.000% | 93 | 669 |
| snce_5__snce_5 | 20 | estrita | +0.092% | +0.092% | +0.092% | -0.000% | 115 | 825 |

P-S1 (o fechamento nao depende do esforco de busca): |economia slow - original| <= 0,05 pp em 4 de 4 layouts (previsao: >= 3 de 4): SUSTENTADA.
P-S2 (a estrita nao depende do esforco de busca): idem, em 4 de 4 (previsao: >= 3 de 4): SUSTENTADA.
P-S3 (o residuo da estrita): economia da estrita no modo slow <= 0,10% em 4 de 4 (previsao: >= 3 de 4): SUSTENTADA; maior valor +0.092%.
P-S4 (estrutural: fechamento >= estrita no modo slow): em 4 de 4 layouts (previsao: todos): SUSTENTADA.
P-S5 (diagnostico: o melhor FO do modo slow no maximo 0,01% acima do original): fechamento em 4 de 4, estrita em 4 de 4 (previsao: >= 3 de 4 em cada): SUSTENTADA.
