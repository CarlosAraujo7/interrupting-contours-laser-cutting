"""
auditar_lcpp1.py  --  AUDITORIA (externa, somente leitura do LCPP-main) do resultado central do LCPP-1: "heuristica forte vs. PCGLNS, 282/282 vitorias".
Roda o pipeline DELES (copiado para esta pasta temporaria: src/, converter.py) numa amostra de instancias e confere, instancia a instancia:
  (R) REPRODUCAO: fo_forte e fo_pcglns recalculados vs. os do `rerun_frente1_282_FINAL.csv` (mesma metodologia: forte 3 s semente 0; PCGLNS max_time=20, Julia 1.12 + `--threads=1,0`).
  (E) ESTRUTURA do caminho da heuristica: nº de corridas de corte por peca, segmentos 'c' fora das arestas de pecas, perna de/para a origem.
  (D) DEFINICOES: o PCGLNS minimiza um CICLO entre contornos (inclui o arco de fechamento, NAO inclui as pernas da origem); a FO da heuristica e um caminho
      a partir da origem. Reavalia os DOIS pela mesma funcao (`calcular_fo`) sobre o mesmo tipo de caminho (origem -> pecas -> origem) e compara.
Saida: JSON por instancia em ./auditoria/.
"""
import sys, os, re, json, time, csv, subprocess, tempfile, statistics
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / "src"))
sys.path.insert(0, str(AQUI / "pcgtsp_comparison"))
from data.load_instances import load_instance
import heuristic_core as hc
import busca_local_arvore as bla
from converter import convert_instance, SCALE
from shapely.geometry import LineString, Point

PCGLNS_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else None
INST = AQUI / "instances" / "generated"
CSV = AQUI / "pcgtsp_comparison" / "rerun_frente1_282_FINAL.csv"
OUT = AQUI / "auditoria"
TB_FORTE, PCGLNS_T = 3.0, 20


def n_perf(cam_classificado):
    """Numero de perfuracoes = corridas contiguas maximais de segmentos de corte ('c')."""
    n, ant = 0, None
    for seg, tag in cam_classificado:
        if tag == "c" and ant != "c":
            n += 1
        ant = tag
    return n


def fo_t(cam_classificado, t):
    """FO do LCPP + t por perfuracao (a FO original do LCPP-main nao tem tempo de perfuracao; = t=0)."""
    return float(hc.calcular_fo(cam_classificado)) + t * n_perf(cam_classificado)


def detect_pi(positions):
    return hc._detectar_precedencia(positions)


def run_pcglns(arq, saida, t, semente=1):
    p = subprocess.run(["julia", "--threads=1,0", "runPCGLNS.jl", str(arq), "-mode=default", f"-max_time={t}", "-verbose=0",
                        f"-output={saida}", f"-seed={semente}"], cwd=str(PCGLNS_DIR), capture_output=True, text=True, errors="replace")
    txt = open(saida, encoding="latin-1").read() if os.path.exists(saida) else ""
    mc = re.search(r"Tour Cost\s*:\s*([\-\d.]+)", txt)
    mt = re.search(r"Tour\s*:\s*\[([^\]]+)\]", txt)
    if not mc or not mt:
        return None
    return {"custo": float(mc.group(1)), "tour": [int(x) for x in mt.group(1).split(",")]}


