# 34 — Plano de pesquisa: dados de máquina para o N1 (14/10/2026)

**ATUALIZAÇÃO (14/10/2026, noite): Carlos decidiu ACEITAR a falta de medição em máquina e contornar com pesquisa e literatura.** O **plano B foi executado** (`docs/35`: base de evidências com tipo e qualidade de cada fonte; `analise_ancoras_por_espessura.py`: âncoras por espessura e curva exata da economia máxima; texto novo no N1). Este plano de coleta (E1-E6) permanece como **trabalho futuro** e é citado como tal no N1.

**Status:** PROPOSTA (nada foi coletado). Hipóteses e limiares abaixo seguem o padrão "pré-especificado" do projeto (protocolo e script de análise escritos e datados no log **antes** dos dados; hashes do código; desvios registrados) e só valem depois que Carlos e Bonfim aprovarem. Pesquisa de 14/10/2026 em paralelo (web; o Claude in Chrome estava desconectado); o que não foi conferido está marcado.

## 1. Pergunta e por que isso move a nota do N1
O N1 conclui que "interromper contornos compra tempo sem corte, e tempo total só com arestas compartilhadas ou reinício/aceleração desprezíveis". Essa conclusão depende de **três coisas que o N1 hoje só ancora em fontes**: (i) o **tempo de um movimento em vazio** τ(d) (aceleração, velocidade, e o tempo fixo de levantar/descer o cabeçote); (ii) o **custo de reiniciar o corte** `t` — de dois tipos: **perfuração num ponto virgem** e **retomada num ponto já cortado** (pré-corte); (iii) a **hipótese de que o tempo de corte não depende da rota** (L/v_c). Uma medição numa máquina real dessas três coisas é o que mais sobe a nota do N1 (estimativa: +5 a +8 pontos) e o que um revisor de C&OR mais provavelmente pedirá.

## 2. O que a pesquisa achou (e o que NÃO achou)
- **Modelo de CAM comercial = o nosso modelo.** A documentação de um CAM de chapa (WSOptics/WSI) parametriza o tempo por espessura com velocidade, aceleração e tempo de perfuração (página `wsidoc.wsoptics.de/en/admin/sheet-cutting.html`; só esses três campos; não vi levantamento de cabeçote nem retomada). Logo medir (v, a, t_perf) por material/espessura é medir o que o CAM usa.
- **Estimativas só com comprimento ÷ avanço subestimam o tempo**; o erro cresce com segmentos curtos e aceleração baixa (Saito, Aoyama & Sano 2016, *IJAT* 10(3):429-437: 7 % contra 51 % de um CAM comercial, em fresamento; Ward et al. 2021, *IJAMT*: > 90 % de acerto modelando o controlador; fóruns de laser relatam estimativas de 8:39 para jobs de 16:55). Precedente metodológico de validar modelo de tempo contra trajetórias medidas no CNC: Woo (2019, tese Waterloo, furação a laser de 5 eixos; detalhes de medição **não lidos** — só o resumo).
- **Perfuração:** Garcia et al. (2019, *Applied Sciences* 9(16):3231; fibra de 5 kW; fotodiodo coaxial no cabeçote Precitec): 20 mm de aço-doce 11-11,5 s (8-8,6 s otimizada); inox/alumínio de 10 mm ≤ 1,5 s; o tempo **programado** é maior que o necessário. Detecção de perfuração por fotodiodos InGaAs/Si na cabeça: *Micromachines* 2022, 13(9):1552 (6-10 kW; só o resumo foi visto).
- **Levantar–mover–descer** é descrito como parcela relevante do tempo entre cortes ("frog jumping" funde os três movimentos), e há **espera de confirmação de posicionamento** antes de disparar (patente); nenhum estudo de tempo mediu isso por separado (**não achei**).
- **Retomada sem nova perfuração:** só patentes (retrair o cabeçote, voltar sobre o caminho já cortado, retomar; ou cortar um trecho curto sob condições de reinício e voltar); **nenhum tempo medido** (**não achei**). Plasma: reiniciar em corte existente é descrito.
- **Rastreamento do CNC:** Siemens SINUMERIK (trace de posição/velocidade/erro de seguimento/torque; precisa ser configurado na tela de trace), Fanuc Servo Guide (só para construtores de máquina qualificados, via Ethernet), Beckhoff TwinCAT Scope (não coberto pela busca; conhecimento geral). **Acesso ao trace depende do fabricante/integrador.**
- **Onde medir:** busca por laboratório/empresa de corte a laser a fibra em Fortaleza (SENAI, UFC, UECE, IFCE, prestadores) **não achou nenhum** — isso é limite da busca, não prova de inexistência. O acesso à máquina é o gargalo real do plano.

