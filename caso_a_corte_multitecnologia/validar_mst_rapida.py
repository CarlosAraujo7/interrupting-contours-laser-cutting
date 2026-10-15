"""
validar_mst_rapida.py  --  a versao rapida (`src_base/quadtree_rapido.py`) devolve EXATAMENTE o mesmo grafo que a original (`quadtree.py`)?
==========================================================================================================================================
Para cada instancia real do CPPLib com precedencia (e para alguns layouts ladrilhados `nome@k`), roda as duas rotinas de construcao do grafo MST
entre pecas e compara: lista de nos, lista de ARESTAS NA ORDEM (u, v, weight, connection normalizado), e o grafo completo. Tambem mede o tempo.
Saida: `RESULTADOS_VALIDACAO_MST_RAPIDA.md`.
Uso:  python validar_mst_rapida.py [--so-reais] [--limite N] > RESULTADOS_VALIDACAO_MST_RAPIDA.md
"""
import os, sys, time, warnings

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
import rodar_ea0 as ea0
import quadtree as qt
import quadtree_rapido as qr
import heuristic_core as hc


def norm(c):
    return tuple(tuple(float(x) for x in p) for p in c)


def assinatura(g):
    return (list(g.nodes()), [(u, v, float(d["weight"]), norm(d["connection"])) for u, v, d in g.edges(data=True)])


def main():
    lim = int(sys.argv[sys.argv.index("--limite") + 1]) if "--limite" in sys.argv else 0
    nomes = [n for n in sorted(ea0.listar())]
    if lim:
        nomes = nomes[:lim]
    extra = [] if "--so-reais" in sys.argv else ["p1xk_1@3", "p3xk_4@4"]
    print("# Validacao da MST rapida (`quadtree_rapido`) contra a original (`quadtree`)\n")
    print("Igualdade EXATA da lista de nos e da lista de arestas (ordem, pesos, coordenadas de `connection`). Tempos de uma execucao, maquina compartilhada.\n")
    print("| instancia | pecas | iguais | t original (s) | t rapida (s) | aceleracao |")
    print("|---|---:|:--:|---:|---:|---:|")
    n_ok, n_tot = 0, 0
    for n in nomes + extra:
        polys = ea0._carregar(n)
        if len(polys) < 2:
            continue
        pos = hc.clusterizar_quadtree(list(polys))          # mesma entrada que a heuristica usa
        t0 = time.time()
        g0 = qt.optimize_cluster_connections_kdtree_vertices_with_full_connectivity(pos, plot=False)
        t1 = time.time()
        g1 = qr.optimize_cluster_connections_kdtree_vertices_rapido(pos, plot=False)
        t2 = time.time()
        ok = assinatura(g0) == assinatura(g1)
        n_ok += int(ok)
        n_tot += 1
        print(f"| {n} | {len(pos)} | {'sim' if ok else '**NAO**'} | {t1 - t0:.2f} | {t2 - t1:.2f} | {(t1 - t0) / max(t2 - t1, 1e-9):.1f}x |", flush=True)
    print(f"\n**{n_ok} de {n_tot} instancias com grafo identico.**")


if __name__ == "__main__":
    main()
