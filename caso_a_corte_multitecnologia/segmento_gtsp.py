"""
segmento_gtsp.py  --  O problema de NIVEL DE SEGMENTO (com perfuracao e precedencia de fechamento) como um GTSP COM PRECEDENCIA sobre ARESTAS ORIENTADAS, resolvido com o PCGLNS
==========================================================================================================================================================================
Reformulacao (classica para o RPP, aqui com perfuracao e Pi de fechamento): cada aresta requerida (lado de contorno, deduplicado) e um GRUPO com 2 cidades = suas duas orientacoes; o grupo 1 e a origem.
Uma cidade (aresta e, orientacao) tem ponto de partida s e de chegada f. O custo do arco (a -> b) e o do deslocamento em vazio entre f(a) e s(b): 0 se coincidem (o corte CONTINUA, sem perfuracao),
senao  d_Chebyshev(f(a), s(b)) / v_air + t_perf  (um novo inicio de corte = uma perfuracao). O tour visita cada grupo uma vez e volta a origem: e uma solucao do nivel de segmento sem nenhum salto escondido.
Precedencia de FECHAMENTO: para cada contorno o e uma aresta designada de fechamento c(o): toda aresta de cada contorno FILHO i de o precede c(o) (ordem de grupos no arquivo .pcglns); como c(i) esta entre
as arestas de i, a transitividade da todos os descendentes antes de c(o), e o ultimo segmento de o fica depois de c(o) ou e c(o): o contorno o so FECHA depois de todos os descendentes. A escolha de c(o) e
refinada iterativamente (a ultima aresta de o na solucao anterior) -- a solucao anterior continua viavel, entao o refinamento nao piora a viabilidade.
O custo e inteiro: round(1e5 * segundos). A FO "honesta" e reavaliada por `caminho_honesto` sobre o caminho resultante.
"""
import os
import re
import sys
import subprocess
import tempfile
from collections import defaultdict

import numpy as np
from shapely.geometry import LineString

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import tsh_segmento as tsh                                      # noqa: E402
import caminho_honesto as ch                                    # noqa: E402

hc = tsh.hc
PCGLNS_DIR = os.path.join(os.path.dirname(AQUI), "ferramentas", "PCGLNS_upstream")
ESC = 100000


