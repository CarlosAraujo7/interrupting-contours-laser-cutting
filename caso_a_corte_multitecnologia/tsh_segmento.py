"""
tsh_segmento.py  --  TSH (two-step heuristic) de Zhang et al. (2024, Expert Syst. Appl. 237:121567, Alg. 1-2, Sec. 4.1) para o problema de NIVEL DE SEGMENTO (arc routing method / ECP, modelo RPP)
==================================================================================================================================================================================
Reimplementacao INDEPENDENTE, a partir do texto do artigo (nao copia nem importa codigo de ninguem). Problema: cada aresta (segmento) do layout deve ser cortada; o cabecote pode entrar/sair
nos vertices e re-percorrer, com o laser desligado, arestas ja cortadas; a rota e um passeio euleriano que comeca e termina na origem. TSH:
  (1) MstConnet: componentes conexos do grafo de arestas requeridas -> grafo completo entre componentes (distancia = menor distancia entre vertices dos dois) -> MST (Prim) -> arestas "de ar";
  (2) McfEven: vertices de grau impar -> emparelhamento perfeito de peso minimo (o artigo o resolve por fluxo de custo minimo; aqui, blossom exato) -> arestas "de ar";
  (3) passeio euleriano (Hierholzer) a partir da origem. Custo de ar = soma das arestas adicionadas; cada aresta requerida e cortada UMA vez.
Metrica: a do LCPP (Chebyshev), para ser comparavel com a FO do `heuristic_core.fo_from_path` (a MESMA funcao usada para todos os metodos do E-A0).
SEM precedencia (como no artigo): o TSH ignora Pi. Serve como (a) referencia de nivel de segmento quase otima (3/2-aproximacao de Frederickson para o RPP metrico; Zhang relata gap ~0,0-0,5% do otimo),
(b) limite para o "preco da precedencia". Arestas coincidentes entre pecas sao deduplicadas (cortadas uma vez). Sem divisao de arestas por cruzamentos (o artigo trata "com divisao" como pre-processamento).
"""
import os
import sys
import itertools
from collections import defaultdict

import numpy as np
import networkx as nx
from shapely.geometry import LineString

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
import heuristic_core as hc                                    # noqa: E402

ND = 8


def _cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def construir_requeridas(polys):
    """-> (coords [vertice -> (x, y)], arestas requeridas [(u, v)] sem duplicatas; o vertice 0 e a ORIGEM (0, 0))."""
    idx = {(0.0, 0.0): 0}
    coords = [(0.0, 0.0)]
    arestas, vistas = [], set()
    for p in polys:
        ring = list(p.exterior.coords)[:-1]
        ids = []
        for (x, y) in ring:
            k = (round(float(x), ND), round(float(y), ND))
            if k not in idx:
                idx[k] = len(coords)
                coords.append(k)
            ids.append(idx[k])
        for i in range(len(ids)):
            u, v = ids[i], ids[(i + 1) % len(ids)]
            if u == v:
                continue
            e = (min(u, v), max(u, v))
            if e not in vistas:
                vistas.add(e)
                arestas.append(e)
    return coords, arestas


def _componentes(n, arestas):
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
    raiz = {}
    comp = [0] * n
    for x in range(n):
        comp[x] = raiz.setdefault(f(x), len(raiz))
    return comp, len(raiz)


def _mst_conecta(coords, comp, nc):
    """MstConnet: Prim sobre o grafo completo de componentes; retorna as arestas de ar (u, v) em vertices."""
    P = np.array(coords, float)
    membros = defaultdict(list)
    for v, c in enumerate(comp):
        membros[c].append(v)
    if nc == 1:
        return []
    D = np.abs(P[:, None, :] - P[None, :, :]).max(axis=2)
    W = np.full((nc, nc), np.inf)
    par = {}
    for a in range(nc):
        ia = np.array(membros[a])
        for b in range(a + 1, nc):
            ib = np.array(membros[b])
            sub = D[np.ix_(ia, ib)]
            k = int(sub.argmin())
            i, j = divmod(k, sub.shape[1])
            W[a, b] = W[b, a] = sub[i, j]
            par[(a, b)] = par[(b, a)] = (int(ia[i]), int(ib[j]))
    dentro = np.zeros(nc, bool)
    dentro[0] = True
    melhor = W[0].copy()
    de = np.zeros(nc, int)
    ar = []
    for _ in range(nc - 1):
        cand = np.where(~dentro, melhor, np.inf)
        b = int(cand.argmin())
        a = int(de[b])
        ar.append(par[(a, b)])
        dentro[b] = True
        upd = (W[b] < melhor) & ~dentro
        melhor = np.where(upd, W[b], melhor)
        de = np.where(upd, b, de)
    return ar


def _matching_paridade(coords, impares):
    """McfEven: emparelhamento perfeito de peso minimo entre os vertices de grau impar (blossom exato)."""
    if not impares:
        return []
    P = np.array([coords[v] for v in impares], float)
    D = np.abs(P[:, None, :] - P[None, :, :]).max(axis=2)
    G = nx.Graph()
    M = float(D.max()) + 1.0
    for i in range(len(impares)):
        for j in range(i + 1, len(impares)):
            G.add_edge(i, j, weight=M - float(D[i, j]))
    m = nx.max_weight_matching(G, maxcardinality=True)
    assert 2 * len(m) == len(impares), "matching nao perfeito"
    return [(impares[i], impares[j]) for i, j in m]


