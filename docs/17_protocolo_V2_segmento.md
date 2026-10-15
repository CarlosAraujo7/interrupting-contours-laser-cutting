# 17 — Protocolo pré-registrado do conjunto confirmatório V2 (nível de segmento × nível de peça)

**Escrito em 12/10/2026, ANTES de qualquer dado de V2 ser gerado ou olhado.** Código congelado por SHA-256 (tabela abaixo); desvios entram em §9 com data. Não é pré-registro externo (OSF etc.): é o mesmo regime dos protocolos `docs/10` e `docs/11`.

## 1. Estatuto dos dados já vistos (honestidade)

O método de nível de segmento (`docs/15`-`docs/16`) foi **desenvolvido e ajustado** nas 84 layouts do CPPLib "com precedência" (E-A0) e ainda está sendo avaliado nas 282 instâncias do LCPP-1; esses resultados são **exploratórios/de desenvolvimento** (o desenho do verificador, dos portais reduzidos e da aresta de fechamento foram escolhidos olhando-os). O conjunto V2 abaixo **não foi usado** em nenhuma etapa.

## 2. Conjunto V2

Os arquivos `.dxf` das categorias do CPPLib `Category - Combined parts` (19) e `Category - No precedence constraints` (30) = **49 arquivos** (`rodar_v2.listar_v2`). Critério de exclusão (fixado antes): layouts com **menos de 2 contornos fechados** após o parser (entidades de 2 vértices [fendas] continuam excluídas, como no E-A0; ver `dxf_parser.py`); a categoria "Cutting techniques" fica **fora** (técnicas especiais). Esperado: 47 de 49 com ≥ 2 contornos.

## 3. Métodos e orçamentos

- **Peça (referência):** PCGLNS upstream no GTSP de peça inteira com Π **estrita** por contenção (`ea0_lib.montar_instancia`), T = 30 s, **10 sementes**; FO = função do LCPP sobre o caminho reconstruído (`ea0_lib.fo_do_tour`).
- **Peça, controle de orçamento:** 1 execução com T = (orçamento total do método de segmento ÷ nº de valores de t), limitado a [30, 600] s — para separar "mais tempo" de "melhor modelo".
- **Segmento (nosso):** GTSP de arcos orientados + PCGLNS, Π de **fechamento**, *noding* das arestas compartilhadas, portais reduzidos, 2 rodadas (a 2ª com a última aresta de cada contorno como aresta de fechamento), `-max_time = min(120, 20 + arcos/4)` s por rodada, semente = índice da rodada; `t_perf` ∈ {0, 1,0 s}. Só entra uma solução que passe **toda** a verificação (`caminho_honesto.verificar`: contígua, origem, cobertura geométrica, Π de fechamento sem violações).
- **TSH (referência sem Π):** `tsh_segmento.py`; não é solução viável (ignora Π); só informativo.
- Hardware/ambiente: o do `ENVIRONMENT.md`; 5 processos; orçamentos em tempo de relógio (válidos para esta máquina).

## 4. Medidas

Para cada layout: **tempo de ar** (= FO − L/v_cut), **tempo de corte** e **tempo total** (FO, com `t_perf` por perfuração: o nível de peça perfura `n_contornos` vezes). Como o nível de peça corta duas vezes uma aresta compartilhada e o de segmento uma só, o **tempo de corte** é reportado separadamente e as conclusões sobre o **ar** valem para todos os layouts; as sobre o **tempo total** são reportadas em todos e nos layouts **sem** arestas compartilhadas. Unidade de análise: o **layout**.

## 5. Hipóteses, predições e regras de decisão (família de Holm: H-V2, H-V3, H-V4a)