def estrutura(positions, caminho):
    chave = lambda a, b: frozenset((tuple(round(v, 6) for v in a), tuple(round(v, 6) for v in b)))
    aresta_peca = {}
    for k, p in enumerate(positions):
        c = list(p.exterior.coords)
        for a, b in zip(c[:-1], c[1:]):
            aresta_peca.setdefault(chave(a, b), []).append(k)
    corridas, atual = [], None
    fora = 0
    for seg, tag in caminho:
        if tag != "c":
            atual = None
            continue
        ks = aresta_peca.get(chave(seg.coords[0], seg.coords[-1]))
        if ks is None:
            fora += 1
            atual = None
            continue
        k = ks[0]
        if atual is None or atual[0] != k:
            atual = [k, 0]
            corridas.append(atual)
        atual[1] += 1
    por = {}
    for k, n in corridas:
        por.setdefault(k, []).append(n)
    split = sum(1 for v in por.values() if len(v) > 1)
    prim = caminho[0][0].coords[0]
    ult = caminho[-1][0].coords[-1]
    return {"n_pecas": len(positions), "corridas": len(corridas), "pecas_em_varias_corridas": split, "seg_corte_fora_de_arestas": fora,
            "inicio": [round(prim[0], 3), round(prim[1], 3)], "fim": [round(ult[0], 3), round(ult[1], 3)],
            "tag_primeiro": caminho[0][1], "tag_ultimo": caminho[-1][1]}


def caminho_de_tour_pcglns(positions, cidades, tour):
    """Tour do PCGLNS (ids de cidade 1-based; cidade = (grupo, vertice)) -> caminho origem -> pecas -> origem no formato do heuristic_core."""
    cam, pos = [], (0.0, 0.0)
    for cid in tour:
        k, v = cidades[cid - 1]
        ring = list(positions[k].exterior.coords)[:-1]
        entrada = ring[v]
        if tuple(entrada) != tuple(pos):
            cam.append((LineString([pos, entrada]), "d"))
        m = len(ring)
        seq = [ring[(v + t) % m] for t in range(m + 1)]
        for a, b in zip(seq[:-1], seq[1:]):
            if tuple(a) != tuple(b):
                cam.append((LineString([a, b]), "c"))
        pos = entrada
    cam.append((LineString([pos, (0.0, 0.0)]), "d"))
    return cam


