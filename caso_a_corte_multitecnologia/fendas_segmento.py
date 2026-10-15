"""
fendas_segmento.py  --  as FENDAS ABERTAS (entidades de 2 vertices) dos DXF do CPPLib incluidas no modelo de segmento e no de peca (docs/28; exploratorio)
===================================================================================================================================================
Ate aqui as 4.702 fendas (~50% das entidades) foram EXCLUIDAS (`dxf_parser.py`). Aqui entram como segmentos requeridos:
  * cada fenda e dividida nas intersecoes com as fronteiras dos contornos; cada PEDACO e um segmento requerido (os que coincidem com uma fronteira sao descartados: ja sao requeridos);
  * a PRECEDENCIA de um pedaco: ele deve ser cortado antes de o contorno que o contem FECHAR (o menor poligono que contem o ponto medio; o mesmo criterio de fechamento dos contornos internos); pedacos fora de todo poligono nao tem restricao;
  * nivel de SEGMENTO: o mesmo GTSP de arcos de `segmento_gtsp.py` (congelado; nao alterado) sobre o grafo com *noding* (`instancias_lcpp1.requeridas_com_noding`, cada pedaco como um "anel" de 2 pontos), Pi de fechamento = contornos + pedacos->dono;
  * nivel de PECA: PCGLNS sobre o GTSP de pecas de `ea0_lib` mais, para cada pedaco, um grupo de 2 cidades (as duas direcoes: entra numa ponta e sai na outra), Pi estrita pedaco -> dono;
  * verificador PROPRIO sobre o grafo com noding: caminho contiguo, parte e volta da origem, cada aresta requerida cortada exatamente uma vez, nenhum corte fora das arestas, e Pi de fechamento (a ultima aresta de cada
    anel -- contorno ou pedaco -- antes da ultima do dono).
Tempo de voo LINEAR (a convencao do LCPP), como no V2. Saida: `fendas_resultados/<nivel>_<layout>[_t<t>].json`.
Uso: python fendas_segmento.py rodar [--workers 8] [--ts 0,1.0] [--layouts a,b]   (padrao: as 14 layouts do CPPLib com ate 130 vertices)
"""
import os
import sys
import json
import time
import shutil
import tempfile
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
OUT = os.path.join(AQUI, "fendas_resultados")
VC, VA = 100.0 / 6.0, 400.0


def _cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def ler_fendas(arq):
    import ezdxf
    out = []
    for e in ezdxf.readfile(arq).modelspace():
        if e.dxftype() != "POLYLINE":
            continue
        pts = [(float(v.dxf.location.x), float(v.dxf.location.y)) for v in e.vertices]
        if len(pts) == 2:
            out.append((pts[0], pts[1]))
    return out


def preparar(nome):
    import rodar_ea0 as ea0
    import instancias_lcpp1 as il
    import segmento_gtsp as sg
    from shapely.geometry import LineString, Point
    from shapely.ops import unary_union, split
    hc = sg.hc
    polys = ea0._carregar(nome)
    fendas = ler_fendas(ea0.listar()[nome])
    bound = unary_union([LineString(list(p.exterior.coords)) for p in polys])
    pedacos, dono_poly = [], []
    for a, b in fendas:
        L = LineString([a, b])
        try:
            partes = list(split(L, bound).geoms)
        except Exception:
            partes = [L]
        for q in partes:
            c = list(q.coords)
            for u, v in zip(c[:-1], c[1:]):
                if _cheb(u, v) <= 1e-9:
                    continue
                mid = Point((u[0] + v[0]) / 2, (u[1] + v[1]) / 2)
                if bound.distance(mid) < 1e-6:
                    continue                                   # coincide com uma fronteira: ja e requerido
                cand = [(p.area, k) for k, p in enumerate(polys) if p.buffer(1e-7).covers(mid)]
                pedacos.append((tuple(u), tuple(v)))
                dono_poly.append(min(cand)[1] if cand else None)
    n = len(polys)
    aneis = [[(float(x), float(y)) for x, y in list(p.exterior.coords)[:-1]] for p in polys]
    aneis_all = aneis + [[a, b] for a, b in pedacos]
    coords, req, dono = il.requeridas_com_noding(aneis_all)
    pos = {c: i for i, c in enumerate(coords)}
    aneis_ids = [[pos[(round(x, il.ND), round(y, il.ND))] for x, y in a_ if (round(x, il.ND), round(y, il.ND)) in pos] for a_ in aneis_all]
    pares_poly = hc._detectar_precedencia(list(polys))
    pares = list(pares_poly) + [(n + j, o) for j, o in enumerate(dono_poly) if o is not None]
    grafo = {"coords": coords, "req": req, "dono": dono, "aneis_ids": aneis_ids}
    return {"nome": nome, "polys": polys, "pedacos": pedacos, "dono_poly": dono_poly, "pares_poly": pares_poly, "pares": pares, "grafo": grafo, "n_fendas": len(fendas)}


