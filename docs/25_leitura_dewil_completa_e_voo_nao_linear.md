# 25 — Leitura completa de Dewil et al. (8 PDFs, 13/10/2026): o que muda e a sensibilidade ao tempo de voo não linear

**Criado em 13/10/2026.** Carlos enviou 8 PDFs. Este documento registra (i) o que cada um é, (ii) os achados que mudam P1/N1, (iii) as predições (**fixadas antes** de calcular a comparação com o nível de peça) e o resultado da sensibilidade ao tempo de voo não linear.

## 1. O que são os 8 arquivos

| arquivo | o que é | uso |
|---|---|---|
| `dewil2011.pdf` | Dewil, Vansteenwegen, Cattrysse (2011), *Cutting Path Optimization Using Tabu Search*, KEM 473:739-748 (11 págs.; as 5 últimas são texto + folha de rosto; **mesmo artigo** do PDF anterior) | lido por inteiro |
| `Heuristics_for_laser_cutting_tool_path_generation.pdf` | **preprint não publicado** (Elsevier, 20/01/2012; 5 págs.) do mesmo grupo: versão curta do que virou Dewil 2014 | só como documento de trabalho (não citar como publicação) |
| `dewil2014.pdf` | Dewil, Vansteenwegen, Cattrysse (2014), *Construction heuristics for generating tool paths for laser cutters*, **IJPR 52(20):5965-5984, versão publicada (T&F)** | lido (págs. 1-5, 13-18; o resto em texto) |
| `dewil2014 (1).pdf` | **é o artigo de 2015** (IJPR 53(6):1761-1776; Dewil, Vansteenwegen, Cattrysse, Laguna, Vossen), versão publicada | texto extraído |
| `dewil2015.pdf` | Dewil, Vansteenwegen, Cattrysse (2015), *Sheet Metal Laser Cutting Tool Path Generation: Dealing with Overlooked Problem Aspects*, KEM 639:517-524 (Crossref ok) | lido (texto) |
| `dewil2015 (1).pdf` | **não é de corte a laser**: Dewil et al. (2015), EJOR, *A minimum cost network flow model for the maximum covering and patrol routing problem* | irrelevante para P1/N1 (sem uso) |
| `areviewofcuttingpathalgorithmsforlasercutters.pdf` | Dewil, Vansteenwegen, Cattrysse (2016), *A review of cutting path algorithms for laser cutters*, IJAMT 87:1865-1884 | lido por inteiro |
| `1-s2.0-S014381661300290X-main.pdf` | Hashemzadeh, Powell, Voisey (2014), *Fibre laser piercing of mild steel*, Opt. Lasers Eng. 55:143-149 | lido por inteiro (a fonte que faltava para `t`) |

## 2. Achados

