# Replica com sementes novas (2 e 3) do fechamento e da estrita, t = 1 s

Economia conservadora (% do tempo total) sobre a referencia de contorno (ver `causa_aninhados_v2.py`). Original = V2 guardado (fechamento) e `causa_aninhados_v2.py` (estrita), sementes 0 e 1; replica = sementes 2 e 3.

| layout | n | fechamento original | fechamento replica | estrita original | estrita replica |
|---|---:|---:|---:|---:|---:|
| ck1x_3__ck1x_3 | 27 | +0.165% | +0.165% | +0.090% | +0.090% |
| cj1x_2__cj1x_2 | 11 | +0.328% | +0.328% | -0.003% | -0.003% |
| cj3x_1__cj3x_1 | 46 | +0.120% | +0.127% | +0.004% | -0.001% |
| snce_5__snce_5 | 20 | +0.153% | +0.153% | +0.092% | +0.092% |

P-C3 (o fechamento se reproduz): economia da replica >= 75% da guardada em 4 de 4 layouts (previsao: >= 3 de 4): SUSTENTADA.
P-C4 (a estrita e estavel): replica a <= 0,05 ponto percentual da original em 4 de 4 layouts (previsao: >= 3 de 4): SUSTENTADA.
