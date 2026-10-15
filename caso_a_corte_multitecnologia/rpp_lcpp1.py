"""
rpp_lcpp1.py  --  LIMITE INFERIOR / OTIMO do nivel de segmento (RPP sem Pi, MILP exato HiGHS) nas instancias PEQUENAS do LCPP-1, para medir a distancia da heuristica do LCPP e do GTSP de arcos ao otimo
=========================================================================================================================================================================================================
O RPP exato (`rpp_exato.resolver_rpp`; Chebyshev; custo de ar minimo de um passeio fechado a partir da origem que corta cada aresta uma vez) e o OTIMO do problema do LCPP-1 quando Pi = vazio
(categorias regular, irregular e ESICUP) e um LIMITE INFERIOR quando ha Pi (`hole`). Instancias lidas pelo leitor proprio com noding (`instancias_lcpp1.py`); so as com ate `--maxv` vertices (padrao 110).
Uso: python rpp_lcpp1.py rodar [--maxv 110] [--limite 600] [--workers 2] [--refazer]   |   python rpp_lcpp1.py resumo > RESULTADOS_RPP_LCPP1.md   (idempotente: pula o que ja tem JSON; `--refazer` refaz so as NAO resolvidas)
"""
import os
import sys
import json
import glob
import time
import warnings

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
DADOS = os.path.join(AQUI, "instancias_lcpp1_dados")
OUT = os.path.join(AQUI, "rpp_lcpp1_resultados")


def _cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def categoria(n):
    for c in ("regular", "irregular", "hole"):
        if f"_{c}_" in n:
            return c
    return "esicup"


def rodar():
    import instancias_lcpp1 as il
    import rpp_exato as rx
    maxv = int(sys.argv[sys.argv.index("--maxv") + 1]) if "--maxv" in sys.argv else 110
    limite = float(sys.argv[sys.argv.index("--limite") + 1]) if "--limite" in sys.argv else 600.0
    os.makedirs(OUT, exist_ok=True)
    itens = []
    for f in sorted(glob.glob(os.path.join(DADOS, "*.txt"))):
        n = os.path.basename(f)[:-4]
        segs = il.ler_segmentos(f)
        aneis = [a for a in il.agrupar_contornos(segs) if len(a) >= 3]
        coords, req, dono = il.requeridas_com_noding(aneis)
        if len(coords) <= maxv:
            itens.append((len(coords), n, coords, req))
    refazer = "--refazer" in sys.argv                      # refaz as instancias que NAO foram resolvidas no limite anterior (JSON com resolvida = false)
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 1
    tarefas = []
    for nv, n, coords, req in sorted(itens, key=lambda x: x[0]):
        f = os.path.join(OUT, f"{n}.json")
        anterior = None
        if os.path.exists(f):
            anterior = json.load(open(f))
            if not (refazer and not anterior.get("resolvida")):
                continue
        tarefas.append((nv, n, coords, req, limite, anterior))
    print(f"[{time.strftime('%H:%M:%S')}] RPP exato: {len(tarefas)} instancias a resolver (limite {limite:g} s, {workers} processos)", flush=True)
    if workers <= 1:
        for t in tarefas:
            print(_um(t), flush=True)
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for msg in ex.map(_um, tarefas, chunksize=1):
                print(msg, flush=True)
    print("RPP LCPP1 CONCLUIDO", flush=True)


def _um(t):
    import rpp_exato as rx
    nv, n, coords, req, limite, anterior = t
    f = os.path.join(OUT, f"{n}.json")
    t0 = time.time()
    r = rx.resolver_rpp(coords, req, limite)
    corte = sum(_cheb(coords[u], coords[v]) for u, v in req)
    reg = {"instancia": n, "vertices": nv, "arestas": len(req), "corte_comprimento": corte, "resolvida": r is not None, "limite_s": limite}
    if r is not None:
        reg.update(ar_otimo=r[0], rodadas=r[2], tempo_s=r[3])
    else:
        reg["tempo_s"] = time.time() - t0
    if anterior is not None:
        reg["tentativa_anterior"] = {"resolvida": anterior.get("resolvida"), "tempo_s": anterior.get("tempo_s"), "limite_s": anterior.get("limite_s", 600.0)}
    json.dump(reg, open(f, "w"))
    return f"[{time.strftime('%H:%M:%S')}] {n}: {nv} vertices -> " + (f"ar otimo {r[0]:.2f} ({r[2]} rodadas, {r[3]:.1f}s)" if r else "sem solucao no limite")