## 3. Dados esperados (o que medir, exatamente)
Notação: `d` distância em mm; "job" = programa de teste executado do início ao fim; todos os tempos em s.

| # | Quantidade | Condição / níveis | Medição | Repetições | Saída | Alimenta no N1 |
|---|---|---|---|---|---|---|
| **E1** | **τ(d)**: tempo de um movimento em vazio | d ∈ {1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000}; eixos X, Y e diagonal; **exatamente o movimento que o pós-processador do CAM emite** (com o levantar/descer do Z que ele inclui); e, se o controlador permitir, uma variante sem Z. Também **sequências encadeadas** de 10 movimentos curtos (d = 5, 20, 50) para ver a fusão de blocos (look-ahead) | trace do CNC (preferido) ou tempo total de N ida-e-voltas ÷ 2N (N = 50) | ≥ 10 (ou N = 50) | curva τ̂(d) com mediana e IQR; ajuste trapezoidal (v, a), com jerk (curva S) e intercepto `a_mov` em d → 0 | Eq. (T), perfis `FIBRA_*`/Dewil, tempo de voo |
| **E2** | **Parcela fixa por movimento** `a_mov` (lift/lower/assentamento) | com e sem Z do pós-processador; altura de levantamento padrão vs. reduzida | diferença entre variantes de E1 (ou intercepto de τ̂) | idem | `a_mov` | o `t` efetivo de uma corrida inclui `a_mov` |
| **E3** | **Perfuração em ponto virgem** `t_perf` | aço-doce 3, 8, 12 (e 20 se houver) mm com O₂; inox 3 e 10 mm com N₂; modo padrão do controlador (e o modo rampa/pulsado, se existir); furos separados ≥ 20 mm | (i) **tempo programado** na tabela de tecnologia (leitura); (ii) **tempo real** "parada no ponto → início do movimento de corte" por trace, fotodiodo/osciloscópio, vídeo de 240 fps ou áudio; (iii) falhas de perfuração | 10 por combinação | `t_perf` (média, mediana, P90) por material/espessura/gás; **`t_start`** = perfuração + espera + rampa de gás + entrada | âncoras de `t` (0,25 / 1 s): substitui fontes de fabricantes por medida |
| **E4** | **Retomada** `t_ret` em ponto já cortado | contorno-teste (quadrado 100 mm, círculo Ø100, L com cantos), 3 e 12 mm. **P0** contorno em 1 corrida; **P1** 2 corridas, a 2ª começa onde a 1ª terminou (desliga/liga no mesmo ponto, sem voo); **P2** 2ª começa noutro vértice já cortado após voo de d ∈ {50, 200}; **P3** 2ª começa em ponto virgem com perfuração. Registrar **o G-code/ISO que o CAM emitiu** e se a máquina perfurou de fato (log/fotodiodo) | tempo total do job (timer do controlador) e/ou trace; foto da qualidade do ponto de retomada | 10 por programa e espessura | **Δ1 = T(P1) − T(P0)** (custo puro de desligar/religar e parar/arrancar no vértice), **Δ2 − τ(d)** (retomada com voo; testa **aditividade**), **Δ3** (perfuração) | o `t` do N1 em **dois regimes** (retomada × perfuração) e o fator que decide o certificado (t_cert = 0,14-0,87 s) |
| **E5** | **Independência da rota do tempo de corte** | mesmo contorno cortado no sentido horário/anti-horário e iniciado em canto, no meio da aresta e em outro vértice; contagem de cantos variada | tempo só de corte (trace) ou diferença de jobs | 10 | variação do tempo de corte (%) e penalidade por canto | hipótese L/v_c do N1 (e a que o custo de parar/arrancar em vértice não é desprezível) |
| **E6** | **Validação em jobs reais** (a prova de fogo) | 12 layouts pequenos do benchmark (4 separados irregulares, 4 "pack", 4 outros; escalados a ~200×300 mm), cada um em **3 rotas**: (A) nível de contorno (PCGLNS), (B) heurística do LCPP-1 como está, (C) heurística + reparo com o `t` medido | tempo total do job (controlador), 3 repetições; cortes e perfurações contados; qualidade fotografada | 12 × 3 × 3 = 108 jobs | erro do modelo (calibrado só com E1-E5) e **qual rota vence na máquina** | resposta empírica ao título do N1 |

**Metadados obrigatórios da máquina** (planilha de registro): fabricante, modelo, ano, potência da fonte, controlador e versão, cabeçote e bico, lente, gás e pressão, tabela de tecnologia usada (velocidade/aceleração/tempo de perfuração programados), software CAM/pós-processador, temperatura/data, operador.

