"""
verificar_continuidade.py  --  O CAMINHO que a heuristica do LCPP devolve e FISICAMENTE CONTIGUO? (auditoria externa; somente leitura do LCPP-main)
==================================================================================================================================================
Pergunta: em `caminho = [(LineString, tag)]`, o fim de cada segmento coincide com o inicio do seguinte? Se nao, os "saltos" entre eles NAO entram na FO (`calcular_fo` soma so os segmentos listados), e a FO
SUBESTIMA o deslocamento em vazio. Este script (copiado, como `auditar_lcpp1.py`, para uma pasta temporaria com `src/`, `pcgtsp_comparison/converter.py` e `instances/generated/` do LCPP-main; o LCPP-main nao
e alterado nem importado por este projeto) roda o pipeline DELES (heuristica original e `busca_local_forte`, 3 s, semente 0) e mede, por instancia:
  - n_saltos e comprimento total dos saltos (Chebyshev, a metrica da FO) entre segmentos consecutivos nao contiguos;
  - FO listada (a que o LCPP-1 reporta) e FO "honesta" = FO listada + (comprimento dos saltos) / v_air  (cada salto como um deslocamento em vazio direto; e um LIMITE INFERIOR do custo real, pois o
    deslocamento real teria de seguir um caminho);
  - o mesmo para o PCGLNS (fo_pcglns do CSV deles, ja contado como ciclo de pecas inteiras, que e contiguo por construcao).
Uso (na pasta temporaria): python verificar_continuidade.py <instancia> [<instancia> ...]
"""
import sys, os, json, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / "src"))
sys.path.insert(0, str(AQUI / "pcgtsp_comparison"))
from data.load_instances import load_instance
import heuristic_core as hc
import busca_local_arvore as bla

INST = AQUI / "instances" / "generated"
CSV = AQUI / "pcgtsp_comparison" / "rerun_frente1_282_FINAL.csv"
V_AIR = 400.0
V_CUT = 100.0 / 6.0


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def saltos(cam):
    """Saltos entre segmentos consecutivos de `cam` (na ORDEM listada), com cada segmento percorrido na orientacao que minimiza o salto TOTAL (programacao dinamica exata sobre as 2 orientacoes
    de cada segmento; a orientacao listada nao e confiavel). A cabeca parte do ponto inicial do 1o segmento (a origem) e deve voltar a ele no fim. Retorna (n_saltos, comprimento Chebyshev total):
    o MENOR deslocamento em vazio que ainda e preciso, alem dos segmentos listados, para executar esses segmentos nessa ordem."""
    n = len(cam)
    ini = [(tuple(s.coords[0]), tuple(s.coords[-1])) for s, _ in cam]
    start = ini[0][0]
    # estado 0 = orientacao listada (a -> b); estado 1 = invertida (b -> a). custo[i][o] = menor salto total ate terminar o segmento i na orientacao o
    INF = float("inf")
    def pontas(i, o):
        a, b = ini[i]
        return (a, b) if o == 0 else (b, a)
    custo = [[INF, INF] for _ in range(n)]
    nsal = [[0, 0] for _ in range(n)]
    for o in (0, 1):
        d = cheb(start, pontas(0, o)[0])
        custo[0][o] = d
        nsal[0][o] = 1 if d > 1e-6 else 0
    for i in range(1, n):
        for o in (0, 1):
            for q in (0, 1):
                d = cheb(pontas(i - 1, q)[1], pontas(i, o)[0])
                c = custo[i - 1][q] + d
                if c < custo[i][o] - 1e-9:
                    custo[i][o] = c
                    nsal[i][o] = nsal[i - 1][q] + (1 if d > 1e-6 else 0)
    melhor, mn = INF, 0
    for o in (0, 1):
        d = cheb(pontas(n - 1, o)[1], start)
        c = custo[n - 1][o] + d
        if c < melhor:
            melhor, mn = c, nsal[n - 1][o] + (1 if d > 1e-6 else 0)
    return mn, melhor


def avaliar(cam):
    cl = hc.reclassificar_tags(cam)
    n, tot = saltos(cl)
    fo = float(hc.calcular_fo(cl))
    return {"fo_listada": fo, "n_saltos": n, "comprimento_saltos": tot, "fo_honesta": fo + tot / V_AIR, "n_seg": len(cl),
            "ar_listado": sum(cheb(s.coords[0], s.coords[1]) for s, t in cl if t == "d"), "corte": sum(cheb(s.coords[0], s.coords[1]) for s, t in cl if t == "c")}


def main(nomes):
    import csv
    ref = {r["instance"]: r for r in csv.DictReader(open(CSV, encoding="utf-8"))}
    saida = {}
    for nome in nomes:
        _, layout = load_instance(INST / f"{nome}.txt")
        cfg = {"root_strategy": "nearest", "child_order": "num_filhos", "mst_strategy": "standard", "vertex_strategy": "nearest", "time_limit": 60.0}
        base = hc.run_heuristic(list(layout), cfg)
        positions = hc.clusterizar_quadtree(hc.resolver_intersecoes(hc.tratar_furos(list(layout))))
        pares = hc._detectar_precedencia(positions)
        G_full = hc._build_full_graph(positions)
        raiz = hc.escolher_raiz_nearest(G_full, positions)
        forte = bla.busca_local_forte(positions, raiz, pares, time_limit=3.0, seed=0)
        r = {"instancia": nome, "n_pares_pi": len(pares), "original": avaliar(base["caminho"]), "forte": avaliar(forte["caminho"])}
        if nome in ref and ref[nome].get("fo_pcglns"):
            r["fo_pcglns_csv"] = float(ref[nome]["fo_pcglns"])
            r["delta_csv_pct"] = float(ref[nome]["delta_pct"]) if "delta_pct" in ref[nome] else None
            r["delta_listada_pct"] = 100 * (r["forte"]["fo_listada"] / r["fo_pcglns_csv"] - 1)
            r["delta_honesta_pct"] = 100 * (r["forte"]["fo_honesta"] / r["fo_pcglns_csv"] - 1)
        saida[nome] = r
        f = r["forte"]
        print(f"{nome}: pi={len(pares)} | forte: FO listada {f['fo_listada']:.2f}, saltos {f['n_saltos']} (comprimento {f['comprimento_saltos']:.0f}), FO honesta {f['fo_honesta']:.2f}"
              + (f" | PCGLNS {r['fo_pcglns_csv']:.2f} | delta listado {r['delta_listada_pct']:+.2f}% -> honesto {r['delta_honesta_pct']:+.2f}%" if 'fo_pcglns_csv' in r else ""), flush=True)
    json.dump(saida, open(AQUI / "continuidade.json", "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
