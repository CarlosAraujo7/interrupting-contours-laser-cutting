"""
caminho_honesto.py  --  FO HONESTA UNICA e VERIFICADOR de caminho para TODOS os metodos (WP-H0 do docs/14; achado de `docs/15`)
===============================================================================================================================
Um metodo so pode reportar uma FO se o que ele devolve e um CAMINHO EXECUTAVEL. Este modulo define o que isso significa e o verifica:
  contiguar(cam)     transforma uma lista [(LineString, tag)] em um caminho CONTIGUO que parte e volta a origem, escolhendo a orientacao de cada segmento (DP exata) e inserindo, entre segmentos
                     nao contiguos, deslocamentos em vazio explicitos ('d', corda direta Chebyshev). Para caminhos ja contiguos (TSH, modo com Pi, tours de pecas) nao muda nada.
  fo_honesta(cam)    FO = sum Chebyshev(c)/v_cut + sum Chebyshev(d)/v_air + t_perf * (nº de corridas contiguas de 'c')  -- sobre o caminho contiguo; mesma convencao da `heuristic_core.calcular_fo`.
  verificar(cam, polys)  contiguidade, origem, cada aresta distinta dos contornos cortada EXATAMENTE uma vez ('c'), nenhum 'c' fora das arestas, e as violacoes de Pi sob DUAS semanticas:
        "estrita"  (a do piece-level e da heuristica com Pi): todo segmento do contorno interno antes do PRIMEIRO segmento do contornos que o contem;
        "relaxada" (a restricao fisica: a peca so e liberada quando o contorno externo FECHA): todo segmento do interno antes do ULTIMO segmento do externo.
O ultimo ponto e relevante para a generalizacao: a semantica relaxada admite muito mais solucoes de nivel de segmento (contornos externos cortados em varias passadas).
"""
import os
import sys
from collections import defaultdict

from shapely.geometry import LineString

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
import heuristic_core as hc                                    # noqa: E402

ND = 6


def _cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _k(p):
    return (round(float(p[0]), ND), round(float(p[1]), ND))


def contiguar(cam, origem=(0.0, 0.0)):
    """-> (caminho contiguo [(LineString, tag)], n_saltos, comprimento_saltos). Sempre comeca e termina em `origem`."""
    cam = list(cam)
    n = len(cam)
    pts = [(tuple(s.coords[0]), tuple(s.coords[-1])) for s, _ in cam]
    INF = float("inf")

    def pontas(i, o):
        a, b = pts[i]
        return (a, b) if o == 0 else (b, a)
    custo = [[INF, INF] for _ in range(n)]
    pai = [[None, None] for _ in range(n)]
    for o in (0, 1):
        custo[0][o] = _cheb(origem, pontas(0, o)[0])
    for i in range(1, n):
        for o in (0, 1):
            for q in (0, 1):
                c = custo[i - 1][q] + _cheb(pontas(i - 1, q)[1], pontas(i, o)[0])
                if c < custo[i][o] - 1e-12:
                    custo[i][o], pai[i][o] = c, q
    fim = [custo[n - 1][o] + _cheb(pontas(n - 1, o)[1], origem) for o in (0, 1)]
    o = 0 if fim[0] <= fim[1] else 1
    ori = [0] * n
    for i in range(n - 1, -1, -1):
        ori[i] = o
        if i > 0:
            o = pai[i][o]
    out, pos, nsal, tot = [], tuple(origem), 0, 0.0
    for i in range(n):
        a, b = pontas(i, ori[i])
        if _cheb(pos, a) > 1e-9:
            out.append((LineString([pos, a]), "d"))
            nsal += 1
            tot += _cheb(pos, a)
        seg, tag = cam[i]
        out.append((LineString([a, b]), tag))
        pos = b
    if _cheb(pos, origem) > 1e-9:
        out.append((LineString([pos, tuple(origem)]), "d"))
        nsal += 1
        tot += _cheb(pos, origem)
    return out, nsal, tot


def fo_honesta(cam, v_cut=None, v_air=None, t_perf=0.0, ja_contiguo=False, origem=(0.0, 0.0)):
    """FO sobre o caminho CONTIGUO. `cam` com tags 'x' e reclassificado como em `heuristic_core.reclassificar_tags`."""
    v_cut = v_cut or hc._DEFAULT_CONFIG["v_cut"]
    v_air = v_air or hc._DEFAULT_CONFIG["v_air"]
    cl = hc.reclassificar_tags(cam)
    if not ja_contiguo:
        cl, nsal, tot = contiguar(cl, origem)
    else:
        nsal, tot = 0, 0.0
    custo, perf, ant = 0.0, 0, None
    for s, t in cl:
        custo += _cheb(s.coords[0], s.coords[-1]) / (v_cut if t == "c" else v_air)
        if t == "c" and ant != "c":
            perf += 1
        ant = t
    return {"fo": custo + t_perf * perf, "n_perfuracoes": perf, "n_saltos": nsal, "comprimento_saltos": tot, "caminho": cl}


