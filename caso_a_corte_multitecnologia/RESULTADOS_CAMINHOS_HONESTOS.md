# Caminhos honestos (contíguos) e verificação — 84 layouts do CPPLib

Cada caminho foi tornado contíguo (`caminho_honesto.contiguar`) e verificado (`caminho_honesto.verificar`): contiguidade, origem, cada aresta distinta cortada exatamente uma vez, e violações de Π sob a semântica **estrita** (todo segmento do contorno interno antes do PRIMEIRO segmento do externo) e **relaxada** (antes do ÚLTIMO segmento do externo: a restrição física).

| método | caminho passa na verificação | saltos inseridos (mediana) | ar honesto (mediana, unid.) | perfurações (mediana) | pares de Π violados: estrita (mediana, % dos pares) | relaxada (mediana, % dos pares) |
|---|---:|---:|---:|---:|---:|---:|
| TSH (sem Π) | 84/84 | 0 | 2476 | 96 | 52 (98.1%) | 14 (43.0%) |
| heurística, modo original (sem Π) | 82/84 | 60 | 7204 | 94 | 48 (96.0%) | 0 (3.6%) |
| heurística com Π (construção) | 82/84 | 0 | 12044 | 53 | 0 (0.0%) | 0 (0.0%) |

Layouts em que o caminho do TSH (que ignora Π) **já satisfaz** todo o Π: semântica relaxada 14/84; estrita 0/84.
Média de pares de Π por layout: 54.7.
Ar honesto de `heur_orig` sobre o do TSH: mediana +183%.
Ar honesto de `heur_pi` sobre o do TSH: mediana +399%.
