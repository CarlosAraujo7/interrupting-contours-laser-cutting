"""
rodar_v2.py  --  CONJUNTO CONFIRMATORIO V2 (docs/17): categorias do CPPLib NAO usadas antes ("Combined parts" e "No precedence constraints"; 49 arquivos), nivel de PECA x nivel de SEGMENTO
================================================================================================================================================================================
Para cada layout (>= 2 contornos fechados; entidades de 2 vertices [fendas] excluidas como no E-A0, ver `dxf_parser.py`):
  peca_10s  : PCGLNS por peca (Pi estrita por contencao, `ea0_lib.montar_instancia`), T = 30 s, sementes 0-9 -> FO media e tempo de ar (= FO - L_pecas/v_cut, L_pecas = soma dos lados dos contornos)
  peca_ctrl : PCGLNS por peca, 1 execucao com T = orcamento total do metodo de segmento (controle da confusao "mais tempo")
  seg_t<t>  : nivel de segmento (GTSP de arcos + PCGLNS, Pi de FECHAMENTO, noding das arestas compartilhadas), t_perf in {0, 1,0} s, 2 rodadas; FO honesta (caminho contiguo, verificado)
  tsh       : TSH sem Pi (referencia de limite sem precedencia; NAO e solucao viavel)
Como o nivel de peca corta duas vezes uma aresta compartilhada e o de segmento uma so, reporta-se SEPARADO: (i) tempo de AR; (ii) tempo de corte; (iii) tempo total.
Saida: `v2_resultados/v2_<arquivo>.json`. Uso: python rodar_v2.py rodar [--workers 5]  |  python rodar_v2.py resumo > RESULTADOS_V2.md
"""
import os
import re
import sys
import json
import glob
import time
import statistics
import subprocess
import tempfile
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
RAIZ_CPPLIB = os.path.join(AQUI, "instances", "cpplib")
CATEGORIAS = ["Category - Combined parts", "Category - No precedence constraints"]
OUT = os.path.join(AQUI, "v2_resultados")
T_PECA = 30
SEMENTES_PECA = 10
T_SEG = (0.0, 1.0)


def listar_v2():
    arqs = []
    for c in CATEGORIAS:
        arqs += sorted(glob.glob(os.path.join(RAIZ_CPPLIB, c, "**", "*.dxf"), recursive=True) + glob.glob(os.path.join(RAIZ_CPPLIB, c, "**", "*.DXF"), recursive=True))
    nomes = {}
    for f in arqs:
        rel = os.path.relpath(f, RAIZ_CPPLIB).replace(os.sep, "__").replace(" ", "_")
        nomes[rel[:-4]] = f
    return nomes


