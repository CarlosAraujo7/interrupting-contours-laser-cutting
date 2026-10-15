# 28 — Âncoras no lugar da máquina real; RPP exato no CPPLib; fendas abertas (exploratório; predições das fendas fixadas antes dos dados)

**Criado em 13/10/2026.** Responde a Carlos ("não tenho acesso a uma máquina real, pense em como contornar isso"; "pode fazer tranquilamente" os itens opcionais).

## 1. O que "máquina real" significava e como contornar

Os parâmetros que decidem o resultado do nível de segmento são três: o **custo de reinício** `t` (perfuração ou *pre-cut*), a **aceleração** (tempo de voo não linear) e a **escala** (1 unidade = quantos mm). Sem máquina, **não calibramos: varremos faixas ANCORADAS em fontes e declaramos o resultado como condicional**:
- **Movimento:** perfis trapezoidais com velocidade/aceleração listadas para máquinas de fibra de 6 kW em **anúncios de revenda** (100 m/min com 1,5 g; 120 m/min por eixo, **170 m/min síncronos, 28 m/s²**) e a **curva de Dewil et al. (2016, Fig. 3)** para CO₂ (leitura de gráfico, aproximada). O nosso perfil LASER (100 m/min, 1,0 g) está no extremo conservador.
- **Reinício:** `t = 0,01 s` e `0,06 s` em torno do **tempo de rompimento** da fibra em chapa fina (2-8 ms; até > 60 ms com pouca pressão; Hashemzadeh et al. 2014; **não inclui** o tempo de máquina) e `0,25 s` e `1 s` para chapa mais grossa (alegações de fabricante: ~0,5-2 s a 9-12 mm; **indicativo**).
- **Escala:** 1 u = 1 mm segue **não confirmado**; o tempo de voo em segundos escala com a escala, mas as conclusões relativas (diferenças entre rotas na mesma curva) são pouco sensíveis a ela porque o ar é ~1-4% do tempo total.
- **Outras vias, sem máquina:** pedir a ficha técnica (aceleração, velocidades, tempos de perfuração por espessura) a fabricantes/revendas; perfis de máquina de CAM abertos/gratuitos; um parceiro da indústria (se existir) pode ceder um G-code com tempos. Nenhuma foi usada aqui.

Resultado (`RESULTADOS_MAPA_REGIMES.md`, `analise_mapa_regimes.py`; rotas guardadas, 60 instâncias, **sem reotimizar**): em **todos** os pontos da grade a rota ciente do reinício fica **a ≤ 0,05%** da de peça (−0,01% a −0,05%); a heurística cega ao reinício fica nivelada só com `t = 0` e perde **~0,1% (t = 0,01 s), 0,6% (0,06 s), 2,9% (0,25 s) e 10,5% (1 s)**; o peso do ar é 1,0% a 1,7% (fibra) e 4,2% (curva de Dewil) do tempo total. **Conclusão dentro das faixas ancoradas: a máquina muda quanto uma rota que ignora o reinício perde, não se entrelaçar contornos dá vantagem de roteamento.** Fontes de revenda/fabricante lidas só em trecho de busca (marcadas `[V-SNIPPET]` nos `.bib`): conferir antes de submeter.

## 2. RPP exato no CPPLib (item 5)

`rpp_cpplib.py` (paralelo, 8 processos, limite de 900 s): MILP do RPP sem Π nas 14 layouts do CPPLib com ≤ 130 vértices (antes: 4 resolvidas a 300 s em máquina compartilhada); resumo compara o ar do GTSP de arcos (t = 0, Π de fechamento) com o limite. Resultados em §5.

## 3. Fendas abertas (item 5)

**O que são** (`RESULTADOS_FENDAS_CPPLIB.md`): 4.702 entidades de 2 vértices; 82,7% **dentro** de um contorno e 17,3% **cruzam** uma fronteira; ~6% do comprimento de corte. **Modelo** (`fendas_segmento.py`): cada fenda é dividida nas interseções com as fronteiras; cada pedaço é um segmento requerido; **precedência:** um pedaço deve ser cortado **antes de o menor contorno que o contém fechar** (pedaços fora de todo contorno são livres); nível de segmento = o GTSP de arcos congelado sobre o grafo com *noding* (cada pedaço como "anel" de 2 pontos) com Π de fechamento = contornos + pedaço→dono; nível de peça = GTSP de peças + um grupo de 2 cidades por pedaço (as duas direções), Π estrita pedaço→dono; **verificador próprio** sobre o grafo com *noding* (contíguo, origem, cada aresta uma vez, nada fora, fechamento). Tempo de voo **linear**; 14 layouts; t ∈ {0; 1 s}.

