# Auditoria externa do resultado central do LCPP-1 ("heurística forte vs. PCGLNS, 282/282 vitórias")

Relatório: `docs/09_auditoria_LCPP1_vs_PCGLNS.md`. **O `LCPP-main` NÃO foi alterado nem importado por este projeto.**

Como foi rodada (06/10/2026):
1. Copiaram-se, para uma pasta TEMPORÁRIA fora do projeto e do LCPP-main: `LCPP-main/src/`, `LCPP-main/pcgtsp_comparison/{converter.py, run_comparison.py, rerun_frente1_282_FINAL.csv}` e `LCPP-main/instances/generated/` (4,9 MB).
2. `auditar_lcpp1.py` (deste diretório; escrito aqui) foi colocado nessa pasta e executado como
   `python auditar_lcpp1.py <ferramentas/PCGLNS_upstream> <instancia> [<instancia> ...]`; ele roda o pipeline DELES (heurística original, `busca_local_forte` 3 s semente 0,
   `convert_instance`, PCGLNS `-max_time=20`, Julia 1.12 `--threads=1,0`) e reavalia sob definições comuns.
3. `resultados/aud_<instancia>.json` = uma execução por instância (17 instâncias: `nomes_amostra.txt` + `albano_pack`); `auditoria_resumo.json` = deltas finais (corte deduplicado como na FO deles).
Para repetir: refazer o passo 1 e rodar o passo 2.
