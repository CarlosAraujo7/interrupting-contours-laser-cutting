"""
instancias_lcpp1.py  --  leitor PROPRIO das instancias .txt do LCPP-1 (formato: 1a linha N; depois N linhas "x1 y1 x2 y2") e construcao do grafo de arestas requeridas COM NODING
===================================================================================================================================================================
Nao usa nem importa codigo do LCPP-main: o formato e trivial e esta descrito no cabecalho do proprio arquivo de instancias. Os segmentos sao agrupados em contornos pela ORDEM do arquivo
(cada contorno e uma cadeia fechada de segmentos consecutivos). Pecas que se tocam / segmentos sobrepostos exigem NODING: a uniao dos segmentos (shapely `unary_union`) divide as arestas nos pontos
de interseccao e funde trechos coincidentes (cada trecho distinto e cortado UMA vez). A posse de cada trecho por contornos (para a precedencia de fechamento) vem do ponto medio.
As instancias sao de terceiros (ESICUP e geradas pelos autores do LCPP-1): ficam so localmente; nao redistribuir.
"""
import os
import sys
from collections import defaultdict

import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
ND = 8


def ler_segmentos(caminho):
    linhas = [l.strip() for l in open(caminho, encoding="utf-8") if l.strip()]
    try:
        int(linhas[0])
        linhas = linhas[1:]
    except ValueError:
        pass
    segs = []
    for l in linhas:
        p = l.split()
        if len(p) >= 4:
            segs.append(tuple(map(float, p[:4])))
    return segs


def agrupar_contornos(segs, tol=1e-6):
    """cadeias fechadas de segmentos consecutivos -> lista de listas de pontos (aneis, sem repetir o ultimo)."""
    aneis, atual = [], []
    for x1, y1, x2, y2 in segs:
        if atual and (abs(atual[-1][0] - x1) > tol or abs(atual[-1][1] - y1) > tol):
            aneis.append(atual)                       # cadeia nao fechou: descarta como esta (contorno aberto)
            atual = []
        if not atual:
            atual = [(x1, y1)]
        atual.append((x2, y2))
        if len(atual) > 2 and abs(atual[0][0] - x2) <= tol and abs(atual[0][1] - y2) <= tol:
            aneis.append(atual[:-1])
            atual = []
    if atual:
        aneis.append(atual)
    return aneis


def poligonos(aneis):
    """Polygons validos (descarta aneis com < 3 pontos); mantem a ordem."""
    out = []
    for a in aneis:
        if len(a) >= 3:
            p = Polygon(a)
            out.append(p if p.is_valid else p.buffer(0))
    return out


def requeridas_com_noding(aneis, tol=1e-7):
    """-> (coords, req [(u, v)], dono {indice de req: set(indices de aneis)}), com a uniao dos segmentos DIVIDIDA nas interseccoes e trechos coincidentes fundidos."""
    linhas = []
    for a in aneis:
        pts = list(a) + [a[0]]
        for p, q in zip(pts[:-1], pts[1:]):
            if p != q:
                linhas.append(LineString([p, q]))
    uni = unary_union(linhas)
    partes = [uni] if uni.geom_type == "LineString" else list(uni.geoms)
    idx = {(0.0, 0.0): 0}
    coords = [(0.0, 0.0)]
    req, vistas = [], set()
    for ln in partes:
        c = list(ln.coords)
        for a, b in zip(c[:-1], c[1:]):
            ka, kb = (round(a[0], ND), round(a[1], ND)), (round(b[0], ND), round(b[1], ND))
            if ka == kb:
                continue
            for k in (ka, kb):
                if k not in idx:
                    idx[k] = len(coords)
                    coords.append(k)
            u, v = idx[ka], idx[kb]
            e = (min(u, v), max(u, v))
            if e not in vistas:
                vistas.add(e)
                req.append(e)
    # posse por ponto medio
    rings = [LineString(list(a) + [a[0]]) for a in aneis]
    dono = defaultdict(set)
    for k, (u, v) in enumerate(req):
        mid = Point((coords[u][0] + coords[v][0]) / 2, (coords[u][1] + coords[v][1]) / 2)
        esc = max(1.0, abs(coords[u][0]), abs(coords[u][1]))
        for ci, r in enumerate(rings):
            if r.distance(mid) <= tol * esc * 10:
                dono[k].add(ci)
    return coords, req, dono