## 4. Como seria a coleta
**Níveis de instrumentação (use o mais alto que o acesso permitir):**
- **L1 — sem acesso ao controlador:** cronômetro e **vídeo de celular a 240 fps** apontado ao cabeçote (+ áudio, que marca o disparo do laser), **timer do job** do controlador. Resolução ~0,03-0,05 s; **basta para os regimes t ≥ 0,25 s e para E4/E6**, não para o rompimento de chapa fina (2-8 ms).
- **L2 — relatórios do controlador:** tempo por bloco/por job exportado (depende do fabricante).
- **L3 — trace do CNC:** posição/velocidade/erro de seguimento a 1-4 ms (SINUMERIK trace; Fanuc Servo Guide só para quem tem acesso de construtor; TwinCAT Scope) + sinais digitais do laser-on e da válvula de gás via PLC/E-S. Dá E1/E2/E5 com precisão de milissegundos.
- **L4 — sensores externos:** fotodiodo (InGaAs/Si) no cabeçote ou externo com osciloscópio para marcar o rompimento (como em Garcia 2019 e *Micromachines* 2022), câmera de alta velocidade.

**Mínimo viável (L1 + timer do job):** E1 por método diferencial (N = 50 ida-e-voltas), E3 por vídeo/áudio, E4 por diferença de jobs, E5, E6. **Ideal:** L3 para E1/E2/E5 e L4 para E3.

**Requisito crítico:** a máquina/CAM precisa aceitar **cortes parciais de contorno com ordem arbitrária e laser ligado/desligado por segmento** (ISO/G-code ou DXF com ordem editável). Controladores abertos (p.ex. software de comando tipo CypCut/FSCUT em máquinas de fabricantes chineses e vários integradores) costumam permitir; sistemas fechados de fabricantes europeus podem exigir o CAM do fabricante. **Verificar isso ANTES de agendar.**

**Ordem de execução (um dia e meio a dois dias de máquina):** (1) aquecimento e registro de metadados; (2) E1/E2 (≈ 1 h); (3) E5 (≈ 1 h); (4) E3 (≈ 1,5 h); (5) E4 (≈ 2 h); (6) E6 (≈ 5-7 h). Material estimado: ~3 m² de aço-doce 3 mm, ~1 m² de 12 mm, ~0,5 m² de inox 3 mm e 10 mm, (20 mm opcional). **Todos os programas de teste são gerados por script (uma versão por máquina) e executados com ordem aleatória (blocos casualizados)** para não confundir com o aquecimento da máquina. Segurança: seguir o operador/técnico da máquina; nenhum teste altera parâmetros de segurança.

## 5. Análise pré-especificada (a escrever e congelar antes dos dados)
Modelo: `T_job = Σ_corte L_i/v_c(m,e) [+ penalidade por canto] + Σ_vazio [a_mov + τ(d; v, a, jerk)] + Σ_corridas t_r`, com `t_r = t_perf` (ponto virgem) ou `t_ret` (retomada). Ajuste por mínimos quadrados robustos com E1-E5; **E6 é só validação (não entra no ajuste)**. Hipóteses propostas (limiares a confirmar por Carlos/Bonfim):
- **H-D1:** o trapézio (v, a) descreve τ(d) com erro relativo mediano ≤ 10 % para d ≥ 20 mm; senão, curva S com jerk.
- **H-D2:** τ(10 mm) < 0,1 s numa máquina de fibra moderna sem Z (trapézio com 1-5 g dá 0,03-0,06 s; a curva de Dewil, CO₂ de 4 kW, dá ~0,2 s); com levantar/descer do pós-processador, `a_mov` 0,1-0,5 s é o que se espera testar.
- **H-D3:** `t_perf` cai nas faixas das fontes: 12 mm de aço-doce em [0,5; 3] s; 20 mm ≥ 5 s; 3 mm em < 0,3 s.
- **H-D4:** `t_ret` (E4, Δ1) < `t_perf` na mesma espessura. **Regra de decisão sobre o N1:** `t_ef = Δ2 − τ(d)` — se ≤ 0,06 s, a heurística cega perde ≤ 0,6 % (mapa de regimes) e o N1 vira "interromper não custa, mas também não ganha em roteamento"; se entre 0,06 e 0,87 s, vale o reparo; **se ≥ 0,87 s, o certificado se aplica na máquina real**.
- **H-D5 (aditividade):** |Δ2 − Δ1 − τ(d)| ≤ 0,05 s.
- **H-D6:** o tempo de corte varia ≤ 1 % entre sentidos e pontos de partida (E5); senão, entra penalidade por canto/parada em vértice.
- **H-D7 (validação):** erro absoluto mediano do modelo em E6 ≤ 3 % (máximo ≤ 5 %) e a **ordem das rotas A/B/C** prevista corretamente em ≥ 80 % dos layouts.
Relatar também o que for **não sustentado** (padrão do projeto). Análise exploratória separada (qualidade da retomada nas fotos; efeito do gás).

