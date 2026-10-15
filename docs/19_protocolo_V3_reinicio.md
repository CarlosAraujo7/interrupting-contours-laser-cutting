# 19 — Protocolo pré-registrado do V3 (custo de reinício: GTSP ciente de t × heurística do LCPP × nível de peça)

**Escrito em 12/10/2026, ANTES de qualquer resultado de V3 existir** (`v3_resultados/` vazio). Código e script de análise congelados por SHA-256 (§7); desvios entram em §9, datados. Mesmo regime dos protocolos `docs/10`, `docs/11`, `docs/17` (não é pré-registro externo).

## 1. Pergunta e estatuto dos dados já vistos

**Pergunta.** Nas instâncias do LCPP-1 (heurística e GTSP de arcos já avaliados a t = 0), o que acontece quando reiniciar o corte custa t > 0 (`docs/18` §4.2: custo de reinício = perfuração ou *pre-cut*)? (a) Ignorar t (rota de t = 0) custa quanto? (b) A heurística do LCPP, cega a t, perde para uma solução ciente de t? (c) A vantagem do nível de segmento sobre o de peça sobrevive a t > 0?

**Dados já vistos (exploratórios; declarados):** nas 282 instâncias, (i) os resultados a t = 0 de peça, heurística e GTSP de arcos (`docs/16` §3.1); (ii) a avaliação da heurística (caminho guardado) sob a FO formal e a t ∈ {0,25; 0,5; 1,0} e da rota do GTSP de t = 0 avaliada a t (`RESULTADOS_HEURISTICA_FORMAL.md`): **a vantagem de t = 0 do nível de segmento sobre o de peça (−0,50%, mediana) se inverte para t ≳ 0,05 s se a rota for cega a t**: heurística × peça = +2,3% (t = 0,25 s; vence em 77/282), +5,1% (0,5 s), +9,9% (1,0 s; 47/282); a heurística faz 54 corridas (mediana) contra 31 contornos e 48,7% das suas corridas recomeçam em vértice já cortado (`docs/18` §7). **Não visto:** nenhuma solução do GTSP **ciente de t** (V3). As predições abaixo sobre o V3 foram fixadas antes de qualquer execução.

## 2. Conjunto

Amostra estratificada das 282 instâncias (`rodar_v3.amostra()`; semente 2027): regular 12, irregular 12, hole 12, esicup 24 = **60** (lista em `rodar_v3.py listar`). Critério de exclusão (fixado antes): instância sem solução verificada em V3 para o t considerado (reportar quantas).

## 3. Métodos e orçamentos

- **G(t), V3:** GTSP de arcos orientados + PCGLNS com custo de reinício t em cada interrupção (arco `a → b` custa `d/v_ar + t` se não contínuo; 0 se contínuo), Π de **fechamento** por contenção, *noding*, portais reduzidos, 2 rodadas (a 2ª com a última aresta de cada contorno como aresta de fechamento), `-max_time = min(120, 20 + arcos/4)` s por rodada; t ∈ {0,25; 1,0} s. Só entra solução que passa **toda** a verificação (`caminho_honesto.verificar`: contígua, origem, cobertura geométrica, Π de fechamento sem violações). É o método **congelado** de `docs/17` com `t_perf = t` (o código é `rodar_v3.py`, derivado de `rodar_lcpp1_segmento.py`).
- **G0(t):** a solução de t = 0 (`lcpp1_segmento_resultados`), avaliada a t (FO(0) + t · corridas).
- **H(t):** heurística do LCPP (original `busca_local_forte`, 3 s, semente 0; pipeline do LCPP-1 numa cópia temporária, sem alterar nem importar o LCPP-main), **FO formal** (Eq. 3 do LCPP-1: cordas diretas entre serviços consecutivos; orientação por DP exata, re-otimizada para cada t).
- **P(t):** PCGLNS por peça (FO a t = 0 com pernas da origem, `auditoria_lcpp1/honesta_282`) + t · nº de contornos (a rota de peça não muda com t: Proposição 1).
- **B(t) = min(G(t), G0(t))**, a melhor solução de segmento verificada conhecida.
- Ambiente: o do `ENVIRONMENT.md`; 3 processos; tempos de relógio; pré-voo `preparar_v3.py` (recusa máquina ocupada/pouca memória/fora da tomada; nunca mata processos de terceiros). Se o pré-voo for forçado, declarar em §9.

