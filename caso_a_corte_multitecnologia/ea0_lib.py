"""
ea0_lib.py  --  biblioteca do experimento E-A0 (plano 07, WP4.2-4.3): heuristica proposta x PCGLNS x VNS-Pi x MASTRI nas MESMAS instancias GEOMETRICAS
=========================================================================================================================================
Todos os metodos resolvem o MESMO problema e sao avaliados pela MESMA funcao de objetivo:

  - Instancia geometrica: pecas = contornos fechados do DXF do CPPLib (`dxf_parser.load_instance_dxf`), origem (0,0) = posicao inicial/final
    da cabeca. Precedencia Pi = contencao geometrica (`heuristic_core._detectar_precedencia`): o contorno interno deve ser cortado ANTES do que o contem.
  - Instancia abstrata (para PCGLNS / VNS-Pi / MASTRI): grupo 1 = origem (1 cidade); grupo k+2 = peca k, com UMA cidade por VERTICE do contorno
    (os baselines tem a MESMA liberdade de ponto de entrada que a heuristica, cujo `vertex_strategy` escolhe entre os vertices); distancia =
    Chebyshev (mm; a metrica da FO do LCPP) x ESCALA arredondada (inteira, como nos `.pcglns` do projeto); mesma peca = 0; Pi codificada em `GTSP_SET_ORDERING` e como arcos
    proibidos (-1) do grupo sucessor para o predecessor, como nas instancias EnsignDaniels/CPP. Ciclo FECHADO com retorno a origem.
  - Objetivo comum: FO = `heuristic_core.fo_from_path` (tempo: corte a v_cut, deslocamento a v_air, perfuracao) sobre o CAMINHO completo
    (o tour vira segmentos 'd' ate o vertice de entrada, 'c' ao longo do contorno inteiro e retorno 'd' a origem). Como o corte de cada contorno
    e constante, a diferenca entre metodos e so o deslocamento (com a reclassificacao de trechos que a funcao faz, igual para todos).
Violacoes de Pi sao contadas com a mesma logica do runner do CPPLib (ordem de corte das pecas).

Limitacoes declaradas: contornos de pecas sao poligonos ja simplificados pelo parser (entidades degeneradas de 2 vertices excluidas, ver
`dxf_parser.py`); ESCALA = 10 (resolucao de 0,1 mm); o custo abstrato nao reclassifica trechos (so a FO final, igual para todos).
"""
from __future__ import annotations

import os
import sys
from typing import Dict, List, Tuple

import numpy as np
from shapely.geometry import LineString, Polygon

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
import heuristic_core as hc  # noqa: E402

hc.MST_RAPIDA = True   # versao rapida e EQUIVALENTE da construcao do grafo (validada: 85/85 grafos identicos; `validar_mst_rapida.py`). Muda so o TEMPO da construcao.
ESCALA = 10
CFG_BASE = {"root_strategy": "nearest", "child_order": "num_filhos", "mst_strategy": "standard", "vertex_strategy": "nearest"}


def vertices(poly: Polygon) -> List[Tuple[float, float]]:
    c = list(poly.exterior.coords)
    return c[:-1]                                   # sem repetir o ultimo


