# 26 — Protocolo pré-registrado: os dois níveis reotimizados para tempo de voo não linear τ(d)

**Escrito em 13/10/2026, ANTES de qualquer resultado em `tau_resultados/`.** Código e análise congelados por SHA-256 (§6); desvios em §8, datados. Aprovado por Carlos ("pode fazer a reotimização com a curva de voo"; ≥ 8 processos).

## 1. Pergunta e o que já foi visto

**Pergunta.** `docs/25` §5 mostrou, **sem reotimizar**, que a vantagem de tempo total do nível de segmento sobre o de peça desaparece sob tempo de voo com aceleração (heurística: −0,47% linear → ≈ 0% LASER → +0,04% DEWIL16; rotas cientes do reinício: −0,03% a −0,07%). Quando **os dois níveis são reotimizados para a mesma curva**, o nível de segmento ainda ganha algo em tempo total? É o análogo, no nível de segmento, do E-A1 do P1.

**Visto antes (declarado):** as avaliações de `docs/25` §5 (rotas guardadas, otimizadas para tempo linear) nas 60 instâncias da amostra do V3; e um **teste funcional** em `art_2_regular_pack` (fora da amostra; PCGLNS 15 s): nível de peça LIN próprio = **54,0083 s, igual ao FO honesto guardado do pipeline do LCPP-1** (validação do modelo de peça próprio); DEWIL16: segmento **55,537 s** contra peça **55,718 s** (−0,32%), 11 movimentos em ambos. **Nenhuma instância da amostra foi reotimizada antes do congelamento.**

## 2. Método

- **Curvas** (Chebyshev; 1 u = 1 mm, **não confirmado**; `analise_voo_nao_linear.tau`): **LASER** (trapezoidal, v = 1667 mm/s, a = 10.000 mm/s²; o perfil do E-A1) e **DEWIL16** (tempo de voo lido, de forma **aproximada**, da Fig. 3 de Dewil et al. 2016: 0,20 s a 10 mm; 0,34 a 50; 0,50 a 100; 0,60 a 200; 0,71 a 330). `t_av = 0` (reinício livre) — o efeito do reinício já está em `docs/19`.
- **Nível de peça** (`reotimizar_tau.py`): PCGLNS (30 s, semente 1) sobre o GTSP de peças inteiras de `ea0_lib.montar_instancia` (origem = cidade 1, ciclo fechado, Π estrita) com a matriz τ(d) entre cidades; é o modelo do E-A1. Também rodado com **LIN** (validação contra o FO guardado do pipeline do LCPP-1).
- **Nível de segmento:** o GTSP de arcos de `segmento_gtsp.py` (congelado, **não alterado**: arcos, grupos, portais reduzidos e Π de fechamento são os do método de `docs/17`); **só a matriz de custos** é substituída por τ(d) (0 se o corte continua). 2 rodadas (a 2ª com a última aresta de cada contorno como aresta de fechamento), `-max_time = min(120, 20 + arcos/4)` s por rodada, sementes 0 e 1; só entra solução verificada (`caminho_honesto.verificar`: contígua, cobertura, 0 violações de Π de fechamento).
- **Medida:** tempo total = corte/v_corte (sobre o caminho de cada nível) + Σ τ(d) dos movimentos em vazio (inclui as pernas de/para a origem). **Conjunto:** os 60 da amostra do V3 (`rodar_v3.amostra()`).
- **Ambiente:** 8 processos (preferência de Carlos), máquina livre; orçamentos em tempo de relógio.

## 3. Hipóteses e predições (decisão por faixa da mediana; IC 95% bootstrap relatado; sem teste de significância)

- **H-R1 (DEWIL16).** Mediana de S/P − 1 em **[−0,15%; +0,05%]**: com ambos os níveis reotimizados, a vantagem de tempo total do segmento é ≤ 0,15% e não há perda relevante.
- **H-R2 (LASER).** Idem, mesma faixa.
- **H-R3 (DEWIL16).** S ≤ G (rota guardada ciente do reinício, avaliada na curva, não reotimizada) em **≥ 75%** das instâncias.
- **H-R4 (descritiva).** Nº médio de movimentos em vazio de S ≤ **40** (H: 60; P: 38).
- **H-R5 (descritiva).** O tempo LIN do nível de peça próprio reproduz o FO honesto guardado em **≥ 95%** das instâncias (|diferença| ≤ 0,05%).
- **H-R6 (descritiva).** Mediana de P/P0 − 1 ≤ 0 (reotimizar o nível de peça para a curva não piora o guardado).
- **Não se alega:** valores absolutos em segundos; a curva DEWIL16 como a de uma máquina específica de Carlos; nada sobre as 222 instâncias fora da amostra.

## 4. Análise

`analise_tau.py` (escrito antes dos resultados): medianas, IC bootstrap (10.000), contagens, validação. Saída: `RESULTADOS_TAU_ANALISE.md`.

## 5. Execução

