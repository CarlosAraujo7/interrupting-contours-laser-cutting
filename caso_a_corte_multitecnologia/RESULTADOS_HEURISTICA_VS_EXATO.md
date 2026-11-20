# PCGLNS de arcos contra o otimo exato (docs/60, estudo H)

Casos avaliaveis: 143 (layouts: 48).

| estudo | t (s) | casos | excesso mediano (%) | excesso max (%) | no otimo | captura mediana |
|---|---:|---:|---:|---:|---:|---:|
| E | 0.06 | 8 | 0.000 | 0.375 | 6 | 1.000 |
| E | 0.25 | 8 | 0.000 | 0.114 | 5 | 1.000 |
| E | 1 | 8 | 0.004 | 0.031 | 4 | 1.000 |
| F | 0.03 | 39 | 0.638 | 10.944 | 15 | 0.956 |
| F | 0.1 | 40 | 0.042 | 4.584 | 18 | 1.000 |
| F | 0.25 | 40 | 0.000 | 3.315 | 25 | -- |

H-1 (mediana do excesso <= 2% e max <= 15%): mediana 0.000%, max 10.944%: **SUSTENTADA**.
H-2 (>= 80% dos casos com excesso <= 5%): 136 de 143: **SUSTENTADA**.
H-3 (o otimo exato e atingido em >= 30% dos casos): 73 de 143: **SUSTENTADA**.
H-4 (captura mediana >= 0,9): mediana 1.000 (75 casos com economia exata > 0,1%): **SUSTENTADA**.
