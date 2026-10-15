"""
caminhos_heuristica_282.py  --  GUARDA os caminhos que a heuristica do LCPP (original e `busca_local_forte`, 3 s, semente 0) devolve nas 282 instancias, para reavaliacao posterior sob QUALQUER convencao
=========================================================================================================================================================================================================
Motivo (docs/18): a FO do LCPP-1 (Eq. 3) e o custo dos deslocamentos entre servicos consecutivos com a metrica de Chebyshev ponderada (Eq. 2); como ela e uma metrica, o deslocamento DIRETO e sempre o mais barato,
mas o codigo emite trajetos poligonais (percorre segmentos ja cortados) e nao conta os saltos entre segmentos nao contiguos. Para medir as tres convencoes (FO listada, FO honesta poligonal, FO formal por cordas)
e para variar t_perf SEM reexecutar a heuristica, guardamos o caminho. Este script e o mesmo pipeline de `continuidade_282.py` (somente leitura do LCPP-main; roda numa PASTA TEMPORARIA com a copia de `src/`,
`pcgtsp_comparison/` e `instances/generated/`; o LCPP-main nao e alterado nem importado por este projeto). Cada segmento e gravado como [x0, y0, x1, y1, tag] apos `reclassificar_tags`.
Uso (na pasta temporaria): python caminhos_heuristica_282.py rodar <pasta_de_saida> [--workers 2]
"""
import sys
import os
import json
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / "src"))
sys.path.insert(0, str(AQUI / "pcgtsp_comparison"))
INST = AQUI / "instances" / "generated"


def _serializar(hc, cam):
    cl = hc.reclassificar_tags(cam)
    return [[float(s.coords[0][0]), float(s.coords[0][1]), float(s.coords[-1][0]), float(s.coords[-1][1]), t] for s, t in cl]


def _job(a):
    nome, saida = a
    f = Path(saida) / f"{nome}.json"
    if f.exists():
        return nome, "pulado"
    from data.load_instances import load_instance
    import heuristic_core as hc
    import busca_local_arvore as bla
    t0 = time.time()
    _, layout = load_instance(INST / f"{nome}.txt")
    cfg = {"root_strategy": "nearest", "child_order": "num_filhos", "mst_strategy": "standard", "vertex_strategy": "nearest", "time_limit": 60.0}
    base = hc.run_heuristic(list(layout), cfg)
    positions = hc.clusterizar_quadtree(hc.resolver_intersecoes(hc.tratar_furos(list(layout))))
    pares = hc._detectar_precedencia(positions)
    G_full = hc._build_full_graph(positions)
    raiz = hc.escolher_raiz_nearest(G_full, positions)
    forte = bla.busca_local_forte(positions, raiz, pares, time_limit=3.0, seed=0)
    r = {"instancia": nome, "n_pares_pi": len(pares), "fo_listada_original": float(hc.calcular_fo(hc.reclassificar_tags(base["caminho"]))),
         "fo_listada_forte": float(hc.calcular_fo(hc.reclassificar_tags(forte["caminho"]))), "original": _serializar(hc, base["caminho"]), "forte": _serializar(hc, forte["caminho"]), "tempo_s": time.time() - t0}
    Path(saida).mkdir(parents=True, exist_ok=True)
    json.dump(r, open(f, "w"))
    return nome, f"listada forte {r['fo_listada_forte']:.2f} ({r['tempo_s']:.1f}s)"


if __name__ == "__main__":
    saida = sys.argv[2]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 2
    nomes = sorted(p.stem for p in INST.glob("*.txt"))
    print(f"[{time.strftime('%H:%M:%S')}] {len(nomes)} instancias, {workers} processos -> {saida}", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, [(n, saida) for n in nomes], chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("CAMINHOS CONCLUIDO", flush=True)