Aba de terminal, 8 processos: `python -u reotimizar_tau.py rodar --workers 8` (idempotente). Estimativa: 240 tarefas (120 de segmento ≈ 150 s cada; 180 de peça ≈ 30 s cada, incluindo LIN) ≈ 40-50 min.

## 6. Código congelado (SHA-256, 13/10/2026)

| arquivo | SHA-256 |
|---|---|
| `reotimizar_tau.py` | `56f6fd6c9127f354cd85b1df008403ceef329251c705bd95f205373372bb91e0` |
| `analise_tau.py` | `3839751363f04aad10e81f45ba87dc0b0ee65d7ef53513e845a2755d1cab165a` |
| `analise_voo_nao_linear.py` (as curvas) | `fcb9a602553c320a512011b6b5138550f9097d8bfe72e2eb26483b583a0a23c3` |
| `segmento_gtsp.py`, `caminho_honesto.py`, `instancias_lcpp1.py` | os de `docs/17` §7 (iguais) |
| `ea0_lib.py` | `e042231260e10331f367ff6eb39f47080101477d8bf86c5d04f41bc3ab83bdce` |

## 7. Limites

Exploratório quanto às curvas (lidas de um gráfico, uma máquina; o LASER não é calibrado); 1 u = 1 mm; PCGLNS não é ótimo (a diferença entre níveis é da ordem do ruído do solver, ~0,05-0,1%); sem pontes nem tempo de reinício nesta etapa.

## 9. Resultados (13/10/2026; `RESULTADOS_TAU_ANALISE.md`; hashes de §6 conferidos intactos DEPOIS; 300 tarefas, 8 processos, 15:53-16:23, aba c7; 120/120 soluções de segmento verificadas; 0 violações de Π no nível de peça)

| hipótese | resultado | decisão |
|---|---|---|
| H-R1 (DEWIL16) S/P − 1 em [−0,15%; +0,05%] | mediana **−0,102%** (IC 95% [−0,424; −0,022]); S < P em 40/60 | **sustentada** |
| H-R2 (LASER) idem | **−0,067%** (IC [−0,111; −0,024]); S < P em 51/60 | **sustentada** |
| H-R3 (DEWIL16) S ≤ G em ≥ 75% | **95,0%** (57/60); S/G − 1 = −0,213% | **sustentada** |
| H-R4 (desc.) nº médio de movimentos de S ≤ 40 | média 51,4 (mediana S 42, P 34) | **fora** (previsão errada: o ótimo com τ usa MAIS voos que G(0,25), 32) |
| H-R5 (desc.) validação do nível de peça próprio (≥ 95% a 0,05%) | 49/60 (mediana 0,011%, máx. 0,27%) | **fora** (diferenças de PCGLNS 30 s × 20 s e de pré-processamento do pipeline) |
| H-R6 (desc.) P/P0 − 1 ≤ 0 | **−0,264%** (P < P0 em 60/60) | dentro |

LASER: S/P −0,067%; P/P0 −0,083%; H/P (sem reotimizar) +0,075%; G/P +0,029%. DEWIL16: S/P −0,102%; H/P +0,106%; G/P +0,090%.

**Decomposição NÃO planejada (exploratória):** em **6 layouts com arestas compartilhadas** o nível de segmento corta cada aresta uma vez e ganha **−0,73% (LASER) / −3,05% (DEWIL16)** (efeito de modelagem, não de roteamento; extremos: `blaz_sep` −5,97% / −7,98%, redução de corte 4,8%); nos **54 layouts com o mesmo comprimento de corte** o efeito de **roteamento** é **−0,042%** em ambas as curvas (S < P em 45/54 LASER e 34/54 DEWIL16), com tempo de ar **−4,2% / −3,3%**. `poly1a_pack` (mesmo corte) tem −3,73% sob DEWIL16 — um caso em que o PCGLNS de peça ficou longe.

**Leitura:** com os **dois níveis reotimizados para a mesma curva**, o nível de segmento mantém uma vantagem **pequena** (−0,07% a −0,10% do tempo total; **−0,04% só de roteamento**, da ordem do ruído do PCGLNS). A previsão de `docs/25` ("a vantagem some") era forte demais para o nível reotimizado e certa para a heurística bruta (+0,08% a +0,11% acima da peça). Resultado para o N1: **sob voo com aceleração o ganho de roteamento do nível de segmento é ~0,04% do tempo total**; o ganho maior (~1-3%) só aparece onde há arestas compartilhadas. **Limites:** curvas aproximadas/não calibradas; 1 u = 1 mm; PCGLNS não é ótimo; reinício livre.

## 8. Desvios e esclarecimentos (datados)

- **13/10/2026, 15:53 (lançamento):** errata de contagem em §5: são **300 tarefas** (120 de segmento + 180 de peça), não 240; nenhum efeito sobre o método. Pré-voo: 0 processos de terceiros, 7,2 GB livres, na tomada; hashes de §6 conferidos antes do lançamento; aba de terminal "c7", 8 processos.
