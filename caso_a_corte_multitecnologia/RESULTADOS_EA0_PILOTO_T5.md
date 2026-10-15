# E-A0 -- heuristica proposta (construcao e construcao + busca local) x PCGLNS x VNS-Pi nas instancias geometricas do CPPLib (T = 5 s)

FO = `fo_from_path` (tempo em s), MESMA funcao para todos, no NIVEL DE PECA; menor e melhor; media das sementes (n entre parenteses). 'Comparavel' = a FO nativa da construcao coincide (tol. 0.0005) com a reavaliada no nivel de peca (mesmo problema que os baselines). Todas as solucoes dos metodos listados respeitam Pi (violacoes = 0), exceto onde marcado. Ver `ea0_lib.py`, `heuristica_ls.py`.

| instancia | pecas | comparavel | PCGLNS | VNS-Pi | heur. (construcao) | heur. + busca local | heur. + VNS |
|---|---:|:--:|---:|---:|---:|---:|---:|
| p1xe_1 | 16 | sim | 933.8 (n=3) | 933.8 (n=3) | 938.9 (n=1) | 934.5 (n=3) | 933.8 (n=3) |
| p1xe_8 | 16 | sim | 709.7 (n=3) | 709.7 (n=3) | 712.6 (n=1) | 711.3 (n=3) | 709.7 (n=3) |
| p1xj_15 | 40 | sim | 1646.9 (n=3) | 1647.2 (n=3) | 1661.2 (n=1) | 1648.8 (n=3) | 1647.1 (n=3) |
| p1xj_6 | 40 | sim | 2599.0 (n=3) | 2599.3 (n=3) | 2624.0 (n=1) | 2601.7 (n=3) | 2599.5 (n=3) |
| p1xk_12 | 80 | sim | 3586.3 (n=3) | 3591.6 (n=3) | 3602.1 (n=1) | 3595.0 (n=3) | 3592.5 (n=3) |
| p1xk_5 | 81 | sim | 4128.6 (n=3) | 4136.3 (n=3) | 4166.5 (n=1) | 4136.6 (n=3) | 4135.9 (n=3) |
| p3xj_1 | 53 | sim | 2816.2 (n=3) | 2817.7 (n=3) | 2832.9 (n=1) | 2824.0 (n=3) | 2821.6 (n=3) |
| p3xj_6 | 60 | sim | 2114.1 (n=3) | 2118.4 (n=3) | 2134.6 (n=1) | 2124.7 (n=3) | 2120.7 (n=3) |
| p3xk_4 | 125 | sim | 4025.0 (n=3) | 4034.5 (n=3) | 4072.2 (n=1) | 4037.1 (n=3) | 4037.2 (n=3) |
| p5xj_1 | 53 | sim | 2964.0 (n=3) | 2969.8 (n=3) | 2979.3 (n=1) | 2970.9 (n=3) | 2969.3 (n=3) |
| p5xj_8 | 24 | sim | 1793.0 (n=3) | 1793.0 (n=3) | 1806.3 (n=1) | 1793.5 (n=3) | 1793.0 (n=3) |
| p7xj_4 | 56 | **nao** | 1482.9 (n=3) | 1483.6 (n=3) | 1502.9 (n=1) | 1488.3 (n=3) | 1485.7 (n=3) |

Gap sobre o PCGLNS (FO media das sementes), so instancias comparaveis; positivo = pior que o PCGLNS; Wilcoxon pareado bilateral (zeros descartados):

| metodo | #inst | gap medio | mediana | melhor que o PCGLNS em | p (Wilcoxon) | tempo medio de parede (s) |
|---|---:|---:|---:|---:|---:|---:|
| VNS-Pi | 11 | +0.10% | +0.05% | 1 de 11 | 0.0078 | 5.2 |
| heur. (construcao) | 11 | +0.74% | +0.74% | 0 de 11 | 0.0010 | 0.7 |
| heur. + busca local | 11 | +0.21% | +0.22% | 0 de 11 | 0.0010 | 1.2 |
| heur. + VNS | 11 | +0.12% | +0.17% | 1 de 11 | 0.0078 | 5.5 |

Fora da comparacao (corte em segmentos / tecnicas especiais; a construcao explora um espaco maior que o GTSP de peca inteira): p7xj_4.
