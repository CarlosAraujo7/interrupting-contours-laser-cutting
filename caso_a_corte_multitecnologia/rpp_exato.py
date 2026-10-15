"""
rpp_exato.py  --  OTIMO EXATO do problema de NIVEL DE SEGMENTO sem precedencia (o "RPP" do arc routing method de Zhang et al. 2024 / Silva et al. 2019) em layouts pequenos, por MILP (HiGHS)
================================================================================================================================================================================
Modelo (versao completa sobre vertices; Chebyshev): y_e in {0,1,2} = nº de vezes que a aresta de AR e = {u, v} (qualquer par de vertices, custo = distancia de Chebyshev) e usada; as arestas requeridas
(lados dos contornos, deduplicados) sao percorridas uma vez, cortando. Passeio euleriano fechado a partir da origem existe sse (i) paridade: grau_requerido(v) + sum_{e em delta(v)} y_e = 2 k_v, k_v inteiro >= 0, e
(ii) conexidade: toda componente S (do grafo das requeridas + arestas de ar) que nao contem a origem exige sum_{e em delta(S)} y_e >= 2 -- cortes adicionados de forma preguicosa (resolver, achar componentes
desconexas, acrescentar o corte, repetir). Minimiza o comprimento de ar. Como o corte e constante, e o otimo do nivel de segmento sem Pi (limite inferior para qualquer variante com Pi).
Validacao: o custo de ar do otimo e comparado com o do TSH (`tsh_segmento.py`), que deve ser >= ao otimo; e, em instancias minusculas, com forca bruta.
Uso: python rpp_exato.py [--maxv 110] [--limite 300]  ->  RESULTADOS_RPP_EXATO.md e rpp_exato.json
"""
import os
import sys
import json
import time
import itertools
import warnings

import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, csr_matrix

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import tsh_segmento as tsh                                      # noqa: E402