## 4. Medidas

Tempo total (corte + ar + t · corridas); nº de corridas; retomadas (corridas que recomeçam em vértice já cortado) × inícios virgens; unidade de análise = a **instância**.

## 5. Hipóteses, predições e regras de decisão (t primário = 1,0 s; t = 0,25 s descritivo; Holm sobre {H-W1, H-W2, H-W3}, α = 0,05)

- **H-W1.** Em ≥ 80% das instâncias, G(1,0) tem **menos corridas** que G0 (binomial unilateral contra 0,80).
- **H-W2 (regret de ignorar o reinício).** Mediana de G0(1,0)/B(1,0) − 1 **≥ 0,3%** (Wilcoxon unilateral contra 0,003; IC bootstrap 95% da mediana com limite inferior ≥ 0,3%).
- **H-W3 (heurística cega a t).** Mediana de H(1,0)/B(1,0) − 1 **≥ 0,5%** (Wilcoxon unilateral contra 0,005; IC bootstrap com limite inferior ≥ 0,5%).
- **H-W4 (descritiva).** B(1,0)/P(1,0) − 1: predição de mediana em [−0,5%; +0,3%]; relatar a fração de instâncias com B < P.
- **H-W5 (descritiva).** Retomadas < 20% das corridas de G(1,0); relatar instâncias com mais inícios virgens que contornos (contorno perfurado duas vezes).
- **Não se alega:** efeito de perfuração física (t é custo de reinício); validade absoluta dos tempos (t não calibrado); vantagem sob a Π estrita; nada sobre as 222 instâncias fora da amostra.

## 6. Análise e relato

`analise_v3.py` (escrito antes dos resultados): Wilcoxon, binomial, bootstrap (10.000 reamostras), Holm; relatar **todas** as exclusões, os casos em que o segmento perde e a tabela por categoria. Saída: `RESULTADOS_V3_ANALISE.md`.

## 7. Código congelado (SHA-256)

**Congelado em 13/10/2026, antes de qualquer execução do V3** (`v3_resultados/` inexistente):

| arquivo | SHA-256 |
|---|---|
| `rodar_v3.py` | `602a69d2d6fe9f0687b176d7a0fa174619ba56a4dfe448521af8ccba9ef031db` |
| `analise_v3.py` | `32375fc7d81efb342200d34368ad2ccf465cdbcc5765b592c058668906e0601c` |
| `preparar_v3.py` | `4c3180eb619368a9d4f0d9041a6f38b03d2b49c9126d19781ed8f0e3805b806d` |
| `avaliar_heuristica_formal.py` | `46863612de5d3ca9331341d89616bb1a2522926f5866b4bffc11ce91f71d2ba3` |
| `segmento_gtsp.py` (= V2) | `c05afffa48356ac107ac204cd51dc5f577422d9301a99085aaf10ea2150201c3` |
| `caminho_honesto.py` (= V2) | `e2469fb46368e7307e92f42a2892a682f93d417e7368ed8ef0a68a9c69782067` |
| `instancias_lcpp1.py` (= V2) | `daf7fb2d6d3ed586d0a88e775effccd328727e09d7dd9c146cf241f643311526` |
| `tsh_segmento.py` (= V2) | `3ce73694f51712812de6cb0f0235fd89fdeadc4817fcc6fda3814f5b3471c246` |
| `lancar_v3.sh` | `3750ec4639937ae45ba81d18690e6146aed782fd71fd67c0c0592a804f9a56ad` |
| `src_base/heuristic_core.py` | `f829b721aadc1571981ba9b336f43c515406892a77d4bb43fdc40b3cd61fbc58` |
| `auditoria_lcpp1/caminhos_282/*.json` (282 arquivos; hash da concatenação em ordem `LC_ALL=C`) | `ba21b1f223eca8ea7343e9c70df2869d77b1a751e3ee10a8fbf76e0ae031fef8` |

