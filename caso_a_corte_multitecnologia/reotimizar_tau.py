"""
reotimizar_tau.py  --  os DOIS NIVEIS reotimizados para um tempo de voo NAO LINEAR tau(d) (docs/26; analogo, no nivel de segmento, do E-A1 do P1)
=================================================================================================================================================
Nivel de PECA: PCGLNS sobre o GTSP de pecas inteiras (`ea0_lib.montar_instancia`: origem = cidade 1, ciclo fechado, Pi estrita) com a matriz de custos tau(d) entre cidades (d = Chebyshev entre o ponto de saida e o de entrada;
cada contorno e cortado inteiro, entrando e saindo no mesmo vertice) -- o mesmo modelo de `rodar_ea1.py`.
Nivel de SEGMENTO: o GTSP de arcos orientados de `segmento_gtsp.py` (congelado; nao e alterado): `montar(...)` constroi arcos, grupos e ordem de Pi de fechamento; aqui so a MATRIZ DE CUSTOS e substituida por
tau(d) (0 se o corte continua, tau(d) entre fim de um arco e inicio do seguinte senao; t_av = 0). 2 rodadas (a 2a com a ultima aresta de cada contorno como aresta de fechamento), como no V3; so entra solucao verificada.
Curvas: LASER (trapezoidal v = 1667 mm/s, a = 10000 mm/s^2) e DEWIL16 (lida, de forma aproximada, da Fig. 3 de Dewil et al. 2016); 1 unidade = 1 mm (nao confirmado). O perfil LIN (400 u/s) roda so no nivel de peca (validacao
contra o caminho de peca guardado). Tempo total = corte/v_corte (sobre o caminho) + soma tau(d) dos movimentos em vazio (inclui as pernas de/para a origem).
Saida: `tau_resultados/<nivel>_<perfil>_<instancia>.json`.
Uso: python reotimizar_tau.py rodar [--workers 8] [--perfis LASER,DEWIL16] [--tempo-peca 30]   (idempotente)
"""
import os
import re
import sys
import json
import time
import shutil
import tempfile
import subprocess
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
OUT = os.path.join(AQUI, "tau_resultados")
DADOS = os.path.join(AQUI, "instancias_lcpp1_dados")
PCGLNS_DIR = os.path.join(os.path.dirname(AQUI), "ferramentas", "PCGLNS_upstream")
ESC = 100000


def _tau():
    import analise_voo_nao_linear as vn
    return vn


def _resolver_arquivo(arq, saida, tempo, semente):
    subprocess.run(["julia", "--threads=1,0", "runPCGLNS.jl", arq, "-mode=default", f"-max_time={tempo}", "-verbose=0", f"-output={saida}", f"-seed={semente}"],
                   cwd=PCGLNS_DIR, capture_output=True, text=True, errors="replace")
    txt = open(saida, encoding="latin-1").read() if os.path.exists(saida) else ""
    m = re.search(r"Tour\s*:\s*\[([^\]]+)\]", txt)
    if not m:
        return None
    tour = [int(x) for x in m.group(1).split(",")]
    if tour[0] != 1:
        k = tour.index(1)
        tour = tour[k:] + tour[:k]
    return tour


def _ler(nome):
    import instancias_lcpp1 as il
    from shapely.geometry import Polygon
    segs = il.ler_segmentos(os.path.join(DADOS, f"{nome}.txt"))
    aneis = [a for a in il.agrupar_contornos(segs) if len(a) >= 3]
    return il, aneis, [Polygon(a) for a in aneis]


