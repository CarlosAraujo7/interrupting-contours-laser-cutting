# 35 — Base de evidências dos parâmetros de máquina do N1 (literatura, fabricantes e derivação) — 14/10/2026

**Decisão de Carlos (14/10/2026):** aceitar a falta de medição em máquina e contornar com pesquisa e literatura. Este documento é o **plano B executado**: para cada parâmetro de que o N1 depende, o que a literatura e os fabricantes sustentam, com o **tipo e a qualidade da fonte** e o que foi **derivado por nós** (explicitamente marcado). O plano de coleta em máquina (`docs/34`) fica como **trabalho futuro**.

**Código de tipo:** **P** = medição em artigo revisado por pares (lida); **F** = página/ficha técnica de fabricante (lida); **V** = alegação de fabricante/imprensa/revenda (lida ou só trecho; marcado); **Pt** = patente (contexto, não medição); **D** = derivado por nós (fórmula e premissas); **—** = não achado.

## 1. Movimento em vazio (τ(d))
| Parâmetro | Valor / faixa | Fonte | Tipo | Estado da conferência |
|---|---|---|---|---|
| Velocidade simultânea dos eixos X/Y | 170 m/min (TRUMPF TruLaser 3030 fiber; Bystronic ByStar Fiber 6225/8025; Salvagnini L3.G4); 156 m/min (Salvagnini L5); 140 m/min (BLM LS7) | páginas dos fabricantes | F | páginas lidas em 14/10 |
| Aceleração dos eixos | 20 m/s² = 2 g (BLM LS7); 1,4 g "em toda a área" (Amada ENSIS AJe); "até 5 g em movimentos curtos" (Salvagnini L5, chapa fina e média-fina) | páginas dos fabricantes | F | idem |
| Z rápido / aceleração do Z | 35 m/min e 15 m/s², curso de 370 mm (KNUTH ACE Laser PRO 3015) | catálogo de revenda (DirectIndustry) | V | trecho de busca |
| Curva não linear do tempo de voo | ~0,2 s a 10 mm; ~0,5 s a 100 mm (CO₂ de 4 kW) | Dewil et al. 2016 (Fig. 3) | P | lida (docs/25) |
| Levantar–mover–descer e espera de posicionamento | existem ("frog jumping" funde os três); espera de confirmação antes de disparar; **nenhum valor medido** | patentes e imprensa | Pt/V | — (sem número) |
| Modelo de tempo de CAM comercial | velocidade, aceleração e tempo de perfuração por espessura | documentação WSOptics | F (documentação) | página lida |
| Erro de estimativas por comprimento ÷ avanço | 51 % (CAM) contra 7 % (modelo do controlador), fresamento; fóruns de laser: 8:39 estimado × 16:55 real | Saito et al. 2016; fóruns | P (resumo)/V | resumo; fóruns como anedota |
| **Derivado:** parcela fixa por movimento (Z) | levantar h e descer h: 2·2√(h/a_Z) (trapézio triangular, h < v_Z²/a_Z = 22,7 mm): h = 5 mm → 0,07 s; 10 mm → 0,10 s; 20 mm → 0,15 s; **+ assentamento do sensor (desconhecido)** | cálculo com Z de 35 m/min e 15 m/s² | **D** | premissa: a máquina levanta h a cada voo (muitas só levantam poucos mm ou fundem o movimento) |

## 2. Velocidade de corte (para estimar o pré-corte)
| Faixa | Fonte | Tipo | Estado |
|---|---|---|---|
| 1 kW, O₂: 9 m/min (1 mm) a 0,6 m/min (12 mm) | tabela de peças que credita IPG/Raycus (1 kW, **não** 6 kW) | V | trecho de busca |
| 6 kW, aço-doce ~3 mm (calibre 11): ~600 pol/min ≈ 15 m/min | relato de fabricante (imprensa) | V | trecho de busca |
| Aço espesso (12,5-16 mm, O₂): ~0,85-0,9 m/min | nota de aplicação IPG nº 06 | F | **tabela com texto embaralhado na extração; não confiável** |
| Uso no N1 | faixas assumidas: chapa fina (1-3 mm) 5-30 m/min; 12 mm 0,6-2 m/min; 20 mm 0,5-1 m/min | — | **D** (premissa; explícita) |

