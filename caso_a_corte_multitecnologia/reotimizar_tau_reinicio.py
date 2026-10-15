"""
reotimizar_tau_reinicio.py  --  o nivel de SEGMENTO reotimizado para tempo de voo nao linear tau(d) E custo de reinicio t > 0 (docs/27)
================================================================================================================================================
Estende `reotimizar_tau.py` (congelado em docs/26; nao e alterado): mesmo GTSP de arcos de `segmento_gtsp.py`, mesma troca da matriz de custos, mas o arco nao contiguo custa tau(d) + t (0 se o corte continua). O nivel de peca nao
depende de t (uma corrida por contorno): o resultado de peca com tau(d) de `tau_resultados/peca_<perfil>_<inst>.json` e reaproveitado, com T_P(t) = T_P(0) + t x corridas. 2 rodadas (a 2a com a aresta de fechamento refinada);
so entra solucao verificada. Saida: `tau_reinicio_resultados/segmento_<perfil>_t<t>_<instancia>.json`.
Uso: python reotimizar_tau_reinicio.py rodar [--workers 8] [--perfis DEWIL16,LASER] [--ts 0.25,1.0]   (idempotente)
"""
import os
import sys
import json
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
OUT = os.path.join(AQUI, "tau_reinicio_resultados")
DADOS = os.path.join(AQUI, "instancias_lcpp1_dados")
ESC = 100000


def job_segmento(nome, perfil, t_av, rodadas=2):
    import segmento_gtsp as sg
    import caminho_honesto as ch
    import analise_voo_nao_linear as vn
    import reotimizar_tau as rt
    hc = sg.hc
    il, aneis, polys = rt._ler(nome)
    t0 = time.time()
    pares = hc._detectar_precedencia(list(polys))
    coords, req, dono = il.requeridas_com_noding(aneis)
    pos = {c: i for i, c in enumerate(coords)}
    aneis_ids = [[pos[(round(x, il.ND), round(y, il.ND))] for x, y in a if (round(x, il.ND), round(y, il.ND)) in pos] for a in aneis]
    grafo = {"coords": coords, "req": req, "dono": dono, "aneis_ids": aneis_ids}
    fech, melhor, hist = None, None, []
    for r in range(rodadas):
        inst = sg.montar(polys, pares, t_perf=0.0, fechamento=fech, portais="reduzido", grafo=grafo)
        A = len(inst["arcos"])
        s, f = [inst["coords"][0]] + [None] * (2 * A), [inst["coords"][0]] + [None] * (2 * A)
        for a, (u, v, _) in enumerate(inst["arcos"]):
            s[1 + 2 * a], f[1 + 2 * a] = inst["coords"][u], inst["coords"][v]
            s[2 + 2 * a], f[2 + 2 * a] = inst["coords"][v], inst["coords"][u]
        S, F = np.array(s, float), np.array(f, float)
        d = np.abs(F[:, None, :] - S[None, :, :]).max(axis=2)
        D = np.rint(np.where(d > 1e-9, vn.tau(d, perfil) + t_av, 0.0) * ESC).astype(np.int64)
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
        c = [[float(g.coords[0][0]), float(g.coords[0][1]), float(g.coords[-1][0]), float(g.coords[-1][1]), tg] for g, tg in h["caminho"]]
        corte, dm, runs = vn.de_caminho(c)
        reg = {"rodada": r, "tempo_pcglns_s": tempo, "corte_s": corte, "n_movimentos": int(len(dm)), "corridas": int(runs), "ok": bool(v["contiguo"] and v["geo_ok"] and v["violacoes_pi_relaxada"] == 0),
               "T": vn.total((corte, dm, runs), perfil, t_av)}
        hist.append(reg)
        if reg["ok"] and (melhor is None or reg["T"] < melhor["T"]):
            melhor = reg
        fech = sg.ultima_aresta_por_contorno(inst, tour)
    return {"nivel": "segmento", "perfil": perfil, "t_av": t_av, "instancia": nome, "n_contornos": len(polys), "arcos": inst["E"], "melhor": melhor, "historico": hist, "tempo_total_s": time.time() - t0}


def _job(a):
    perfil, t_av, nome = a
    f = os.path.join(OUT, f"segmento_{perfil}_t{t_av:g}_{nome}.json")
    if os.path.exists(f):
        return perfil, t_av, nome, "pulado"
    r = job_segmento(nome, perfil, t_av)
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f, "w"))
    m = r["melhor"]
    return perfil, t_av, nome, (f"T={m['T']:.3f}s mov={m['n_movimentos']} corridas={m['corridas']} em {r['tempo_total_s']:.0f}s" if m else "SEM SOLUCAO VIAVEL")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "rodar":
        import rodar_v3 as rv
        workers = arg("--workers", int, 8)
        perfis = arg("--perfis", str, "DEWIL16,LASER").split(",")
        ts = [float(x) for x in arg("--ts", str, "0.25,1.0").split(",")]
        tarefas = [(p, t, n) for p in perfis for t in ts for n in rv.amostra()]
        print(f"[{time.strftime('%H:%M:%S')}] segmento com tau(d) + t: {len(tarefas)} tarefas ({perfis} x t {ts} x 60 instancias), {workers} processos", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for p, t, n, msg in ex.map(_job, tarefas, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {p} t={t:g} {n}: {msg}", flush=True)
        print("TAU+REINICIO CONCLUIDO", flush=True)
