# Tempo de ar (parcela não cortante) — 84 layouts do CPPLib

Os gaps de FO do E-A0 diluem as diferenças pelo tempo de corte (constante). Aqui, o tempo de AR = FO − L/v_cut (peça) ou a soma dos segmentos 'd' (nativo de segmento), em s. Referência de **peça** (com Π): PCGLNS; referência de **segmento** (sem Π): TSH.

Participação do ar na FO do PCGLNS (mediana): 0.58% (min 0.39%, máx 1.43%).

## Nível de peça (com Π): gap do tempo de ar sobre o PCGLNS

| método | gap de FO (mediana) | **gap do tempo de ar (mediana)** | **média** | melhor / pior que o PCGLNS (nº de layouts) |
|---|---:|---:|---:|---:|
| heurística (construção com Π) | +0.84% | +140.9% | +143.3% | 0 / 84 |
| construção + busca local | +0.26% | +46.4% | +43.6% | 0 / 81 |
| construção + VNS | +0.06% | +8.4% | +14.5% | 0 / 73 |
| VNS-Π | +0.03% | +4.2% | +8.5% | 0 / 72 |
| MASTRI (viola Π) | +0.46% | +80.6% | +80.8% | 0 / 84 |

## Nível de segmento: gap do tempo de ar sobre o TSH (sem Π)

| método | **gap do tempo de ar (mediana)** | **média** | melhor / pior que o TSH |
|---|---:|---:|---:|
| heurística, modo original, ar **listado** (como a FO do LCPP-main; caminho NÃO contíguo) | -42.9% | -42.3% | 84 / 0 |
| heurística, modo original, ar listado **+ saltos** (limite inferior do custo real) | +183.0% | +192.4% | 0 / 84 |
| heurística com Π (construção; caminho contíguo) | +398.8% | +467.4% | 0 / 84 |
| PCGLNS (peça inteira, com Π) | +112.0% | +140.8% | 0 / 84 |

## Controle: o comprimento de corte é o mesmo?

Diferença relativa do comprimento de corte, heurística (nativo) × TSH: mediana 0.000%, máx 5.079%; soma dos lados dos contornos × TSH (arestas deduplicadas): mediana 0.000%, máx 0.000%.
Perfurações (corridas de corte), mediana: TSH 96; heurística original 51; heurística com Π 53; nº de peças 53.
