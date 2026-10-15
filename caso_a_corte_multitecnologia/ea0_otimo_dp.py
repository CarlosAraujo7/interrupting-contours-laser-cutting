"""
ea0_otimo_dp.py  --  OTIMO EXATO do problema abstrato do E-A0 nas instancias pequenas (resposta a "sem limites inferiores/otimos", docs/12 B4)
==========================================================================================================================
Programacao dinamica sobre subconjuntos de pecas (Held-Karp com grupos e precedencia): f[S][k] = menor custo abstrato (Chebyshev x ESCALA, inteiro,
o MESMO das matrizes do PCGLNS) de um caminho que parte da origem, visita exatamente as pecas de S respeitando Pi e termina na cidade k (a entrada
de uma peca; o contorno e cortado por inteiro e a saida e a propria entrada). Fecha com o retorno a origem. Apenas subconjuntos fechados para baixo
sob Pi sao alcancaveis (a precedencia reduz muito o numero de estados). O custo exato e o do problema que PCGLNS, VNS-Pi e a heuristica resolvem;
a FO (`fo_from_path`) do tour otimo e comparada com a FO de cada metodo (que pode diferir um pouco por reclassificar trechos).
Uso: python ea0_otimo_dp.py [--maxestados 400000]  ->  RESULTADOS_EA0_OTIMO_DP.md e ea0_otimo_dp.json
"""
import os
import sys
import json
import time
import statistics
import warnings

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import ea0_lib as lib                      # noqa: E402
import rodar_ea0 as ea0                    # noqa: E402

hc = lib.hc
INF = np.iinfo(np.int64).max // 4


def resolver_dp(inst, max_estados):
    cid = inst["cidades"]
    N = len(cid)
    D = np.where(inst["D"] < 0, INF, inst["D"]).astype(np.int64)
    grupos = sorted({c[2] for c in cid if c[2] != 1})
    gi = {g: i for i, g in enumerate(grupos)}
    n = len(grupos)
    nos = [np.array([i for i, c in enumerate(cid) if c[2] == g]) for g in grupos]
    pred = [0] * n
    for p, s in inst["pares"]:
        pred[gi[s]] |= 1 << gi[p]
    f = {0: np.full(N, INF, dtype=np.int64)}
    f[0][0] = 0
    par = {0: np.full(N, -1, dtype=np.int64)}
    camadas = [[0]]
    estados = 1
    for _ in range(n):
        novos = {}
        for S in camadas[-1]:
            fv = f[S]
            ativo = np.where(fv < INF)[0]
            if ativo.size == 0:
                continue
            for g in range(n):
                if S >> g & 1 or (pred[g] & S) != pred[g]:
                    continue
                M = fv[ativo][:, None] + D[np.ix_(ativo, nos[g])]
                j = M.argmin(axis=0)
                val = M[j, np.arange(M.shape[1])]
                T = S | (1 << g)
                if T not in f:
                    f[T] = np.full(N, INF, dtype=np.int64)
                    par[T] = np.full(N, -1, dtype=np.int64)
                    novos[T] = 1
                    estados += 1
                    if estados > max_estados:
                        return None, estados
                melhor = val < f[T][nos[g]]
                idx = nos[g][melhor]
                f[T][idx] = val[melhor]
                par[T][idx] = ativo[j[melhor]]
        camadas.append(list(novos))
    cheio = (1 << n) - 1
    fv = f[cheio]
    ativo = np.where(fv < INF)[0]
    total = fv[ativo] + D[ativo, 0]
    k = int(ativo[total.argmin()])
    custo = int(total.min())
    tour, S = [], cheio
    while S:
        tour.append(k + 1)
        pk = int(par[S][k])
        g = gi[cid[k][2]]
        S ^= 1 << g
        k = pk
    tour.append(1)
    return (custo, tour[::-1]), estados


def main():
    maxe = int(sys.argv[sys.argv.index("--maxestados") + 1]) if "--maxestados" in sys.argv else 400000
    npec = json.load(open(os.path.join(ea0.OUT if hasattr(ea0, "OUT") else os.path.join(AQUI, "ea0_resultados"), "_n_pecas.json")))
    v_cut, v_air = hc._DEFAULT_CONFIG["v_cut"], hc._DEFAULT_CONFIG["v_air"]
    metodos = ["pcglns", "vns_pi", "heur_pi", "heur_ls", "heur_vns"]
    resultados = {}
    for nome, k in sorted(npec.items(), key=lambda kv: kv[1]):
        if k < 2 or k > 24:
            continue
        polys = ea0._carregar(nome)
        inst = lib.montar_instancia(polys)
        t0 = time.time()
        r, est = resolver_dp(inst, maxe)
        if r is None:
            print(f"{nome}: {k} pecas -- DP excedeu {maxe} estados ({est}); nao resolvida", flush=True)
            resultados[nome] = {"n_pecas": k, "resolvida": False, "estados": est}
            continue
        custo, tour = r
        viol = lib.violacoes(inst, tour)
        fo_opt = lib.fo_do_tour(polys, inst, tour, v_cut, v_air)
        linha = {"n_pecas": k, "resolvida": True, "estados": est, "custo_abstrato": custo, "fo_otimo": fo_opt, "violacoes": viol, "tempo_dp_s": time.time() - t0, "metodos": {}}
        pasta = os.path.join(AQUI, "ea0_resultados")
        for m in metodos:
            vals = []
            for s in range(10):
                f = os.path.join(pasta, f"ea0_{nome}_{m}_T30_s{s}.json")
                if os.path.exists(f):
                    d = json.load(open(f))
                    if "fo" in d:
                        vals.append(d["fo_reavaliada"] if m.startswith("heur") and "fo_reavaliada" in d else d["fo"])
            if vals:
                linha["metodos"][m] = {"min": min(vals), "media": statistics.mean(vals), "max": max(vals), "n": len(vals)}
        resultados[nome] = linha
        gp = ", ".join(f"{m}: {100 * (v['media'] / fo_opt - 1):+.3f}%" for m, v in linha["metodos"].items())
        print(f"{nome}: {k} pecas, {est} estados, custo abstrato {custo}, FO otima {fo_opt:.4f}, viol={viol} | gap da media sobre a FO do tour otimo: {gp}", flush=True)
    json.dump(resultados, open(os.path.join(AQUI, "ea0_otimo_dp.json"), "w"), indent=1)
    res = {n: r for n, r in resultados.items() if r["resolvida"]}
    L = ["# E-A0: otimo exato (DP sobre subconjuntos com precedencia) nas instancias pequenas", "",
         f"Instancias com 2 a 24 pecas; resolvidas pela DP (teto de {maxe} estados): {len(res)} de {len(resultados)}. Gap = FO media (10 sementes, T = 30 s) / FO do tour otimo do problema abstrato - 1. "
         "A FO pode diferir um pouco do custo abstrato (reclassificacao de trechos), por isso um metodo pode ficar levemente ABAIXO de zero.", "",
         "| instancia | pecas | estados | FO otima | " + " | ".join(metodos) + " |", "|---|---:|---:|---:|" + "---:|" * len(metodos)]
    for n, r in res.items():
        L.append(f"| {n} | {r['n_pecas']} | {r['estados']} | {r['fo_otimo']:.4f} | " + " | ".join(f"{100 * (r['metodos'][m]['media'] / r['fo_otimo'] - 1):+.3f}%" if m in r["metodos"] else "--" for m in metodos) + " |")
    open(os.path.join(AQUI, "RESULTADOS_EA0_OTIMO_DP.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
