# 60 — Protocolo do estudo H: distância do PCGLNS de arcos ao ótimo exato com custo de reinício — 20/11/2026

**Escrito ANTES dos dados do estudo H.** Contexto: os layouts aninhados reais (V2, estudo G) só têm o PCGLNS de arcos como solver de nível de segmento, sem certificado de otimalidade (ataque R1-3 de `docs/53`). Os estudos E e F produzem **valores exatos** M(t) em 48 layouts pequenos (8 com cortes comuns e 40 novos). Este estudo mede a **distância do PCGLNS de arcos a esses ótimos**, com o mesmo método e orçamentos de V2 (GTSP de arcos + PCGLNS, Π de fechamento refinada, 2 rodadas, tempo = min(120, 20 + arcos/4) s por rodada, portais reduzidos). Execução autorizada por Carlos (20/11/2026: "já dei aval pra fazer tudo de execução que for necessário").

## 1. Casos
Um caso = (layout, t) com M(t) provado exato: **estudo E** (8 layouts de `grupo_comum_resultados/`), t ∈ {0,06; 0,25; 1,0} s; **estudo F** (40 layouts de `confirmacao_novos_resultados/`), t ∈ {0,03; 0,1; 0,25} s. As formas dos layouts de E vêm dos arquivos do benchmark (contornos de `instancias_lcpp1`) e as de F do gerador de `confirmacao_novos.py` (mesmas sementes). Sem furos: Π = ∅. A solução do PCGLNS é a melhor das 2 rodadas **verificada** (contígua, geometria ok, 0 violações).

## 2. Grandezas
`T_h` = tempo da solução verificada (FO honesta = L/v_c + ar/v_a + t R); `M(t)` = tempo exato (MILP); `T_P(t)` = referência de contorno exata (E: `T_P(0) + t n`; F: `P0 + t n`); `NC_h = T_h − L/v_c` e `NC* = M − L/v_c` = tempo **não cortante** (ar + reinícios) da solução e do ótimo. **Excesso** `= (NC_h − NC*)/NC*` (em %); **lacuna no total** `= (T_h − M)/T_P` (em %); **captura** `= (T_P − T_h)/(T_P − M)` nos casos com economia exata `S_total = T_P − M > 1e-3 · T_P`.

## 3. Previsões
**Estrutural (violar = erro de código, de avaliação ou do MILP; investigar, não relatar como achado):** **H-S1** `T_h ≥ M(t)` em todo caso (tolerância 1e-9 relativa); **H-S2** a FO guardada = L/v_c + ar/v_a + t R (1e-6); **H-S3** toda solução é verificada.
**Empíricas:** **H-1** a **mediana** do excesso é ≤ 2% e o máximo ≤ 15%. **H-2** ≥ 80% dos casos têm excesso ≤ 5%. **H-3** o PCGLNS **atinge o ótimo exato** (excesso ≤ 1e-6) em ≥ 30% dos casos. **H-4** a **mediana da captura** é ≥ 0,9 (a economia do PCGLNS é pelo menos 90% da exata). Para a leitura: nos layouts de contorno (9 de V2/DP) o PCGLNS por peça atingiu o ótimo em todos; o GTSP de arcos em t = 0 atingiu o ótimo de ar em 17 de 33 layouts do LCPP-1, com a heurística própria do LCPP a +0,6% de ar.
**Regra de decisão:** cada previsão é "sustentada" só se vale como escrito, nos casos avaliáveis (≥ 100 casos de 144 possíveis; senão "inconclusivo" e só a tabela). Tudo é relatado, inclusive o que não se sustentar.

## 4. Execução, congelamento e uso no N1
`heuristica_vs_exato.py` (3 processos; ~1 h; `OMP_NUM_THREADS=1`); o manifesto `estudo_h_manifesto.json` guarda o SHA-256 do código, de `escala_fibra_aninhados.py` (`_segmento`), `segmento_gtsp.py`, `caminho_honesto.py`, `confirmacao_novos.py`, `grupo_comum.py` e **deste protocolo**; `verificar` antes de `resultados`. No N1 entra como uma subseção curta (distância do solver de arcos ao ótimo) e muda a leitura das economias medidas só com o PCGLNS: se o excesso é pequeno, essas economias são quase exatas; se é grande, são **limites inferiores** da economia verdadeira.
