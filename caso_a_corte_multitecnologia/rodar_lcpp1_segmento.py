"""
rodar_lcpp1_segmento.py  --  nivel de segmento com Pi de fechamento (GTSP de arcos + PCGLNS) nas 282 instancias do LCPP-1, comparado com a heuristica do LCPP HONESTA e com o PCGLNS por peca HONESTO
===================================================================================================================================================================================================
Instancias: `instancias_lcpp1_dados/*.txt` (copia local dos dados do LCPP-1; terceiros: nao redistribuir). Leitor proprio (`instancias_lcpp1.py`) com noding. Para cada instancia: Pi por contencao
(`heuristic_core._detectar_precedencia` sobre os contornos), t_perf = 0 (a convencao do LCPP), 2 rodadas (refinamento da aresta de fechamento), `tempo` = min(120, 20 + arcos/4) s por rodada.
Comparacao (ja calculadas em `auditoria_lcpp1/`): `fo_forte` HONESTA = FO listada + saltos (DP), `fo_pcglns_honesta` = PCGLNS por peca com as pernas da origem; deltas sobre o PCGLNS por peca honesto.
Uso: python rodar_lcpp1_segmento.py rodar [--workers 5] [--rodadas 2] [--instancias a,b]  |  python rodar_lcpp1_segmento.py resumo > RESULTADOS_LCPP1_SEGMENTO.md
"""
import os
import sys
import csv
import json
import glob
import time
import statistics
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
DADOS = os.path.join(AQUI, "instancias_lcpp1_dados")
OUT = os.path.join(AQUI, "lcpp1_segmento_resultados")
AUD = os.path.join(AQUI, "auditoria_lcpp1")


def _job(a):
    nome, rodadas = a
    f = os.path.join(OUT, f"{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    import instancias_lcpp1 as il
    import segmento_gtsp as sg
    import caminho_honesto as ch
    from shapely.geometry import Polygon
    hc = sg.hc
    t0 = time.time()
    segs = il.ler_segmentos(os.path.join(DADOS, f"{nome}.txt"))
    aneis = [a_ for a_ in il.agrupar_contornos(segs) if len(a_) >= 3]
    polys = [Polygon(a_) for a_ in aneis]
    pares = hc._detectar_precedencia(list(polys))
    coords, req, dono = il.requeridas_com_noding(aneis)
    pos = {c: i for i, c in enumerate(coords)}
    aneis_ids = [[pos[(round(x, il.ND), round(y, il.ND))] for x, y in a_ if (round(x, il.ND), round(y, il.ND)) in pos] for a_ in aneis]
    grafo = {"coords": coords, "req": req, "dono": dono, "aneis_ids": aneis_ids}
    fech, melhor, hist = None, None, []
    for r in range(rodadas):
        inst = sg.montar(polys, pares, t_perf=0.0, fechamento=fech, portais="reduzido", grafo=grafo)
        tempo = int(min(120, 20 + inst["E"] / 4))
        tour = sg.resolver(inst, tempo=tempo, semente=r)
        if tour is None:
            hist.append({"rodada": r, "erro": "sem tour"})
            continue
        cam = sg.caminho_do_tour(inst, tour)
        h = ch.fo_honesta(cam, ja_contiguo=True)
        v = ch.verificar(h["caminho"], polys, pares_pi=pares)
        ar = sum(ch._cheb(s.coords[0], s.coords[-1]) for s, t in h["caminho"] if t == "d")
        reg = {"rodada": r, "fo": h["fo"], "ar": ar, "n_perf": h["n_perfuracoes"], "geo_ok": v["geo_ok"], "contiguo": v["contiguo"], "viol_fechamento": v["violacoes_pi_relaxada"], "viol_estrita": v["violacoes_pi_estrita"]}
        hist.append(reg)
        if v["contiguo"] and v["geo_ok"] and v["violacoes_pi_relaxada"] == 0 and (melhor is None or reg["fo"] < melhor["fo"]):
            melhor = reg
        fech = sg.ultima_aresta_por_contorno(inst, tour)
    res = {"instancia": nome, "n_contornos": len(polys), "n_pares_pi": len(pares), "arcos": inst["E"], "arestas": len(req), "melhor": melhor, "historico": hist, "tempo_total_s": time.time() - t0}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(f, "w"))
    return nome, (f"fo={melhor['fo']:.3f}" if melhor else "SEM SOLUCAO VIAVEL") + f" em {res['tempo_total_s']:.0f}s"


