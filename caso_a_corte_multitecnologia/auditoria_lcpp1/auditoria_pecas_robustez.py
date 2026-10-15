"""
auditoria_pecas_robustez.py  --  ROBUSTEZ da referencia de nivel de peca (PCGLNS por peca do pipeline do LCPP-1): mais sementes e mais tempo que na auditoria honesta (docs/24)
=====================================================================================================================================================================
A auditoria honesta (`auditoria_honesta_282.py`) usou PCGLNS com 1 semente e 20 s por instancia. Aqui, nas instancias da amostra do V3, roda 3 sementes x 60 s e grava o FO honesto (caminho contiguo, pernas da origem)
de cada uma, para ver se a referencia de peca estava subotima. Roda numa PASTA TEMPORARIA com a copia do pipeline (src/, pcgtsp_comparison/converter.py, instances/generated/); o LCPP-main nao e alterado nem importado.
Uso (na pasta temporaria): python auditoria_pecas_robustez.py <PCGLNS_upstream_dir> <saida> <arquivo_de_nomes> [--workers 8] [--T 60] [--sementes 1,2,3]
"""
import sys
import os
import re
import json
import time
import tempfile
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

AQUI = Path(__file__).resolve().parent
PCGLNS_DIR = Path(sys.argv[1])
SAIDA = Path(sys.argv[2])
NOMES = [x for x in open(sys.argv[3], encoding="utf-8").read().strip().split(",") if x]
arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
T = arg("--T", int, 60)
SEMENTES = [int(x) for x in arg("--sementes", str, "1,2,3").split(",")]


def _job(a):
    nome, semente = a
    f = SAIDA / f"{nome}__s{semente}.json"
    if f.exists():
        return nome, semente, "pulado"
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
    tmp = Path(tempfile.mkdtemp(prefix="rob_"))
    arq, saida = tmp / f"{nome}.pcglns", tmp / "o.tour"
    stats = convert_instance(fp, arq)
    res = au.run_pcglns(arq, saida, T, semente)
    r = {"instancia": nome, "semente": semente, "T": T, "cut_time_fixed": stats["cut_time_fixed"]}
    if res is not None:
        cidades = [(k, v) for k, p in enumerate(positions) for v in range(len(list(p.exterior.coords)) - 1)]
        n_dim = int(re.search(r"DIMENSION\s*:\s*(\d+)", open(arq, encoding="latin-1").read()).group(1))
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
    SAIDA.mkdir(parents=True, exist_ok=True)
    json.dump(r, open(f, "w"))
    return nome, semente, f"FO honesta {r.get('fo_pcglns_honesta')}"


if __name__ == "__main__":
    workers = arg("--workers", int, 8)
    tarefas = [(n, s) for s in SEMENTES for n in NOMES]
    print(f"[{time.strftime('%H:%M:%S')}] PCGLNS por peca (robustez): {len(NOMES)} instancias x sementes {SEMENTES} x T = {T} s = {len(tarefas)} tarefas, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, s, msg in ex.map(_job, tarefas, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n} s={s}: {msg}", flush=True)
    print("ROBUSTEZ CONCLUIDA", flush=True)