- **H-V1 (viabilidade).** ≥ 95% dos layouts de V2 recebem solução de segmento verificada com t = 0. *Rejeita-se* se < 95%.
- **H-V2 (tempo de ar, t = 0).** O tempo de ar do segmento é menor que o da peça; **mediana** da redução relativa ≥ 20% nos layouts sem arestas compartilhadas. Wilcoxon unilateral sobre as razões (log), com Holm; e critério de tamanho: limite inferior do IC bootstrap (10.000 reamostras) da mediana ≥ 20%.
- **H-V3 (tempo total, t = 0).** O tempo total do segmento ≤ o da peça em **≥ 75%** dos layouts (teste dos sinais unilateral, Holm).
- **H-V4a (tecnologia, regret).** Mediana do excesso de tempo total ao usar a rota de t = 0 quando t = 1 s, sobre a rota de t = 1 s: **≥ 0,2%** (IC bootstrap com limite inferior > 0). **H-V4b (descritiva, sem teste):** a vantagem do segmento sobre a peça em tempo total com t = 1 s fica entre −0,1% e +0,1% (mediana).
- **Predição qualitativa (não testada):** o número de perfurações do segmento com t = 1 s é menor que com t = 0 em ≥ 80% dos layouts.
- **Não se alega:** vantagem sob a semântica estrita de Π; vantagem nas fendas (excluídas); validade física dos tempos (perfuração não calibrada).

## 6. Análise e relato

Wilcoxon, sinais e bootstrap descritos acima; layouts como unidades; tamanho de efeito (mediana e IC); relatar **todas** as exclusões; relatar o controle de orçamento e os layouts em que o segmento perde; macros/tabelas por script (`rodar_v2.py resumo`).

## 7. Código congelado (SHA-256, 12/10/2026)

| arquivo | SHA-256 |
|---|---|
| `segmento_gtsp.py` | `c05afffa48356ac107ac204cd51dc5f577422d9301a99085aaf10ea2150201c3` |
| `caminho_honesto.py` | `e2469fb46368e7307e92f42a2892a682f93d417e7368ed8ef0a68a9c69782067` |
| `rodar_v2.py` | `2a6ccd3095c1ae1dc6f36715415e67a9f56cfd634469f3932e4ad3224e6cc41e` |
| `instancias_lcpp1.py` | `daf7fb2d6d3ed586d0a88e775effccd328727e09d7dd9c146cf241f643311526` |
| `tsh_segmento.py` | `3ce73694f51712812de6cb0f0235fd89fdeadc4817fcc6fda3814f5b3471c246` |
| `ea0_lib.py` | `e042231260e10331f367ff6eb39f47080101477d8bf86c5d04f41bc3ab83bdce` |
| `dxf_parser.py` | `a27e678b7c5ea6a640cbbe1e6324f34f646bb20dde507f6ee51db07b40d37595` |

(Dependências não congeladas aqui: `ferramentas/PCGLNS_upstream` [commit `bc09d9d`], `src_base/heuristic_core.py`, `requirements.txt`.)

## 8. Execução

`python rodar_v2.py rodar --workers 5` e `python rodar_v2.py resumo > RESULTADOS_V2.md`, na máquina ociosa (pré-voo manual: sem outros jobs pesados).

## 9. Desvios e esclarecimentos (datados)

- **12/10/2026 (após a execução de V2):** nenhum desvio do protocolo. Execução: `rodar_v2.py rodar --workers 5` (06:35-08:43; 49 arquivos, 0 erros); hashes do código congelado **conferidos intactos antes e depois** da execução. A **análise** foi implementada em `analise_v2.py` (escrito antes de os resultados de V2 serem vistos; só os contadores do log — nº de contornos e 'ok' — tinham sido vistos; SHA-256 `fe6bf3ffb4ad140da3fbb5409e5c499516b06a0cc6465b00821a045b19a2b54d`), implementando exatamente os testes de §5-6; uma errata tipográfica no texto impresso foi corrigida e o script reexecutado. Resultados: `RESULTADOS_V2_ANALISE.md`.
- **12/10/2026 (esclarecimento de interpretação; nenhum dado nem análise alterados):** depois de ler Dewil et al. (2015) (`docs/18` §4), a "perfuração" `t_perf` cobrada a **cada** interrupção do corte deve ser lida como **custo de reinício** (perfuração ou *pre-cut*), não como perfuração física: no modelo de Dewil a retomada de um contorno custa um *pre-cut* e só o início de um *pierce group* custa perfuração. As predições H-V4a/H-V4b e a qualitativa foram sustentadas **sob esse custo de reinício**; elas **não** provam efeito da perfuração física sobre a rota. O mesmo vale para o rótulo "tecnologia" nas varreduras de `docs/16`.