def _canonizador(polys, tol=1e-5):
    """Mapeia pontos para ids canonicos de vertices dos contornos, com TOLERANCIA (arredondar por casas decimais falha quando o valor esta perto do meio-passo)."""
    import numpy as np
    from scipy.spatial import cKDTree
    pts = [tuple(c) for p in polys for c in list(p.exterior.coords)[:-1]]
    A = np.array(pts, float)
    pai = list(range(len(pts)))

    def f(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x
    tree = cKDTree(A)
    for a, b in tree.query_pairs(r=tol):
        ra, rb = f(a), f(b)
        if ra != rb:
            pai[ra] = rb
    raiz = [f(i) for i in range(len(pts))]
    def canon(q):
        d, i = tree.query(np.array(q[:2], float))
        return raiz[i] if d <= tol else ("fora", _k(q))
    return canon


def verificar(cam, polys, pares_pi=None, origem=(0.0, 0.0), tol=1e-6):
    """-> dict com os testes. `cam` ja deve estar CONTIGUO e classificado ('c'/'d'). `pares_pi` = [(interno, externo)] em indices de `polys` (default: `hc._detectar_precedencia`)."""
    r = {}
    ok_cont = True
    for (s1, _), (s2, _) in zip(cam[:-1], cam[1:]):
        if _cheb(s1.coords[-1], s2.coords[0]) > tol * 100:
            ok_cont = False
            break
    r["contiguo"] = ok_cont
    r["parte_e_volta_origem"] = _cheb(cam[0][0].coords[0], origem) <= tol * 100 and _cheb(cam[-1][0].coords[-1], origem) <= tol * 100
    canon = _canonizador(polys)
    aresta = {}
    dono = defaultdict(list)
    for k, p in enumerate(polys):
        c = list(p.exterior.coords)
        for a, b in zip(c[:-1], c[1:]):
            e = frozenset((canon(a), canon(b)))
            if len(e) < 2:
                continue
            aresta.setdefault(e, 0)
            dono[e].append(k)
    cortes = defaultdict(int)
    fora = 0
    ordem_corte = {}
    for pos, (s, t) in enumerate(cam):
        if t != "c":
            continue
        e = frozenset((canon(s.coords[0]), canon(s.coords[-1])))
        if e in aresta:
            cortes[e] += 1
            ordem_corte.setdefault(e, pos)
        else:
            fora += 1
    r["arestas_distintas"] = len(aresta)
    r["arestas_nao_cortadas"] = sum(1 for e in aresta if cortes[e] == 0)
    r["arestas_cortadas_mais_de_uma_vez"] = sum(1 for e in aresta if cortes[e] > 1)
    r["segmentos_de_corte_fora_das_arestas"] = fora
    if pares_pi is None:
        pares_pi = hc._detectar_precedencia(list(polys))
    primeiro, ultimo = {}, {}
    for e, ks in dono.items():
        if e in ordem_corte:
            for k in ks:
                primeiro[k] = min(primeiro.get(k, 10 ** 12), ordem_corte[e])
                ultimo[k] = max(ultimo.get(k, -1), ordem_corte[e])
    estrita = relaxada = 0
    for i, j in pares_pi:                  # i (interno) antes de j (externo)
        if i not in ultimo or j not in primeiro:
            continue
        if ultimo[i] > primeiro[j]:
            estrita += 1
        if ultimo[i] > ultimo[j]:
            relaxada += 1
    r["n_pares_pi"] = len(pares_pi)
    r["violacoes_pi_estrita"] = estrita
    r["violacoes_pi_relaxada"] = relaxada
    # verificacao GEOMETRICA (tolera a divisao de arestas por cruzamentos/contatos feita no pre-processamento da heuristica): a uniao dos segmentos de corte deve coincidir com a uniao dos
    # contornos e cada trecho deve ser cortado uma unica vez (comprimento total de corte = comprimento da uniao).
    from shapely.ops import unary_union
    cortes_geo = [s for s, t in cam if t == "c"]
    uniao_corte = unary_union(cortes_geo)
    uniao_contornos = unary_union([LineString(list(p.exterior.coords)) for p in polys])
    L_corte = sum(s.length for s in cortes_geo)
    L_uniao = uniao_contornos.length
    r["geo_comprimento_corte"] = L_corte
    r["geo_comprimento_uniao_contornos"] = L_uniao
    tolb = 1e-6 * max(1.0, max((abs(c) for p in polys for xy in p.exterior.coords for c in xy), default=1.0))
    r["geo_diferenca_simetrica"] = uniao_corte.difference(uniao_contornos.buffer(tolb)).length + uniao_contornos.difference(uniao_corte.buffer(tolb)).length   # tolerante a nos diferentes
    r["geo_ok"] = abs(L_corte - L_uniao) <= 1e-6 * max(L_uniao, 1.0) and r["geo_diferenca_simetrica"] <= 1e-6 * max(L_uniao, 1.0)
    r["ok_arestas_exatas"] = r["arestas_nao_cortadas"] == 0 and r["arestas_cortadas_mais_de_uma_vez"] == 0 and fora == 0
    r["ok"] = ok_cont and r["parte_e_volta_origem"] and (r["ok_arestas_exatas"] or r["geo_ok"])
    return r


def autoteste():
    from shapely.geometry import box
    import tsh_segmento as tsh
    polys = [box(10, 10, 20, 20), box(40, 10, 50, 20)]
    t = tsh.resolver_tsh(polys)
    h = fo_honesta(t["caminho"], ja_contiguo=True)
    v = verificar(t["caminho"], polys, pares_pi=[])
    assert v["ok"], v
    assert abs(h["fo"] - t["fo"]) < 1e-9, (h["fo"], t["fo"])
    # um caminho NAO contiguo (dois segmentos separados) e consertado
    cam = [(LineString([(10, 10), (20, 10)]), "c"), (LineString([(40, 10), (30, 10)]), "c")]
    cc, n, tot = contiguar(cam)
    assert all(_cheb(a[0].coords[-1], b[0].coords[0]) < 1e-9 for a, b in zip(cc[:-1], cc[1:]))
    assert n == 3 and abs(tot - 60.0) < 1e-9, (n, tot)       # origem->(10,10): 10; (20,10)->(30,10): 10; (40,10)->origem: 40
    print("autoteste caminho_honesto OK:", n, "saltos", tot)


if __name__ == "__main__":
    autoteste()
