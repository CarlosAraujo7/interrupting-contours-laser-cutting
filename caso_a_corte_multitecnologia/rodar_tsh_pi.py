"""
rodar_tsh_pi.py  --  TSH com precedencia de FECHAMENTO (`tsh_pi.py`) nas 84 layouts do CPPLib: viabilidade, custo de ar, perfuracoes, e comparacao com o piece-level (PCGLNS) e o LCPP honesto
============================================================================================================================================================================================
Grava `tshpi_resultados/tshpi_<inst>.json`. Verificacao pelo `caminho_honesto.verificar` (contiguidade, cobertura, Pi estrita e relaxada). Limite de tempo por layout (padrao 120 s).
Uso: python rodar_tsh_pi.py rodar [--workers 5] [--limite 120]  |  python rodar_tsh_pi.py resumo > RESULTADOS_TSH_PI.md
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
OUT = os.path.join(AQUI, "tshpi_resultados")
EA0 = os.path.join(AQUI, "ea0_resultados")


def _job(a):
    nome, limite = a
    f = os.path.join(OUT, f"tshpi_{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    import random
    import rodar_ea0 as ea0
    import ea0_lib as lib
    import tsh_pi
    import caminho_honesto as ch
    from shapely.geometry import LineString
    hc = lib.hc
    polys = ea0._carregar(nome)
    pares = hc._detectar_precedencia(list(polys))
    desc = tsh_pi._descendentes(len(polys), pares)
    coords, req, ar, dono = tsh_pi._multigrafo(polys)
    t0 = time.time()
    rng = random.Random(0)
    seq, tent = None, 0
    while seq is None and time.time() - t0 < limite:
        seq = tsh_pi.passeio_fleury(coords, req, ar, dono, desc, rng)
        tent += 1
    r = {"instancia": nome, "n_pecas": len(polys), "n_pares_pi": len(pares), "tentativas": tent, "tempo_s": time.time() - t0, "resolvida": seq is not None,
         "ar_cheb": float(sum(tsh_pi.tsh._cheb(coords[u], coords[v]) for u, v in ar))}
    if seq is not None:
        cam = [(LineString([coords[u], coords[v]]), t) for u, v, t, _ in seq]
        h = ch.fo_honesta(cam, ja_contiguo=True)
        v = ch.verificar(h["caminho"], polys, pares_pi=pares)
        r.update(fo=h["fo"], n_perf=h["n_perfuracoes"], verif=v)
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f, "w"))
    return nome, f"resolvida={r['resolvida']} tent={tent} {r['tempo_s']:.1f}s" + (f" ok={r['verif']['ok']} relax={r['verif']['violacoes_pi_relaxada']}" if seq is not None else "")


def _media_fo(nome, metodo, tempo=30):
    v = []
    for f in glob.glob(os.path.join(EA0, f"ea0_{nome}_{metodo}_T{tempo}_s*.json")):
        d = json.load(open(f))
        if d.get("fo") is not None:
            v.append(d["fo_reavaliada"] if metodo.startswith("heur") and d.get("fo_reavaliada") is not None else d["fo"])
    return statistics.mean(v) if v else None


def resumo():
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "tshpi_*.json")))]
    cam = {os.path.basename(f)[4:-5]: json.load(open(f)) for f in glob.glob(os.path.join(AQUI, "caminhos_resultados", "cam_*.json"))}
    ar_dir = {os.path.basename(f)[3:-5]: json.load(open(f)) for f in glob.glob(os.path.join(AQUI, "ar_resultados", "ar_*.json"))}
    ok = [r for r in R if r["resolvida"] and r["verif"]["ok"] and r["verif"]["violacoes_pi_relaxada"] == 0]
    print(f"# TSH-Π (precedência de fechamento) — {len(R)} layouts do CPPLib\n")
    print(f"Layouts com solução viável encontrada pelo passeio de Fleury com portão: **{len(ok)}/{len(R)}** (verificadas: contíguo, cada trecho cortado uma vez, Π relaxada com 0 violações). "
          f"Tentativas (mediana): {statistics.median(r['tentativas'] for r in R):.0f}; tempo (mediana): {statistics.median(r['tempo_s'] for r in R):.2f} s; máx. {max(r['tempo_s'] for r in R):.1f} s.\n")
    L = []
    for r in ok:
        n = r["instancia"]
        pg = _media_fo(n, "pcglns")
        a = ar_dir.get(n)
        if pg is None or a is None:
            continue
        vc, va = a["L_pecas"] / a["v_cut"], a["v_air"]
        ar_pcglns = (pg - vc) * va                                  # unidades de distancia de ar do PCGLNS (peça, Π estrita)
        c = cam.get(n)
        L.append((n, r["n_pecas"], r["ar_cheb"], ar_pcglns, c["heur_orig"]["ar"] if c else None, c["heur_pi"]["ar"] if c else None, r["n_perf"], r["n_pecas"]))
    g = lambda i, j: np.array([100 * (x[i] / x[j] - 1) for x in L if x[i] is not None and x[j] is not None])
    print("Ar em unidades de distância (Chebyshev). `TSH-Π` tem o MESMO ar do TSH (mesmo multigrafo). Referência de peça: PCGLNS (Π **estrita**, média de 10 sementes). Heurística: modo original e com Π, com os saltos contados.\n")
    print("| comparação (mediana dos gaps de ar) | valor |")
    print("|---|---:|")
    print(f"| TSH-Π em relação ao PCGLNS (peça, Π estrita) | {np.median(g(2, 3)):+.1f}% (média {g(2, 3).mean():+.1f}%) |")
    print(f"| TSH-Π em relação à heurística original honesta (Π relaxada quase satisfeita) | {np.median(g(2, 4)):+.1f}% |")
    print(f"| TSH-Π em relação à heurística com Π estrita (honesta) | {np.median(g(2, 5)):+.1f}% |")
    print(f"| PCGLNS em relação ao TSH-Π | {np.median(g(3, 2)):+.1f}% |")
    print(f"\nPerfurações do TSH-Π (mediana): {statistics.median(x[6] for x in L):.0f} contra {statistics.median(x[7] for x in L):.0f} contornos (piece-level = nº de contornos).")
    print("\n| layout | contornos | ar TSH-Π | ar PCGLNS (peça) | gap | perfurações |")
    print("|---|---:|---:|---:|---:|---:|")
    for x in sorted(L, key=lambda x: x[1])[:40]:
        print(f"| {x[0]} | {x[1]} | {x[2]:.0f} | {x[3]:.0f} | {100 * (x[2] / x[3] - 1):+.0f}% | {x[6]} |")
    nao = [r["instancia"] for r in R if not (r["resolvida"] and r["verif"]["ok"] and r["verif"]["violacoes_pi_relaxada"] == 0)]
    print(f"\nSem solução viável no limite: {nao}")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    if modo == "resumo":
        resumo()
        sys.exit(0)
    import rodar_ea0 as ea0
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 5
    limite = float(sys.argv[sys.argv.index("--limite") + 1]) if "--limite" in sys.argv else 120.0
    nomes = [n for n in sorted(ea0.listar()) if len(ea0._carregar(n)) >= 2]
    print(f"[{time.strftime('%H:%M:%S')}] TSH-Pi: {len(nomes)} layouts, {workers} processos, limite {limite} s", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, [(n, limite) for n in nomes], chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("TSHPI CONCLUIDO", flush=True)