## 3. Perfuração em ponto virgem (t_perf)
| Espessura / material / potência | Tempo | Fonte | Tipo | Estado |
|---|---|---|---|---|
| 2 mm aço-doce, fibra 1,4-2 kW, ≥ 2 bar | rompimento 2-8 ms (dezenas de ms com menos potência/pressão); **não** inclui descida do cabeçote, rampa de gás e posicionamento | Hashemzadeh, Powell & Voisey 2014 | P | lida (PDF) |
| 20 mm aço-doce, fibra 5 kW (cabeçote Precitec) | 11-11,5 s; **8-8,6 s** após otimização por fotodiodo (−25 %); o tempo programado é maior que o necessário | Garcia et al. 2019 (*Appl. Sci.* 9(16):3231) | P | lida na página |
| 10 mm inox e alumínio, fibra 5 kW | perfuração "rápida" (≤ 1,5 s) | Garcia et al. 2019 | P | idem |
| 9 mm aço-carbono | 2 s (onda contínua padrão) × 0,5 s (SmartPierce, Prima Power Laserdyne) | West Manufacturing News, jan/2018 | V | página lida |
| 12 mm aço-doce, 5 kW, nitrogênio | < 1 s ("até 90 % de redução") | Prima Power / Production Engineering Solutions, 30/04/2015 | V | página lida |
| 3/4 pol (19 mm) e 1 pol (25 mm), 12 kW | ~0,8 s e ~2 s ("rapid pierce"); método de baixa potência: até 15 s em 1 pol | Piranha-Whitney | V | página lida; material não informado |
| 19 mm aço-doce, CO₂ 4 kW | ~20 s | patente (contexto) | Pt | — |
| 1 pol aço-carbono, 6 kW, pulsado (técnica antiga) | 20-60 s | patente (contexto) | Pt | — |
| Calibre 8 (~4 mm), chapa aninhada com centenas de furos | de 8 s para 3 s por furo ("economizou 20 min") | MetalForming, maio/2013 | V | **página não encontrada (404): não verificado** |
| Perfuração em movimento (chapa fina) | Eagle MyEFLY até 6 mm (a cabeça não para); MyEFAST até 20 mm (taxa controlada); Prima Smart Cut: até 5 mm sem pausa entre perfurar e cortar, "até 30 %" de ciclo contra a perfuração tradicional | fabricantes/imprensa | V | trechos de busca |
| Efeito de potência, gás, pressão | o tempo e o diâmetro dependem de potência, gás e pressão | Hashemzadeh 2014; Garcia 2019 | P | lidas |

**Faixa suportada (fibra de 5-12 kW, estado da técnica):** chapa fina ≤ 3 mm: **≈ 0 (em movimento) a poucas dezenas de ms** (rompimento 2-8 ms; sem número de máquina para o atraso programado); 9-12 mm: **0,5-2 s**; ~20 mm: **2 s (12 kW, "rapid") a 11,5 s (5 kW, medido)**; 25 mm: ~2 s (12 kW, alegado) a 15 s (baixa potência).

## 4. Retomada em ponto já cortado (t_ret) — o parâmetro SEM medição publicada
| Evidência | Fonte | Tipo |
|---|---|---|
| a retomada de um contorno custa um **pré-corte** ("um par de mm"), bem menos que uma perfuração | Dewil et al. 2015 ("overlooked aspects") | P (lida) |
| métodos de retomada: retrair o cabeçote, voltar sobre o caminho cortado e retomar; ou cortar um trecho curto sob condições de reinício e voltar ao ponto de interrupção; em plasma, reiniciar em corte existente | patentes (US 5.852.276; 5.847.359; 5.994.668; plasma US 10.195.682) | Pt |
| **nenhum tempo de retomada medido, em nenhuma fonte** | — | — |
| **Derivado (limite inferior):** t_ret ≥ ℓ_pc/v_c + parada/arranque no vértice (v_c²/a ≈ 6 ms a 250 mm/s e 10 m/s²) + latência do laser (modulação por corrente da bomba, da ordem de dezenas de µs: desprezível) + levantar/descer se houver (0,07-0,15 s) | cálculo | **D** |
| **Derivado (limite superior):** t_ret ≤ t_perf (uma perfuração nova) | — | **D** |
| **Resultado derivado** (ℓ_pc = 2 mm; faixas de v_c da seção 2; com/sem Z): chapa fina (1-3 mm): **0,015-0,17 s**; 12 mm: **0,06-0,3 s**; 20 mm: **0,13-0,4 s**. Limite superior: t_perf da seção 3 | `analise_ancoras_por_espessura.py` | **D** |