def _pcglns_peca(polys, inst, tempo, semente):
    import ea0_lib as lib
    from rodar_ea0 import PCGLNS_DIR
    hc = lib.hc
    tmp = tempfile.mkdtemp(prefix="v2_")
    arq, saida = os.path.join(tmp, "x.pcglns"), os.path.join(tmp, "o.tour")
    lib.escrever_pcglns(inst, arq, "x")
    subprocess.run(["julia", "--threads=1,0", "runPCGLNS.jl", arq, "-mode=default", f"-max_time={tempo}", "-verbose=0", f"-output={saida}", f"-seed={semente}"],
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
    v_cut, v_air = hc._DEFAULT_CONFIG["v_cut"], hc._DEFAULT_CONFIG["v_air"]
    return {"fo": lib.fo_do_tour(polys, inst, tour, v_cut, v_air), "violacoes": lib.violacoes(inst, tour)}


def _job(a):
    nome, arq = a
    f = os.path.join(OUT, f"v2_{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    import dxf_parser
    import ea0_lib as lib
    import instancias_lcpp1 as il
    import segmento_gtsp as sg
    import caminho_honesto as ch
    import tsh_segmento as tsh
    hc = lib.hc
    nm, polys, info = dxf_parser.load_instance_dxf(arq)
    r = {"instancia": nome, "arquivo": os.path.relpath(arq, RAIZ_CPPLIB), "n_contornos": len(polys), "info": {k: info.get(k) for k in ("n_dxf_entities", "n_pieces_used", "n_entities_excluded")}}
    if len(polys) < 2:
        r["motivo"] = "menos de 2 contornos"
        json.dump(r, open(f, "w"))
        return nome, "poucos contornos"
    pares = hc._detectar_precedencia(list(polys))
    r["n_pares_pi"] = len(pares)
    v_cut, v_air = hc._DEFAULT_CONFIG["v_cut"], hc._DEFAULT_CONFIG["v_air"]
    L_pecas = float(sum(ch._cheb(a_, b_) for p in polys for a_, b_ in zip(list(p.exterior.coords)[:-1], list(p.exterior.coords)[1:])))
    r["L_pecas"] = L_pecas
    t0 = time.time()
    # segmento
    aneis = [list(p.exterior.coords)[:-1] for p in polys]
    coords, req, dono = il.requeridas_com_noding(aneis)
    pos = {c: i for i, c in enumerate(coords)}
    aneis_ids = [[pos[(round(float(x), il.ND), round(float(y), il.ND))] for x, y in a_ if (round(float(x), il.ND), round(float(y), il.ND)) in pos] for a_ in aneis]
    grafo = {"coords": coords, "req": req, "dono": dono, "aneis_ids": aneis_ids}
    r["L_segmento"] = float(sum(ch._cheb(coords[u], coords[v]) for u, v in req))
    tsh_res = tsh.resolver_tsh(polys)
    r["tsh"] = {"ar": tsh_res["ar_cheb"], "fo": tsh_res["fo"], "n_perf": tsh_res["n_perfuracoes"]}
    orcamento = 0.0
    for t in T_SEG:
        fech, melhor, hist = None, None, []
        for rd in range(2):
            inst = sg.montar(polys, pares, t_perf=t, fechamento=fech, portais="reduzido", grafo=grafo)
            tempo = int(min(120, 20 + inst["E"] / 4))
            t1 = time.time()
            tour = sg.resolver(inst, tempo=tempo, semente=rd)
            orcamento += time.time() - t1
            if tour is None:
                hist.append({"rodada": rd, "erro": "sem tour"})
                continue
            cam = sg.caminho_do_tour(inst, tour)
            h = ch.fo_honesta(cam, t_perf=t, ja_contiguo=True)
            v = ch.verificar(h["caminho"], polys, pares_pi=pares)
            ar = sum(ch._cheb(s.coords[0], s.coords[-1]) for s, tg in h["caminho"] if tg == "d")
            reg = {"rodada": rd, "fo": h["fo"], "ar": ar, "n_perf": h["n_perfuracoes"], "contiguo": v["contiguo"], "geo_ok": v["geo_ok"], "viol_fechamento": v["violacoes_pi_relaxada"], "viol_estrita": v["violacoes_pi_estrita"]}
            hist.append(reg)
            if v["contiguo"] and v["geo_ok"] and v["violacoes_pi_relaxada"] == 0 and (melhor is None or reg["fo"] < melhor["fo"]):
                melhor = reg
            fech = sg.ultima_aresta_por_contorno(inst, tour)
        r[f"seg_t{t:g}"] = {"melhor": melhor, "historico": hist, "arcos": inst["E"]}
    r["orcamento_segmento_s"] = orcamento
    # peca: 10 sementes a 30 s e o controle com o orcamento do segmento (por t)
    inst_p = lib.montar_instancia(polys)
    fos = []
    for s in range(SEMENTES_PECA):
        x = _pcglns_peca(polys, inst_p, T_PECA, s)
        if x:
            fos.append(x["fo"])
    r["peca_10s"] = {"fo_media": statistics.mean(fos) if fos else None, "fo_min": min(fos) if fos else None, "n": len(fos)}
    tc = int(min(600, max(T_PECA, orcamento / len(T_SEG))))
    x = _pcglns_peca(polys, inst_p, tc, 0)
    r["peca_ctrl"] = {"tempo": tc, "fo": x["fo"] if x else None}
    r["tempo_total_s"] = time.time() - t0
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f, "w"))
    return nome, f"contornos={len(polys)} pi={len(pares)} seg0={'ok' if r['seg_t0']['melhor'] else 'SEM'} seg1={'ok' if r['seg_t1']['melhor'] else 'SEM'} em {r['tempo_total_s']:.0f}s"


