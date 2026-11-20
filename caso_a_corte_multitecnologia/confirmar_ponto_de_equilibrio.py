"""
confirmar_ponto_de_equilibrio.py  --  CONFERENCIA INDEPENDENTE do ponto de equilibrio exato dos estudos E e F (docs/59_desvios.md, D2; 20/11/2026)
=======================================================================================================================================================
Regra (fixada antes de analisar os resultados): depois de `verificar`, para TODOS os layouts do estudo E com t_c^G exato e > 0, e para uma amostra de 10 layouts do estudo F com t_c exato e > 0
(`random.Random(2026).sample` sobre os nomes ordenados), dois MILPs NOVOS (formulacao de `verificar_certificado_milp.resolver_t`, sem reaproveitar a trilha do Newton): em t_c (1 - 1e-3) a economia sobre a linha-base
e > 1e-7 do tempo da linha-base e em t_c (1 + 1e-3) e <= 1e-7. Linha-base: E, o plano G (c_G, R_min); F, o plano de contorno (P0, n). Limite de 1 800 s por MILP; falhas sao investigadas e relatadas.
Uso: python confirmar_ponto_de_equilibrio.py rodar [--workers 2] [--limite 1800] | resultados
"""
import glob
import json
import os
import random
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
import verificar_certificado_milp as vm  # noqa: E402
import grupo_comum as gc  # noqa: E402
import confirmacao_novos as cn  # noqa: E402
import tsh_segmento as tsh  # noqa: E402

OUT = os.path.join(AQUI, "confirmacao_pe_resultados")
VC, VA = vm.VC, vm.VA
TOL = 1e-7


def amostra_F():
    ex = sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(cn.OUT, "*.json")) if json.load(open(f))["status"] == "exato" and json.load(open(f)).get("t_c"))
    return random.Random(2026).sample(ex, min(10, len(ex)))


def tarefas():
    T = []
    for f in sorted(glob.glob(os.path.join(gc.OUT, "*.json"))):
        r = json.load(open(f))
        if r["status"] == "exato" and r.get("t_c"):
            T.append(("E", r["instancia"]))
    for nome in amostra_F():
        T.append(("F", nome))
    return T


def _job(a):
    estudo, nome, limite = a
    f = os.path.join(OUT, f"{estudo}_{nome}.json")
    if os.path.exists(f):
        return estudo, nome, "pulado"
    if estudo == "E":
        r = json.load(open(os.path.join(gc.OUT, f"{nome}.json")))
        d = gc.dados(nome)
        coords, req, L = d["coords"], d["req"], r["L"]
        c_base, R_base, ar_base = r["cG"], r["R_min"], r["AG"]
    else:
        r = json.load(open(os.path.join(cn.OUT, f"{nome}.json")))
        fam, n_, sem = r["familia"], r["n"], r["semente"]
        polys = cn.gerar(fam, n_, sem)
        coords, req = tsh.construir_requeridas(polys)
        L = r["L"]
        c_base, R_base, ar_base = r["P0"], r["n"], r["AP"]
    inst = vm.preparar(coords, req)
    t_c = r["t_c"]
    out = {"estudo": estudo, "instancia": nome, "t_c": t_c, "pontos": []}
    t0 = time.time()
    for fator, esperado_positivo in ((1 - 1e-3, True), (1 + 1e-3, False)):
        t = t_c * fator
        res = vm.resolver_t(inst, req, t, limite, corte_sup=ar_base / VA + t * (R_base + 1))
        if not res.get("otimo"):
            out["pontos"].append({"t": t, "fator": fator, "status": "sem_prova"})
            continue
        M = L / VC + res["ar_custo"] - t
        T_base = c_base + t * R_base
        S = T_base - M
        out["pontos"].append({"t": t, "fator": fator, "S": S, "T_base": T_base, "R": res["n_ar"] - 1, "ok": (S > TOL * T_base) == esperado_positivo})
    out["ok"] = len(out["pontos"]) == 2 and all(p.get("ok") for p in out["pontos"])
    out["tempo_s"] = time.time() - t0
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(f, "w"), indent=1)
    return estudo, nome, ("OK" if out["ok"] else "FALHA ou sem prova") + f" em {out['tempo_s']:.0f}s"


def resultados():
    fs = sorted(glob.glob(os.path.join(OUT, "*.json")))
    R = [json.load(open(f)) for f in fs]
    L = ["# Conferencia independente do ponto de equilibrio (docs/59_desvios D2)", "", "| estudo | layout | t_c (s) | S(t_c(1-1e-3)) | S(t_c(1+1e-3)) | resultado |", "|---|---|---:|---:|---:|---|"]
    for r in R:
        s = lambda p: (f"{p['S']:.3e}" if "S" in p else "sem prova")
        L.append(f"| {r['estudo']} | {r['instancia']} | {r['t_c']:.6f} | {s(r['pontos'][0])} | {s(r['pontos'][1]) if len(r['pontos']) > 1 else '--'} | {'OK' if r['ok'] else 'FALHA/sem prova'} |")
    for e in ("E", "F"):
        x = [r for r in R if r["estudo"] == e]
        if x:
            L.append(f"\nEstudo {e}: {sum(1 for r in x if r['ok'])} de {len(x)} conferidos.")
    open(os.path.join(AQUI, "RESULTADOS_CONFIRMACAO_PE.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "resultados"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "resultados":
        resultados()
    elif modo == "rodar":
        workers, limite = arg("--workers", int, 2), arg("--limite", float, 1800.0)
        T = tarefas()
        print(f"[{time.strftime('%H:%M:%S')}] Conferencia do ponto de equilibrio: {len(T)} layouts ({sum(1 for e, _ in T if e == 'E')} de E, {sum(1 for e, _ in T if e == 'F')} de F), {workers} processos", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for e, n_, msg in ex.map(_job, [(e, n, limite) for e, n in T], chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {e} {n_}: {msg}", flush=True)
        print("CONFERENCIA CONCLUIDA", flush=True)