def verificar(cam, P):
    """Verificador sobre o grafo com noding. -> dict(ok, ...)."""
    import instancias_lcpp1 as il
    g = P["grafo"]
    ND = il.ND
    pos = {(round(x, ND), round(y, ND)): i for i, (x, y) in enumerate(g["coords"])}
    idx = {(min(u, v), max(u, v)): e for e, (u, v) in enumerate(g["req"])}
    cortes, fora, contiguo, prev = {}, 0, True, None
    for p, (s, tg) in enumerate(cam):
        a, b = s.coords[0], s.coords[-1]
        if prev is not None and _cheb(prev, a) > 1e-6:
            contiguo = False
        prev = b
        if tg == "c":
            ka, kb = pos.get((round(a[0], ND), round(a[1], ND))), pos.get((round(b[0], ND), round(b[1], ND)))
            e = idx.get((min(ka, kb), max(ka, kb))) if ka is not None and kb is not None else None
            if e is None:
                fora += 1
            else:
                cortes.setdefault(e, []).append(p)
    nao = sum(1 for e in range(len(g["req"])) if e not in cortes)
    dup = sum(1 for e in cortes if len(cortes[e]) > 1)
    ultimo = {}
    for e, cs in g["dono"].items():
        if e in cortes:
            for c in cs:
                ultimo[c] = max(ultimo.get(c, -1), max(cortes[e]))
    viol = sum(1 for i, o in P["pares"] if i in ultimo and o in ultimo and ultimo[i] > ultimo[o])
    origem = _cheb(cam[0][0].coords[0], (0.0, 0.0)) < 1e-6 and _cheb(cam[-1][0].coords[-1], (0.0, 0.0)) < 1e-6
    return {"contiguo": contiguo, "origem": origem, "nao_cortadas": nao, "duplicadas": dup, "fora": fora, "violacoes_fechamento": viol, "ok": bool(contiguo and origem and nao == 0 and dup == 0 and fora == 0 and viol == 0)}


def medidas(cam):
    corte = sum(_cheb(s.coords[0], s.coords[-1]) for s, t in cam if t == "c") / VC
    ar = sum(_cheb(s.coords[0], s.coords[-1]) for s, t in cam if t == "d") / VA
    runs, ant = 0, None
    for s, t in cam:
        if t == "c" and ant != "c":
            runs += 1
        ant = t
    return {"corte_s": corte, "ar_s": ar, "corridas": runs, "n_movimentos": sum(1 for s, t in cam if t == "d" and _cheb(s.coords[0], s.coords[-1]) > 1e-7)}


def job_segmento(nome, t_av, rodadas=2):
    import segmento_gtsp as sg
    t0 = time.time()
    P = preparar(nome)
    fech, melhor, hist = None, None, []
    for r in range(rodadas):
        inst = sg.montar(P["polys"], P["pares"], t_perf=t_av, fechamento=fech, portais="reduzido", grafo=P["grafo"])
        tempo = int(min(120, 20 + inst["E"] / 4))
        tour = sg.resolver(inst, tempo=tempo, semente=r)
        if tour is None:
            hist.append({"rodada": r, "erro": "sem tour"})
            continue
        cam = sg.caminho_do_tour(inst, tour)
        v = verificar(cam, P)
        m = medidas(cam)
        reg = {"rodada": r, "tempo_pcglns_s": tempo, **m, "fo": m["corte_s"] + m["ar_s"] + t_av * m["corridas"], "verif": v}
        hist.append(reg)
        if v["ok"] and (melhor is None or reg["fo"] < melhor["fo"]):
            melhor = reg
        fech = sg.ultima_aresta_por_contorno(inst, tour)
    return {"nivel": "segmento", "instancia": nome, "t_av": t_av, "n_contornos": len(P["polys"]), "n_pedacos": len(P["pedacos"]), "n_fendas": P["n_fendas"], "arcos": inst["E"], "n_pares_fenda": len(P["pares"]) - len(P["pares_poly"]),
            "melhor": melhor, "historico": hist, "tempo_total_s": time.time() - t0}