def _euler(n, req, ar):
    """Hierholzer a partir da origem (vertice 0) em multigrafo com arestas requeridas e de ar; -> lista [(u, v, tipo)] na ordem do passeio."""
    adj = defaultdict(list)
    todas = [(u, v, "c") for u, v in req] + [(u, v, "d") for u, v in ar]
    for k, (u, v, t) in enumerate(todas):
        adj[u].append((v, k))
        adj[v].append((u, k))
    usada = [False] * len(todas)
    ptr = defaultdict(int)
    pilha = [(0, None)]
    circ = []
    while pilha:
        v, e = pilha[-1]
        while ptr[v] < len(adj[v]) and usada[adj[v][ptr[v]][1]]:
            ptr[v] += 1
        if ptr[v] == len(adj[v]):
            pilha.pop()
            if e is not None:
                circ.append((v, e))
        else:
            w, k = adj[v][ptr[v]]
            usada[k] = True
            pilha.append((w, k))
    circ.reverse()
    seq, atual = [], 0
    for w, k in circ:
        u0, v0, t = todas[k]
        a, b = (u0, v0) if u0 == atual else (v0, u0)
        assert a == atual, "passeio nao contiguo"
        seq.append((a, b, t))
        atual = b
    assert len(seq) == len(todas), "passeio nao cobre todas as arestas"
    return seq


def resolver_tsh(polys, v_cut=None, v_air=None):
    """-> dict com fo (FO do LCPP, mesma funcao do E-A0), ar_cheb (comprimento de ar), n_comp, n_impares, n_perfuracoes e o caminho [(LineString, 'c'|'d')]."""
    v_cut = v_cut or hc._DEFAULT_CONFIG["v_cut"]
    v_air = v_air or hc._DEFAULT_CONFIG["v_air"]
    coords, req = construir_requeridas(polys)
    comp, nc = _componentes(len(coords), req)
    mst = _mst_conecta(coords, comp, nc)
    grau = defaultdict(int)
    for u, v in req + mst:
        grau[u] += 1
        grau[v] += 1
    impares = sorted(v for v, g in grau.items() if g % 2 == 1)
    mt = _matching_paridade(coords, impares)
    ar = mst + mt
    seq = _euler(len(coords), req, ar)
    cam = [(LineString([coords[a], coords[b]]), t) for a, b, t in seq]
    perf = sum(1 for i, (_, t) in enumerate(cam) if t == "c" and (i == 0 or cam[i - 1][1] != "c"))
    ar_len = sum(_cheb(coords[u], coords[v]) for u, v in ar)
    return {"fo": float(hc.fo_from_path(cam, v_cut=v_cut, v_air=v_air)), "ar_cheb": float(ar_len), "n_comp": nc, "n_impares": len(impares), "n_perfuracoes": perf, "caminho": cam,
            "n_req": len(req), "corte_cheb": float(sum(_cheb(coords[u], coords[v]) for u, v in req))}


def saltos_caminho(cam):
    """Saltos entre segmentos consecutivos de `cam` (na ORDEM listada), com cada segmento percorrido na orientacao que minimiza o salto TOTAL (programacao dinamica exata sobre as 2 orientacoes
    de cada segmento; a orientacao listada nao e confiavel). A cabeca parte do ponto inicial do 1o segmento (a origem) e deve voltar a ele no fim. Retorna (n_saltos, comprimento Chebyshev total):
    o MENOR deslocamento em vazio que ainda e preciso, alem dos segmentos listados, para executar esses segmentos nessa ordem."""
    n = len(cam)
    ini = [(tuple(s.coords[0]), tuple(s.coords[-1])) for s, _ in cam]
    start = ini[0][0]
    # estado 0 = orientacao listada (a -> b); estado 1 = invertida (b -> a). custo[i][o] = menor salto total ate terminar o segmento i na orientacao o
    INF = float("inf")
    def pontas(i, o):
        a, b = ini[i]
        return (a, b) if o == 0 else (b, a)
    custo = [[INF, INF] for _ in range(n)]
    nsal = [[0, 0] for _ in range(n)]
    for o in (0, 1):
        d = _cheb(start, pontas(0, o)[0])
        custo[0][o] = d
        nsal[0][o] = 1 if d > 1e-6 else 0
    for i in range(1, n):
        for o in (0, 1):
            for q in (0, 1):
                d = _cheb(pontas(i - 1, q)[1], pontas(i, o)[0])
                c = custo[i - 1][q] + d
                if c < custo[i][o] - 1e-9:
                    custo[i][o] = c
                    nsal[i][o] = nsal[i - 1][q] + (1 if d > 1e-6 else 0)
    melhor, mn = INF, 0
    for o in (0, 1):
        d = _cheb(pontas(n - 1, o)[1], start)
        c = custo[n - 1][o] + d
        if c < melhor:
            melhor, mn = c, nsal[n - 1][o] + (1 if d > 1e-6 else 0)
    return mn, melhor


def autoteste():
    from shapely.geometry import box
    # dois quadrados separados: o passeio fecha pela origem e cobre as 8 arestas
    r = resolver_tsh([box(10, 10, 20, 20), box(40, 10, 50, 20)])
    assert r["n_req"] == 8 and r["n_comp"] == 3, r
    assert abs(r["corte_cheb"] - 80) < 1e-9
    assert r["ar_cheb"] > 0
    print("autoteste TSH OK:", {k: v for k, v in r.items() if k != "caminho"})


if __name__ == "__main__":
    autoteste()