**Visto antes (declarado):** um teste funcional em `p1xe_7` (o menor layout; 16 fendas, todas dentro de contornos): segmento **FO 406,40, ar 3,20 s, 29 corridas, verificado**; peça (15 s) **FO 407,08, ar 3,88 s**, 0 violações (redução do ar de 17% nesse layout). **Nenhum outro layout rodou com fendas antes do congelamento.**

**Hipóteses** (`analise_fendas.py`; decisão por limiar/faixa da mediana; sem teste de significância): **H-F1** viabilidade verificada em 14/14 (t = 0 e 1 s); **H-F2** o ar do segmento **aumenta** com as fendas (mediana ≥ +10%); **H-F3** o segmento reduz o ar da peça (ambos com fendas) em ≥ 30% (mediana); **H-F4** tempo total de S ≤ P em ≥ 75%; **H-F5 (desc.)** a t = 1 s o tempo total fica em [−0,3%; +0,3%]; **H-F6 (desc.)** 0 violações de Π no nível de peça.

## 4. Código congelado (SHA-256, 13/10/2026)

| arquivo | SHA-256 |
|---|---|
| `fendas_segmento.py` | `c292e20895354e530418dc18a7c709010f51c6475db3b7611f564980caef008f` |
| `analise_fendas.py` | `6b71150a1aab6017a2d284937ffc02eca5ac981252b9119273517a60501e91f0` |
| `rpp_cpplib.py` | `882eb9e8e6e62c7a43a743158358c3314a2db66c91be8d37cb3668faf60c448d` |
| `cpplib_vertices.json` | `8e1e0ad13fc7d84296319710b3fe6537dea477655f1386b01d72c08118cab733` |
| `segmento_gtsp.py`, `caminho_honesto.py`, `instancias_lcpp1.py`, `ea0_lib.py`, `dxf_parser.py` | os de `docs/17` §7 (iguais) |

## 5. Resultados

(13/10/2026; hashes de §4 conferidos intactos DEPOIS; RPP: 8 processos, 20:15-~20:45, aba c9; fendas: 5 processos, 20:46-~21:10, aba c10; memória disponível 0,6-2,0 GB)

**RPP exato no CPPLib (`RESULTADOS_RPP_CPPLIB.md`):** das **14** layouts com ≤ 130 vértices, **6 resolvidas** em 900 s (as outras 8 não); o GTSP de arcos (t = 0, Π de fechamento) **iguala o limite — ótimo certificado — em 4** (p1xe_7, p1xe_6, p5xj_4, p5xe_1), está **+6,1%** acima em p3xe_2 (MILP de 585 s) e **+0,9%** em p1xe_1 (880 s). (Os 4 certificados são os mesmos de `docs/16`; o ganho é a quantificação do gap nas outras duas.)

**Fendas (`RESULTADOS_FENDAS_ANALISE.md`; 14 layouts; tempo de voo linear):** **todas as predições sustentadas** — H-F1 viabilidade **14/14** (t = 0 e t = 1 s) com verificador próprio; H-F2 o ar do segmento **sobe** com as fendas, mediana **+81,8%** (IC [+43,9; +122,9]; máx. +687%); H-F3 redução do ar sobre o nível de peça (ambos com fendas) **30,9%** (IC [16,6; 38,5]; **por pouco**: limiar 30%); H-F4 segmento ≤ peça em **14/14**, tempo total mediano **−0,263%** (IC [−0,386; −0,163]); H-F5 a t = 1 s **+0,016%** (24 corridas × 24); H-F6 0 violações de Π no nível de peça. Duas layouts (p3xe_1, p1xe_3) não têm fendas. **Leitura:** as fendas **não mudam o quadro**: o ganho do segmento em ar diminui (de ~57% para ~31%) e o de tempo total fica ~−0,26% a t = 0 e ~0 a t = 1 s, como sem fendas; mas elas **aumentam muito o ar** (+82%), porque são elementos curtos dispersos dentro das peças.

**Mapa de regimes (`RESULTADOS_MAPA_REGIMES.md`):** ver §1.


## 6. Limites

Exploratório; 14 layouts pequenos do CPPLib (os maiores não foram tentados); tempo de voo linear; o piso de `t` e a aceleração vêm de anúncios, não de medições; PCGLNS não é ótimo; a regra de precedência das fendas (antes do fechamento do contorno que as contém) é **nossa** (fecha o espírito da de Dewil et al.), sem validação física.

## 7. Desvios e esclarecimentos (datados)

- **13/10/2026 ~20:50 (lançamento das fendas):** hashes de §4 conferidos intactos; **5 processos em vez de 8** (desvio da preferência de Carlos, declarado): a memória disponível era **≈ 2,0 GB** (navegador e aplicativos abertos; antes 4,4 GB) e 8 processos de PCGLNS levariam ao swap, distorcendo os orçamentos de relógio; o runner é idempotente (pode-se relançar com mais processos se a memória liberar). RPP do CPPLib concluído antes (8 processos).
