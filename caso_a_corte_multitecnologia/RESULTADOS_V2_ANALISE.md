# Análise pré-registrada do conjunto V2 (`docs/17`)

Arquivos em V2: 49; com < 2 contornos fechados (excluídos pela regra do protocolo): 2 (ontour_nesting__cj1x_9__cj1x_9, x_outer_contours__sce_6__sce_6); **analisados: 47**.

## H-V1 — viabilidade
Solução de segmento verificada (t = 0): **47/47** = 100.0% (critério ≥ 95%). t = 1 s: 47/47.

Layouts com arestas compartilhadas (o corte do segmento é menor): 0/47; sem: 47.

## H-V2 — tempo de ar (t = 0; layouts sem arestas compartilhadas, n = 47)
Redução relativa do tempo de ar do segmento sobre a peça: mediana **56.5%** (média 47.3%), IC 95% bootstrap da mediana [35.6%; 65.1%]. Wilcoxon unilateral (H0: redução < 20%): p = 1.293e-07. Segmento menor em 44/47.

(Descritivo, todos os layouts, n = 47): redução mediana do ar 56.5%.

## H-V3 — tempo total (t = 0)
Segmento ≤ peça em **44/47** layouts (93.6%; critério ≥ 75%); binomial unilateral contra 0,75: p = 0.0009898. Nos layouts sem arestas compartilhadas: 44/47. Gap de FO (mediana): -0.301% (sem compartilhadas: -0.301%).

## H-V4a — regret entre tecnologias (n = 47)
Excesso de tempo total ao usar a rota de t = 0 com t = 1 s: mediana **1.304%** (máx. 3.90%); IC 90% bootstrap [1.052%; 1.863%]; Wilcoxon unilateral (H0: ≤ 0,2%): p = 1.35e-13.

## H-V4b — vantagem do segmento sobre a peça com t = 1 s (descritiva)
Mediana +0.024% (IC 95% [-0.019%; +0.045%]); critério descritivo: entre −0,1% e +0,1%. Segmento menor em 18/47.

## Predição qualitativa — perfurações
Menos perfurações com t = 1 s que com t = 0 em **47/47** (100.0%; critério ≥ 80%). Mediana de perfurações: t = 0: 99; t = 1 s: 60; contornos: 57.

## Holm (α = 0,05)
| hipótese | p | ajustado | decisão |
|---|---:|---:|---|
| H-V4a | 1.35e-13 | 4.05e-13 | rejeita H0 (predição sustentada) |
| H-V2 | 1.293e-07 | 2.586e-07 | rejeita H0 (predição sustentada) |
| H-V3 | 0.0009898 | 0.0009898 | rejeita H0 (predição sustentada) |

## Resumo das predições

- H-V1 (≥ 95% viáveis): SUSTENTADA (100.0%).
- H-V2 (redução mediana do ar ≥ 20%, sem arestas compartilhadas): mediana 56.5%, limite inferior do IC 35.6% → SUSTENTADA (p Holm: ver tabela).
- H-V3 (≥ 75% dos layouts com segmento ≤ peça): 93.6% → SUSTENTADA (p bruto 0.0009898).
- H-V4a (regret mediano ≥ 0,2%): 1.304%, limite inferior do IC 90% 1.052% → SUSTENTADA.
- H-V4b (descritiva): mediana +0.024% → dentro de ±0,1%.
- Predição qualitativa (perfurações): 100.0% → SUSTENTADA.

## Controle de orçamento
Segmento (t = 0) sobre o PCGLNS por peça com o MESMO orçamento: tempo total, mediana -0.301% (n = 47); segmento menor em 44/47.

## Por categoria
| categoria | n | redução mediana do ar (t = 0) | gap de FO mediano |
|---|---:|---:|---:|
| Combined_parts | 18 | 56.6% | -0.299% |
| No_precedence | 29 | 49.9% | -0.318% |
