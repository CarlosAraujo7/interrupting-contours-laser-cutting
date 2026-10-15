# E-A0 -- investigacao dos ~0,7% (heuristica proposta vs. PCGLNS no nivel de peca)

A = tour da heuristica; B = mesma ordem de pecas com vertices de entrada OTIMOS (DP exata); C = A + busca local do VNS-Pi (descida pura, melhor de 5 sementes); D = VNS-Pi (Shake + busca local) a partir de A por T s (media de 3 sementes); P = PCGLNS (media do piloto, T=30 s); V = VNS-Pi do piloto (a partir do NearestFirst-Pi). FO no nivel de peca (`fo_from_path`); 'fecha' = fracao do gap A->P recuperada: (A - x)/(A - P).

| instancia | pecas | A heuristica | B vertices otimos (fecha) | C + busca local (fecha) | D + VNS T s (fecha) | P PCGLNS | V VNS-Pi | gap A vs. P | t heur (s) | t busca local (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| p1xe_1 | 16 | 938.9 | 936.8 (41%) | 934.2 (92%) | 933.8 (100%) | 933.8 | 933.8 | +0.55% | 2 | 0.0 |
| p1xe_8 | 16 | 712.6 | 711.2 (47%) | 711.0 (55%) | 709.7 (100%) | 709.7 | 709.7 | +0.41% | 0 | 0.0 |
| p1xj_15 | 40 | 1661.2 | 1658.7 (17%) | 1648.1 (91%) | 1647.1 (99%) | 1646.9 | 1647.0 | +0.87% | 0 | 0.2 |
| p1xj_6 | 40 | 2624.0 | 2619.0 (20%) | 2600.6 (94%) | 2599.5 (98%) | 2599.0 | 2599.0 | +0.96% | 0 | 0.1 |
| p1xk_12 | 80 | 3602.1 | 3599.9 (14%) | 3594.8 (46%) | 3592.5 (61%) | 3586.3 | 3589.8 | +0.44% | 0 | 0.5 |
| p1xk_5 | 81 | 4166.5 | 4165.1 (4%) | 4136.2 (80%) | 4135.6 (82%) | 4128.6 | 4131.8 | +0.92% | 0 | 0.9 |
| p3xj_1 | 53 | 2832.9 | 2830.1 (16%) | 2822.4 (63%) | 2821.1 (70%) | 2816.2 | 2816.5 | +0.59% | 0 | 0.2 |
| p3xj_6 | 60 | 2134.6 | 2131.4 (16%) | 2124.5 (50%) | 2120.7 (68%) | 2114.1 | 2115.4 | +0.97% | 0 | 0.2 |
| p3xk_4 | 125 | 4072.2 | 4068.6 (8%) | 4036.5 (75%) | 4037.2 (74%) | 4024.6 | 4032.7 | +1.18% | 1 | 2.4 |
| p5xj_1 | 53 | 2979.3 | 2974.5 (31%) | 2969.9 (61%) | 2969.3 (65%) | 2964.0 | 2968.3 | +0.52% | 1 | 0.6 |
| p5xj_8 | 24 | 1806.3 | 1804.3 (15%) | 1793.3 (98%) | 1793.0 (100%) | 1793.0 | 1793.0 | +0.74% | 0 | 0.0 |

Gap medio sobre o PCGLNS (media das instancias): A +0.74%; B +0.61%; C +0.18%; D +0.12%.
Fracao media do gap A->P recuperada: B 21%; C 73%; D 83%.