def resumo():
    from heuristic_core import _DEFAULT_CONFIG as D
    VC, VA = D["v_cut"], D["v_air"]
    import avaliar_heuristica_formal as af
    L = []
    for f in sorted(glob.glob(os.path.join(OUT, "*.json"))):
        r = json.load(open(f))
        n = r["instancia"]
        if not r["resolvida"]:
            continue
        try:
            cam = json.load(open(os.path.join(af.CAM, f"{n}.json")))["forte"]
            g = json.load(open(os.path.join(AQUI, "lcpp1_segmento_resultados", f"{n}.json")))
            h = json.load(open(os.path.join(AQUI, "auditoria_lcpp1", "honesta_282", f"{n}.json")))
        except FileNotFoundError:
            continue
        if not g.get("melhor") or "fo_pcglns_honesta" not in h:
            continue
        hf = af.fo_formal(cam, 0.0)
        LB = r["corte_comprimento"] / VC + r["ar_otimo"] / VA
        L.append({"n": n, "cat": categoria(n), "v": r["vertices"], "ar_opt": r["ar_otimo"] / VA, "ar_h": hf["ar"], "ar_g": g["melhor"]["ar"] / VA, "ar_p": h["fo_pcglns_honesta"] - r["corte_comprimento"] / VC,
                  "LB": LB, "H": hf["fo"], "G": g["melhor"]["fo"], "P": h["fo_pcglns_honesta"], "t": r["tempo_s"]})
    print(f"# Distância ao ótimo (RPP exato sem Π) nas instâncias pequenas do LCPP-1 — {len(L)} resolvidas\n")
    print("Para Π = ∅ (regular, irregular, ESICUP) o RPP exato é o **ótimo** do problema do LCPP-1; para `hole` é **limite inferior**. Tempo de ar em segundos (Chebyshev/v_ar; ar do nível de peça = FO − corte/v_corte).\n")
    pct = lambda a, b: 100 * (a / b - 1)
    for rot, S in (("Π = ∅ (ótimo)", [x for x in L if x["cat"] != "hole"]), ("hole (limite inferior)", [x for x in L if x["cat"] == "hole"]), ("todas", L)):
        if not S:
            continue
        print(f"## {rot} — n = {len(S)}\n")
        print("| método | gap do **ar** ao ótimo (mediana) | máx. | no ótimo (≤ 0,01%) | gap da **FO** (mediana) |\n|---|---:|---:|---:|---:|")
        for nome, k_ar, k_fo in (("heurística do LCPP (formal)", "ar_h", "H"), ("GTSP de arcos + PCGLNS (2 rodadas)", "ar_g", "G"), ("PCGLNS por peça", "ar_p", "P")):
            a = np.array([pct(x[k_ar], x["ar_opt"]) for x in S if x["ar_opt"] > 1e-9])
            fo = np.array([pct(x[k_fo], x["LB"]) for x in S])
            print(f"| {nome} | {np.median(a):+.2f}% | {a.max():+.2f}% | {int((a <= 0.01).sum())}/{len(a)} | {np.median(fo):+.3f}% |")
        print()
    print("## Por instância (Π = ∅)\n| instância | vértices | ar ótimo (s) | heurística | GTSP | peça | tempo MILP (s) |\n|---|---:|---:|---:|---:|---:|---:|")
    for x in sorted([x for x in L if x["cat"] != "hole"], key=lambda x: x["v"]):
        print(f"| {x['n']} | {x['v']} | {x['ar_opt']:.3f} | {x['ar_h']:.3f} | {x['ar_g']:.3f} | {x['ar_p']:.3f} | {x['t']:.1f} |")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    resumo() if modo == "resumo" else rodar()
