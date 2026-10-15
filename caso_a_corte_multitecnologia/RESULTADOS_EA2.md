# E-A2 -- teto de ganho do roteamento (fracao do tempo fora do corte) -- 83 instancias do CPPLib com precedencia

Fracao nao cortante = (tempo em vazio + tempo de perfuracao) / tempo total, com a rota da heuristica proposta (construcao com Pi). E o TETO do que qualquer otimizacao de rota pode economizar (o corte e constante). `k` = mm por unidade do DXF (**escala NAO confirmada**; o laser original do LCPP e em unidades do DXF e nao depende de k). Mediana [min; max] sobre as instancias. Criterio G1 do plano 07: >= 5% em pelo menos um perfil.

| perfil | k = 0.1 | k = 0.5 | k = 1.0 | k = 2.0 |
|---|---:|---:|---:|---:|
| laser (LCPP original) | 1.39% [0.83; 2.86] | (= k independente) | (= k independente) | (= k independente) |
| plasma 45A 24GA (~0.6mm) | 9.88% [6.13; 18.65] | 9.88% [6.13; 18.65] | 9.88% [6.13; 18.65] | 9.88% [6.13; 18.65] |
| plasma 45A 16GA (~1.5mm) | 19.25% [13.21; 28.60] | 10.31% [7.23; 17.71] | 9.01% [6.03; 16.35] | 8.34% [5.40; 15.65] |
| plasma 45A 14GA (~1.9mm) | 24.93% [17.16; 39.01] | 11.85% [8.10; 18.72] | 9.41% [6.58; 16.28] | 8.21% [5.48; 15.01] |
| plasma 45A 10GA (~3.4mm) | 25.28% [16.57; 40.66] | 9.83% [6.62; 14.94] | 7.16% [4.81; 11.66] | 5.62% [3.88; 10.03] |
| plasma 45A 3/16in (~4.8mm) | 21.40% [13.56; 35.75] | 7.53% [4.94; 12.03] | 5.34% [3.54; 8.57] | 4.02% [2.75; 7.14] |
| plasma 45A 1/4in (~6.4mm) | 15.37% [9.35; 27.19] | 4.74% [3.13; 8.18] | 3.38% [2.21; 5.37] | 2.48% [1.66; 4.33] |
| plasma 45A 3/8in (~9.5mm) | 14.03% [8.33; 25.27] | 4.02% [2.56; 7.19] | 2.71% [1.78; 4.30] | 1.93% [1.28; 3.27] |
| plasma 45A 1/2in (~12.7mm) | 9.90% [5.70; 18.62] | 2.59% [1.63; 4.87] | 1.69% [1.09; 2.81] | 1.18% [0.77; 1.95] |

Decomposicao (mediana, k = 1): fracao em vazio / fracao em perfuracao

| perfil | em vazio | em perfuracao |
|---|---:|---:|
| laser (LCPP original) | 1.39% | 0.00% |
| plasma 45A 24GA (~0.6mm) | 9.88% | 0.00% |
| plasma 45A 16GA (~1.5mm) | 7.65% | 1.33% |
| plasma 45A 14GA (~1.9mm) | 6.92% | 2.39% |
| plasma 45A 10GA (~3.4mm) | 4.08% | 2.80% |
| plasma 45A 3/16in (~4.8mm) | 2.73% | 2.35% |
| plasma 45A 1/4in (~6.4mm) | 1.57% | 1.61% |
| plasma 45A 3/8in (~9.5mm) | 1.08% | 1.49% |
| plasma 45A 1/2in (~12.7mm) | 0.60% | 1.02% |

**Criterio G1 (mediana >= 5% em algum perfil, k = 1):** ATENDIDO; maior fracao mediana: plasma 45A 24GA (~0.6mm) = 9.88%.
Menor fracao mediana (k = 1): laser (LCPP original) = 1.39%.
