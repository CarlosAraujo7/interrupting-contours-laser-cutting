# 23 — Protocolo pré-registrado: reparo ciente do custo de reinício da heurística do LCPP

**Escrito em 13/10/2026, ANTES de qualquer resultado do reparo na amostra do V3** (`reparo_resultados/` inexistente). Código e script de análise congelados por SHA-256 (§6); desvios entram em §8, datados. Mesmo regime de `docs/17`/`docs/19`/`docs/21` (não é pré-registro externo).

## 1. Pergunta, motivação e estatuto dos dados já vistos

**Pergunta.** O V3 (`docs/19` §10) mostrou que a heurística do LCPP, cega ao custo de reinício `t`, fica **+10,2%** (t = 1 s) acima da melhor solução de nível de segmento conhecida, B(t) = min(G(t), G0(t)). Um **reparo barato** (busca local própria sobre a ordem de serviço que ela já devolveu, em segundos) recupera a maior parte desse excesso? Se sim, o N1 passa de diagnóstico a **diagnóstico + método**: uma versão ciente do reinício da heurística, ~100× mais rápida que o PCGLNS.

**Método (`reparo_reinicio.py`).** A partir dos trechos de corte, em ordem, do caminho da heurística (busca local forte, 3 s; `auditoria_lcpp1/caminhos_282/`), minimiza a FO formal com custo de reinício `t` por corrida: flip de orientação, 2-opt com inversão, Or-opt de blocos de 1-3 serviços (direto ou invertido), DP exata das orientações no fim (o *dir-opt* de Dewil et al., 2011); melhor melhora por iteração; **parada determinística** (convergência ou `max_iter` = 5000; o limite de 120 s é só salvaguarda e é reportado); precedência de **fechamento** verificada por movimento nas instâncias com furo (posse dos servicos por contorno calculada geometricamente). Cada solução final é verificada (`caminho_honesto.verificar` + checagem geométrica de Π).

**Desenvolvimento (declarado):** o código foi escrito e depurado em **cinco instâncias FORA da amostra do V3** (`art_2_regular_pack`, `art_3_hole_sep`, `albano_pack`, `art_16_regular_pack`, `han100_pack`; t = 1 s): redução do tempo total de **−10,7%, −8,8%, −0,07%, −6,5%, −0,10%** em relação à heurística; todas convergiram em ≤ 1,5 s e foram verificadas. **Nenhuma instância da amostra do V3 foi rodada com o reparo antes do congelamento.** Os resultados do V3 (B, G, G0, H, P) já são conhecidos e entram só como referência.

## 2. Conjunto e condições

Os mesmos 60 da amostra do V3 (`rodar_v3.amostra()`), t ∈ {0,25; 1,0}. **8 processos** (preferência de Carlos), máquina livre (pré-voo); a busca é determinística (não depende do relógio), então o número de processos não afeta o resultado, só o tempo.

## 3. Medidas

Para cada instância e t: FO formal (corte + ar + t·corridas) da heurística (H) e do reparo (Rep); corridas; iterações; convergência; tempo de busca; verificação. Referências do V3: B(t) = min(G(t), G0(t)); P(t) = PCGLNS por peça + t·contornos.

## 4. Hipóteses e regras de decisão (t primário = 1,0 s; t = 0,25 s descritivo; Holm sobre {H-P1, H-P2}, α = 0,05)

- **H-P1.** Mediana de Rep/B − 1 **≤ 3%** (Wilcoxon unilateral de Rep/B − 1 − 0,03 < 0; IC bootstrap 95%). *Base:* H/B − 1 = +10,2%.
- **H-P2.** Mediana da redução (H − Rep)/H **≥ 5%** (Wilcoxon unilateral; IC bootstrap).
- **H-P3.** **100%** das soluções finais verificadas (contíguas, parte e volta à origem, cobertura geométrica, 0 violações de Π de fechamento) e **nenhuma pior** que a inicial (propriedade do código).
- **H-P4 (descritiva).** Fração do excesso recuperada, (H − Rep)/(H − B): mediana **≥ 50%**.
- **H-P5 (descritiva).** **≥ 95%** das buscas convergem (sem atingir `max_iter` nem o limite de tempo); tempo mediano de busca **≤ 5 s**.
- **H-P6 (descritiva).** Rep/P − 1 com mediana em **[−0,5%; +1,0%]**.
- **Não se alega:** que o reparo alcança B(t) em todas as instâncias; otimalidade; vantagem a t = 0 (onde a heurística já é boa); nada sobre as 222 instâncias fora da amostra.

## 5. Análise