def job_peca(nome, tempo=30):
    import ea0_lib as lib
    import reotimizar_tau as rt
    from shapely.geometry import LineString
    t0 = time.time()
    P = preparar(nome)
    polys, ped = P["polys"], P["pedacos"]
    inst = lib.montar_instancia(polys)
    cid = list(inst["cidades"])                         # (x, y, grupo, peca, vertice)
    saida = [(c[0], c[1]) for c in cid]
    n = len(polys)
    for j, (a, b) in enumerate(ped):
        g = n + 2 + j
        cid.append((a[0], a[1], g, -2 - j, 0))
        saida.append(b)
        cid.append((b[0], b[1], g, -2 - j, 1))
        saida.append(a)
    ex = np.array(saida, float)
    en = np.array([[c[0], c[1]] for c in cid], float)
    D = np.rint(np.abs(ex[:, None, :] - en[None, :, :]).max(axis=2) * lib.ESCALA).astype(np.int64)
    grupo = np.array([c[2] for c in cid])
    D[grupo[:, None] == grupo[None, :]] = 0
    pares = [(i + 2, o + 2) for i, o in P["pares"]]
    for pred, suc in pares:
        D[np.ix_(grupo == suc, grupo == pred)] = -1
    inst2 = {"cidades": cid, "D": D, "pares": pares, "n_grupos": n + 1 + len(ped)}
    tmp = tempfile.mkdtemp(prefix="fp_")
    try:
        arq, sai = os.path.join(tmp, "i.pcglns"), os.path.join(tmp, "o.tour")
        lib.escrever_pcglns(inst2, arq, nome)
        tour = rt._resolver_arquivo(arq, sai, tempo, 1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    r = {"nivel": "peca", "instancia": nome, "n_contornos": n, "n_pedacos": len(ped), "tempo_pcglns_s": tempo}
    if tour is None:
        r["erro"] = "sem tour"
    else:
        cam, pos = [], (0.0, 0.0)
        for cidx in tour:
            x, y, g, k, v = cid[cidx - 1]
            if k == -1:
                continue
            if (x, y) != pos:
                cam.append((LineString([pos, (x, y)]), "d"))
            if k >= 0:
                ring = list(polys[k].exterior.coords)[:-1]
                m = len(ring)
                seq = [ring[(v + t) % m] for t in range(m + 1)]
                for a, b in zip(seq[:-1], seq[1:]):
                    if a != b:
                        cam.append((LineString([a, b]), "c"))
                pos = (x, y)
            else:
                fim = saida[cidx - 1]
                cam.append((LineString([(x, y), fim]), "c"))
                pos = fim
        if pos != (0.0, 0.0):
            cam.append((LineString([pos, (0.0, 0.0)]), "d"))
        viol = sum(1 for pr, sc in pares if pr in {cid[c - 1][2]: 0 for c in tour} and False)
        ordem_g = {}
        for t_, cidx in enumerate(tour):
            ordem_g[cid[cidx - 1][2]] = t_
        viol = sum(1 for pr, sc in pares if pr in ordem_g and sc in ordem_g and ordem_g[pr] > ordem_g[sc])
        r.update(medidas(cam))
        r["corridas"] = n + len(ped)                    # uma corrida por contorno e por pedaco (nivel de peca)
        r["violacoes_pi"] = int(viol)
        r["fo"] = r["corte_s"] + r["ar_s"]
    r["tempo_total_s"] = time.time() - t0
    return r


def _job(a):
    nivel, nome, t_av = a
    f = os.path.join(OUT, f"{nivel}_{nome}" + (f"_t{t_av:g}" if nivel == "segmento" else "") + ".json")
    if os.path.exists(f):
        return nivel, nome, t_av, "pulado"
    r = job_segmento(nome, t_av) if nivel == "segmento" else job_peca(nome)
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f, "w"))
    if nivel == "segmento":
        m = r["melhor"]
        return nivel, nome, t_av, (f"fo={m['fo']:.2f} ar={m['ar_s']:.2f}s corridas={m['corridas']} ({r['n_fendas']} fendas, {r['n_pedacos']} pedacos) em {r['tempo_total_s']:.0f}s" if m else "SEM SOLUCAO VERIFICADA")
    return nivel, nome, t_av, (f"fo={r['fo']:.2f} ar={r['ar_s']:.2f}s viol={r['violacoes_pi']} em {r['tempo_total_s']:.0f}s" if "fo" in r else "ERRO")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "rodar":
        workers = arg("--workers", int, 8)
        ts = [float(x) for x in arg("--ts", str, "0,1.0").split(",")]
        if "--layouts" in sys.argv:
            nomes = arg("--layouts", str, "").split(",")
        else:
            V = json.load(open(os.path.join(AQUI, "cpplib_vertices.json")))
            nomes = [n for v, n in V if v <= 130]
        tarefas = [("segmento", n, t) for t in ts for n in nomes] + [("peca", n, 0.0) for n in nomes]
        print(f"[{time.strftime('%H:%M:%S')}] fendas: {len(nomes)} layouts x t {ts} (segmento) + peca = {len(tarefas)} tarefas, {workers} processos", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for nivel, n, t, msg in ex.map(_job, tarefas, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {nivel} {n} t={t:g}: {msg}", flush=True)
        print("FENDAS CONCLUIDO", flush=True)
