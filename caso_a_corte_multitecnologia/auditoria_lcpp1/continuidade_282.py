"""
continuidade_282.py  --  verificar_continuidade.py em TODAS as 282 instancias do CSV do LCPP-1 (pasta temporaria com a copia do pipeline deles), em paralelo
=========================================================================================================================================================
Para cada instancia: heuristica original e `busca_local_forte` (3 s, semente 0) -> FO listada, saltos entre segmentos consecutivos (orientacao que minimiza o salto: LIMITE INFERIOR), FO "honesta" = listada + saltos/v_air;
compara com o fo_pcglns do CSV (ciclo de pecas inteiras, contiguo por construcao). Grava `continuidade_282/<instancia>.json` e imprime o resumo.
Uso (na pasta temporaria com src/, pcgtsp_comparison/ e instances/generated/): python continuidade_282.py rodar [--workers 5]  |  python continuidade_282.py resumo
"""
import sys, os, json, csv, time, statistics
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

AQUI = Path(__file__).resolve().parent
OUT = AQUI / "continuidade_282_dp"
CSV = AQUI / "pcgtsp_comparison" / "rerun_frente1_282_FINAL.csv"


def _job(nome):
    f = OUT / f"{nome}.json"
    if f.exists():
        return nome, "pulado"
    sys.path.insert(0, str(AQUI))
    import verificar_continuidade as vc
    from data.load_instances import load_instance
    hc, bla = vc.hc, vc.bla
    t0 = time.time()
    _, layout = load_instance(vc.INST / f"{nome}.txt")
    cfg = {"root_strategy": "nearest", "child_order": "num_filhos", "mst_strategy": "standard", "vertex_strategy": "nearest", "time_limit": 60.0}
    base = hc.run_heuristic(list(layout), cfg)
    positions = hc.clusterizar_quadtree(hc.resolver_intersecoes(hc.tratar_furos(list(layout))))
    pares = hc._detectar_precedencia(positions)
    G_full = hc._build_full_graph(positions)
    raiz = hc.escolher_raiz_nearest(G_full, positions)
    forte = bla.busca_local_forte(positions, raiz, pares, time_limit=3.0, seed=0)
    r = {"instancia": nome, "n_pares_pi": len(pares), "original": vc.avaliar(base["caminho"]), "forte": vc.avaliar(forte["caminho"]), "tempo_s": time.time() - t0}
    OUT.mkdir(exist_ok=True)
    json.dump(r, open(f, "w"))
    return nome, f"forte: listada {r['forte']['fo_listada']:.2f}, honesta {r['forte']['fo_honesta']:.2f}"


def resumo():
    ref = {r["instance"]: r for r in csv.DictReader(open(CSV, encoding="utf-8"))}
    linhas = []
    for f in sorted(OUT.glob("*.json")):
        r = json.load(open(f))
        n = r["instancia"]
        if n not in ref or not ref[n].get("fo_pcglns"):
            continue
        pg = float(ref[n]["fo_pcglns"])
        fl, fh = r["forte"]["fo_listada"], r["forte"]["fo_honesta"]
        linhas.append((n, ref[n].get("categoria") or ref[n].get("category") or ref[n].get("instance_type") or "", pg, fl, fh, r["forte"]["n_saltos"], r["forte"]["comprimento_saltos"],
                       100 * (fl / pg - 1), 100 * (fh / pg - 1), float(ref[n]["fo_forte"]), 100 * (float(ref[n]["fo_forte"]) / pg - 1)))
    dl = [x[7] for x in linhas]
    dh = [x[8] for x in linhas]
    dcsv = [x[10] for x in linhas]
    print(f"instancias: {len(linhas)}")
    print(f"delta do CSV (fo_forte deles / fo_pcglns - 1): mediana {statistics.median(dcsv):+.3f}%, media {statistics.mean(dcsv):+.3f}%, vitorias {sum(1 for x in dcsv if x < 0)}/{len(dcsv)}")
    print(f"delta recomputado (FO listada): mediana {statistics.median(dl):+.3f}%, media {statistics.mean(dl):+.3f}%, vitorias {sum(1 for x in dl if x < 0)}/{len(dl)}")
    print(f"delta com SALTOS contados (limite inferior do custo real): mediana {statistics.median(dh):+.3f}%, media {statistics.mean(dh):+.3f}%, vitorias {sum(1 for x in dh if x < 0)}/{len(dh)}")
    perda = [h - l for l, h in zip(dl, dh)]
    print(f"correcao (pontos percentuais): mediana {statistics.median(perda):+.3f}, max {max(perda):+.3f}; saltos por instancia: mediana {statistics.median(x[5] for x in linhas):.0f}")
    pior = sorted(linhas, key=lambda x: -(x[8] - x[7]))[:5]
    print("maiores correcoes:", [(x[0], round(x[7], 2), round(x[8], 2)) for x in pior])


if __name__ == "__main__":
    if sys.argv[1:2] == ["resumo"]:
        resumo()
        sys.exit(0)
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 5
    nomes = [r["instance"] for r in csv.DictReader(open(CSV, encoding="utf-8"))]
    print(f"[{time.strftime('%H:%M:%S')}] {len(nomes)} instancias, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, nomes, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("CONTINUIDADE CONCLUIDA", flush=True)
