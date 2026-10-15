# Análise pré-registrada do reparo ciente do reinício (`docs/23`)

Amostra: 60 instâncias; resultados do reparo: 60.

## t = 0.25 s (n = 60)

- **Rep/B − 1:** mediana **+0.296%** (IC 95% [+0.162%; +0.427%]); antes do reparo H/B − 1: +2.535%; Rep ≤ B em 12/60.
- **Redução (H − Rep)/H:** mediana **2.12%** (IC 95% [1.90%; 2.34%]); Rep < H em 60/60; corridas: H 60 → Rep 36.
- **Fração do excesso recuperada** (H − Rep)/(H − B): mediana **89.6%** (n = 55).
- **Verificação (H-P3):** 60/60 soluções verificadas e não piores que a inicial. **Convergência:** 60/60; tempo mediano da busca 1.87 s (máx. 18.0 s); iterações medianas 28.
- **Rep × nível de peça:** mediana **+0.022%** (IC 95% [-0.176%; +0.120%]); Rep < P em 29/60.

## t = 1.0 s (n = 60)

- **Rep/B − 1:** mediana **+0.562%** (IC 95% [+0.262%; +0.901%]); antes do reparo H/B − 1: +10.210%; Rep ≤ B em 6/60.
- **Redução (H − Rep)/H:** mediana **8.64%** (IC 95% [7.87%; 9.28%]); Rep < H em 60/60; corridas: H 60 → Rep 36.
- **Fração do excesso recuperada** (H − Rep)/(H − B): mediana **92.7%** (n = 57).
- **Verificação (H-P3):** 60/60 soluções verificadas e não piores que a inicial. **Convergência:** 60/60; tempo mediano da busca 1.95 s (máx. 17.6 s); iterações medianas 28.
- **Rep × nível de peça:** mediana **+0.049%** (IC 95% [-0.061%; +0.159%]); Rep < P em 25/60.

## Holm (α = 0,05; t = 1,0 s)
| hipótese | p | ajustado | decisão |
|---|---:|---:|---|
| H-P1 | 3.436e-10 | 6.871e-10 | rejeita H0 (predição sustentada) |
| H-P2 | 0.0001548 | 0.0001548 | rejeita H0 (predição sustentada) |

## Resumo das predições (t = 1,0 s)

- H-P1 (mediana de Rep/B − 1 ≤ 3%): +0.562% → SUSTENTADA (p bruto 3.436e-10).
- H-P2 (redução mediana ≥ 5%): 8.64% → SUSTENTADA (p bruto 0.0001548).
- H-P3 (100% verificadas e não piores): 60/60 → SUSTENTADA.
- H-P4 (descritiva; fração recuperada ≥ 50%): 92.7% → dentro.
- H-P5 (descritiva; ≥ 95% convergem; tempo mediano ≤ 5 s): 100.0%; 1.95 s → dentro.
- H-P6 (descritiva; Rep/P − 1 em [−0,5%; +1,0%]): +0.049% → dentro.

## Por categoria (t = 1,0 s)
| categoria | n | Rep/B − 1 | H/B − 1 | redução | Rep/P − 1 |
|---|---:|---:|---:|---:|---:|
| regular | 12 | +0.625% | +10.586% | 9.32% | +0.047% |
| irregular | 12 | +0.617% | +10.962% | 9.18% | +0.617% |
| hole | 12 | +0.687% | +9.090% | 7.43% | -0.277% |
| esicup | 24 | +0.203% | +9.130% | 7.03% | -0.055% |