def montar_instancia(polys: List[Polygon]) -> Dict:
    """-> dict com cidades [(x, y, grupo, peca, vertice)], grupos, pares (pred, suc) em ids de GRUPO e a matriz (int)."""
    cidades = [(0.0, 0.0, 1, -1, 0)]              # cidade 1 = origem, grupo 1
    for k, p in enumerate(polys):
        for v, (x, y) in enumerate(vertices(p)):
            cidades.append((x, y, k + 2, k, v))
    n = len(cidades)
    xy = np.array([[c[0], c[1]] for c in cidades], float)
    # METRICA = CHEBYSHEV (L-infinito), a MESMA de `heuristic_core.calcular_fo` (que mede cada segmento por `chebyshev(p0, p1)`) e do conversor do LCPP-main.
    # (Ate 05/10/2026 este arquivo usava Euclidiana: os baselines otimizavam uma metrica DIFERENTE da que os avaliava -- corrigido; resultados antigos em
    # `ea0_resultados_euclid/`.)
    D = np.rint(np.abs(xy[:, None, :] - xy[None, :, :]).max(axis=2) * ESCALA).astype(np.int64)
    grupo = np.array([c[2] for c in cidades])
    D[grupo[:, None] == grupo[None, :]] = 0         # mesma peca: 0
    pares_pecas = hc._detectar_precedencia(list(polys))            # (interno, pai): interno antes do pai
    pares = [(i + 2, j + 2) for i, j in pares_pecas]
    for pred, suc in pares:                          # arcos do grupo sucessor para o predecessor: proibidos
        D[np.ix_(grupo == suc, grupo == pred)] = -1
    return {"cidades": cidades, "D": D, "pares": pares, "n_grupos": len(polys) + 1}


def parsed_de_instancia(inst: Dict, nome: str = "inst") -> Dict:
    """Mesma estrutura que `mastri.parse_pcglns` devolve, montada direto da instancia (sem escrever/ler o arquivo .pcglns)."""
    cid = inst["cidades"]
    group_cities: Dict[int, List[int]] = {}
    for i, c in enumerate(cid, 1):
        group_cities.setdefault(c[2], []).append(i)
    return {"dim": len(cid), "matrix": inst["D"].tolist(), "city_group": {i: c[2] for i, c in enumerate(cid, 1)},
            "group_cities": group_cities, "pares": list(inst["pares"]), "start_group": 1, "name": nome}


def escrever_pcglns(inst: Dict, caminho: str, nome: str) -> None:
    n = len(inst["cidades"])
    grupos: Dict[int, List[int]] = {}
    for i, c in enumerate(inst["cidades"], 1):
        grupos.setdefault(c[2], []).append(i)
    ordem: Dict[int, List[int]] = {}
    for pred, suc in inst["pares"]:
        ordem.setdefault(pred, []).append(suc)
    with open(caminho, "w", encoding="latin-1") as f:
        f.write(f"NAME : {nome}\nTYPE : PCGLNS\nCOMMENT : gerado de DXF do CPPLib (E-A0)\nDIMENSION : {n}\nGTSP_SETS : {len(grupos)}\n"
                "EDGE_WEIGHT_TYPE : EXPLICIT\nEDGE_WEIGHT_FORMAT : FULL_MATRIX\nEDGE_WEIGHT_SECTION\n")
        for i in range(n):
            f.write(" ".join(map(str, inst["D"][i])) + "\n")
        f.write("GTSP_SET_SECTION\n")
        for g in sorted(grupos):
            f.write(f"{g} " + " ".join(map(str, grupos[g])) + " -1\n")
        f.write("GTSP_SET_ORDERING\n")
        for pred in sorted(ordem):
            f.write(f"{pred} " + " ".join(map(str, ordem[pred])) + " -1\n")
        f.write("START_GROUP_SECTION\n1\nEOF\n")


def caminho_de_tour(polys: List[Polygon], inst: Dict, tour: List[int]) -> List[Tuple[LineString, str]]:
    """Tour (ids de cidade 1-based, comecando na origem) -> caminho [(LineString, 'd'|'c')] no formato de `run_heuristic`."""
    cam: List[Tuple[LineString, str]] = []
    pos = (0.0, 0.0)
    for cid in tour:
        x, y, g, k, v = inst["cidades"][cid - 1]
        if k < 0:
            continue                                  # origem
        if (x, y) != pos:
            cam.append((LineString([pos, (x, y)]), "d"))
        ring = list(polys[k].exterior.coords)[:-1]
        m = len(ring)
        seq = [ring[(v + t) % m] for t in range(m + 1)]
        for a, b in zip(seq[:-1], seq[1:]):
            if a != b:
                cam.append((LineString([a, b]), "c"))
        pos = (x, y)
    if pos != (0.0, 0.0):
        cam.append((LineString([pos, (0.0, 0.0)]), "d"))
    return cam