`analise_reparo.py` (escrito antes dos resultados): Wilcoxon, bootstrap (10.000 reamostras), Holm, tabela por categoria; relatar **todas** as exclusões e os casos em que o reparo não melhora. Saída: `RESULTADOS_REPARO_ANALISE.md`.

## 6. Código congelado (SHA-256, 13/10/2026)

| arquivo | SHA-256 |
|---|---|
| `reparo_reinicio.py` | `e1bda96da2a4c21b61a0cae1454977e60a42210e9aabe5724573ad9261c0a9e8` |
| `analise_reparo.py` | `db81411640305362e4bf7b48cff0f379b0a3b4113373952a6139c0620ae0ac72` |
| `analise_v3.py` | `32375fc7d81efb342200d34368ad2ccf465cdbcc5765b592c058668906e0601c` |
| `rodar_v3.py` | `602a69d2d6fe9f0687b176d7a0fa174619ba56a4dfe448521af8ccba9ef031db` |
| `avaliar_heuristica_formal.py` | `46863612de5d3ca9331341d89616bb1a2522926f5866b4bffc11ce91f71d2ba3` |
| `segmento_gtsp.py`, `caminho_honesto.py`, `instancias_lcpp1.py` (= `docs/17`/`docs/19`) | `c05afffa…150201c3`, `e2469fb4…82067`, `daf7fb2d…311526` |
| `src_base/heuristic_core.py` | `f829b721aadc1571981ba9b336f43c515406892a77d4bb43fdc40b3cd61fbc58` |
| `v3_resultados/*.json` (120 arquivos; concatenação em ordem `LC_ALL=C`) | `42576014cf7f061fee8df1d04e64e2e81b5ad1890ea7e81e8ab368cef69b9cf3` |
| `auditoria_lcpp1/caminhos_282/*.json` (282) | `ba21b1f223eca8ea7343e9c70df2869d77b1a751e3ee10a8fbf76e0ae031fef8` |

## 7. Execução

`python reparo_reinicio.py rodar --workers 8 --ts 0.25,1.0 --amostra v3` (aba de terminal; idempotente) e `python analise_reparo.py > RESULTADOS_REPARO_ANALISE.md`. Estimativa: < 5 min.

## 9. Resultados (13/10/2026; `RESULTADOS_REPARO_ANALISE.md`; hashes de §6 conferidos intactos DEPOIS da execução; 120 tarefas, 8 processos, ~20 s no total)

**Todas as predições foram sustentadas** (Holm sobre H-P1, H-P2; t = 1,0 s; 60 instâncias):

| hipótese | resultado (t = 1,0 s) | decisão |
|---|---|---|
| H-P1 mediana de Rep/B − 1 ≤ 3% | **+0,562%** (IC 95% [+0,262; +0,901]); antes do reparo +10,210%; p Holm 6,9·10⁻¹⁰ | sustentada |
| H-P2 redução mediana ≥ 5% | **8,64%** (IC 95% [7,87; 9,28]); Rep < H em 60/60; p Holm 1,5·10⁻⁴ | sustentada |
| H-P3 100% verificadas e não piores | **60/60** (contíguas, origem, cobertura, 0 violações de Π de fechamento) | sustentada |
| H-P4 (descritiva) fração do excesso recuperada ≥ 50% | **92,7%** (n = 57) | dentro |
| H-P5 (descritiva) ≥ 95% convergem; tempo mediano ≤ 5 s | **100%**; **1,95 s** (máx. 17,6 s) | dentro |
| H-P6 (descritiva) Rep/P − 1 em [−0,5%; +1,0%] | **+0,049%** (IC 95% [−0,061; +0,159]); Rep < P em 25/60 | dentro |

A t = 0,25 s: Rep/B −1 **+0,296%** (antes +2,535%), 89,6% do excesso recuperado, Rep/P +0,022%. Corridas (mediana): heurística 60 → reparo 36 (melhor solução ciente: 31). Por categoria (t = 1): Rep/B − 1 de +0,20% (esicup) a +0,69% (hole); em `irregular` Rep/P = +0,617% (o maior desvio do nível de peça). **Leitura:** uma busca local determinística de ~2 s sobre a ordem de serviço **fecha ~93% do excesso de 10% da heurística cega ao reinício** e a deixa a +0,56% da melhor solução de nível de segmento conhecida e no nível do nível de peça — a heurística passa a ser, na prática, uma solução ciente do reinício a ~1/70 do tempo do PCGLNS sobre arcos.

## 8. Desvios e esclarecimentos (datados)

- **13/10/2026:** nenhum desvio; hashes conferidos antes (no congelamento) e depois da execução.