def _componentes_grafo(n, arestas):
    pai = list(range(n))

    def f(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x
    for u, v in arestas:
        a, b = f(u), f(v)
        if a != b:
            pai[a] = b
    return [f(x) for x in range(n)]


def resolver_rpp(coords, req, limite_s=300.0, max_rodadas=200):
    """-> (custo de ar otimo, [(u, v, y)], rodadas, tempo) ou None se estourou o limite."""
    n = len(coords)
    P = np.array(coords, float)
    D = np.abs(P[:, None, :] - P[None, :, :]).max(axis=2)
    pares = [(u, v) for u in range(n) for v in range(u + 1, n)]
    m = len(pares)
    pidx = {p: k for k, p in enumerate(pares)}
    grau_req = np.zeros(n, int)
    for u, v in req:
        grau_req[u] += 1
        grau_req[v] += 1
    # variaveis: y_0..y_{m-1} (inteiras 0..2) e k_0..k_{n-1} (inteiras >= 0)
    c = np.concatenate([np.array([D[u, v] for u, v in pares]), np.zeros(n)])
    A = lil_matrix((n, m + n))
    for k, (u, v) in enumerate(pares):
        A[u, k] = 1
        A[v, k] = 1
    for v in range(n):
        A[v, m + v] = -2
    b = -grau_req.astype(float)                                       # sum y - 2 k = - grau_req
    cons = [LinearConstraint(csr_matrix(A), b, b)]
    lb = np.zeros(m + n)
    ub = np.concatenate([np.full(m, 2.0), np.full(n, 2.0 * n)])
    cortes = []
    t0 = time.time()
    for rodada in range(1, max_rodadas + 1):
        restante = limite_s - (time.time() - t0)
        if restante <= 1:
            return None
        res = milp(c, constraints=cons + cortes, integrality=np.ones(m + n), bounds=Bounds(lb, ub), options={"time_limit": restante, "disp": False})
        if res.x is None or res.status not in (0,):
            return None
        y = np.rint(res.x[:m]).astype(int)
        ar = [(pares[k][0], pares[k][1], int(y[k])) for k in range(m) if y[k] > 0]
        arestas = list(req) + [(u, v) for u, v, _ in ar]
        raiz = _componentes_grafo(n, arestas)
        # vertices isolados (sem aresta) nao contam
        com_aresta = set(x for e in arestas for x in e) | {0}                  # a origem e sempre um vertice ativo (o passeio parte e volta a ela)
        comps = {}
        for v in com_aresta:
            comps.setdefault(raiz[v], []).append(v)
        # a componente da origem (vertice 0) e a de referencia
        r0 = raiz[0]
        if len(comps) == 1:
            custo = float(sum(D[u, v] * yy for u, v, yy in ar))
            return custo, ar, rodada, time.time() - t0
        for r, S in comps.items():
            if r == r0:
                continue
            Sset = set(S)
            row = lil_matrix((1, m + n))
            for k, (u, v) in enumerate(pares):
                if (u in Sset) != (v in Sset):
                    row[0, k] = 1
            cortes.append(LinearConstraint(csr_matrix(row), 2.0, np.inf))
    return None


def forca_bruta(coords, req, max_arestas=8):
    """Para instancias minusculas: menor multiconjunto de arestas de ar (cada par 0..2 vezes) que torna o grafo euleriano e conexo -- via enumeracao de subconjuntos de pares (so p/ n <= 7)."""
    n = len(coords)
    P = np.array(coords, float)
    D = np.abs(P[:, None, :] - P[None, :, :]).max(axis=2)
    pares = [(u, v) for u in range(n) for v in range(u + 1, n)]
    grau_req = [0] * n
    for u, v in req:
        grau_req[u] += 1
        grau_req[v] += 1
    melhor = np.inf
    for r in range(0, max_arestas + 1):
        for comb in itertools.combinations_with_replacement(range(len(pares)), r):
            if any(comb.count(k) > 2 for k in set(comb)):
                continue
            g = list(grau_req)
            for k in comb:
                g[pares[k][0]] += 1
                g[pares[k][1]] += 1
            if any(x % 2 for x in g):
                continue
            custo = sum(D[pares[k]] for k in comb)
            if custo >= melhor:
                continue
            arestas = list(req) + [pares[k] for k in comb]
            raiz = _componentes_grafo(n, arestas)
            ativos = set(x for e in arestas for x in e)
            if len(set(raiz[x] for x in ativos)) == 1 and 0 in ativos:
                melhor = custo
    return melhor


def autoteste():
    from shapely.geometry import box
    polys = [box(10, 10, 20, 20), box(40, 10, 50, 20)]
    coords, req = tsh.construir_requeridas(polys)
    r = resolver_rpp(coords, req)
    assert r is not None
    tshr = tsh.resolver_tsh(polys)
    print("autoteste RPP: otimo", r[0], "TSH", tshr["ar_cheb"])
    assert r[0] <= tshr["ar_cheb"] + 1e-9
    # forca bruta num caso com 3 vertices requeridos + origem (triangulo)
    from shapely.geometry import Polygon
    tri = [Polygon([(10, 0), (20, 0), (15, 8)])]
    coords, req = tsh.construir_requeridas(tri)
    fb = forca_bruta(coords, req, max_arestas=6)
    ex = resolver_rpp(coords, req)[0]
    print("forca bruta", fb, "MILP", ex)
    assert abs(fb - ex) < 1e-9


def main():
    import rodar_ea0 as ea0
    maxv = int(sys.argv[sys.argv.index("--maxv") + 1]) if "--maxv" in sys.argv else 110
    limite = float(sys.argv[sys.argv.index("--limite") + 1]) if "--limite" in sys.argv else 300.0
    npec = json.load(open(os.path.join(AQUI, "ea0_resultados", "_n_pecas.json")))
    ar_dir = os.path.join(AQUI, "ar_resultados")
    out = {}
    for nome in sorted(ea0.listar(), key=lambda n: npec.get(n, 999)):
        if npec.get(nome, 999) < 2:
            continue
        polys = ea0._carregar(nome)
        coords, req = tsh.construir_requeridas(polys)
        if len(coords) > maxv:
            continue
        t0 = time.time()
        r = resolver_rpp(coords, req, limite)
        f = os.path.join(ar_dir, f"ar_{nome}.json")
        extra = json.load(open(f)) if os.path.exists(f) else None
        if r is None:
            print(f"{nome}: {len(coords)} vertices -- sem solucao no limite", flush=True)
            out[nome] = {"vertices": len(coords), "resolvida": False}
            continue
        custo, ar, rodadas, tt = r
        reg = {"vertices": len(coords), "n_pecas": len(polys), "resolvida": True, "ar_otimo": custo, "rodadas": rodadas, "tempo_s": tt}
        if extra:
            reg.update(ar_tsh=extra["tsh"]["A_ar"], ar_heur_orig=extra["heur_orig"]["A_ar"], ar_heur_pi=extra["heur_pi"]["A_ar"])
        out[nome] = reg
        print(f"{nome}: {len(coords)} vert, {len(polys)} pecas: otimo ar={custo:.1f}" + (f" | TSH {extra['tsh']['A_ar']:.1f} | heur_orig {extra['heur_orig']['A_ar']:.1f} | heur_pi {extra['heur_pi']['A_ar']:.1f}" if extra else "") + f" | {rodadas} rodadas, {tt:.1f}s", flush=True)
    json.dump(out, open(os.path.join(AQUI, "rpp_exato.json"), "w"), indent=1)


if __name__ == "__main__":
    if "--autoteste" in sys.argv:
        autoteste()
    else:
        main()