def violacoes(inst: Dict, tour: List[int]) -> int:
    """Pares de Pi violados na ordem de corte das pecas do tour."""
    pos_g = {}
    for t, cid in enumerate(tour):
        pos_g[inst["cidades"][cid - 1][2]] = t
    return sum(1 for pred, suc in inst["pares"] if pred in pos_g and suc in pos_g and pos_g[pred] > pos_g[suc])


def fo_do_tour(polys: List[Polygon], inst: Dict, tour: List[int], v_cut: float, v_air: float, t_perf: float = 0.0) -> float:
    return float(hc.fo_from_path(caminho_de_tour(polys, inst, tour), v_cut=v_cut, v_air=v_air, tempo_perfuracao=t_perf))


def tour_de_caminho(polys: List[Polygon], inst: Dict, cam) -> List[int]:
    """Caminho da heuristica -> tour de cidades (origem + (peca, vertice de ENTRADA) na ordem de corte)."""
    chave = lambda x, y: (round(x, 6), round(y, 6))
    por_vertice: Dict[Tuple[float, float], List[Tuple[int, int]]] = {}
    verts = []
    for k, p in enumerate(polys):
        vs = vertices(p)
        verts.append({chave(x, y) for x, y in vs})
        for v, (x, y) in enumerate(vs):
            por_vertice.setdefault(chave(x, y), []).append((k, v))
    cid = {(c[3], c[4]): i for i, c in enumerate(inst["cidades"], 1) if c[3] >= 0}
    vistos, tour = set(), [1]
    for seg, tag in cam:
        if tag != "c":
            continue
        a, b = seg.coords[0], seg.coords[-1]
        for k, v in por_vertice.get(chave(*a), []):
            if k not in vistos and chave(*b) in verts[k]:
                vistos.add(k)
                tour.append(cid[(k, v)])
                break
    assert len(vistos) == len(polys), (len(vistos), len(polys))
    return tour


def autoteste() -> None:
    """A FO do caminho da PROPRIA heuristica reconstruido pelo tour de entradas deve ser coerente: converte o caminho da heuristica
    num tour (peca, vertice de entrada) e confere que `fo_do_tour` reproduz o `fo_total` dela (tolerancia de reclassificacao)."""
    import glob
    import dxf_parser
    f = glob.glob(os.path.join(AQUI, "instances", "cpplib", "**", "p1xk_10.dxf"), recursive=True)[0]
    nome, polys, info = dxf_parser.load_instance_dxf(f)
    res = hc.run_heuristic(list(polys), {**CFG_BASE, "time_limit": 30, "enforce_precedence": True})
    cam = res["caminho"]
    inst = montar_instancia(polys)
    # recupera, para cada peca, o vertice de entrada = primeiro ponto de corte da peca
    entrada = {}
    ordem = []
    for seg, tag in cam:
        if tag != "c":
            continue
        a = seg.coords[0]
        for k, p in enumerate(polys):
            if k not in entrada and any(abs(a[0] - x) < 1e-9 and abs(a[1] - y) < 1e-9 for x, y in vertices(p)) and p.exterior.distance(seg) < 1e-9:
                entrada[k] = a
                ordem.append(k)
                break
    assert len(ordem) == len(polys), (len(ordem), len(polys))
    tour = [1]
    for k in ordem:
        v = next(i for i, (x, y) in enumerate(vertices(polys[k])) if (x, y) == entrada[k])
        tour.append(next(i for i, c in enumerate(inst["cidades"], 1) if c[3] == k and c[4] == v))
    fo = fo_do_tour(polys, inst, tour, hc._DEFAULT_CONFIG["v_cut"], hc._DEFAULT_CONFIG["v_air"])
    print(f"autoteste: fo_total da heuristica = {res['fo_total']:.2f}; FO do tour reconstruido = {fo:.2f}; violacoes de Pi = {violacoes(inst, tour)}")


if __name__ == "__main__":
    autoteste()
