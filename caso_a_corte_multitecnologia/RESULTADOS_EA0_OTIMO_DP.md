# E-A0: otimo exato (DP sobre subconjuntos com precedencia) nas instancias pequenas

Instancias com 2 a 24 pecas; resolvidas pela DP (teto de 70000 estados): 9 de 14. Gap = FO media (10 sementes, T = 30 s) / FO do tour otimo do problema abstrato - 1. A FO pode diferir um pouco do custo abstrato (reclassificacao de trechos), por isso um metodo pode ficar levemente ABAIXO de zero.

| instancia | pecas | estados | FO otima | pcglns | vns_pi | heur_pi | heur_ls | heur_vns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| p1xe_7 | 5 | 10 | 307.1875 | +0.000% | +0.000% | +0.602% | +0.000% | +0.000% |
| p1xe_6 | 6 | 33 | 284.8601 | +0.000% | +0.000% | +0.737% | +0.000% | +0.000% |
| p5xe_1 | 9 | 257 | 373.3541 | +0.000% | +0.000% | +0.438% | +0.000% | +0.000% |
| p5xj_4 | 14 | 8193 | 453.6903 | +0.000% | +0.000% | +1.471% | +0.012% | +0.000% |
| p3xe_2 | 14 | 1126 | 659.8707 | +0.000% | +0.000% | +0.473% | +0.182% | +0.000% |
| p1xe_1 | 16 | 12801 | 933.7815 | -0.000% | -0.000% | +0.551% | +0.069% | -0.000% |
| p1xe_8 | 16 | 5001 | 709.6946 | +0.000% | +0.000% | +0.408% | +0.210% | +0.000% |
| p1xe_2 | 17 | 65537 | 845.2241 | +0.000% | +0.000% | +1.029% | +0.010% | +0.000% |
| p3xe_1 | 21 | 18226 | 540.5760 | +0.000% | +0.006% | +0.483% | +0.148% | +0.003% |
