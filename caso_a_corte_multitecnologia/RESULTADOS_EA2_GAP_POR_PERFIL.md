# E-A2 (complemento) -- o gap de rota em cada perfil de tecnologia (k = 1.0; 11 instancias comparaveis do piloto, FO a T = 30 s)

Gap de cada metodo sobre o PCGLNS, no TEMPO TOTAL de cada perfil, com as mesmas rotas. O corte e a perfuracao por contorno sao constantes; so o tempo em vazio muda entre os metodos, e seu peso relativo depende do perfil. Aproximacao: n_perf = n_pecas. **Escala `k` NAO confirmada** (sensibilidade: `--k`). O laser original do LCPP e em unidades do DXF (k nao se aplica).

| perfil | fracao nao cortante (mediana) | VNS-Pi | heuristica + busca local | heuristica (construcao) |
|---|---:|---:|---:|---:|
| laser (LCPP original) | 0.53% | +0.05% | +0.21% | +0.74% |
| plasma 45A 24GA (~0.6mm) | 3.97% | +0.41% | +1.57% | +5.55% |
| plasma 45A 16GA (~1.5mm) | 4.47% | +0.31% | +1.20% | +4.24% |
| plasma 45A 14GA (~1.9mm) | 4.89% | +0.28% | +1.07% | +3.81% |
| plasma 45A 10GA (~3.4mm) | 3.99% | +0.16% | +0.62% | +2.20% |
| plasma 45A 3/16in (~4.8mm) | 3.12% | +0.11% | +0.41% | +1.47% |
| plasma 45A 1/4in (~6.4mm) | 1.99% | +0.06% | +0.24% | +0.84% |
| plasma 45A 3/8in (~9.5mm) | 1.69% | +0.04% | +0.16% | +0.58% |
| plasma 45A 1/2in (~12.7mm) | 1.10% | +0.02% | +0.09% | +0.32% |

Leitura: a coluna 'heuristica (construcao)' no laser e o gap do E-A0 (~+0,7%); no plasma fino a MESMA rota custa varias vezes mais em tempo total, porque o corte e rapido e o deslocamento pesa mais. A rota otima, porem, e a mesma em todos os perfis.