**A. Calibração do custo de reinício `t` (a pendência 3 de `docs/22`), agora com fontes lidas:**
1. **Chapa fina, laser de fibra (Hashemzadeh et al. 2014; aço doce 2 mm; 0,6-2 kW):** o tempo de **rompimento** (laser ligado até furar) é **2-8 ms** com N₂ a ≥ 2 bar (Fig. 14: de 8,3 ms a 1,4 kW/2 bar a 1,7 ms a 2 kW/12 bar) e **4,5-8 ms** com O₂ (Fig. 15); sobe a ~24 ms a 1 kW/2 bar e a **> 60 ms** a 0,3 bar de N₂ (Fig. 7). **Isto exclui** o tempo de máquina (descida do cabeçote, rampa de gás, posicionamento), que o artigo não mede. Conclusão sustentada: em chapa fina de fibra o custo físico de iniciar o corte é da ordem de **10⁻³-10⁻¹ s**.
2. **Dewil 2011 (chapa fina):** os custos de perfuração extra foram **desconsiderados** porque "poucos pontos de perfuração extras foram introduzidos" e, em chapa fina, o efeito no tempo total é **desprezível** — isto é o regime **`t ≈ 0`** do LCPP-1 e de grande parte do nosso trabalho.
3. **Dewil 2014 / preprint 2012 (chapa grossa, 6 mm inox):** "como a perfuração é tão cara, o ótimo da maioria das instâncias práticas tem **exatamente uma perfuração por *pierce group***"; "os tempos de perfuração dominam severamente os tempos de voo"; a pré-empção compensa só com *pre-cut*; **nenhum valor numérico** de perfuração/*pre-cut*.
4. **Dewil 2015 (KEM 639):** um *pre-cut* é cortar **"um par de milímetros"** do elemento adjacente; custo **bem menor** que o de uma perfuração; **pontes** (continuar cortando sobre o descarte em vez de voo + perfuração) só valem até um comprimento limite que depende de material, espessura e máquina — **o nosso modelo não tem pontes** (limitação a declarar).
5. **Leitura em unidades do benchmark:** `t* = 0,042 s` (equilíbrio mediano) equivale a **16,8 unidades de distância de voo** (`t*·v_voo`, v = 400 u/s) e a **0,7 unidades de corte** (`t*·v_corte`, 16,7 u/s). Um *pre-cut* de ~2 unidades (mm) custa 2/16,7 ≈ **0,12 s** de corte ≈ **3 × t\***, mais o tempo de chaveamento do feixe (não informado). Logo: (a) com perfuração de fibra em chapa fina (≤ ~0,06 s só de laser) a ordem de grandeza **é comparável ao equilíbrio**; (b) em chapa grossa, o custo de reinício é muito maior que `t*` e o nível de peça (Hoeft & Palekar) é o regime natural.

**B. Tempo de voo não linear (Dewil 2016, Fig. 3; 4 kW CO₂, mm):** o tempo de um movimento em vazio **não é `d/v`**: lido do gráfico (leitura visual; **aproximada**): ~0,20 s a 10 mm; ~0,34 s a 50 mm; ~0,50 s a 100 mm; ~0,60 s a 200 mm; ~0,71 s a 330 mm — côncavo, com **piso de ~0,2 s** para qualquer movimento ≥ 10 mm. Para a convenção do LCPP (`d/400`) isso é **8× maior a 10 mm** e 2× a 100 mm. **Consequência potencial:** cada voo extra custa ≥ 0,2 s, o que funciona como um custo adicional **por voo**; o nível de segmento usa **mais** voos (60 contra 38) e, portanto, a sua vantagem de tempo de ar (0,5% do total sob voo linear) pode **desaparecer ou inverter**. É a mesma estrutura de "custo de reinício" (V3), agora vinda da cinemática, e **o E-A1 do P1 só testou isto no nível de peça**.

**C. Posicionamento (Dewil 2016):** (i) "**atualmente não existe abordagem de solução para o ICP**" (o geral); (ii) "**não há *benchmarks* de referência** para cutting path com contornos internos ou cortes comuns… forte necessidade de *benchmarks* públicos" — apoia a nossa avaliação em benchmarks públicos e a de CPPLib (publicado em 2021, depois do artigo); (iii) "**técnicas híbridas que misturam exatas e heurísticas estão ausentes**" — nosso MILP + heurística + PCGLNS; (iv) "o ECP com precedências expressas como **PCGTSP** … **não há testes computacionais extensos** nesta formulação" e "a área se beneficiaria de uma **heurística PCGTSP rápida e eficaz**" — o PCGLNS sobre arcos é exatamente isso; (v) **o custo de voo "não linear, Chebyshev"** é a prática da área (a nossa e a do LCPP são lineares); (vi) as precedências de Dewil: "**todos os elementos de um contorno interno antes do último elemento do externo**" (= fechamento).
**D. O LCPP-1 está próximo demais de Dewil (2011):** além do problema e da formulação (já em `docs/18` §4.4), a **hierarquia de classes** CCP/ECP/ICP, a fórmula *dir-opt* (DP) e as buscas Or-opt/pp3-opt estão em 2011/2016; **o LCPP-1 cita Dewil (2016) como "nível de contorno"**, o que não condiz com o texto lido (que trata ECP/ICP). Sem ação sobre o LCPP-1 (decisão de Carlos); nos nossos textos citamos corretamente.

## 3. Sensibilidade ao tempo de voo não linear (exploratória) — predições fixadas ANTES

Avaliar, **sem reotimizar**, as rotas guardadas da amostra do V3 (60 instâncias) sob três curvas de tempo de voo para cada movimento (Chebyshev, 1 u = 1 mm, **não confirmado**): **LIN** (400 u/s, a do LCPP), **LASER** (trapezoidal v = 1667 mm/s, a = 10.000 mm/s², o perfil do E-A1) e **DEWIL16** (a curva lida da Fig. 3, acima). Rotas: **P** = PCGLNS por peça (caminho reconstituído, 20 s, semente 1, mesma configuração da auditoria honesta), **H** = heurística (ordem guardada, orientações por DP linear), **Rep** = heurística reparada (t = 1 s), **G(0,25)** e **G(1,0)** = soluções ciente do reinício do V3. Tempo total = corte/v_corte + Σ τ(d) + t·corridas, com `t ∈ {0; 0,25; 1}`; relatar mediana e IC bootstrap de T_X/T_P − 1.
- **P-A1.** Sob DEWIL16 e `t = 0`, a heurística H **não** é mais rápida que P em **≥ 50%** das instâncias (a vantagem de t = 0 se perde).
- **P-A2.** Sob DEWIL16, G(0,25) fica **mais perto de P** que H (|G(0,25)/P − 1| < |H/P − 1| em mediana) e dentro de **±1%** de P.
- **P-A3.** Sob LASER (aceleração alta), as ordens entre os métodos são as de LIN (|ΔT/T| da heurística sobre P ≤ 0,5% em mediana).
- **Visto antes (declarado):** uma conta rápida só com H e G(1 s) sob DEWIL16 deu ar(H) ≈ 7,3 s contra o piso de 7,6 s do nível de peça (38 voos × 0,2 s) — insuficiente para decidir.

## 4. Execução

`caminhos_peca_amostra.py` (aba de terminal; 60 instâncias × PCGLNS 20 s; 8 processos; ~4 min) → `analise_voo_nao_linear.py > RESULTADOS_VOO_NAO_LINEAR.md`.

## 5. Resultado (13/10/2026; `RESULTADOS_VOO_NAO_LINEAR.md`; 60 instâncias; hashes: `analise_voo_nao_linear.py` `fcb9a602…83a0a23c3`, `caminhos_peca_amostra.py` `4a63bfc2…1128574`)

**Validação:** o tempo LIN do caminho de peça reconstituído reproduz o FO honesto guardado (diferença 0,0000%). **Predições P-A1, P-A2 e P-A3: todas sustentadas.**

| T(rota)/T(peça) − 1 (mediana), `t_av` = 0 | LIN | LASER | DEWIL16 |
|---|---:|---:|---:|
| H (heurística cega ao reinício) | **−0,47%** (60/60 mais rápida) | −0,00% (30/60) | **+0,04%** (26/60) |
| Rep (reparo; t = 1 s) | +0,05% | +0,01% | +0,04% |
| G(1,0) (ciente do reinício) | −0,03% | −0,02% | −0,03% |
| G(0,25) | −0,07% | −0,03% | −0,05% |

Movimentos em vazio (mediana): peça 38; H 60; Rep 36; G 32. Tempo de ar sob DEWIL16 é 3,3-6,4× o linear (peça 8,97 s contra 2,15 s; H 7,32 s contra 1,08 s). Com `t_av` > 0 o quadro do V3 se mantém (H +2,4% a 0,25 s e +10,0% a 1 s sob DEWIL16; G ≈ −0,03% a −0,05%).

**Leitura:** (1) a vantagem de nível de segmento sobre o de peça que o LCPP-1 reporta (−0,47%, sob voo linear) **desaparece** quando o tempo de voo tem aceleração (LASER) ou o piso de ~0,2 s por movimento da curva de Dewil (+0,04%): a heurística passa a **empatar** com o nível de peça; (2) as rotas cientes do reinício (G) ficam **−0,03% a −0,07%** sob qualquer curva — o ganho **máximo** do nível de segmento, e minúsculo; (3) o reparo empata com a peça (+0,04%-+0,06%). **O resultado do nível de segmento é, portanto, sensível ao modelo de tempo de voo tanto quanto ao custo de reinício;** o N1 deve dizê-lo, no resumo e na discussão, e não vender o nível de segmento como superior sem essa ressalva. **Limites:** as rotas não foram reotimizadas para a curva (tanto a de peça quanto as de segmento foram otimizadas para tempo linear; um PCGLNS com a matriz τ(d) pode mudar os números em décimos de ponto); a curva DEWIL16 foi lida de um gráfico e vale para uma máquina CO₂ de 4 kW; 1 u = 1 mm não confirmado; o perfil LASER é o do E-A1 (não calibrado).

**Reotimização feita (13/10; `docs/26` §9):** com os dois níveis reotimizados para a curva, o nível de segmento ainda ganha **−0,07% (LASER) e −0,10% (DEWIL16)** do tempo total, dos quais só **−0,04% é roteamento** (54 layouts de mesmo corte); o resto vem de cortar uma vez as arestas compartilhadas (6 layouts: −0,7% a −3,1%). A leitura "a vantagem some" vale para a heurística **sem** reotimizar (+0,04% a +0,11% sobre a peça), não para o nível de segmento reotimizado.