def construir_arcos(polys, portais="todos", k_vizinhos=4, grafo=None):
    """Grafo das arestas requeridas deduplicadas -> ARCOS (cadeias maximais de vertices de grau 2 sem 'portal'). `portais`: 'todos' (cada aresta e um arco) ou 'reduzido' (portais =
    pontos de ramificacao/compartilhamento + origem + pontas do TSH + extremos de cada contorno + pares mais proximos entre contornos vizinhos). -> (coords, arcos [(u, v, [arestas])], dono_arco [conjunto de contornos])"""
    if grafo is not None:                                          # instancias com noding (LCPP-1): grafo pre-calculado
        coords, req, dono, aneis = grafo["coords"], grafo["req"], grafo["dono"], grafo["aneis_ids"]
    else:
        coords, req = tsh.construir_requeridas(polys)
        pos = {c: i for i, c in enumerate(coords)}
        chave = {(min(u, v), max(u, v)): k for k, (u, v) in enumerate(req)}
        dono = defaultdict(set)
        aneis = []
        for ci, p in enumerate(polys):
            ring = list(p.exterior.coords)[:-1]
            ids = [pos[(round(float(x), tsh.ND), round(float(y), tsh.ND))] for x, y in ring]
            aneis.append(ids)
            for i in range(len(ids)):
                u, v = ids[i], ids[(i + 1) % len(ids)]
                k = chave.get((min(u, v), max(u, v)))
                if k is not None:
                    dono[k].add(ci)
    grau = defaultdict(int)
    inc = defaultdict(list)
    for k, (u, v) in enumerate(req):
        grau[u] += 1
        grau[v] += 1
        inc[u].append(k)
        inc[v].append(k)
    quebra = {v for v, g in grau.items() if g != 2} | {0}
    if portais == "todos":
        quebra |= set(grau)
    else:
        P = np.array(coords, float)
        # pontas do TSH (arestas de ar)
        comp, nc = tsh._componentes(len(coords), req)
        mst = tsh._mst_conecta(coords, comp, nc)
        g2 = defaultdict(int)
        for u, v in req + mst:
            g2[u] += 1
            g2[v] += 1
        impares = sorted(v for v, g in g2.items() if g % 2 == 1)
        mt = tsh._matching_paridade(coords, impares)
        for u, v in mst + mt:
            quebra.add(u)
            quebra.add(v)
        # extremos de cada contorno e pares mais proximos entre contornos vizinhos
        for ids in aneis:
            A = P[ids]
            for col in (0, 1):
                quebra.add(ids[int(A[:, col].argmin())])
                quebra.add(ids[int(A[:, col].argmax())])
        cent = np.array([P[ids].mean(axis=0) for ids in aneis])
        from scipy.spatial import cKDTree
        arv = cKDTree(cent)
        for ci, ids in enumerate(aneis):
            _, viz = arv.query(cent[ci], k=min(k_vizinhos + 1, len(aneis)))
            for cj in np.atleast_1d(viz):
                if cj == ci:
                    continue
                A, B = P[ids], P[aneis[cj]]
                d = np.abs(A[:, None, :] - B[None, :, :]).max(axis=2)
                i, j = divmod(int(d.argmin()), d.shape[1])
                quebra.add(ids[i])
                quebra.add(aneis[cj][j])
    # cadeias
    usada = set()
    arcos = []
    for b in sorted(quebra):
        for k0 in inc[b]:
            if k0 in usada:
                continue
            cadeia = [k0]
            usada.add(k0)
            u0, v0 = req[k0]
            cur = v0 if u0 == b else u0
            while cur not in quebra:
                prox = [k for k in inc[cur] if k not in usada]
                if not prox:
                    break
                k1 = prox[0]
                usada.add(k1)
                cadeia.append(k1)
                u1, v1 = req[k1]
                cur = v1 if u1 == cur else u1
            arcos.append((b, cur, cadeia))
    # ciclos sem vertice de quebra: nao ocorre (todo contorno tem >= 1 quebra pelos extremos) -- garantir
    faltando = [k for k in range(len(req)) if k not in usada]
    assert not faltando, f"arestas fora dos arcos: {len(faltando)}"
    dono_arco = [set().union(*[dono[k] for k in cad]) for _, _, cad in arcos]
    return coords, req, arcos, dono_arco


def montar(polys, pares, t_perf=0.0, fechamento=None, v_air=None, portais="todos", grafo=None):
    """-> dict com cidades, matriz inteira, grupos, ordem. `fechamento` {contorno: indice de ARCO} (default: o 1o arco do contorno)."""
    v_air = v_air or hc._DEFAULT_CONFIG["v_air"]
    coords, req, arcos, dono_arco = construir_arcos(polys, portais, grafo=grafo)
    A = len(arcos)
    arcos_do_contorno = defaultdict(list)
    for a, donos in enumerate(dono_arco):
        for c in donos:
            arcos_do_contorno[c].append(a)
    n = 1 + 2 * A
    s = [coords[0]] + [None] * (2 * A)
    f = [coords[0]] + [None] * (2 * A)
    for a, (u, v, _) in enumerate(arcos):
        s[1 + 2 * a], f[1 + 2 * a] = coords[u], coords[v]
        s[2 + 2 * a], f[2 + 2 * a] = coords[v], coords[u]
    S = np.array(s, float)
    F = np.array(f, float)
    d = np.abs(F[:, None, :] - S[None, :, :]).max(axis=2)
    custo = d / v_air + np.where(d > 1e-9, t_perf, 0.0)
    D = np.rint(custo * ESC).astype(np.int64)
    grupo = np.zeros(n, int)
    grupo[1::2] = 2 + np.arange(A)
    grupo[2::2] = 2 + np.arange(A)
    grupo[0] = 1
    D[grupo[:, None] == grupo[None, :]] = 0
    if fechamento is None:
        fechamento = {c: arcos_do_contorno[c][0] for c in arcos_do_contorno}
    ordem = defaultdict(set)
    for i, o in pares:                                           # i (interno) antes de o (externo)
        co = fechamento[o]
        for a in arcos_do_contorno[i]:
            if a != co:
                ordem[2 + a].add(2 + co)
    return {"coords": coords, "req": req, "arcos": arcos, "D": D, "grupo": grupo, "ordem": ordem, "arestas_do_contorno": arcos_do_contorno, "E": A, "fechamento": fechamento, "n": n, "t_perf": t_perf}


