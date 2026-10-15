# ENVIRONMENT — ambiente de execução dos experimentos (WP0.2)

Registrado em 02/10/2026 (continuação 68 do log). Vale para todos os resultados gerados a partir de 01/10/2026; resultados mais antigos foram produzidos na nuvem (Cowork) e **não** são comparáveis em tempo.

| Item | Valor |
|---|---|
| Máquina | notebook do Carlos; CPU **Intel Core i5-12450H (12 threads)**; **15,7 GB** de RAM |
| SO | Windows 11 Home (10.0.26200) |
| Python | 3.12.10 (MSC v.1943, AMD64); pacotes em `requirements.txt` |
| Julia | 1.12.7 (PCGLNS; precisa de `--threads=1,0`, ver `CLAUDE.md`) |
| WSL2 | Ubuntu, kernel 6.18.33.2-microsoft-standard-WSL2, gcc 15.2.0 |
| LKH-3 | 3.0.14 (Helsgaun, jun/2026), compilado do fonte no WSL2; proveniência e hashes em `ferramentas/LEIA-ME.md` |
| Concorde | não instalado (só há binários Linux/Solaris; opcional) |
| PrusaSlicer | **2.9.6** portátil (`prusa-slicer-console.exe`), instalado em 06/10/2026 em `C:\Users\vinic\ferramentas_externas\PrusaSlicer-2.9.6\` (fora do OneDrive, fora do projeto); origem, hash e licença em `ferramentas/LEIA-ME.md`. Os G-codes antigos do Caso B vieram do 2.7.2 (apt, nuvem); ver o teste de equivalência na continuação 95 do log |
| trimesh | 5.1.1 (Caso B; ver `requirements.txt`) |

## Ressalvas de medição (leia antes de citar um tempo)

1. **A máquina é compartilhada** com outros trabalhos do Carlos e roda a regeneração em segundo plano; **os tempos de CPU/parede dos resultados atuais estão inflados e só valem como ordem de grandeza.** Execuções finais para o manuscrito devem ser feitas em máquina ociosa (plano 07, WP0.6).
2. O notebook pode hibernar por bateria em rodadas longas: usar ≤6 workers, na tomada, com `request_keep_awake`.
3. Nenhuma calibração de CPU (estilo DIMACS) foi feita ainda; tempos entre máquinas não são comparáveis sem ela.
4. Console do Windows em cp1252: use `PYTHONIOENCODING=utf-8`. Arquivos `.pcglns` têm bytes não-ASCII (ler como latin-1).

## Como reproduzir (resumo)

- Caso C: `caso_c_pcb_drilling_aoi/instances/` — `rodar_biblioteca_sintetica.py`, `rodar_lkh.py`, `rodar_adm3_multisemente.py`; relatórios por `gerar_relatorio_resultados.py`, `gerar_comparacao_caso_c.py`, `analise_estatistica_caso_c.py`. Todos idempotentes (pulam o que já existe).
- Caso A: `caso_a_corte_multitecnologia/` — `comparar_vns_zhang.py [--pi]`, `comparar_3_metodos.py`; o pipeline geométrico exige `ezdxf` (1.4.4, instalado em 03/10/2026).
- Caso B: fatiar com `prusa-slicer-console.exe --export-gcode --layer-height 0.2 --first-layer-height 0.35 --nozzle-diameter 0.4 --perimeters 3 --top-solid-layers 3 --bottom-solid-layers 3 --fill-density "100%" --fill-pattern rectilinear --fill-angle 45 --output <saida.gcode> <entrada.stl>` (o `%` em `--fill-density` é obrigatório) e medir com `caso_b_manufatura_aditiva/instances/analisar_gcode.py`. Nenhum G-code é versionado (reproduzíveis em ~1 s por instância de seção constante). **Piloto de perímetros (06/10/2026):** `python caso_b_manufatura_aditiva/rodar_piloto_perimetros.py > RESULTADOS_PILOTO_PERIMETROS.md` (fatia sozinho numa pasta temporária; usa o PrusaSlicer em `PRUSASLICER` ou no caminho padrão; precisa do LKH-3 no WSL para a referência da engrenagem; idempotente por instância via `piloto_perimetros_resultados/`; ~1 h na engrenagem com a máquina compartilhada). **Rodada confirmatória (protocolo `docs/10_protocolo_caso_B.md`):** `python caso_b_manufatura_aditiva/instances/gerar_instancias_piloto.py` (14 STLs por semente; só `numpy`, `shapely`, `trimesh`; sem motor de triangulação externo) → `python caso_b_manufatura_aditiva/rodar_caso_b_confirmatorio.py --conjunto C [--variante externo_primeiro] [--workers 3]` (~3 min com 3 workers; LKH-3 no WSL para os blocos sem DP exata) → `python caso_b_manufatura_aditiva/analise_estatistica_caso_b.py --conjunto C [--variante ...] > RESULTADOS_CASO_B_*.md`. O fatiamento das placas é determinístico; o do Stanford Bunny não é.
- `python reproduzir_smoke.py` (≈1 min; `--completo` inclui Dalavi 121/400 no A-DM3 e 400 no DM4-T): confere DM4-T e A-DM3 contra os valores publicados (Dalavi), os autotestes dos deltas do VNS (Zhang e VNS-Π) e que os resultados do LKH-3 reproduzem os ótimos da TSPLIB. Primeira execução (02/10/2026): 16/16 verificações passaram. **Não** testa clone limpo em outra máquina — pendência do aceite do WP0.2.
