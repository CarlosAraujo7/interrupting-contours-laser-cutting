# Escala de maquina de fibra: layouts aninhados reais (G1) e layouts densos (G2) (docs/59, Estudo G)

Economia da rota ciente do reinicio (resolvida em t'' no benchmark e avaliada na maquina de ar 140 m/min, t' = t'' v_a/v_a') sobre a referencia de contorno; convencao CONSERVADORA (contorno cobrado so as corridas da rota).

## G1 (layouts reais, CPPLib): 47 layouts

| corte (m/min) | t'' (s) | t' (ms) | economia do total: mediana | max | % com > 0,1% | economia do nao cortante: mediana | parcela de ar no total: mediana | corridas: mediana (contornos) |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 15 | 0 | 0.0 | 0.7667% | 1.8437% | 89% | 56.51% | 1.38% | 99 (57) |
| 15 | 0.06 | 10.3 | 0.6179% | 1.6719% | 74% | 37.75% | 1.37% | 87 (57) |
| 15 | 0.25 | 42.9 | 0.2202% | 1.3098% | 55% | 10.77% | 1.34% | 75 (57) |
| 15 | 1 | 171.4 | -0.0965% | 0.9976% | 26% | -1.69% | 1.30% | 60 (57) |
| 30 | 0 | 0.0 | 1.5115% | 3.6043% | 91% | 56.51% | 2.71% | 99 (57) |
| 30 | 0.06 | 10.3 | 1.2105% | 3.2600% | 77% | 37.75% | 2.68% | 87 (57) |
| 30 | 0.25 | 42.9 | 0.4321% | 2.5722% | 55% | 10.77% | 2.63% | 75 (57) |
| 30 | 1 | 171.4 | -0.1852% | 1.9394% | 26% | -1.69% | 2.48% | 60 (57) |

## G2 (densos sinteticos): 9 layouts

| corte (m/min) | t'' (s) | t' (ms) | economia do total: mediana | max | % com > 0,1% | economia do nao cortante: mediana | parcela de ar no total: mediana | corridas: mediana (contornos) |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 15 | 0 | 0.0 | -0.1943% | -0.0811% | 0% | -4.25% | 4.50% | 74 (60) |
| 15 | 0.06 | 10.3 | -0.2583% | -0.0740% | 0% | -2.15% | 4.12% | 60 (60) |
| 15 | 0.25 | 42.9 | -0.2906% | -0.0580% | 0% | -0.94% | 3.24% | 60 (60) |
| 15 | 1 | 171.4 | -0.1410% | -0.0312% | 0% | -0.22% | 1.75% | 60 (60) |
| 30 | 0 | 0.0 | -0.3717% | -0.1550% | 0% | -4.25% | 8.62% | 74 (60) |
| 30 | 0.06 | 10.3 | -0.4613% | -0.1310% | 0% | -2.15% | 7.30% | 60 (60) |
| 30 | 0.25 | 42.9 | -0.4437% | -0.0880% | 0% | -0.94% | 4.93% | 60 (60) |
| 30 | 1 | 171.4 | -0.1733% | -0.0383% | 0% | -0.22% | 2.15% | 60 (60) |

G-1 (medianas nao crescentes em t''; 15 m/min): 0.7667, 0.6179, 0.2202, -0.0965 %: **SUSTENTADA**.
G-2 (t''=0,06 s, t'=10,3 ms: mediana <= 1,0% e max <= 3,0% do total): mediana 0.6179%, max 1.6719%: **SUSTENTADA**.
G-3 (t'' = 0,25 e 1 s: mediana <= 0,1%): 0.2202%, -0.0965%: **NAO SUSTENTADA**.
G-4 (a t''=0,06 s a rota ainda economiza > 0,01% em >= 50% dos layouts): 38 de 47: **SUSTENTADA**.
G-5 (corridas nao crescentes em t'' em >= 80% dos layouts): 47 de 47: **SUSTENTADA**.
G-6 (densos: a t''=0,06 s a economia e <= 0,2% do total em todos e a parcela de ar de contorno e >= 3 vezes a mediana dos layouts reais — a tensao entre ter ar para poupar e poder poupa-lo): economia max -0.0740%, parcela de ar mediana 4.12% contra 1.37% nos reais: **SUSTENTADA**.