def escrever(inst, caminho):
    n, E = inst["n"], inst["E"]
    with open(caminho, "w", encoding="latin-1") as fh:
        fh.write(f"NAME : seg\nTYPE : PCGLNS\nCOMMENT : segmento (E-A0)\nDIMENSION : {n}\nGTSP_SETS : {E + 1}\nEDGE_WEIGHT_TYPE : EXPLICIT\nEDGE_WEIGHT_FORMAT : FULL_MATRIX\nEDGE_WEIGHT_SECTION\n")
        for i in range(n):
            fh.write(" ".join(map(str, inst["D"][i])) + "\n")
        fh.write("GTSP_SET_SECTION\n1 1 -1\n")
        for k in range(E):
            fh.write(f"{2 + k} {2 + 2 * k} {3 + 2 * k} -1\n")           # cidades 1-based: aresta k -> 2k+2 e 2k+3
        fh.write("GTSP_SET_ORDERING\n")
        for pred in sorted(inst["ordem"]):
            fh.write(f"{pred} " + " ".join(map(str, sorted(inst["ordem"][pred]))) + " -1\n")
        fh.write("START_GROUP_SECTION\n1\nEOF\n")


def resolver(inst, tempo=60, semente=0):
    tmp = tempfile.mkdtemp(prefix="seg_")
    arq, saida = os.path.join(tmp, "seg.pcglns"), os.path.join(tmp, "o.tour")
    escrever(inst, arq)
    p = subprocess.run(["julia", "--threads=1,0", "runPCGLNS.jl", arq, "-mode=default", f"-max_time={tempo}", "-verbose=0", f"-output={saida}", f"-seed={semente}"],
                       cwd=PCGLNS_DIR, capture_output=True, text=True, errors="replace")
    txt = open(saida, encoding="latin-1").read() if os.path.exists(saida) else ""
    m = re.search(r"Tour\s*:\s*\[([^\]]+)\]", txt)
    for x in os.listdir(tmp):
        try:
            os.remove(os.path.join(tmp, x))
        except OSError:
            pass
    try:
        os.rmdir(tmp)
    except OSError:
        pass
    if not m:
        return None
    tour = [int(x) for x in m.group(1).split(",")]
    if tour[0] != 1:
        k = tour.index(1)
        tour = tour[k:] + tour[:k]
    return tour


def caminho_do_tour(inst, tour):
    """tour (cidades 1-based) -> caminho contiguo [(LineString, tag)] origem -> ... -> origem (cada arco expandido em suas arestas)."""
    coords, req, arcos = inst["coords"], inst["req"], inst["arcos"]
    cam, pos = [], coords[0]
    for cid in tour[1:]:
        k, o = divmod(cid - 2, 2)
        u, v, cadeia = arcos[k]
        a, b = (coords[u], coords[v]) if o == 0 else (coords[v], coords[u])
        if tsh._cheb(pos, a) > 1e-9:
            cam.append((LineString([pos, a]), "d"))
        seq = cadeia if o == 0 else list(reversed(cadeia))
        cur = u if o == 0 else v
        for e in seq:
            eu, ev = req[e]
            nxt = ev if eu == cur else eu
            cam.append((LineString([coords[cur], coords[nxt]]), "c"))
            cur = nxt
        pos = coords[cur]
    if tsh._cheb(pos, coords[0]) > 1e-9:
        cam.append((LineString([pos, coords[0]]), "d"))
    return cam


def ultima_aresta_por_contorno(inst, tour):
    ordem = {}
    for p, cid in enumerate(tour[1:]):
        k = (cid - 2) // 2
        ordem[k] = p
    fech = {}
    for c, arestas in inst["arestas_do_contorno"].items():
        fech[c] = max(arestas, key=lambda k: ordem.get(k, -1))
    return fech