(Dependências não congeladas aqui: `ferramentas/PCGLNS_upstream` [commit `bc09d9d`], `requirements.txt`; `lcpp1_segmento_resultados/`, `auditoria_lcpp1/honesta_282/` são entradas já existentes e não são alteradas.) Conferir com `sha256sum` antes e depois da execução.

## 8. Execução

`bash lancar_v3.sh` (pré-voo + manifesto `v3_manifesto.json` + 3 processos; idempotente; ~3-5 h).

## 10. Resultados (13/10/2026; `RESULTADOS_V3_ANALISE.md`; hashes de §7 conferidos intactos DEPOIS da execução)

120 tarefas concluídas (60 instâncias × t ∈ {0,25; 1,0}); **60/60 com solução verificada em ambos os t**; execução em máquina livre (pré-voo sem `--forcar`), 3 processos (a execução foi interrompida uma vez e retomada; ver §9). **Todas as predições pré-registradas foram sustentadas** (Holm sobre H-W1…H-W3, t = 1,0 s):

| hipótese | resultado (t = 1,0 s) | decisão |
|---|---|---|
| H-W1 corridas: G(t) < G0 em ≥ 80% | **60/60** (100%); mediana de corridas 60 → 31 (contornos: 37); p Holm 1,5·10⁻⁶ | sustentada |
| H-W2 regret de ignorar o reinício ≥ 0,3% | mediana **10,06%** (IC 95% [9,23; 10,34]; máx. 33,4%); p Holm 4,4·10⁻¹⁰ | sustentada |
| H-W3 heurística (formal) ≥ 0,5% acima de B | mediana **+10,21%** (IC 95% [9,70; 10,95]); heurística ≤ B em 3/60; p Holm 4,4·10⁻¹⁰ | sustentada |
| H-W4 (descritiva) B/P − 1 em [−0,5%; +0,3%] | mediana **−0,041%** (IC 95% [−0,150; −0,007]); B < P em 42/60 | dentro |
| H-W5 (descritiva) retomadas < 20% das corridas | **10,7%**; instâncias com mais inícios virgens que contornos: **0/60** | dentro |

A t = 0,25 s: regret 2,44% (IC [2,26; 2,64]), heurística +2,54% acima de B, B/P −0,114% (B < P em 46/60), retomadas 19,4%. Por categoria (t = 1,0): regret 8,9% a 10,6% e B/P entre −0,002% e **−1,63% (hole)**. **Leitura:** a rota ciente do reinício **recupera a estrutura de uma corrida por contorno** (31 corridas para 37 contornos: corridas < contornos onde há arestas comuns) e fica no nível da referência de peça (−0,04%); a rota cega a t (a de t = 0, ou a heurística) perde ~10% a t = 1 s. **Nenhum contorno é perfurado duas vezes** nas soluções do V3 (0/60 com virgens > contornos) — a hipótese usada em `docs/18` §4.2 para equiparar o nosso `t` por corrida ao modelo de Dewil (a menos de uma constante) é verificada nesta amostra.

## 9. Desvios e esclarecimentos (datados)

- **13/10/2026, lançamento:** hashes de §7 **conferidos intactos antes do lançamento** (`sha256sum`; os 11 arquivos e o conjunto dos 282 caminhos coincidem); pré-voo `preparar_v3.py` passou **sem forçar** (0 rodadas pesadas de outros trabalhos; 5,9 GB disponíveis; na tomada); `bash lancar_v3_estrita.sh` às 12:19 (3 processos; 120 tarefas = 60 instâncias × t ∈ {0,25; 1,0}); manifesto `v3_manifesto.json`. Nenhum desvio até aqui.
- **13/10/2026, 12:52 — interrupção operacional e relançamento (sem efeito científico):** a pedido de Carlos (rodar em terminais visíveis, não em segundo plano do Claude), a cadeia lançada via Bash (`sh -c ...`) foi **encerrada por mim** (`taskkill /T` só nos meus processos) com **91 de 120 tarefas concluídas e gravadas**; as 29 restantes foram relançadas no terminal "c1" do app (`python -u rodar_v3.py rodar --workers 3 --ts 0.25,1.0 --rodadas 2`, seguido de `rodar_estrita.py`); o runner é idempotente (as tarefas em curso na interrupção, 3 instâncias grandes, foram refeitas do zero). Hashes inalterados.
