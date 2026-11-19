# Causa da economia persistente nos layouts aninhados (t = 1 s)

Economia = % do tempo total sobre a referencia de contorno (PCGLNS, media de 10 sementes; Pi estrita), versao conservadora (ver docstring). Fechamento = V2 guardado; estrita = rodada nova com o mesmo metodo e orcamento.

| layout | n | rho_1 | corridas (fech./estr.) | economia fechamento | economia estrita | DP exata: FO / referencia - 1 |
|---|---:|---:|---|---:|---:|---|
| ck1x_3__ck1x_3 | 27 | 0.43 | 28 / 26 | +0.165% | +0.090% | nao resolvida |
| cj1x_2__cj1x_2 | 11 | 0.31 | 12 / 11 | +0.328% | -0.003% | -0.0000% |
| cj3x_1__cj3x_1 | 46 | 0.35 | 40 / 39 | +0.120% | +0.004% | nao resolvida |
| snce_5__snce_5 | 20 | 0.45 | 14 / 13 | +0.153% | +0.092% | nao resolvida |

P-C1 (alivio da precedencia): economia estrita < metade da de fechamento em 2 de 4 layouts (a previsao: >= 3 de 4): NAO SUSTENTADA.
P-C2 (folga da referencia): DP exata resolvida em 1 layouts; referencia acima do otimo em no maximo -0.0000%: a referencia NAO e a causa (|gap| <= 0,02%).
