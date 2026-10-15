"""
auditoria_honesta_282.py  --  PCGLNS (pipeline do LCPP-1) reavaliado como CAMINHO CONTIGUO origem -> pecas -> origem, nas 282 instancias, para comparar com a heuristica contando os saltos
==================================================================================================================================================================================
O `fo_pcglns` do CSV do LCPP-1 e `(custo do ciclo)/v_air + corte` SEM as pernas da origem; a FO da heuristica e a soma dos segmentos LISTADOS (caminho NAO contiguo: ver `verificar_continuidade.py`).
Aqui os DOIS lados sao contados sobre caminhos fisicamente executaveis: PCGLNS -> tour de pecas -> caminho `origem -> entrada -> contorno inteiro -> ... -> origem` (mesma conversao de `auditar_lcpp1.py`);
heuristica -> FO listada + MENOR deslocamento em vazio para executar os segmentos listados na ordem listada (`verificar_continuidade.saltos`, DP exata sobre a orientacao de cada segmento).
Roda na pasta temporaria (copia do pipeline: src/, pcgtsp_comparison/converter.py, instances/generated/). PCGLNS: `-max_time=20`, semente 1, Julia 1.12 `--threads=1,0` (como na auditoria de 17 instancias).
Uso: python auditoria_honesta_282.py <PCGLNS_upstream_dir> rodar [--workers 4]  |  python auditoria_honesta_282.py resumo
"""
import sys, os, re, json, csv, time, statistics, subprocess, tempfile
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

AQUI = Path(__file__).resolve().parent
OUT = AQUI / "honesta_282"
OUT_DP = AQUI / "continuidade_282_dp"
CSV = AQUI / "pcgtsp_comparison" / "rerun_frente1_282_FINAL.csv"
PCGLNS_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else None
PCGLNS_T = 20


def _job(nome):
    f = OUT / f"{nome}.json"
    if f.exists():
        return nome, "pulado"
    sys.path.insert(0, str(AQUI))
    sys.path.insert(0, str(AQUI / "src"))
    sys.path.insert(0, str(AQUI / "pcgtsp_comparison"))
    import auditar_lcpp1 as au
    import heuristic_core as hc
    from data.load_instances import load_instance
    from converter import convert_instance, SCALE
    au.PCGLNS_DIR = PCGLNS_DIR
    fp = au.INST / f"{nome}.txt"
    _, layout = load_instance(fp)
    positions = hc.clusterizar_quadtree(hc.resolver_intersecoes(hc.tratar_furos(list(layout))))
    tmp = Path(tempfile.mkdtemp(prefix="hon_"))
    arq, saida = tmp / f"{nome}.pcglns", tmp / "o.tour"
    stats = convert_instance(fp, arq)
    res = au.run_pcglns(arq, saida, PCGLNS_T)
    r = {"instancia": nome, "cut_time_fixed": stats["cut_time_fixed"]}
    if res is not None:
        cidades = [(k, v) for k, p in enumerate(positions) for v in range(len(list(p.exterior.coords)) - 1)]
        n_dim = int(re.search(r"DIMENSION\s*:\s*(\d+)", open(arq, encoding="latin-1").read()).group(1))
        r["n_cidades_pcglns"], r["n_cidades_posicoes"] = n_dim, len(cidades)
        r["fo_pcglns_formula_deles"] = (res["custo"] / SCALE) / hc._V_AIR + stats["cut_time_fixed"]
        if n_dim == len(cidades):
            cam = au.caminho_de_tour_pcglns(positions, cidades, res["tour"])
            r["fo_pcglns_honesta"] = float(hc.fo_from_path(cam))
    for x in tmp.iterdir():
        try:
            x.unlink()
        except OSError:
            pass
    try:
        tmp.rmdir()
    except OSError:
        pass
    OUT.mkdir(exist_ok=True)
    json.dump(r, open(f, "w"))
    return nome, f"pcglns honesta {r.get('fo_pcglns_honesta')}"


def resumo():
    ref = {r["instance"]: r for r in csv.DictReader(open(CSV, encoding="utf-8"))}
    L = []
    for f in sorted(OUT.glob("*.json")):
        h = json.load(open(f))
        n = h["instancia"]
        g = OUT_DP / f"{n}.json"
        if "fo_pcglns_honesta" not in h or not g.exists():
            continue
        d = json.load(open(g))
        L.append((n, float(ref[n]["fo_forte"]), float(ref[n]["fo_pcglns"]), d["forte"]["fo_listada"], d["forte"]["fo_honesta"], h["fo_pcglns_honesta"], d["forte"]["n_saltos"]))
    pct = lambda a, b: 100 * (a / b - 1)
    c_csv = [pct(x[1], x[2]) for x in L]                    # como no LCPP-1
    c_lis = [pct(x[3], x[5]) for x in L]                    # heuristica listada x PCGLNS com pernas da origem
    c_hon = [pct(x[4], x[5]) for x in L]                    # AMBOS honestos
    print(f"instancias: {len(L)}")
    for nome, v in (("LCPP-1 (CSV: forte listada x PCGLNS sem pernas da origem)", c_csv), ("heuristica LISTADA x PCGLNS COM pernas da origem", c_lis), ("AMBOS HONESTOS (heuristica com saltos x PCGLNS com pernas)", c_hon)):
        print(f"{nome}: mediana {statistics.median(v):+.3f}%, media {statistics.mean(v):+.3f}%, vitorias da heuristica {sum(1 for x in v if x < 0)}/{len(v)}")
    pior = sorted(L, key=lambda x: -(pct(x[4], x[5])))[:6]
    print("instancias em que a heuristica perde mais (honesto):", [(x[0], round(pct(x[4], x[5]), 2)) for x in pior])


if __name__ == "__main__":
    if "resumo" in sys.argv:
        resumo()
        sys.exit(0)
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    nomes = [r["instance"] for r in csv.DictReader(open(CSV, encoding="utf-8"))]
    print(f"[{time.strftime('%H:%M:%S')}] PCGLNS honesto: {len(nomes)} instancias, {workers} processos, T = {PCGLNS_T} s", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, nomes, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("HONESTA CONCLUIDA", flush=True)
