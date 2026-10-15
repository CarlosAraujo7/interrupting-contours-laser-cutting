"""
caminhos_peca_amostra.py  --  GUARDA o CAMINHO do PCGLNS por peca (mesma configuracao da auditoria honesta: 20 s, semente 1) nas instancias da amostra do V3, para avaliar o tempo de voo sob curvas nao lineares (docs/25)
==========================================================================================================================================================================================================
Idem `auditoria_pecas_robustez.py`, mas grava, alem do FO honesto, os segmentos do caminho contiguo origem -> pecas -> origem ([x0, y0, x1, y1, tag]; tag 'c' corte, 'd' deslocamento). Roda numa PASTA TEMPORARIA com a copia do
pipeline do LCPP-1 (src/, pcgtsp_comparison/converter.py, instances/generated/); o LCPP-main nao e alterado nem importado.
Uso (na pasta temporaria): python caminhos_peca_amostra.py <PCGLNS_upstream_dir> <saida> <arquivo_de_nomes> [--workers 8] [--T 20] [--semente 1]
"""
import sys
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
T = arg("--T", int, 20)
SEMENTE = arg("--semente", int, 1)


def _job(nome):
    f = SAIDA / f"{nome}.json"
    if f.exists():
        return nome, "pulado"
    sys.path.insert(0, str(AQUI))
    sys.path.insert(0, str(AQUI / "src"))
    sys.path.insert(0, str(AQUI / "pcgtsp_comparison"))
    import auditar_lcpp1 as au
    import heuristic_core as hc
    from data.load_instances import load_instance
    from converter import convert_instance
    au.PCGLNS_DIR = PCGLNS_DIR
    fp = au.INST / f"{nome}.txt"
    _, layout = load_instance(fp)
    positions = hc.clusterizar_quadtree(hc.resolver_intersecoes(hc.tratar_furos(list(layout))))
    tmp = Path(tempfile.mkdtemp(prefix="pca_"))
    arq, saida = tmp / f"{nome}.pcglns", tmp / "o.tour"
    stats = convert_instance(fp, arq)
    res = au.run_pcglns(arq, saida, T, SEMENTE)
    r = {"instancia": nome, "T": T, "semente": SEMENTE, "cut_time_fixed": stats["cut_time_fixed"]}
    if res is not None:
        cidades = [(k, v) for k, p in enumerate(positions) for v in range(len(list(p.exterior.coords)) - 1)]
        n_dim = int(re.search(r"DIMENSION\s*:\s*(\d+)", open(arq, encoding="latin-1").read()).group(1))
        if n_dim == len(cidades):
            cam = au.caminho_de_tour_pcglns(positions, cidades, res["tour"])
            cl = hc.reclassificar_tags(cam)
            r["fo_pcglns_honesta"] = float(hc.fo_from_path(cam))
            r["caminho"] = [[float(s.coords[0][0]), float(s.coords[0][1]), float(s.coords[-1][0]), float(s.coords[-1][1]), t] for s, t in cl]
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
    return nome, f"FO honesta {r.get('fo_pcglns_honesta')}"


if __name__ == "__main__":
    workers = arg("--workers", int, 8)
    print(f"[{time.strftime('%H:%M:%S')}] caminhos de peca: {len(NOMES)} instancias, T = {T} s, semente {SEMENTE}, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, NOMES, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("CAMINHOS DE PECA CONCLUIDO", flush=True)
