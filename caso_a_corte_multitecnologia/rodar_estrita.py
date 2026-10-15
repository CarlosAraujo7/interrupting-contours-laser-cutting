"""
rodar_estrita.py  --  SENSIBILIDADE a semantica de Pi no nivel de segmento: ESTRITA (todo trecho do contorno interno antes de QUALQUER trecho do externo) x FECHAMENTO (o externo so fecha depois dos internos; docs/18, docs/21)
===========================================================================================================================================================================================================
Mesmo metodo do nivel de segmento (`rodar_segmento.py`: GTSP de arcos orientados + PCGLNS, portais reduzidos, `tempo` = min(120, 20 + arcos/4) s por rodada), trocando SO a ordem entre grupos: para cada par (i interno, o externo) de Pi,
todo arco de i precede todo arco de o (em vez de todo arco de i preceder o arco de fechamento c(o)). `segmento_gtsp.py` NAO e alterado (congelado em docs/17); a ordem estrita e montada aqui sobre `inst["arestas_do_contorno"]`.
2 rodadas com sementes 0 e 1 (a estrita nao tem aresta de fechamento a refinar); so entra solucao verificada (`caminho_honesto.verificar`: contigua, cobertura, ZERO violacoes de Pi estrita).
Layouts: `lista_varredura_t.txt` (30 layouts de menos de 200 arcos). t_perf em {0, 1,0}. As solucoes de FECHAMENTO para comparar ja existem em `segmento_resultados/seg_<inst>_t<t>.json` (mesmos parametros).
Saida: `estrita_resultados/est_<inst>_t<t>.json`.
Uso: python rodar_estrita.py rodar [--workers 3] [--ts 0,1] [--rodadas 2] [--instancias a,b]
"""
import os
import sys
import json
import time
import warnings
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
OUT = os.path.join(AQUI, "estrita_resultados")


def lista():
    return open(os.path.join(AQUI, "lista_varredura_t.txt"), encoding="utf-8").read().strip().split(",")


def ordem_estrita(inst, pares):
    """todo arco do contorno interno i precede todo arco do contorno externo o (grupos 2 + arco)."""
    ordem = defaultdict(set)
    ad = inst["arestas_do_contorno"]
    for i, o in pares:
        for a in ad[i]:
            for b in ad[o]:
                if a != b:
                    ordem[2 + a].add(2 + b)
    return ordem


def _job(a):
    nome, t_perf, rodadas = a
    f = os.path.join(OUT, f"est_{nome}_t{t_perf:g}.json")
    if os.path.exists(f):
        return nome, t_perf, "pulado"
    import rodar_ea0 as ea0
    import ea0_lib as lib
    import segmento_gtsp as sg
    import caminho_honesto as ch
    hc = lib.hc
    polys = ea0._carregar(nome)
    pares = hc._detectar_precedencia(list(polys))
    t0 = time.time()
    melhor, hist = None, []
    for r in range(rodadas):
        inst = sg.montar(polys, pares, t_perf=t_perf, fechamento=None, portais="reduzido")
        inst["ordem"] = ordem_estrita(inst, pares)
        tempo = int(min(120, 20 + inst["E"] / 4))
        tour = sg.resolver(inst, tempo=tempo, semente=r)
        if tour is None:
            hist.append({"rodada": r, "erro": "sem tour"})
            continue
        cam = sg.caminho_do_tour(inst, tour)
        h = ch.fo_honesta(cam, t_perf=t_perf, ja_contiguo=True)
        v = ch.verificar(h["caminho"], polys, pares_pi=pares)
        ar = sum(ch._cheb(s.coords[0], s.coords[-1]) for s, tg in h["caminho"] if tg == "d")
        reg = {"rodada": r, "fo": h["fo"], "ar": ar, "n_perf": h["n_perfuracoes"], "ok": v["ok"], "viol_fechamento": v["violacoes_pi_relaxada"], "viol_estrita": v["violacoes_pi_estrita"], "tempo_pcglns_s": tempo}
        hist.append(reg)
        if v["ok"] and v["violacoes_pi_estrita"] == 0 and (melhor is None or reg["fo"] < melhor["fo"]):
            melhor = reg
    res = {"instancia": nome, "t_perf": t_perf, "n_pecas": len(polys), "n_pares_pi": len(pares), "E": inst["E"], "n_restricoes": sum(len(v) for v in inst["ordem"].values()), "melhor": melhor, "historico": hist,
           "tempo_total_s": time.time() - t0}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(f, "w"))
    return nome, t_perf, (f"fo={melhor['fo']:.3f} ar={melhor['ar']:.0f} perf={melhor['n_perf']}" if melhor else "SEM SOLUCAO VIAVEL (estrita)") + f" em {res['tempo_total_s']:.0f}s"


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "rodar":
        workers, rodadas = arg("--workers", int, 3), arg("--rodadas", int, 2)
        ts = [float(x) for x in arg("--ts", str, "0,1").split(",")]
        nomes = arg("--instancias", str, "").split(",") if "--instancias" in sys.argv else lista()
        tarefas = [(n, t, rodadas) for n in nomes for t in ts]
        print(f"[{time.strftime('%H:%M:%S')}] estrita: {len(nomes)} layouts x t em {ts}, {rodadas} rodadas, {workers} processos", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for n, t, msg in ex.map(_job, tarefas, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {n} t={t:g}: {msg}", flush=True)
        print("ESTRITA CONCLUIDA", flush=True)
