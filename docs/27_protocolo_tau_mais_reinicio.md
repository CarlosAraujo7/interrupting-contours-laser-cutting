# 27 — Protocolo pré-registrado: tempo de voo não linear τ(d) e custo de reinício `t` combinados (nível de segmento reotimizado)

**Escrito em 13/10/2026, ANTES de qualquer resultado em `tau_reinicio_resultados/`.** Código e análise congelados por SHA-256 (§5); desvios em §7, datados. Fecha a pendência "reinício + τ(d) combinados" de `docs/26` §9.

## 1. Pergunta e o que já foi visto

**Pergunta.** `docs/19` (V3) mostrou o efeito do reinício com voo **linear**; `docs/26` mostrou o efeito do voo **não linear** com reinício **livre**. Com **os dois ao mesmo tempo** (τ(d) + `t` por corrida), o nível de segmento, reotimizado para ambos, ainda iguala ou supera o nível de peça, e ignorar o reinício ainda custa caro?

**Visto antes (declarado):** os resultados de `docs/19` (linear, t > 0), `docs/25` e `docs/26` (τ(d), t = 0), e um **teste funcional** em `art_2_regular_pack` (fora da amostra; DEWIL16, t = 1): T = 64,686 s com 9 corridas para 10 contornos. **Nenhuma instância da amostra foi rodada com τ(d) + t antes do congelamento.** O nível de peça **não** depende de `t` (uma corrida por contorno), então se reaproveita `tau_resultados/peca_<curva>_<inst>.json` com `T_P(t) = T_P(0) + t·corridas`.

## 2. Método

`reotimizar_tau_reinicio.py` (não altera nenhum código congelado): o GTSP de arcos de `segmento_gtsp.py` com a matriz de custos substituída por **τ(d) + t** para o arco não contíguo (0 se o corte continua); 2 rodadas (a 2ª com a aresta de fechamento refinada), `-max_time = min(120, 20 + arcos/4)` s por rodada, sementes 0 e 1; só entra solução verificada (`caminho_honesto.verificar`). **Curvas** DEWIL16 e LASER de `docs/25`/`docs/26` (1 u = 1 mm, não confirmado); **t ∈ {0,25; 1,0} s**; 60 instâncias da amostra do V3 → **240 tarefas**. Medida: tempo total = corte/v_corte + Σ τ(d) + t·corridas.

## 3. Hipóteses e predições (decisão por faixa/limiar da mediana; IC 95% bootstrap relatado; sem teste de significância)

- **H-C1 (DEWIL16, t = 1,0).** Mediana de S_t/P_t − 1 em **[−0,15%; +0,05%]**.
- **H-C2 (LASER, t = 1,0).** Idem.
- **H-C3 (DEWIL16, t = 1,0).** Mediana de S_0/S_t − 1 **≥ 2%**: a rota ótima para t = 0 (de `docs/26`), avaliada em t = 1 s, perde ≥ 2% para a rota reotimizada (ignorar o reinício custa caro **mesmo** com a curva de voo).
- **H-C4 (descritiva; DEWIL16, t = 1,0).** Mediana das corridas de S_t ≤ mediana dos contornos + 2.
- **H-C5, H-C6 (descritivas; t = 0,25, DEWIL16 e LASER).** Mediana de S_t/P_t − 1 em [−0,15%; +0,05%].
- **Não se alega:** valores absolutos em segundos; nenhuma das duas curvas como a de uma máquina específica; nada fora da amostra.

## 4. Análise

`analise_tau_reinicio.py` (escrito antes dos resultados) → `RESULTADOS_TAU_REINICIO_ANALISE.md`.

## 5. Código congelado e execução

| arquivo | SHA-256 |
|---|---|
| `reotimizar_tau_reinicio.py` | `43ccccd763d7bd0afa5b0ced1806bb9132e99ceb8115ed296a02a51c64221a65` |
| `analise_tau_reinicio.py` | `e6ed257ef9407dbdfeea5f7a7575da3a4cae1fbd01224dcb78aa7f72a9df5fc9` |
| `reotimizar_tau.py` e `analise_tau.py`, `analise_voo_nao_linear.py`, `segmento_gtsp.py`, `caminho_honesto.py`, `instancias_lcpp1.py`, `ea0_lib.py` | os de `docs/26` §6 (iguais) |

Aba de terminal, 8 processos: `python -u reotimizar_tau_reinicio.py rodar --workers 8` (idempotente); estimativa ~75 min (240 tarefas ≈ 150 s cada).

## 6. Limites

Os de `docs/26` §7, mais: memória livre baixa na máquina (≈ 3,9 GB no lançamento), o que pode reduzir o rendimento por relógio do PCGLNS com 8 processos.

## 8. Resultados (13/10/2026; `RESULTADOS_TAU_REINICIO_ANALISE.md`; hashes de §5 conferidos intactos DEPOIS; 240 tarefas, 8 processos, 18:00-~18:45, aba c8; 240/240 soluções verificadas; memória disponível 1,7-2,2 GB durante a execução, sem swap relevante)

| hipótese | resultado | decisão |
|---|---|---|
| H-C1 (DEWIL16, t = 1) S_t/P_t − 1 em [−0,15%; +0,05%] | mediana **+0,007%** (IC 95% [0,000; +0,018]); S_t < P_t em 21/60 | **sustentada** |
| H-C2 (LASER, t = 1) idem | **+0,003%** (IC [−0,007; +0,004]); 25/60 | **sustentada** |
| H-C3 (DEWIL16, t = 1) S_0/S_t − 1 ≥ 2% | **+1,27%** (IC [+0,22; +3,24]; máx. +27,8%) | **NÃO sustentada** (previsão alta demais; LASER: +1,34%) |
| H-C4 (desc.) corridas de S_t ≤ contornos + 2 | 31 contra 37 + 2 | dentro |
| H-C5 (desc.; DEWIL16, t = 0,25) | +0,006% | dentro |
| H-C6 (desc.; LASER, t = 0,25) | −0,000% | dentro |

Excesso da rota de t = 0 (mediana; máx.) a t = 0,25 s: DEWIL16 +0,23% (máx. +9,1%), LASER +0,35% (máx. +5,4%). **Decomposição (a mesma de `docs/26`, aplicada aqui; exploratória):** nos **54 layouts de mesmo corte** o efeito de roteamento é **+0,010% (DEWIL16) e +0,004% (LASER) a t = 1 s** — **nenhuma vantagem**; nos 6 layouts com arestas compartilhadas, S_t ganha **−6,4% (DEWIL16) e −3,0% (LASER)** a t = 1 s (−3,0% e −1,5% a 0,25 s). **Leitura:** quando o voo acelera **e** reiniciar custa tempo, o nível de segmento reotimizado fica **no mesmo nível** do de peça em roteamento (31 corridas × 37 contornos; a diferença de corridas vem das arestas compartilhadas); o único ganho é o corte único das arestas compartilhadas. Ignorar o reinício ainda custa 1,3% (mediana; até 28%) a 1 s, abaixo dos ≥ 2% previstos.

## 7. Desvios e esclarecimentos (datados)

- **13/10/2026 ~18:05 (lançamento):** hashes de §5 conferidos antes do lançamento; **memória disponível 3,9 GB (< 4 GB do critério do pré-voo dos protocolos anteriores)**, com nenhum processo de terceiros e nenhum job do Carlos em andamento (o uso vem do navegador e dos aplicativos abertos); lançado mesmo assim com 8 processos (preferência de Carlos), com monitoramento da memória disponível durante a execução; se cair abaixo de ~0,5 GB, interromper e relançar com menos processos (o runner é idempotente). Aba "c8".
