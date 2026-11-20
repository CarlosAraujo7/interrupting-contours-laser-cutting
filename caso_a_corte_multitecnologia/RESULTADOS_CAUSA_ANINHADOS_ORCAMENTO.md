# Orcamento do PCGLNS no nivel de segmento (600 s por rodada, sementes 0 e 1) nos 4 layouts aninhados, t = 1 s

Economia conservadora (% do tempo total) sobre a referencia de contorno de V2 (`causa_aninhados_v2.economia`). Original = V2 guardado (fechamento) e `causa_aninhados_v2.py` (estrita), com `min(120, 20 + E/4)` s por rodada; 600 s = este experimento (docs/55).

| layout | n | E | orcamento original (s) | fechamento original | fechamento 600 s | dFO fechamento | estrita original | estrita 600 s | dFO estrita |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ck1x_3__ck1x_3 | 27 | 111 | 47 | +0.165% | +0.165% | +0.000% | +0.090% | +0.090% | +0.000% |
| cj1x_2__cj1x_2 | 11 | 59 | 34 | +0.328% | +0.328% | +0.000% | -0.003% | -0.003% | +0.000% |
| cj3x_1__cj3x_1 | 46 | 263 | 85 | +0.120% | +0.128% | -0.009% | +0.004% | +0.037% | -0.003% |
| snce_5__snce_5 | 20 | 170 | 62 | +0.153% | +0.153% | +0.000% | +0.092% | +0.092% | +0.000% |

P-O1a (o fechamento nao depende do orcamento): |economia 600 s - original| <= 0,05 pp em 4 de 4 layouts (previsao: >= 3 de 4): SUSTENTADA.
P-O1b (a estrita nao depende do orcamento): idem, em 4 de 4 (previsao: >= 3 de 4): SUSTENTADA.
P-O2 (estrutural: fechamento >= estrita com 600 s): em 4 de 4 layouts (previsao: todos): SUSTENTADA.
P-O3 (o residuo da estrita): economia da estrita com 600 s <= 0,10% em 4 de 4 (previsao: >= 3 de 4): SUSTENTADA; maior valor +0.092%.
P-O4 (convergencia: o melhor FO muda <= 0,01% entre os orcamentos): fechamento em 4 de 4, estrita em 4 de 4 (previsao: >= 3 de 4 em cada): SUSTENTADA.