def auditar(nome, ref):
    f = OUT / f"aud_{nome}.json"
    if f.exists():
        return
    fp = INST / f"{nome}.txt"
    _, layout = load_instance(fp)
    cfg_orig = {"root_strategy": "nearest", "child_order": "num_filhos", "mst_strategy": "standard", "vertex_strategy": "nearest", "time_limit": 60.0}
    t0 = time.time(); base = hc.run_heuristic(list(layout), cfg_orig); t_base = time.time() - t0
    positions = hc.clusterizar_quadtree(hc.resolver_intersecoes(hc.tratar_furos(list(layout))))
    pares = detect_pi(positions)
    G_full = hc._build_full_graph(positions)
    raiz = hc.escolher_raiz_nearest(G_full, positions)
    t0 = time.time(); forte = bla.busca_local_forte(positions, raiz, pares, time_limit=TB_FORTE, seed=0); t_forte = time.time() - t0
    fo_forte = float(forte["fo_total"])
    est = estrutura(positions, forte["caminho"])
    TS = [0.0, 0.5, 1.0, 2.0, 5.0]       # tempo de perfuracao (s) por perfuracao: o LCPP-1 usa 0 (padrao); sensibilidade
    fo_forte_t = {str(t): fo_t(forte["caminho"], t) for t in TS}; n_perf_forte = n_perf(forte["caminho"])
    # a heuristica reduzida a nivel de PECA INTEIRA: ordem da primeira vez que cada peca e tocada + vertice de entrada = onde o corte comeca
    cidades = []
    for k, p in enumerate(positions):
        for v in range(len(list(p.exterior.coords)) - 1):
            cidades.append((k, v))
    id_de = {kv: i + 1 for i, kv in enumerate(cidades)}
    rkey = lambda c: (round(c[0], 6), round(c[1], 6))
    vert = {}
    for k, p in enumerate(positions):
        for v, c in enumerate(list(p.exterior.coords)[:-1]):
            vert.setdefault(rkey(c), []).append((k, v))
    visto, tour_forte = set(), []
    for seg, tag in forte["caminho"]:
        if tag != "c":
            continue
        a, b = rkey(seg.coords[0]), rkey(seg.coords[-1])
        for k, v in vert.get(a, []):
            if k not in visto and b in {rkey(c) for c in list(positions[k].exterior.coords)[:-1]}:
                visto.add(k)
                tour_forte.append(id_de[(k, v)])
                break
    # PCGLNS pelo pipeline deles
    tmp = Path(tempfile.mkdtemp(prefix="aud_"))
    arq, saida = tmp / f"{nome}.pcglns", tmp / "o.tour"
    stats = convert_instance(fp, arq)
    res = run_pcglns(arq, saida, PCGLNS_T)
    r = {"instancia": nome, "ref_csv": ref, "fo_baseline_aqui": float(base["fo_total"]), "t_baseline": t_base, "fo_forte_aqui": fo_forte, "t_forte": t_forte,
         "estrutura_forte": est, "cut_time_fixed": stats["cut_time_fixed"], "n_pecas_conv": stats.get("n_groups") or stats.get("n_polygons")}
    if res is not None:
        r["fo_pcglns_aqui"] = (res["custo"] / SCALE) / hc._V_AIR + stats["cut_time_fixed"]       # formula DELES
        # cidades (grupo, vertice) na ordem do arquivo .pcglns: reconstruir a partir das posicoes (grupo = peca em ordem; cidade = vertice)
        cidades, mapa = [], []
        for k, p in enumerate(positions):
            for v in range(len(list(p.exterior.coords)) - 1):
                cidades.append((k, v))
        # o conversor pode inserir uma cidade extra; so reavalia se o numero de cidades confere
        n_dim = int(re.search(r"DIMENSION\s*:\s*(\d+)", open(arq, encoding="latin-1").read()).group(1))
        r["n_cidades_pcglns"], r["n_cidades_posicoes"] = n_dim, len(cidades)
        if n_dim == len(cidades):
            cam = caminho_de_tour_pcglns(positions, cidades, res["tour"])
            r["fo_pcglns_reavaliada_origem"] = float(hc.fo_from_path(cam))
            camc = hc.reclassificar_tags(cam); r["fo_pcglns_reav_t"] = {str(t): fo_t(camc, t) for t in TS}; r["n_perf_pcglns"] = n_perf(camc)
            # confere o mapeamento cidade->(peca, vertice): custo do ciclo recalculado (Chebyshev x SCALE) vs. o custo impresso pelo PCGLNS
            pts = []
            for cid in res["tour"]:
                k, v = cidades[cid - 1]
                pts.append(list(positions[k].exterior.coords)[v])
            ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
            ciclo = sum(ch(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts)))
            r["check_custo_ciclo_recalculado"] = ciclo
            r["check_custo_ciclo_pcglns"] = res["custo"] / SCALE
            if len(tour_forte) == len(positions):
                camf = caminho_de_tour_pcglns(positions, cidades, tour_forte)
                r["fo_forte_peca"] = float(hc.fo_from_path(camf))
                camfc = hc.reclassificar_tags(camf); r["fo_forte_peca_t"] = {str(t): fo_t(camfc, t) for t in TS}; r["n_perf_forte_peca"] = n_perf(camfc)
            r["fo_forte_t"] = fo_forte_t; r["n_perf_forte"] = n_perf_forte
            # a heuristica forte, mesma definicao (ela ja e origem -> ... -> origem?): usa o proprio fo_total
        r["pcglns_custo_ciclo_mm"] = res["custo"] / SCALE
        r["pcglns_tour_primeiro"] = res["tour"][:3]
    OUT.mkdir(exist_ok=True)
    json.dump(r, open(f, "w"))
    print(nome, "forte", round(fo_forte, 2), "csv", ref.get("fo_forte"), "| pcglns", round(r.get("fo_pcglns_aqui", 0), 2), "csv", ref.get("fo_pcglns"), "| reav.origem", r.get("fo_pcglns_reavaliada_origem"), flush=True)


if __name__ == "__main__":
    rows = {r["instance"]: r for r in csv.DictReader(open(CSV, encoding="utf-8"))}
    nomes = [a for a in sys.argv[2:]] if len(sys.argv) > 2 else []
    for n in nomes:
        auditar(n, rows[n])
