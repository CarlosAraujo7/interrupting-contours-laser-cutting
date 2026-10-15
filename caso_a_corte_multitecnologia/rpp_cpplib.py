"""
rpp_cpplib.py  --  OTIMO / LIMITE INFERIOR exato (RPP sem Pi, MILP HiGHS) nas layouts PEQUENAS do CPPLib, em paralelo, e distancia do GTSP de arcos (t = 0) ao limite (docs/28; exploratorio)
===========================================================================================================================================================================================
Mesmo modelo de `rpp_exato.resolver_rpp` (Chebyshev; passeio fechado de custo de ar minimo a partir da origem que corta cada aresta uma vez; sem Pi: e um LIMITE INFERIOR para o problema com Pi de fechamento),
aplicado as layouts com >= 2 contornos e ate `--maxv` vertices (`cpplib_vertices.json`), com `--limite` s por layout e `--workers` processos. Os resultados antigos de `rpp_exato.json` (limite de 300 s, maquina compartilhada)
sao refeitos quando nao resolvidos. Saida: `rpp_cpplib_resultados/<layout>.json`. Resumo: compara o ar do GTSP de arcos (t = 0; `segmento_resultados/seg_<layout>_t0.json`) com o limite.
Uso: python rpp_cpplib.py rodar [--maxv 130] [--limite 900] [--workers 8]   |   python rpp_cpplib.py resumo > RESULTADOS_RPP_CPPLIB.md
"""
import os
import sys
import json
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
OUT = os.path.join(AQUI, "rpp_cpplib_resultados")


def _job(a):
    nome, limite = a
    f = os.path.join(OUT, f"{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    import rodar_ea0 as ea0
    import tsh_segmento as tsh
    import rpp_exato as rx
    polys = ea0._carregar(nome)
    coords, req = tsh.construir_requeridas(polys)
    t0 = time.time()
    r = rx.resolver_rpp(coords, req, limite)
    reg = {"instancia": nome, "vertices": len(coords), "arestas": len(req), "resolvida": r is not None, "limite_s": limite}
    if r is not None:
        reg.update(ar_otimo=r[0], rodadas=r[2], tempo_s=r[3])
    else:
        reg["tempo_s"] = time.time() - t0
    os.makedirs(OUT, exist_ok=True)
    json.dump(reg, open(f, "w"))
    return nome, (f"{len(coords)} vertices -> ar otimo {r[0]:.1f} ({r[2]} rodadas, {r[3]:.0f}s)" if r else f"{len(coords)} vertices -> sem solucao em {limite:g}s")


def resumo():
    L = []
    for f in sorted(os.listdir(OUT)) if os.path.isdir(OUT) else []:
        r = json.load(open(os.path.join(OUT, f)))
        g = os.path.join(AQUI, "segmento_resultados", f"seg_{r['instancia']}_t0.json")
        if not os.path.exists(g):
            continue
        s = json.load(open(g))
        if r["resolvida"] and s.get("melhor"):
            L.append((r["instancia"], r["vertices"], r["ar_otimo"], s["melhor"]["ar"], s["n_pares_pi"], r["tempo_s"]))
    n_tot = len(os.listdir(OUT)) if os.path.isdir(OUT) else 0
    print(f"# Limite inferior exato (RPP sem Π) nas layouts pequenas do CPPLib — {len(L)} resolvidas de {n_tot}\n")
    print("O RPP exato ignora Π (limite inferior do problema com Π de fechamento); o GTSP de arcos (t = 0, Π de fechamento) vem de `segmento_resultados/`. Ar em unidades de comprimento (Chebyshev).\n")
    if not L:
        return
    gap = np.array([100 * (x[3] / x[2] - 1) for x in L if x[2] > 1e-9])
    print(f"Gap do ar do GTSP de arcos sobre o limite: mediana **{np.median(gap):+.1f}%** (mín. {gap.min():+.1f}%, máx. {gap.max():+.1f}%); no limite (≤ 0,01%) em {int((gap <= 0.01).sum())}/{len(gap)} layouts "
          f"(**ótimo certificado** onde o GTSP iguala o limite).\n")
    print("| layout | vértices | pares Π | ar do limite | ar do GTSP | gap | tempo MILP (s) |\n|---|---:|---:|---:|---:|---:|---:|")
    for n, v, a, b, p, t in sorted(L, key=lambda x: x[1]):
        print(f"| {n} | {v} | {p} | {a:.1f} | {b:.1f} | {100 * (b / a - 1) if a > 1e-9 else 0:+.1f}% | {t:.0f} |")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "resumo":
        resumo()
        sys.exit(0)
    maxv, limite, workers = arg("--maxv", int, 130), arg("--limite", float, 900.0), arg("--workers", int, 8)
    V = json.load(open(os.path.join(AQUI, "cpplib_vertices.json")))
    nomes = [n for v, n in V if v <= maxv]
    print(f"[{time.strftime('%H:%M:%S')}] RPP exato no CPPLib: {len(nomes)} layouts (<= {maxv} vertices), limite {limite:g} s, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, [(n, limite) for n in nomes], chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("RPP CPPLIB CONCLUIDO", flush=True)
