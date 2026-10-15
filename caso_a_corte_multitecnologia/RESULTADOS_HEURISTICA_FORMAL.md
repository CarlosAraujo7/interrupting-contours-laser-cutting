# A heurística do LCPP sob a FO formal do LCPP-1 (Eq. 3) e sob custo de reinício — 282 instâncias com caminho guardado (282 com GTSP e PCGLNS por peça honestos)

Busca local forte (3 s, semente 0). **poligonal** = caminho executável como emitido (saltos contados); **formal** = corda direta entre serviços consecutivos, orientação por DP (`docs/18` §7).

- FO poligonal sobre a FO listada pelo código: mediana +0.363% (média +0.358%).
- FO formal sobre a poligonal: mediana -0.018% (média -0.082%); formal ≤ poligonal em 282/282.

## t = 0 (convenção do LCPP-1): heurística × PCGLNS por peça × GTSP de arcos

| comparação | mediana | média | vitórias do primeiro |
|---|---:|---:|---:|
| heurística poligonal × PCGLNS por peça | -0.470% | -0.929% | 253/282 |
| heurística formal × PCGLNS por peça | -0.503% | -1.012% | 277/282 |
| heurística formal × GTSP de arcos (PCGLNS, 2 rodadas) | -0.049% | -0.041% | 186/282 |
| heurística poligonal × GTSP de arcos | -0.010% | +0.042% | 150/282 |

### Por categoria (heurística formal)
| categoria | n | × peça (mediana) | vitórias | × GTSP (mediana) | vitórias |
|---|---:|---:|---:|---:|---:|
| regular | 50 | -0.685% | 50/50 | -0.107% | 45/50 |
| irregular | 50 | -0.529% | 50/50 | -0.017% | 33/50 |
| hole | 50 | -0.225% | 45/50 | +0.024% | 19/50 |
| esicup | 132 | -0.513% | 132/132 | -0.068% | 89/132 |

## t > 0 — tempo total (corte + ar + t·corridas)

Heurística: ordem de serviço fixa, orientação re-otimizada por DP para cada t (formal). Peça: PCGLNS por peça + t·(nº de contornos) (a rota de peça não muda com t: Proposição 1). **GTSP(t = 0) avaliado em t = limite superior do ótimo ciente de t** (a rota de t = 0 com o seu nº de corridas).

| t (s) | corridas da heurística (mediana) | corridas do GTSP(0) (mediana) | contornos (mediana) | heurística × peça | heurística × GTSP(0)@t | GTSP(0)@t × peça |
|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 54 | 51 | 31 | -0.503% (277/282) | -0.049% (186/282) | -0.463% (282/282) |
| 0.25 | 54 | 51 | 31 | +2.340% (77/282) | +0.161% (96/282) | +2.092% (75/282) |
| 0.5 | 54 | 51 | 31 | +5.108% (70/282) | +0.313% (90/282) | +4.521% (61/282) |
| 1.0 | 54 | 51 | 31 | +9.889% (47/282) | +0.590% (87/282) | +8.698% (39/282) |

## Retomadas × inícios virgens (heurística, t = 0.0; `docs/18` §4.2)
Fração das corridas que **recomeçam num vértice já cortado** (retomada: custo de *pre-cut*/reinício, não de perfuração no modelo de Dewil): mediana 48.7% (quartis 47.1-49.2%).
Inícios virgens (perfurações físicas no modelo de Dewil): mediana 28; contornos: mediana 31.
