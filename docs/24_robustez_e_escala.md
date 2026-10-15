# 24 — Robustez da avaliação e escala (exploratório; predições registradas antes dos dados)

**Escrito em 13/10/2026, antes de qualquer resultado destas três checagens.** Aprovado por Carlos ("pode seguir com essa sequência recomendada") com **8 processos** como piso. São checagens de **ressalvas** do N1 (`docs/22` §3, itens 2 e 4), não testes de hipóteses novas; sem correção de multiplicidade; medianas e contagens.

## 1. Três checagens

**(a) Heurística reexecutada com a máquina livre.** As 282 rodadas da heurística do LCPP (`busca_local_forte`, 3 s, semente 0) usadas em todo o N1 foram gravadas **com a máquina compartilhada**; a busca local forte é limitada por relógio. Reexecuta-se o mesmo pipeline (cópia temporária do LCPP-main; não alterado nem importado) com 8 processos → `auditoria_lcpp1/caminhos_282_reexec/`; **a rodada gravada continua sendo a usada** (congelada em `docs/19`/`docs/23`); a reexecução só mede a sensibilidade. *Predição:* mediana de |ΔFO formal| ≤ 0,1% e vitórias sobre a referência de peça iguais a ±5 em 282.

**(b) Robustez da referência de nível de peça.** A referência (PCGLNS por peça do pipeline do LCPP-1, FO honesta) usou 1 semente × 20 s. Nas 60 instâncias do V3: 3 sementes × 60 s (`auditoria_lcpp1/pecas_robustez/`). *Predição:* o melhor das sementes melhora a referência em mediana ≤ 0,05% e as vitórias da heurística (formal, t = 0) mudam em ≤ 2 de 60.

**(c) Escala (> 300 arcos).** Nos 10 maiores layouts do CPPLib de desenvolvimento (E = 580 … 374 arcos; `rodar_escala.py`): o mesmo GTSP de arcos (Π de fechamento, t = 0, portais reduzidos, 1 rodada, semente 0) com PCGLNS 120 s e 600 s; compara FO honesta e tempo de ar. *Predições:* P-E1 — a mediana do ganho de **tempo total** de 600 s sobre 120 s é ≤ 0,2% (diluição); P-E2 — a mediana do ganho em **tempo de ar** é ≥ 5% (o PCGLNS não converge em 120 s nos layouts grandes). Só entram soluções verificadas.

## 2. Condições e ressalvas

8 processos (preferência de Carlos), máquina livre (verificada pela lista de processos antes do lançamento; **não** se rodou `preparar_v3.py` para não sobrescrever o manifesto do V3). Com 8 processos o orçamento de relógio do PCGLNS rende menos por processo que nas rodadas de 3-5 processos; em (c) a comparação 120 s × 600 s é feita **dentro da mesma rodada**; em (b) 60 s ≫ tempo de convergência dos clusters ≤ 175. A reexecução (a) usa 8 processos contra 2 da rodada gravada (sob carga alheia).

## 3. Código (SHA-256, 13/10/2026)

| arquivo | SHA-256 |
|---|---|
| `rodar_escala.py` | `f68225d5e0f0e36f94851fec4b005d8b71f56b7782ccca17627551bda7c1f289` |
| `comparar_robustez.py` | `851d30dfc06a4d4949bb1907ee4e0f3e33a5a824a61e6871a0ba662f45812e79` |
| `auditoria_lcpp1/auditoria_pecas_robustez.py` | `1fbf829c3c5b54817973858466248cf77f7fdafe2a5cec59afd3dfb2f490a87e` |
| `auditoria_lcpp1/caminhos_heuristica_282.py` (= o de `docs/19`) | `d1fd017a6f4c2fe10791b338cc780c78a910533649ade367c335e74c81dd0bb8` |
| `auditoria_lcpp1/nomes_amostra_v3.txt` | `21393384cff420621a4b8c9a11bde8fd8a9efe540ff51979cbfeda4c7a69fc30` |

## 4. Execução (aba de terminal; uma linha de PowerShell encadeada — a política de execução do sistema bloqueia scripts `.ps1`, e **não foi alterada**)

Em sequência, 8 processos cada: (a) ~8-10 min; (b) 180 tarefas × 60 s ≈ 25 min; (c) 20 tarefas (10 de 600 s e 10 de 120 s) ≈ 25-30 min. Total ≈ 1 h. Análise: `python comparar_robustez.py > RESULTADOS_ROBUSTEZ.md` e `python rodar_escala.py resumo > RESULTADOS_ESCALA.md`.

## 6. Resultados (13/10/2026; `RESULTADOS_ROBUSTEZ.md`, `RESULTADOS_ESCALA.md`; hashes de §3 conferidos intactos DEPOIS; 8 processos; as três etapas em ~35 min)

**(a) Heurística reexecutada com a máquina livre (282):** FO formal **idêntica em 246/282**; menor em 14, maior em 22; |máx.| **0,231%**; a t = 1 s |máx.| 4,92% (orientações/DP em uma instância). **Vitórias sobre a referência de peça: formal 277 → 279; poligonal 253 → 254.** *Predição* (mediana de |ΔFO| ≤ 0,1%; vitórias ±5): **sustentada.** A rodada gravada continua a usada no N1.

**(b) Referência de peça, 3 sementes × 60 s (60 instâncias):** o melhor das sementes melhora a referência em **mediana 0,0000%** (máx. −0,1055%; melhor em 18, igual em 42, pior em 0); dispersão entre sementes: mediana 0,0047%, máx. 0,118%; **vitórias da heurística 60 → 60 (formal), 54 → 53 (poligonal).** *Predição* (melhora mediana ≤ 0,05%; vitórias ±2): **sustentada.**

**(c) Escala (10 layouts, 374-580 arcos; PCGLNS 120 s × 600 s):** tempo **total**: 600 s melhor que 120 s em **10/10**, mediana **−0,192%** (de −0,243% a −0,040%); tempo de **ar**: mediana **−30,2%** (de −14,2% a −42,7%). *Predições:* P-E1 (ganho mediano de tempo total ≤ 0,2%): **sustentada** (0,192%, por pouco); P-E2 (ganho mediano de ar ≥ 5%): **sustentada**. **Leitura:** o PCGLNS **não converge em 120 s** nos layouts grandes; a diluição esconde isso no tempo total (≤ 0,25%), mas **o ar fica ~30% acima** — as reduções de ar de nível de segmento reportadas para layouts grandes (−8% nas > 300 arcos em `docs/16`) são **conservadoras**. As soluções de 600 s seriam a referência certa; não foram usadas nos números já reportados.

## 5. Desvios e esclarecimentos (datados)

- **13/10/2026:** `rodar_escala.py` (congelado) importa `heuristic_core` sem `src_base` no `sys.path` no modo `resumo`; **não foi alterado**: rodou-se com `PYTHONPATH=../src_base`. A política de execução do sistema bloqueia `.ps1`; usou-se uma linha encadeada na aba de terminal c5.
