"""
auditar_caminhos.py  --  FO honesta + verificacao de caminho (`caminho_honesto.py`) para TSH, heuristica (modo original e com Pi) nas 84 layouts do CPPLib
=========================================================================================================================================================
Para cada layout: gera o caminho de cada metodo, torna-o CONTIGUO, verifica (cobertura das arestas, origem, Pi sob as semanticas estrita e relaxada), e grava FO honesta, tempo de ar, perfuracoes.
Perguntas: (i) o caminho do modo com Pi e do TSH passam na verificacao? (ii) QUANTAS restricoes de Pi o TSH (que ignora Pi) ja satisfaz sob a semantica RELAXADA (fisica) e sob a ESTRITA?
(iii) qual o tempo de ar honesto de cada um?
Uso: python auditar_caminhos.py rodar [--workers 5]  |  python auditar_caminhos.py resumo > RESULTADOS_CAMINHOS_HONESTOS.md
"""
import os
import sys
import json
import glob
import time
import statistics
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
OUT = os.path.join(AQUI, "caminhos_resultados")


def _job(nome):
    f = os.path.join(OUT, f"cam_{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    import rodar_ea0 as ea0
    import ea0_lib as lib
    import tsh_segmento as tsh
    import caminho_honesto as ch
    hc = lib.hc
    polys = ea0._carregar(nome)
    pares = hc._detectar_precedencia(list(polys))
    r = {"instancia": nome, "n_pecas": len(polys), "n_pares_pi": len(pares)}
    va = hc._DEFAULT_CONFIG["v_air"]
    vc = hc._DEFAULT_CONFIG["v_cut"]
    t = tsh.resolver_tsh(polys)
    for chave, cam, cont in (("tsh", t["caminho"], True),):
        h = ch.fo_honesta(cam, ja_contiguo=cont)
        v = ch.verificar(h["caminho"], polys, pares_pi=pares)
        r[chave] = {"fo": h["fo"], "n_perf": h["n_perfuracoes"], "saltos": h["n_saltos"], "ar": sum(ch._cheb(s.coords[0], s.coords[-1]) for s, tg in h["caminho"] if tg == "d"), "verif": v}
    for chave, enforce in (("heur_orig", False), ("heur_pi", True)):
        cfg = {**lib.CFG_BASE, "time_limit": 120, "enforce_precedence": enforce}
        res = hc.run_heuristic(list(polys), cfg)
        h = ch.fo_honesta(res["caminho"], ja_contiguo=False)
        v = ch.verificar(h["caminho"], polys, pares_pi=pares)
        r[chave] = {"fo": h["fo"], "fo_listada": float(res["fo_total"]), "n_perf": h["n_perfuracoes"], "saltos": h["n_saltos"], "comprimento_saltos": h["comprimento_saltos"],
                    "ar": sum(ch._cheb(s.coords[0], s.coords[-1]) for s, tg in h["caminho"] if tg == "d"), "verif": v}
    r["L_corte"] = t["corte_cheb"]
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f, "w"))
    return nome, f"pi={len(pares)} tsh_ok={r['tsh']['verif']['ok']} orig_ok={r['heur_orig']['verif']['ok']} pi_ok={r['heur_pi']['verif']['ok']}"


def resumo():
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "cam_*.json")))]
    print(f"# Caminhos honestos (contíguos) e verificação — {len(R)} layouts do CPPLib\n")
    print("Cada caminho foi tornado contíguo (`caminho_honesto.contiguar`) e verificado (`caminho_honesto.verificar`): contiguidade, origem, cada aresta distinta cortada exatamente uma vez, "
          "e violações de Π sob a semântica **estrita** (todo segmento do contorno interno antes do PRIMEIRO segmento do externo) e **relaxada** (antes do ÚLTIMO segmento do externo: a restrição física).\n")
    print("| método | caminho passa na verificação | saltos inseridos (mediana) | ar honesto (mediana, unid.) | perfurações (mediana) | pares de Π violados: estrita (mediana, % dos pares) | relaxada (mediana, % dos pares) |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for m, nome in (("tsh", "TSH (sem Π)"), ("heur_orig", "heurística, modo original (sem Π)"), ("heur_pi", "heurística com Π (construção)")):
        ok = sum(1 for r in R if r[m]["verif"]["ok"])
        st = [r[m]["verif"]["violacoes_pi_estrita"] for r in R]
        rl = [r[m]["verif"]["violacoes_pi_relaxada"] for r in R]
        tot = [max(r["n_pares_pi"], 1) for r in R]
        pst = 100 * sum(st) / sum(tot)
        prl = 100 * sum(rl) / sum(tot)
        print(f"| {nome} | {ok}/{len(R)} | {statistics.median(r[m]['saltos'] for r in R):.0f} | {statistics.median(r[m]['ar'] for r in R):.0f} | {statistics.median(r[m]['n_perf'] for r in R):.0f} | "
              f"{statistics.median(st):.0f} ({pst:.1f}%) | {statistics.median(rl):.0f} ({prl:.1f}%) |")
    sem_viol_rel = sum(1 for r in R if r["tsh"]["verif"]["violacoes_pi_relaxada"] == 0)
    sem_viol_est = sum(1 for r in R if r["tsh"]["verif"]["violacoes_pi_estrita"] == 0)
    print(f"\nLayouts em que o caminho do TSH (que ignora Π) **já satisfaz** todo o Π: semântica relaxada {sem_viol_rel}/{len(R)}; estrita {sem_viol_est}/{len(R)}.")
    print(f"Média de pares de Π por layout: {statistics.mean(r['n_pares_pi'] for r in R):.1f}.")
    ar_t = [r["tsh"]["ar"] for r in R]
    for m in ("heur_orig", "heur_pi"):
        g = [100 * (r[m]["ar"] / r["tsh"]["ar"] - 1) for r in R]
        print(f"Ar honesto de `{m}` sobre o do TSH: mediana {statistics.median(g):+.0f}%.")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    if modo == "resumo":
        resumo()
        sys.exit(0)
    import rodar_ea0 as ea0
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 5
    nomes = [n for n in sorted(ea0.listar()) if len(ea0._carregar(n)) >= 2]
    print(f"[{time.strftime('%H:%M:%S')}] caminhos honestos: {len(nomes)} layouts, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, nomes, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("CAMINHOS CONCLUIDO", flush=True)
