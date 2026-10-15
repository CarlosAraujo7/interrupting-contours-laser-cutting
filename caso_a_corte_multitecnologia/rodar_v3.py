"""
rodar_v3.py  --  V3 (pre-registrado em docs/19): GTSP de arcos CIENTE do custo de reinicio t > 0 nas instancias do LCPP-1 (amostra estratificada), comparado com a heuristica do LCPP (cega a t) e com o PCGLNS por peca
=====================================================================================================================================================================================================
Reutiliza o metodo congelado de `rodar_lcpp1_segmento.py` (leitor proprio com noding, Pi de fechamento por contencao, 2 rodadas, `tempo` = min(120, 20 + arcos/4) s por rodada) com t_perf = t, e GUARDA o caminho
da melhor solucao (para contar corridas que recomecam em vertice ja cortado x vertice virgem, e para auditorias posteriores).
Amostra: `amostra()` -- semente 2027, estratificada por categoria (regular 12, irregular 12, hole 12, esicup 24 = 60).
Uso: python rodar_v3.py listar | rodar [--workers 3] [--ts 0.25,1.0] [--rodadas 2] | resumo
"""
import os
import sys
import json
import glob
import time
import random
import warnings
from concurrent.futures import ProcessPoolExecutor

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
DADOS = os.path.join(AQUI, "instancias_lcpp1_dados")
OUT = os.path.join(AQUI, "v3_resultados")
COTAS = {"regular": 12, "irregular": 12, "hole": 12, "esicup": 24}


def categoria(n):
    for c in ("regular", "irregular", "hole"):
        if f"_{c}_" in n:
            return c
    return "esicup"


def amostra():
    nomes = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(DADOS, "*.txt")))
    rng = random.Random(2027)
    out = []
    for cat, cota in COTAS.items():
        pool = [n for n in nomes if categoria(n) == cat]
        out += sorted(rng.sample(pool, min(cota, len(pool))))
    return out


def _job(a):
    nome, t, rodadas = a
    f = os.path.join(OUT, f"{nome}__t{t}.json")
    if os.path.exists(f):
        return nome, t, "pulado"
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
        inst = sg.montar(polys, pares, t_perf=t, fechamento=fech, portais="reduzido", grafo=grafo)
        tempo = int(min(120, 20 + inst["E"] / 4))
        tour = sg.resolver(inst, tempo=tempo, semente=r)
        if tour is None:
            hist.append({"rodada": r, "erro": "sem tour"})
            continue
        cam = sg.caminho_do_tour(inst, tour)
        h = ch.fo_honesta(cam, ja_contiguo=True, t_perf=t)
        v = ch.verificar(h["caminho"], polys, pares_pi=pares)
        ar = sum(ch._cheb(s.coords[0], s.coords[-1]) for s, tg in h["caminho"] if tg == "d")
        # corridas que comecam em vertice JA CORTADO (retomada) x virgem (docs/18 §4.2)
        k = lambda p: (round(p[0], 6), round(p[1], 6))
        tocados, ant, virg, ret = set(), None, 0, 0
        for s, tg in h["caminho"]:
            if tg == "c":
                if ant != "c":
                    if k(s.coords[0]) in tocados:
                        ret += 1
                    else:
                        virg += 1
                tocados.add(k(s.coords[0]))
                tocados.add(k(s.coords[-1]))
            ant = tg
        reg = {"rodada": r, "fo": h["fo"], "ar": ar, "n_perf": h["n_perfuracoes"], "virgens": virg, "retomadas": ret, "geo_ok": v["geo_ok"], "contiguo": v["contiguo"],
               "viol_fechamento": v["violacoes_pi_relaxada"], "viol_estrita": v["violacoes_pi_estrita"],
               "caminho": [[float(s.coords[0][0]), float(s.coords[0][1]), float(s.coords[-1][0]), float(s.coords[-1][1]), tg] for s, tg in h["caminho"]]}
        hist.append(reg)
        if v["contiguo"] and v["geo_ok"] and v["violacoes_pi_relaxada"] == 0 and (melhor is None or reg["fo"] < melhor["fo"]):
            melhor = reg
        fech = sg.ultima_aresta_por_contorno(inst, tour)
    res = {"instancia": nome, "t_perf": t, "n_contornos": len(polys), "n_pares_pi": len(pares), "arcos": inst["E"], "melhor": melhor,
           "historico": [{k_: v_ for k_, v_ in x.items() if k_ != "caminho"} for x in hist], "tempo_total_s": time.time() - t0}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(f, "w"))
    return nome, t, (f"fo={melhor['fo']:.3f} R={melhor['n_perf']} (virg {melhor['virgens']}, ret {melhor['retomadas']})" if melhor else "SEM SOLUCAO VIAVEL") + f" em {res['tempo_total_s']:.0f}s"


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "listar"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "listar":
        A = amostra()
        print(len(A), "instancias:", ", ".join(A))
        sys.exit(0)
    if modo == "rodar":
        workers, rodadas = arg("--workers", int, 3), arg("--rodadas", int, 2)
        ts = [float(x) for x in arg("--ts", str, "0.25,1.0").split(",")]
        tarefas = [(n, t, rodadas) for n in amostra() for t in ts]
        print(f"[{time.strftime('%H:%M:%S')}] V3: {len(tarefas)} tarefas, {workers} processos", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for n, t, msg in ex.map(_job, tarefas, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {n} t={t}: {msg}", flush=True)
        print("V3 CONCLUIDO", flush=True)
