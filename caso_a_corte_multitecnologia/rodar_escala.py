"""
rodar_escala.py  --  ESCALA do nivel de segmento: o PCGLNS sobre o GTSP de arcos converge nos layouts GRANDES (> 300 arcos)? (docs/24; exploratorio)
=======================================================================================================================================================
Para os layouts do CPPLib com mais arcos (E > 300 nos resultados de t = 0 de `segmento_resultados/`), resolve o mesmo GTSP de arcos (Pi de fechamento padrao, t = 0, portais reduzidos, 1 rodada, semente 0) com orcamentos
de PCGLNS de 120 s (o limite usado nas 84 layouts) e 600 s, e compara a FO honesta e o tempo de ar: quanto o orcamento curto deixa na mesa nos layouts grandes? So entra solucao verificada
(`caminho_honesto.verificar`). Nao altera nenhum arquivo congelado. Saida: `escala_resultados/esc_<inst>_T<tempo>.json`.
Uso: python rodar_escala.py rodar [--workers 8] [--maximo 10] [--tempos 120,600]   |   python rodar_escala.py resumo > RESULTADOS_ESCALA.md
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
OUT = os.path.join(AQUI, "escala_resultados")


def grandes(maximo):
    L = []
    for f in glob.glob(os.path.join(AQUI, "segmento_resultados", "seg_*_t0.json")):
        r = json.load(open(f))
        if r.get("E", 0) > 300 and r.get("melhor"):
            L.append((r["E"], r["instancia"]))
    return [n for _, n in sorted(L, reverse=True)[:maximo]]


def _job(a):
    nome, tempo = a
    f = os.path.join(OUT, f"esc_{nome}_T{tempo}.json")
    if os.path.exists(f):
        return nome, tempo, "pulado"
    import rodar_ea0 as ea0
    import ea0_lib as lib
    import segmento_gtsp as sg
    import caminho_honesto as ch
    hc = lib.hc
    polys = ea0._carregar(nome)
    pares = hc._detectar_precedencia(list(polys))
    t0 = time.time()
    inst = sg.montar(polys, pares, t_perf=0.0, fechamento=None, portais="reduzido")
    tour = sg.resolver(inst, tempo=tempo, semente=0)
    res = {"instancia": nome, "tempo_pcglns_s": tempo, "E": inst["E"], "n_pecas": len(polys), "n_pares_pi": len(pares)}
    if tour is None:
        res["erro"] = "sem tour"
    else:
        cam = sg.caminho_do_tour(inst, tour)
        h = ch.fo_honesta(cam, t_perf=0.0, ja_contiguo=True)
        v = ch.verificar(h["caminho"], polys, pares_pi=pares)
        ar = sum(ch._cheb(s.coords[0], s.coords[-1]) for s, tg in h["caminho"] if tg == "d")
        res.update({"fo": h["fo"], "ar": ar, "n_perf": h["n_perfuracoes"], "ok": bool(v["ok"] and v["violacoes_pi_relaxada"] == 0)})
    res["tempo_total_s"] = time.time() - t0
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(f, "w"))
    return nome, tempo, (f"E={res['E']} fo={res.get('fo', float('nan')):.3f} ar={res.get('ar', float('nan')):.0f} ok={res.get('ok')}")


def resumo():
    from heuristic_core import _DEFAULT_CONFIG as D
    VA = D["v_air"]
    por = {}
    for f in sorted(glob.glob(os.path.join(OUT, "esc_*.json"))):
        r = json.load(open(f))
        if r.get("fo") is not None and r.get("ok"):
            por.setdefault(r["instancia"], {})[r["tempo_pcglns_s"]] = r
    L = [(n, d) for n, d in por.items() if 120 in d and 600 in d]
    print(f"# Escala do nível de segmento: PCGLNS 120 s × 600 s em layouts grandes (> 300 arcos) — {len(L)} layouts com os dois orçamentos\n")
    if not L:
        return
    dfo = np.array([100 * (d[600]["fo"] / d[120]["fo"] - 1) for _, d in L])
    dar = np.array([100 * (d[600]["ar"] / d[120]["ar"] - 1) for _, d in L])
    print(f"- Tempo total (FO): 600 s contra 120 s, mediana **{np.median(dfo):+.3f}%** (mín. {dfo.min():+.3f}%, máx. {dfo.max():+.3f}%); 600 s melhor em {int((dfo < -1e-9).sum())}/{len(L)}.")
    print(f"- Tempo de **ar**: mediana **{np.median(dar):+.1f}%** (mín. {dar.min():+.1f}%, máx. {dar.max():+.1f}%).\n")
    print("| layout | arcos | contornos | FO 120 s | FO 600 s | gap FO | ar 120 s | ar 600 s | gap ar |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for n, d in sorted(L, key=lambda x: -x[1][120]["E"]):
        a, b = d[120], d[600]
        print(f"| {n} | {a['E']} | {a['n_pecas']} | {a['fo']:.2f} | {b['fo']:.2f} | {100 * (b['fo'] / a['fo'] - 1):+.3f}% | {a['ar'] / VA:.2f} | {b['ar'] / VA:.2f} | {100 * (b['ar'] / a['ar'] - 1):+.1f}% |")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "resumo":
        resumo()
        sys.exit(0)
    workers, maximo = arg("--workers", int, 8), arg("--maximo", int, 10)
    tempos = [int(x) for x in arg("--tempos", str, "120,600").split(",")]
    nomes = grandes(maximo)
    tarefas = sorted([(n, tp) for n in nomes for tp in tempos], key=lambda x: -x[1])           # as longas primeiro
    print(f"[{time.strftime('%H:%M:%S')}] escala: {len(nomes)} layouts grandes x tempos {tempos} = {len(tarefas)} tarefas, {workers} processos: {nomes}", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, tp, msg in ex.map(_job, tarefas, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n} T={tp}: {msg}", flush=True)
    print("ESCALA CONCLUIDA", flush=True)
