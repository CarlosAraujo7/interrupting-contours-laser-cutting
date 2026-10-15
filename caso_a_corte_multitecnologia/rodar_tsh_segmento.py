"""
rodar_tsh_segmento.py  --  TSH (nivel de segmento, SEM Pi) nas layouts do CPPLib e comparacao com a heuristica do LCPP (ja gravada em `ea0_resultados/`)
================================================================================================================================================
Para cada layout (84): resolve o TSH (`tsh_segmento.py`) e grava `tsh_resultados/tsh_<inst>.json` (FO nativa, comprimento de ar, componentes, perfuracoes, tempo). Compara com o que o E-A0 ja gravou:
  heur_orig  = heuristica do LCPP no MODO ORIGINAL (sem garantia de Pi; FO NATIVA de nivel de segmento),
  heur_pi    = heuristica com Pi (construcao; FO NATIVA),
  pcglns     = PCGLNS no GTSP de peca inteira, COM Pi (media de 10 sementes, T = 30 s).
`gap_X = FO_X / FO_TSH - 1`: positivo = X pior que o TSH. O TSH ignora Pi (como no artigo de Zhang): e uma referencia de segmento quase otima e um limite para o "preco da precedencia".
Uso: python rodar_tsh_segmento.py rodar [--workers 4]  |  python rodar_tsh_segmento.py resumo > RESULTADOS_TSH_SEGMENTO.md
"""
import os
import sys
import json
import time
import glob
import statistics
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
OUT = os.path.join(AQUI, "tsh_resultados")
EA0 = os.path.join(AQUI, "ea0_resultados")


def _job(nome):
    f = os.path.join(OUT, f"tsh_{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    import rodar_ea0 as ea0
    import tsh_segmento as tsh
    polys = ea0._carregar(nome)
    t0 = time.time()
    r = tsh.resolver_tsh(polys)
    r.pop("caminho")
    r.update(instancia=nome, n_pecas=len(polys), tempo_s=time.time() - t0)
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f, "w"))
    return nome, f"fo={r['fo']:.3f} ar={r['ar_cheb']:.1f} comp={r['n_comp']} perf={r['n_perfuracoes']} em {r['tempo_s']:.1f}s"


def _media(nome, metodo, campo="fo", tempo=30):
    v = []
    for f in glob.glob(os.path.join(EA0, f"ea0_{nome}_{metodo}_T{tempo}_s*.json")):
        r = json.load(open(f))
        if r.get(campo) is not None:
            v.append(r[campo])
    return statistics.mean(v) if v else None


def resumo():
    nomes = sorted(os.path.basename(f)[4:-5] for f in glob.glob(os.path.join(OUT, "tsh_*.json")))
    print(f"# TSH (nível de segmento, sem Π) × heurística do LCPP × PCGLNS nas {len(nomes)} layouts do CPPLib\n")
    print("FO em s (convenção do LCPP). `gap` = FO do método / FO do TSH − 1 (positivo = pior que o TSH). O TSH **ignora Π**; heur_orig também (viola Π); heur_pi e PCGLNS respeitam Π. "
          "heur_orig/heur_pi: FO NATIVA de nível de segmento; PCGLNS: peça inteira, média de 10 sementes (T = 30 s).\n")
    L = []
    for n in nomes:
        t = json.load(open(os.path.join(OUT, f"tsh_{n}.json")))
        ho, hp, pg = _media(n, "heur_orig"), _media(n, "heur_pi"), _media(n, "pcglns")
        if None in (ho, hp, pg):
            continue
        L.append((n, t["n_pecas"], t["fo"], ho, hp, pg, t["n_perfuracoes"], t["tempo_s"]))
    print("| layout | peças | TSH | heur_orig | heur_pi | PCGLNS | gap heur_orig | gap heur_pi | gap PCGLNS | perfurações do TSH |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for n, k, f, ho, hp, pg, pf, ts in L:
        print(f"| {n} | {k} | {f:.2f} | {ho:.2f} | {hp:.2f} | {pg:.2f} | {100 * (ho / f - 1):+.2f}% | {100 * (hp / f - 1):+.2f}% | {100 * (pg / f - 1):+.2f}% | {pf} |")
    g = lambda i: np.array([100 * (x[i] / x[2] - 1) for x in L])
    print(f"\nMediana (média) dos gaps sobre o TSH: heur_orig {np.median(g(3)):+.2f}% ({g(3).mean():+.2f}%); heur_pi {np.median(g(4)):+.2f}% ({g(4).mean():+.2f}%); PCGLNS {np.median(g(5)):+.2f}% ({g(5).mean():+.2f}%). "
          f"Layouts em que o TSH é pior que heur_orig: {int((g(3) < 0).sum())}/{len(L)}; que heur_pi: {int((g(4) < 0).sum())}/{len(L)}; que o PCGLNS: {int((g(5) < 0).sum())}/{len(L)}. "
          f"Tempo médio do TSH: {statistics.mean(x[7] for x in L):.2f} s.")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    if modo == "resumo":
        resumo()
        sys.exit(0)
    import rodar_ea0 as ea0
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    nomes = [n for n in sorted(ea0.listar()) if len(ea0._carregar(n)) >= 2]
    print(f"[{time.strftime('%H:%M:%S')}] TSH em {len(nomes)} layouts, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, nomes, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("TSH CONCLUIDO", flush=True)
