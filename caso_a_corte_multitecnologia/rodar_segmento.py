"""
rodar_segmento.py  --  nivel de SEGMENTO com Pi de fechamento e perfuracao, via GTSP de arestas orientadas + PCGLNS (`segmento_gtsp.py`), nas layouts do CPPLib
====================================================================================================================================================
Para cada (layout, t_perf): `rodadas` rodadas (a 1a com a aresta de fechamento padrao, as seguintes com a ULTIMA aresta de cada contorno da solucao anterior -- refinamento monotono em viabilidade);
guarda a melhor FO honesta (sobre o caminho contiguo, com t_perf por perfuracao) e as verificacoes (`caminho_honesto.verificar`). `tempo` por solucao = min(120, 20 + arcos/4) s; arcos com portais REDUZIDOS (cadeias entre pontos de ramificacao, pontas do TSH, extremos e pares vizinhos).
Saida: `segmento_resultados/seg_<inst>_t<t>.json`.  Comparacao: nivel de peca = PCGLNS do E-A0 (media de 10 sementes, T = 30 s) + t_perf x nº de contornos.
Uso: python rodar_segmento.py rodar --t 0 [--workers 5] [--rodadas 2] [--instancias a,b,c]   |   python rodar_segmento.py resumo --t 0 > RESULTADOS_SEGMENTO_t0.md
"""
import os
import sys
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
OUT = os.path.join(AQUI, "segmento_resultados")
EA0 = os.path.join(AQUI, "ea0_resultados")


def _job(a):
    nome, t_perf, rodadas = a
    f = os.path.join(OUT, f"seg_{nome}_t{t_perf:g}.json")
    if os.path.exists(f):
        return nome, "pulado"
    import rodar_ea0 as ea0
    import ea0_lib as lib
    import segmento_gtsp as sg
    import caminho_honesto as ch
    hc = lib.hc
    polys = ea0._carregar(nome)
    pares = hc._detectar_precedencia(list(polys))
    t0 = time.time()
    fech, melhor = None, None
    hist = []
    for r in range(rodadas):
        inst = sg.montar(polys, pares, t_perf=t_perf, fechamento=fech, portais="reduzido")
        tempo = int(min(120, 20 + inst["E"] / 4))
        tour = sg.resolver(inst, tempo=tempo, semente=r)
        if tour is None:
            hist.append({"rodada": r, "erro": "sem tour"})
            continue
        cam = sg.caminho_do_tour(inst, tour)
        h = ch.fo_honesta(cam, t_perf=t_perf, ja_contiguo=True)
        v = ch.verificar(h["caminho"], polys, pares_pi=pares)
        ar = sum(ch._cheb(s.coords[0], s.coords[-1]) for s, t in h["caminho"] if t == "d")
        reg = {"rodada": r, "fo": h["fo"], "ar": ar, "n_perf": h["n_perfuracoes"], "ok": v["ok"], "viol_fechamento": v["violacoes_pi_relaxada"], "viol_estrita": v["violacoes_pi_estrita"], "tempo_pcglns_s": tempo}
        hist.append(reg)
        if v["ok"] and v["violacoes_pi_relaxada"] == 0 and (melhor is None or reg["fo"] < melhor["fo"]):
            melhor = reg
        fech = sg.ultima_aresta_por_contorno(inst, tour)
    res = {"instancia": nome, "t_perf": t_perf, "n_pecas": len(polys), "n_pares_pi": len(pares), "E": inst["E"], "portais": "reduzido", "melhor": melhor, "historico": hist, "tempo_total_s": time.time() - t0}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(f, "w"))
    return nome, (f"fo={melhor['fo']:.3f} ar={melhor['ar']:.0f} perf={melhor['n_perf']}" if melhor else "SEM SOLUCAO VIAVEL") + f" em {res['tempo_total_s']:.0f}s"