def resumo():
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "v2_*.json")))]
    R = [r for r in R if r.get("peca_10s")]
    print(f"# Conjunto confirmatório V2 (CPPLib: Combined parts + No precedence constraints) — {len(R)} layouts com ≥ 2 contornos\n")
    ok0 = sum(1 for r in R if r["seg_t0"]["melhor"])
    ok1 = sum(1 for r in R if r["seg_t1"]["melhor"])
    print(f"Soluções de segmento viáveis e verificadas: t = 0: {ok0}/{len(R)}; t = 1 s: {ok1}/{len(R)}.\n")
    import ea0_lib                                          # noqa: F401  (poe src_base no path)
    from heuristic_core import _DEFAULT_CONFIG as D
    hc_vcut, va = D["v_cut"], D["v_air"]
    linhas = []
    for r in R:
        if not (r["seg_t0"]["melhor"] and r["peca_10s"]["fo_media"]):
            continue
        Lp = r["L_pecas"]
        ar_peca = r["peca_10s"]["fo_media"] - Lp / hc_vcut
        ar_seg = r["seg_t0"]["melhor"]["ar"] / va
        fo_seg = r["seg_t0"]["melhor"]["fo"]
        compart = abs(r["L_segmento"] - Lp) > 1e-6 * Lp
        linhas.append((r["instancia"], r["n_contornos"], r["n_pares_pi"], ar_peca, ar_seg, r["peca_10s"]["fo_media"], fo_seg, compart, r))
    if not linhas:
        return
    g_ar = np.array([100 * (x[4] / x[3] - 1) for x in linhas if x[3] > 1e-9])
    g_fo = np.array([100 * (x[6] / x[5] - 1) for x in linhas])
    print(f"**t = 0.** Tempo de ar do segmento sobre o da peça: mediana {np.median(g_ar):+.1f}% (média {g_ar.mean():+.1f}%); tempo total: mediana {np.median(g_fo):+.3f}%; "
          f"segmento menor em {int((g_fo < 0).sum())}/{len(g_fo)} layouts. Layouts com arestas compartilhadas (o corte do segmento é menor): {sum(1 for x in linhas if x[7])}.")
    sem = [x for x in linhas if not x[7] and x[3] > 1e-9]
    if sem:
        g = np.array([100 * (x[4] / x[3] - 1) for x in sem])
        print(f"Sem arestas compartilhadas ({len(sem)} layouts): ar do segmento sobre o da peça: mediana {np.median(g):+.1f}%.")
    ctrl = [(100 * (r["seg_t0"]["melhor"]["fo"] / r["peca_ctrl"]["fo"] - 1)) for _, _, _, _, _, _, _, _, r in linhas if r["peca_ctrl"]["fo"]]
    print(f"Controle (PCGLNS por peça com o mesmo orçamento do segmento): tempo total do segmento sobre o da peça controle: mediana {np.median(ctrl):+.3f}%.\n")
    print("| layout | contornos | pares Π | ar peça | ar segmento | gap ar | FO peça | FO segmento | gap FO | corte compartilhado |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|")
    for x in sorted(linhas, key=lambda x: x[1]):
        print(f"| {x[0][:60]} | {x[1]} | {x[2]} | {x[3]:.2f} | {x[4]:.2f} | {100 * (x[4] / x[3] - 1) if x[3] > 1e-9 else float('nan'):+.1f}% | {x[5]:.2f} | {x[6]:.2f} | {100 * (x[6] / x[5] - 1):+.3f}% | {'sim' if x[7] else ''} |")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    if modo == "resumo":
        resumo()
        sys.exit(0)
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 5
    nomes = listar_v2()
    print(f"[{time.strftime('%H:%M:%S')}] V2: {len(nomes)} arquivos, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, list(nomes.items()), chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("V2 CONCLUIDO", flush=True)