def job_peca(nome, perfil, tempo):
    import ea0_lib as lib
    vn = _tau()
    il, aneis, polys = _ler(nome)
    t0 = time.time()
    inst = lib.montar_instancia(polys)
    xy = np.array([[c[0], c[1]] for c in inst["cidades"]], float)
    dist = np.abs(xy[:, None, :] - xy[None, :, :]).max(axis=2)
    D = np.rint(vn.tau(dist, perfil) * ESC).astype(np.int64)
    grupo = np.array([c[2] for c in inst["cidades"]])
    D[grupo[:, None] == grupo[None, :]] = 0
    D[inst["D"] == -1] = -1
    inst2 = dict(inst)
    inst2["D"] = D
    tmp = tempfile.mkdtemp(prefix="tp_")
    try:
        arq, saida = os.path.join(tmp, "i.pcglns"), os.path.join(tmp, "o.tour")
        lib.escrever_pcglns(inst2, arq, nome)
        tour = _resolver_arquivo(arq, saida, tempo, 1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    r = {"nivel": "peca", "perfil": perfil, "instancia": nome, "tempo_pcglns_s": tempo, "n_pecas": len(polys)}
    if tour is None:
        r["erro"] = "sem tour"
    else:
        cam = lib.caminho_de_tour(polys, inst, tour)
        c = [[float(s.coords[0][0]), float(s.coords[0][1]), float(s.coords[-1][0]), float(s.coords[-1][1]), t] for s, t in cam]
        corte, d, runs = vn.de_caminho(c)
        r.update({"violacoes_pi": int(lib.violacoes(inst, tour)), "corte_s": corte, "n_movimentos": int(len(d)), "corridas": int(runs),
                  "T": {p: vn.total((corte, d, runs), p, 0.0) for p in ("LIN", "LASER", "DEWIL16")}})
    r["tempo_total_s"] = time.time() - t0
    return r


def job_segmento(nome, perfil, rodadas=2):
    import segmento_gtsp as sg
    import caminho_honesto as ch
    vn = _tau()
    hc = sg.hc
    il, aneis, polys = _ler(nome)
    t0 = time.time()
    pares = hc._detectar_precedencia(list(polys))
    coords, req, dono = il.requeridas_com_noding(aneis)
    pos = {c: i for i, c in enumerate(coords)}
    aneis_ids = [[pos[(round(x, il.ND), round(y, il.ND))] for x, y in a if (round(x, il.ND), round(y, il.ND)) in pos] for a in aneis]
    grafo = {"coords": coords, "req": req, "dono": dono, "aneis_ids": aneis_ids}
    fech, melhor, hist = None, None, []
    for r in range(rodadas):
        inst = sg.montar(polys, pares, t_perf=0.0, fechamento=fech, portais="reduzido", grafo=grafo)
        # substitui SO a matriz de custos por tau(d) (a ordem de Pi, os grupos e os arcos sao os do metodo congelado)
        A = len(inst["arcos"])
        s, f = [inst["coords"][0]] + [None] * (2 * A), [inst["coords"][0]] + [None] * (2 * A)
        for a, (u, v, _) in enumerate(inst["arcos"]):
            s[1 + 2 * a], f[1 + 2 * a] = inst["coords"][u], inst["coords"][v]
            s[2 + 2 * a], f[2 + 2 * a] = inst["coords"][v], inst["coords"][u]
        S, F = np.array(s, float), np.array(f, float)
        d = np.abs(F[:, None, :] - S[None, :, :]).max(axis=2)
        D = np.rint(np.where(d > 1e-9, vn.tau(d, perfil), 0.0) * ESC).astype(np.int64)
        D[inst["grupo"][:, None] == inst["grupo"][None, :]] = 0
        inst["D"] = D
        tempo = int(min(120, 20 + inst["E"] / 4))
        tour = sg.resolver(inst, tempo=tempo, semente=r)
        if tour is None:
            hist.append({"rodada": r, "erro": "sem tour"})
            continue
        cam = sg.caminho_do_tour(inst, tour)
        h = ch.fo_honesta(cam, ja_contiguo=True)
        v = ch.verificar(h["caminho"], polys, pares_pi=pares)
        c = [[float(sg_.coords[0][0]), float(sg_.coords[0][1]), float(sg_.coords[-1][0]), float(sg_.coords[-1][1]), tg] for sg_, tg in h["caminho"]]
        corte, dm, runs = vn.de_caminho(c)
        reg = {"rodada": r, "tempo_pcglns_s": tempo, "corte_s": corte, "n_movimentos": int(len(dm)), "corridas": int(runs), "ok": bool(v["contiguo"] and v["geo_ok"] and v["violacoes_pi_relaxada"] == 0),
               "T": {p: vn.total((corte, dm, runs), p, 0.0) for p in ("LIN", "LASER", "DEWIL16")}}
        hist.append(reg)
        if reg["ok"] and (melhor is None or reg["T"][perfil] < melhor["T"][perfil]):
            melhor = reg
        fech = sg.ultima_aresta_por_contorno(inst, tour)
    return {"nivel": "segmento", "perfil": perfil, "instancia": nome, "n_contornos": len(polys), "n_pares_pi": len(pares), "arcos": inst["E"], "melhor": melhor, "historico": hist, "tempo_total_s": time.time() - t0}


def _job(a):
    nivel, perfil, nome, tempo_peca = a
    f = os.path.join(OUT, f"{nivel}_{perfil}_{nome}.json")
    if os.path.exists(f):
        return nivel, perfil, nome, "pulado"
    r = job_peca(nome, perfil, tempo_peca) if nivel == "peca" else job_segmento(nome, perfil)
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f, "w"))
    if nivel == "peca":
        return nivel, perfil, nome, (f"T={r['T'][perfil]:.3f}s mov={r.get('n_movimentos')} em {r['tempo_total_s']:.0f}s" if "T" in r else "ERRO")
    m = r["melhor"]
    return nivel, perfil, nome, (f"T={m['T'][perfil]:.3f}s mov={m['n_movimentos']} em {r['tempo_total_s']:.0f}s" if m else "SEM SOLUCAO VIAVEL")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "rodar":
        import rodar_v3 as rv
        workers, tempo_peca = arg("--workers", int, 8), arg("--tempo-peca", int, 30)
        perfis = arg("--perfis", str, "LASER,DEWIL16").split(",")
        nomes = arg("--instancias", str, "").split(",") if "--instancias" in sys.argv else rv.amostra()
        tarefas = [("segmento", p, n, tempo_peca) for p in perfis for n in nomes] + [("peca", p, n, tempo_peca) for p in perfis + ["LIN"] for n in nomes]
        print(f"[{time.strftime('%H:%M:%S')}] reotimizacao com tau(d): {len(nomes)} instancias, perfis {perfis} (+ LIN so no nivel de peca) = {len(tarefas)} tarefas, {workers} processos", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for nivel, p, n, msg in ex.map(_job, tarefas, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {nivel} {p} {n}: {msg}", flush=True)
        print("REOTIMIZACAO TAU CONCLUIDA", flush=True)