## 6. Se não houver máquina (plano B, por ordem de custo)
1. **Perguntas exatas a engenheiros de aplicação de fabricantes/revendas** (modelo de e-mail em PT-BR a redigir): tempo de perfuração programado e real por espessura/gás; aceleração e velocidade por eixo; tempo de levantar/descer; se o controlador retoma um contorno **sem** perfurar e em quanto tempo; se aceita G-code arbitrário.
2. **Simulador CAM/estimador do fabricante** (licença de demonstração de Lantek/SigmaNEST/TruTops etc.): importar nossos layouts e rotas e comparar o tempo estimado das rotas A/B/C — dá o que o **CAM** acha, não a máquina.
3. **Mais literatura medida** (por exemplo, o texto completo de Woo 2019 e *Micromachines* 2022 para os métodos de medição).
4. Reescrever o N1 declarando que `t` e τ(d) são âncoras (como hoje) — nota fica em ~73.

## 7. Acesso: o que fazer
Não achei laboratório/prestador local; caminhos: (a) **prestador industrial** de corte a laser (metalmecânica no Ceará): pedir 1-2 dias de uso fora do horário, com operador, em troca de coautoria/agradecimento e dos resultados da otimização (uma proposta atraente: "reduzimos o tempo de corte de X %"); (b) **SENAI-CE, UFC, IFCE, UECE**: consultar coordenações de metalmecânica/engenharia mecânica; (c) **fabricantes e revendas** com centro de demonstração (TRUMPF, Bystronic, BLM, Durma e Bodor têm representação no Brasil — conferir); (d) contatos industriais de Bonfim e Plácido (UNIFOR). **Posso redigir a carta/e-mail de convite e o questionário de pré-visita.**

## 8. O que os agentes entregam ANTES da coleta (sem máquina)
1. Protocolo pré-especificado (este plano + hipóteses aprovadas), datado no log, com hashes.
2. **Gerador de programas de teste** (ISO/G-code genérico e DXF com ordem de corte) para E1-E6, parametrizado por máquina, com ordem casualizada.
3. **Planilha de registro** (CSV) e **script de análise** (ajuste do modelo, testes H-D1…H-D7, figuras), validados com **dados sintéticos** (ensaio geral).
4. Cartas/e-mails (prestador, SENAI/UFC/IFCE, fabricantes) e o questionário de fabricantes.
5. Lista de verificação de segurança e de requisitos da máquina/CAM.

## 9. Cronograma e esforço (estimativa)
Semana 0: itens 1-5 acima (2-3 dias de agente). Semanas 1-3: negociar acesso (Carlos/Bonfim). Semana 3-5: coleta (1-2 dias de máquina). Semana 5-6: análise e revisão do N1 (seções 5, 6.4-6.5, discussão, resumo; ressalvas viram resultados). Entregável final: N1 com **dados de máquina próprios** ou, no plano B, com perguntas respondidas por fabricantes.

## 10. Limites e o que NÃO afirmar
Uma máquina e um controlador não representam "as máquinas"; a retomada pode ter qualidade inaceitável (o N1 não modela qualidade); acelerações de catálogo ≠ operação; resultados valem para os materiais/espessuras testados. Não afirmar nada sobre peças reais da indústria sem coletar. Não generalizar a perfuração de 20 mm (8-11,5 s) para a retomada.

## 11. Extensão (pendências do P1' e do N3 em uma linha)
**P1' (FDM):** confirmação humana da leitura do `PerimeterOrder.cpp` (guia `docs/31`) e, se houver impressora, **medir tempo de viagem/retração/aceleração** com G-code instrumentado (≈ 1 h; log do firmware). **N3 (PCB):** tempos reais de furação (descida, troca de broca, deslocamento) numa furadeira CNC — mesma lógica de E1/E3.

## 12. Fontes desta pesquisa (conferir antes de citar)
Garcia et al. 2019, doi 10.3390/app9163231 (lido na página); *Micromachines* 2022, 13(9):1552 (resumo); Saito, Aoyama & Sano 2016, doi 10.20965/ijat.2016.p0429 (resumo); Ward et al. 2021, *IJAMT* 10.1007/s00170-021-07211-2 (resumo); Woo 2019, uwspace.uwaterloo.ca (resumo); documentação WSOptics `wsidoc.wsoptics.de/en/admin/sheet-cutting.html` (página lida); Siemens/Fanuc/Beckhoff: páginas de produto e blog técnico (não verificado contra a documentação oficial); patentes de retomada de corte a laser (US 5.852.276, US 5.847.359, US 5.994.668; leitura de resumo).
