"""
explorar_fendas.py  --  o que sao as entidades de 2 vertices ("fendas") dos DXF do CPPLib? (exploratorio; docs/18 §6 item 5)
==========================================================================================================================
Para cada arquivo .dxf da categoria com precedencia (85) conta as POLYLINE com 2 vertices e as classifica geometricamente em relacao aos contornos fechados da mesma instancia:
  dentro      a fenda esta contida (fechada) num contorno que NAO e furo dela (esta dentro de uma peca ou de um furo), sem cruzar nenhuma fronteira
  cruza       a fenda cruza a fronteira de algum contorno num ponto interior (exigiria noding)
  toca        so toca fronteiras em extremos
  fora        nao toca nenhum contorno e nao esta dentro de nenhum
Tambem compara o comprimento total das fendas com o dos contornos. Nao altera nenhum arquivo do projeto.
Uso: python explorar_fendas.py > RESULTADOS_FENDAS_CPPLIB.md
"""
import os
import sys
import statistics
from pathlib import Path

import ezdxf
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = Path(AQUI) / "instances" / "cpplib" / "Category - All example with precedence constraints"


def ler(fp):
    doc = ezdxf.readfile(str(fp))
    polys, fendas = [], []
    for e in doc.modelspace():
        if e.dxftype() != "POLYLINE":
            continue
        pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        if len(pts) == 2:
            fendas.append(LineString(pts))
        elif len(pts) >= 3:
            try:
                p = Polygon(pts)
                if not p.is_valid:
                    p = p.buffer(0)
                if p.area > 1e-6 and p.geom_type == "Polygon":
                    polys.append(p)
            except Exception:
                pass
    return polys, fendas


def classificar(f, polys, bordas):
    inter = f.intersection(bordas)
    if not inter.is_empty:
        pts = [inter] if inter.geom_type == "Point" else list(getattr(inter, "geoms", [inter]))
        ext = [LineString(f.coords).interpolate(0), LineString(f.coords).interpolate(f.length)]
        so_extremos = all(any(p.distance(x) < 1e-6 for x in ext) for p in pts if p.geom_type == "Point") and all(p.geom_type == "Point" for p in pts)
        return "toca" if so_extremos else "cruza"
    if any(p.covers(f) for p in polys):
        return "dentro"
    return "fora"


def main():
    vistos, arqs = set(), []
    for fp in sorted(list(RAIZ.rglob("*.dxf")) + list(RAIZ.rglob("*.DXF"))):          # o Windows nao distingue maiusculas: sem esta deduplicacao cada arquivo aparece duas vezes
        k = str(fp.resolve()).lower()
        if k not in vistos:
            vistos.add(k)
            arqs.append(fp)
    tot = {"dentro": 0, "cruza": 0, "toca": 0, "fora": 0}
    razoes, n_f, n_p, comp_f = [], [], [], []
    por_arq = []
    for fp in arqs:
        polys, fendas = ler(fp)
        if not fendas:
            por_arq.append((fp.parent.name, len(polys), 0, 0, 0.0))
            continue
        bordas = unary_union([LineString(list(p.exterior.coords)) for p in polys]) if polys else LineString()
        cont = {"dentro": 0, "cruza": 0, "toca": 0, "fora": 0}
        for f in fendas:
            cont[classificar(f, polys, bordas)] += 1
        for k in tot:
            tot[k] += cont[k]
        Lc = sum(p.exterior.length for p in polys)
        Lf = sum(f.length for f in fendas)
        razoes.append(Lf / Lc if Lc > 0 else float("nan"))
        n_f.append(len(fendas))
        n_p.append(len(polys))
        por_arq.append((fp.parent.name, len(polys), len(fendas), cont["cruza"] + cont["toca"], Lf / Lc if Lc > 0 else 0.0))
    n = sum(tot.values())
    print("# Fendas (entidades de 2 vértices) dos DXF do CPPLib — exploratório\n")
    print(f"Arquivos: {len(arqs)}; com fendas: {len(n_f)}; fendas: {n}; contornos fechados: {sum(p for _, p, *_ in por_arq)}.\n")
    print("| classe | fendas | % |\n|---|---:|---:|")
    for k, v in tot.items():
        print(f"| {k} | {v} | {100 * v / n:.1f}% |")
    print(f"\nMediana do nº de fendas por layout: {statistics.median(n_f):.0f} (contornos: {statistics.median(n_p):.0f}); comprimento das fendas ÷ comprimento dos contornos: mediana {statistics.median(razoes):.3f}, máx. {max(razoes):.3f}.")
    print("\n| layout | contornos | fendas | fendas que tocam/cruzam | L fendas / L contornos |\n|---|---:|---:|---:|---:|")
    for nome, p, f, tc, r in por_arq[:15]:
        print(f"| {nome} | {p} | {f} | {tc} | {r:.3f} |")


if __name__ == "__main__":
    main()