def resumo():
    csvf = os.path.join(AUD, "..", "..", "caso_a_corte_multitecnologia", "x")
    ref = {}
    sc = os.path.join(AQUI, "auditoria_lcpp1")
    L = []
    for f in sorted(glob.glob(os.path.join(OUT, "*.json"))):
        r = json.load(open(f))
        n = r["instancia"]
        d = os.path.join(sc, "continuidade_282_dp", f"{n}.json")
        h = os.path.join(sc, "honesta_282", f"{n}.json")
        if not (os.path.exists(d) and os.path.exists(h) and r["melhor"]):
            continue
        d, h = json.load(open(d)), json.load(open(h))
        if "fo_pcglns_honesta" not in h:
            continue
        pg = h["fo_pcglns_honesta"]
        L.append((n, r["n_contornos"], r["n_pares_pi"], r["arcos"], r["melhor"]["fo"], d["forte"]["fo_honesta"], d["forte"]["fo_listada"], pg, r["melhor"]["n_perf"]))
    pct = lambda a, b: 100 * (a / b - 1)
    seg_pg = np.array([pct(x[4], x[7]) for x in L])
    her_pg = np.array([pct(x[5], x[7]) for x in L])
    seg_her = np.array([pct(x[4], x[5]) for x in L])
    print(f"# Nível de segmento (GTSP de arcos + PCGLNS, Π de fechamento, t_perf = 0) nas instâncias do LCPP-1 — {len(L)} instâncias com resultado\n")
    print("Todos os valores são FO **honestas** (caminho contíguo; a heurística com os saltos contados; o PCGLNS por peça com as pernas da origem).\n")
    print("| comparação | mediana | média | vitórias do primeiro |")
    print("|---|---:|---:|---:|")
    print(f"| nosso segmento × PCGLNS por peça | {np.median(seg_pg):+.3f}% | {seg_pg.mean():+.3f}% | {int((seg_pg < 0).sum())}/{len(L)} |")
    print(f"| heurística do LCPP (forte, honesta) × PCGLNS por peça | {np.median(her_pg):+.3f}% | {her_pg.mean():+.3f}% | {int((her_pg < 0).sum())}/{len(L)} |")
    print(f"| **nosso segmento × heurística do LCPP (honesta)** | {np.median(seg_her):+.3f}% | {seg_her.mean():+.3f}% | {int((seg_her < 0).sum())}/{len(L)} |")
    print("\n| instância | contornos | pares Π | arcos | nosso | heurística honesta | PCGLNS peça | nosso×heur | nosso×peça |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for x in sorted(L, key=lambda x: pct(x[4], x[5]))[:25]:
        print(f"| {x[0]} | {x[1]} | {x[2]} | {x[3]} | {x[4]:.2f} | {x[5]:.2f} | {x[7]:.2f} | {pct(x[4], x[5]):+.2f}% | {pct(x[4], x[7]):+.2f}% |")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    arg = lambda f, t, d: t(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "resumo":
        resumo()
        sys.exit(0)
    workers, rodadas = arg("--workers", int, 5), arg("--rodadas", int, 2)
    nomes = arg("--instancias", str, "").split(",") if "--instancias" in sys.argv else sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(DADOS, "*.txt")))
    print(f"[{time.strftime('%H:%M:%S')}] LCPP-1 segmento: {len(nomes)} instancias, {rodadas} rodadas, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, [(n, rodadas) for n in nomes], chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("LCPP1 SEGMENTO CONCLUIDO", flush=True)