def _media_fo(nome, metodo="pcglns", tempo=30):
    v = []
    for f in glob.glob(os.path.join(EA0, f"ea0_{nome}_{metodo}_T{tempo}_s*.json")):
        d = json.load(open(f))
        if d.get("fo") is not None:
            v.append(d["fo"])
    return statistics.mean(v) if v else None


def resumo(t_perf):
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, f"seg_*_t{t_perf:g}.json")))]
    ar_dir = {os.path.basename(f)[3:-5]: json.load(open(f)) for f in glob.glob(os.path.join(AQUI, "ar_resultados", "ar_*.json"))}
    tp = {os.path.basename(f)[6:-5]: json.load(open(f)) for f in glob.glob(os.path.join(AQUI, "tshpi_resultados", "tshpi_*.json"))}
    print(f"# Nível de segmento (GTSP de arestas + PCGLNS), Π de fechamento, t_perf = {t_perf:g} s — {len(R)} layouts\n")
    ok = [r for r in R if r["melhor"]]
    print(f"Com solução viável verificada (contígua, cobertura, fechamento sem violações): {len(ok)}/{len(R)}.\n")
    L = []
    for r in ok:
        n = r["instancia"]
        a = ar_dir.get(n)
        pg = _media_fo(n)
        if a is None or pg is None:
            continue
        vc, va = a["L_pecas"] / a["v_cut"], a["v_air"]
        fo_peca = pg + t_perf * r["n_pecas"]
        ar_peca = (pg - vc)
        ar_seg = r["melhor"]["ar"] / va
        L.append((n, r["n_pecas"], r["E"], r["melhor"]["fo"], fo_peca, 100 * (r["melhor"]["fo"] / fo_peca - 1), 100 * (ar_seg / ar_peca - 1), r["melhor"]["n_perf"], tp.get(n)))
    if not L:
        return
    g_fo = np.array([x[5] for x in L])
    g_ar = np.array([x[6] for x in L])
    print(f"Gap do tempo TOTAL (FO com t_perf) do nível de segmento sobre o de peça (PCGLNS do E-A0 + t x nº de contornos): mediana {np.median(g_fo):+.3f}%, média {g_fo.mean():+.3f}%; "
          f"menor em {int((g_fo < 0).sum())}/{len(L)} layouts.")
    print(f"Gap do tempo de AR sobre o de peça: mediana {np.median(g_ar):+.1f}%, média {g_ar.mean():+.1f}%.")
    print(f"Perfurações do nível de segmento (mediana): {statistics.median(x[7] for x in L):.0f} contra {statistics.median(x[1] for x in L):.0f} contornos.\n")
    print("| layout | contornos | arestas | FO segmento | FO peça (+t·n) | gap FO | gap ar | perfurações | ar TSH-Π |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for x in sorted(L, key=lambda x: x[2]):
        t_ = x[8]
        tpi = f"{t_['ar_cheb']:.0f}" if t_ and t_.get("resolvida") else "—"
        print(f"| {x[0]} | {x[1]} | {x[2]} | {x[3]:.2f} | {x[4]:.2f} | {x[5]:+.3f}% | {x[6]:+.1f}% | {x[7]} | {tpi} |")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    arg = lambda f, t, d: t(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    t_perf = arg("--t", float, 0.0)
    if modo == "resumo":
        resumo(t_perf)
        sys.exit(0)
    import rodar_ea0 as ea0
    workers, rodadas = arg("--workers", int, 5), arg("--rodadas", int, 2)
    nomes = arg("--instancias", str, "").split(",") if "--instancias" in sys.argv else [n for n in sorted(ea0.listar()) if len(ea0._carregar(n)) >= 2]
    print(f"[{time.strftime('%H:%M:%S')}] segmento GTSP: {len(nomes)} layouts, t_perf = {t_perf:g}, {rodadas} rodadas, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, [(n, t_perf, rodadas) for n in nomes], chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("SEGMENTO CONCLUIDO", flush=True)
