# 21 — Sensibilidade: Π estrita × Π de fechamento no nível de segmento (exploratório, predições registradas antes dos dados)

**Escrito em 13/10/2026, antes de qualquer resultado em `estrita_resultados/`.** Aprovado por Carlos ("é com você, eu aprovo e pode fazer"). **Exploratório:** sem teste de hipótese formal e sem correção de multiplicidade; medianas, IC bootstrap 95% da mediana e contagens; as predições servem para evitar a leitura retrospectiva.

## 1. Pergunta e o que já foi visto

**Pergunta.** O ganho do nível de segmento sobre o de peça (ar −38% a −57%) vem de **interromper contornos** ou de **relaxar a semântica de Π** (o externo só precisa *fechar* depois dos internos — Dewil et al., 2015 — em vez de ter **todos** os trechos depois dos internos, a semântica do PCGTSP)? Se a estrita já preserva a maior parte do ganho, o resultado não depende da escolha de semântica; se não, a escolha é decisiva e precisa de justificativa física (Dewil: o contorno só se solta da chapa quando fecha).

**Visto antes de fixar as predições (declarado):** os resultados de **fechamento** (84 layouts; varredura de t; V2) e **um teste funcional** do executor da estrita em `p1xe_7`, t = 0, 1 rodada: estrita **ar 885 contra 235 (fechamento)** e tempo total **307,01 contra 305,39 (+0,53%)**, solução verificada (0 violações de Π estrita). As predições P-S2 e P-S3 foram **ajustadas depois desse teste** (de "+2% a +30%" para "≥ +30%" e de "≤ +0,5%" para "≤ +1%"); P-S1 e P-S4 foram fixadas antes.

## 2. Método

Idêntico ao nível de segmento de `docs/16` (GTSP de arcos orientados + PCGLNS, portais reduzidos, `-max_time = min(120, 20 + arcos/4)` s), trocando **só** as restrições de ordem: para cada par (i interno, o externo) de Π, **todo arco de i precede todo arco de o** (em vez de todo arco de i preceder o arco de fechamento c(o)); 2 rodadas (sementes 0 e 1); só entra solução verificada com **0 violações de Π estrita** (`caminho_honesto.verificar`). Layouts: os 30 de `lista_varredura_t.txt` (< 200 arcos); t ∈ {0, 1,0 s}. Referência de fechamento: `segmento_resultados/seg_<inst>_t<t>.json` (mesmos parâmetros); referência de peça: PCGLNS do E-A0 (média de 10 sementes, T = 30 s) + t × nº de contornos. `segmento_gtsp.py` não é alterado.

## 3. Predições (t = 0; sem teste formal)

- **P-S1.** O fechamento é ≤ estrita (tempo total) em **≥ 90%** dos layouts (a estrita é um subconjunto do fechamento; só ruído do solver pode inverter).
- **P-S2.** Preço da estrita no **ar**: mediana **≥ +30%** (ajustada; ver §1).
- **P-S3.** Preço da estrita no **tempo total**: mediana **≤ +1%** (ajustada; ver §1).
- **P-S4.** A estrita **ainda reduz o ar** frente ao nível de peça: redução mediana **≥ 10%**.
- Descritivo: o mesmo a t = 1,0 s; corridas das duas semânticas.

## 4. Execução e análise

`python rodar_estrita.py rodar --workers 3 --ts 0,1` (idempotente; **só com a máquina livre**: o pré-voo de `preparar_v3.py` serve de critério — mesma regra de `docs/17`/`docs/19`) e `python analise_estrita.py > RESULTADOS_ESTRITA.md` (escrito antes dos dados; imprime as predições e a tabela por layout).

## 5. Código congelado (SHA-256, 13/10/2026)

| arquivo | SHA-256 |
|---|---|
| `rodar_estrita.py` | `97169c47e91a1e8a7c924c59361faf3e2536b8124f3ddbd99bab58b26e32cdfb` |
| `analise_estrita.py` | `0b34ad0397d0632060a1f85fb9073a42ca41226e8e14ab0578b5e5bda5c44c04` |
| `segmento_gtsp.py`, `caminho_honesto.py`, `tsh_segmento.py`, `ea0_lib.py`, `dxf_parser.py` | os de `docs/17` §7 (iguais) |

## 6. Limites

Exploratório (n = 30, layouts de desenvolvimento); a estrita usa restrições par a par (O(arcos_i × arcos_o)) e pode ser mais difícil para o PCGLNS que o fechamento; orçamentos de relógio (máquina compartilhada, se forçado); `t` é custo de reinício (`docs/18` §4); fendas excluídas.

## 7. Desvios e esclarecimentos (datados)

- **13/10/2026:** `analise_estrita.py` (frozen) importa `heuristic_core` sem `src_base` no `sys.path` e falhou na primeira execução; **não foi alterado** (hash intacto): rodou-se com `PYTHONPATH=../src_base`. Hashes de §5 conferidos intactos antes do lançamento.

## 8. Resultados (13/10/2026; `RESULTADOS_ESTRITA.md`; exploratório; 60 tarefas, 3 processos, máquina livre)

Estrita **viável e verificada em 30/30** layouts, em t = 0 e t = 1 s.

| | t = 0 | t = 1 s |
|---|---:|---:|
| preço da estrita no **ar** (mediana; IC 95%) | **+14,96%** [+10,44; +30,70]; máx. +285,9% | +2,60% [−0,15; +13,33] |
| preço da estrita no **tempo total** | **+0,057%** [+0,024; +0,089] | −0,018% [−0,045; −0,000] |
| fechamento ≤ estrita (tempo total) | 26/30 | 11/30 |
| estrita × peça: redução do ar (mediana) | **47,3%** [38,6; 60,4] | 0,0% [−0,4; 9,1] |
| estrita × peça: tempo total (mediana; menor em) | −0,336% (30/30) | +0,000% (12/30) |
| corridas (mediana): estrita × fechamento | 51 × 52 | 32 × 32 |

**Predições (t = 0):** P-S1 (fechamento ≤ estrita em ≥ 90%): **86,7% → NÃO SUSTENTADA**; P-S2 (preço no ar ≥ +30%): **+14,96% → NÃO SUSTENTADA** (a previsão, ajustada depois de um único teste em `p1xe_7` com preço de +277%, superestimou a mediana); P-S3 (preço no tempo total ≤ +1%): +0,057% → sustentada; P-S4 (estrita ainda reduz o ar ≥ 10% sobre a peça): 47,3% → sustentada. **Leitura:** a semântica de Π **não decide** o resultado de nível de segmento — a estrita preserva a maior parte da redução de ar sobre o nível de peça (47% contra ~57%) e custa só +0,06% de tempo total; a t = 1 s as duas semânticas e a referência de peça são indistinguíveis. **P-S1 falhou porque o PCGLNS não é ótimo:** toda solução estrita é solução de fechamento, então uma estrita melhor que a de fechamento (4/30 a t = 0; 19/30 a t = 1 s) prova que a solução de fechamento do PCGLNS não era ótima nesse layout (ruído do solver da ordem de 0,1%).