## 5. Independência da rota do tempo de corte (L/v_c)
Sem medição achada. A literatura de estimativa de tempo de CNC mostra desvios por aceleração em trajetórias curvas (Saito 2016); no N1 o efeito de **parar e arrancar num vértice** entra em `t_ret` (acima) e a hipótese L/v_c continua uma premissa declarada. (Medição proposta: E5 do `docs/34`, trabalho futuro.)

## 6. O que NÃO foi achado (e o N1 deve dizer)
Tempo medido de retomada/pré-corte; custo de levantar/descer e de assentamento do cabeçote; atraso de perfuração programado em chapa fina; trace real de movimento em vazio de máquina de fibra; fração do ciclo gasta em perfuração ou voo num estudo de tempo controlado; tabelas de tempo de perfuração de CAMs comerciais (ficam nos bancos de tecnologia do fabricante). **Fontes não verificadas (404/403):** MetalForming 2013 e 2015, F&M 2016, The Fabricator, Laser Focus World, página da Bodor/Durma (já removidas do N1).

## 7. Uso no N1 (FEITO em 15/10/2026)
Resultado: **§6.5 do N1 "Restart costs by sheet thickness and the exact saving"** (Tabela 8, Figura 4; `analise_ancoras_por_espessura.py`, `RESULTADOS_ANCORAS_POR_ESPESSURA.md`). **Curva exata (MILP com custo de reinício; layouts disjuntos sem furos; t = 0: RPP exato):** economia máxima de qualquer plano sobre o ótimo de contorno = mediana **0,68 %** (t = 0; máx. 0,92 %), **0,63 %** (0,01 s), **0,42 %** (0,03 s), **0,16 %** (0,06 s), **0 em mediana a 0,1 s** (máx. 0,08 %), **0 a partir de 0,25 s**; ponto de equilíbrio exato entre 0,06 e 0,1 s em mediana (até 0,1-0,25 s). **Distância ao ótimo exato:** heurística cega ao reinício +0,003 % (t = 0), +0,02 % (0,01 s), +0,32 % (0,06 s), +2,6 % (0,25 s), +16 % (1 s); nível de contorno +0,70 / +0,64 / +0,16 / 0 / 0 %. **Âncoras por espessura:** perfuração: chapa fina 0,002-0,21 s; 9-12 mm 0,5-2,1 s; 20-25 mm 2-12 s; **retomada derivada** (pré-corte de 2 mm + parada/arranque + Z, ≤ perfuração): 0,004-0,21 / 0,06-0,46 / 0,12-0,42 s. **Leitura:** interromper contornos só pode render tempo total em chapa fina e se a retomada custar menos de ~0,06-0,1 s (ganho ≤ 0,9 %); de 9 mm para cima não rende. **Limite principal:** a retomada é DERIVADA, não medida (nenhuma fonte a mede).
Plano original deste item:
1. **Âncoras por espessura** (Figura e Tabela novas): faixa de `t_perf` e de `t_ret` por espessura, com o tipo de fonte, contra os limiares do N1 (0,06 s; t_cert 0,14-0,87 s; 0,87 s) e contra a **curva exata da economia máxima** em função de `t` (MILP; `docs/33` e `RESULTADOS_CERTIFICADO_MILP.md`).
2. Texto: o N1 diz que `t_ret` **não foi medido por ninguém**, que usamos intervalos suportados pela literatura, e o que cada regime implica.
3. Limitações e trabalho futuro: o plano de coleta (`docs/34`).
