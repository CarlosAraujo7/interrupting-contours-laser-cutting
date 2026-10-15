# Âncoras de reinício por espessura contra a curva exata da economia máxima (14/10/2026; exploratório; plano B sem máquina)

Premissas explícitas: pré-corte ℓ = 2 mm (Dewil et al. 2015: "um par de mm"); aceleração de corte 10 m/s²; levantar/descer do Z de 0 a 0,15 s; velocidades de corte por classe: Thin sheet (up to 3 mm): 5.0-30.0 m/min; Medium plate (9 to 12 mm): 0.6-2.0 m/min; Thick plate (20 to 25 mm): 0.5-1.0 m/min. **A retomada (`t_ret`) não foi medida por nenhuma fonte encontrada: é derivada.**

| classe | perfuração t_perf (s) | regimes | retomada t_ret derivada (s) | regimes | fontes da perfuração |
|---|---|---|---|---|---|
| Thin sheet (up to 3 mm) | 0.002 a 0.21 | R1, R2 | 0.004 a 0.21 | R1, R2 | Hashemzadeh 2014 (breakthrough 2-8 ms; tens of ms at lower power); on-the-fly piercing up to 5-6 mm (vendors) |
| Medium plate (9 to 12 mm) | 0.5 a 2.15 | R2, R3 | 0.06 a 0.461 | R1, R2 | West 2018 (9 mm: 0.5-2 s); Prima Power 2015 (12 mm: < 1 s); Garcia 2019 (10 mm stainless/aluminium: <= 1.5 s) |
| Thick plate (20 to 25 mm) | 2 a 11.7 | R3 | 0.12 a 0.418 | R2 | Piranha-Whitney (25 mm, 12 kW: ~2 s); Garcia 2019 (20 mm, 5 kW: 8-11.5 s) |

Regimes: R1 t ≤ 0,06 s; R2 0,06 < t < 0,87 s; R3 t ≥ 0,87 s (certificado).

## Curva exata da economia máxima de qualquer plano sobre o ótimo de contorno (layouts disjuntos sem furos; MILP exato com custo de reinício; t = 0: RPP exato)

| t (s) | layouts | economia, mediana (%) | máxima (%) |
|---:|---:|---:|---:|
| 0 | 18 | 0.682 | 0.923 |
| 0.01 | 9 | 0.629 | 0.795 |
| 0.03 | 9 | 0.417 | 0.542 |
| 0.06 | 7 | 0.156 | 0.239 |
| 0.1 | 7 | 0.000 | 0.077 |
| 0.25 | 10 | 0.000 | 0.000 |
| 0.5 | 8 | 0.000 | 0.000 |
| 1 | 4 | 0.000 | 0.000 |

## Distância ao ótimo exato em função de t (mesmos layouts; % acima do ótimo do MILP; t = 0: RPP exato)

| t (s) | layouts | heurística do LCPP (cega ao reinício), mediana / máx. | rota de arcos de t = 0, mediana / máx. | nível de contorno (PCGLNS), mediana / máx. |
|---:|---:|---|---|---|
| 0 | 18 | +0.003 / +0.294 | +0.025 / +0.204 | +0.699 / +0.935 |
| 0.01 | 9 | +0.018 / +0.324 | +0.035 / +0.184 | +0.643 / +0.821 |
| 0.06 | 7 | +0.315 / +1.261 | +0.283 / +1.026 | +0.157 / +0.349 |
| 0.25 | 10 | +2.630 / +6.029 | +2.257 / +5.268 | +0.000 / +0.106 |
| 1 | 4 | +16.441 / +20.052 | +14.738 / +17.749 | +0.000 / +0.000 |

**Leitura:** a economia máxima só é positiva para t abaixo de um ponto de equilíbrio exato (por layout); acima dele o nível de contorno é ótimo. As faixas por espessura devem ser lidas contra essa curva.
