# Análise pré-registrada do V3 (`docs/19`)

Amostra: 60 instâncias; com todos os insumos: 60; com solução de V3 verificada em t = 1,0: 60.

## t = 0.25 s (n = 60)

- Corridas: G(t) < G0 em **57/60** (95.0%); mediana de corridas G0 = 60, G(t) = 31, contornos = 37.
- **Regret da rota cega a t** G0(t)/B(t) − 1: mediana **2.436%** (IC 95% [2.257%; 2.635%]; máx. 11.61%).
- **Heurística do LCPP (formal) sobre B(t):** mediana **+2.535%** (IC 95% [+2.358%; +2.717%]); heurística ≤ B em 5/60.
- **Segmento (melhor conhecido) × peça** B(t)/P(t) − 1: mediana **-0.114%** (IC 95% [-0.305%; -0.023%]); B < P em 46/60. Só G(t) × peça: mediana -0.114%.
- Retomadas (corridas que recomeçam em vértice já cortado): **19.4%** das corridas; instâncias com mais inícios virgens que contornos: 0/60.

## t = 1.0 s (n = 60)

- Corridas: G(t) < G0 em **60/60** (100.0%); mediana de corridas G0 = 60, G(t) = 31, contornos = 37.
- **Regret da rota cega a t** G0(t)/B(t) − 1: mediana **10.062%** (IC 95% [9.227%; 10.344%]; máx. 33.41%).
- **Heurística do LCPP (formal) sobre B(t):** mediana **+10.210%** (IC 95% [+9.700%; +10.947%]); heurística ≤ B em 3/60.
- **Segmento (melhor conhecido) × peça** B(t)/P(t) − 1: mediana **-0.041%** (IC 95% [-0.150%; -0.007%]); B < P em 42/60. Só G(t) × peça: mediana -0.041%.
- Retomadas (corridas que recomeçam em vértice já cortado): **10.7%** das corridas; instâncias com mais inícios virgens que contornos: 0/60.

## Holm (α = 0,05; t = 1,0 s)
| hipótese | p | ajustado | decisão |
|---|---:|---:|---|
| H-W2 | 1.474e-10 | 4.421e-10 | rejeita H0 (predição sustentada) |
| H-W3 | 1.781e-10 | 4.421e-10 | rejeita H0 (predição sustentada) |
| H-W1 | 1.532e-06 | 1.532e-06 | rejeita H0 (predição sustentada) |

## Resumo das predições (t = 1,0 s)

- H-W1 (≥ 80% com menos corridas): 100.0% → SUSTENTADA (p bruto 1.532e-06).
- H-W2 (regret mediano ≥ 0,3%): 10.062% → SUSTENTADA (p bruto 1.474e-10).
- H-W3 (heurística ≥ 0,5% acima de B): +10.210% → SUSTENTADA (p bruto 1.781e-10).
- H-W4 (descritiva; predição: mediana de B/P − 1 em [−0,5%; +0,3%]): -0.041% → dentro.
- H-W5 (descritiva; predição: retomadas < 20% das corridas): 10.7% → dentro.

## Por categoria (t = 1,0 s)
| categoria | n | regret G0 | heurística sobre B | B sobre peça |
|---|---:|---:|---:|---:|
| regular | 12 | 10.609% | +10.586% | -0.025% |
| irregular | 12 | 9.765% | +10.962% | -0.002% |
| hole | 12 | 9.990% | +9.090% | -1.626% |
| esicup | 24 | 8.920% | +9.130% | -0.071% |
