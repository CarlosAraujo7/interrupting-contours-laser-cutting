"""
investigar_gap_ea0.py  --  POR QUE a heuristica proposta fica ~0,7% acima do PCGLNS/VNS-Pi no nivel de peca? (E-A0, continuacao 84)
================================================================================================================================
Para cada instancia comparavel do piloto, parte do TOUR da heuristica com Pi (`enforce_precedence=True`, convertido em tour de (peca, vertice de
entrada)) e mede, com a MESMA funcao de objetivo (`heuristic_core.fo_from_path`):
  A  = FO do tour da heuristica (nivel de peca);
  B  = mesma ORDEM de pecas, vertices de entrada OTIMOS (programacao dinamica exata sobre as camadas de vertices; Chebyshev) -> isola o efeito
       da regra `vertex_strategy='nearest'` (hipotese H1);
  C  = A seguido de BUSCA LOCAL do VNS-Pi (`vns_zhang_pi._local_search_pi`, descida pura, 5 sementes, melhor) -> quanto da diferenca e fechado
       por uma busca local simples sobre o tour de pecas (hipotese H3; envolve ordem e entradas);
  D  = VNS-Pi com T segundos A PARTIR do tour da heuristica (Shake + LocalSearch) -> o que um pos-processamento curto alcanca;
  P  = PCGLNS (media das sementes do piloto, T=30 s) -- referencia;  V = VNS-Pi do piloto (partindo do NearestFirst-Pi).
Saida: `investigacao_gap_ea0/gap_<instancia>.json` (idempotente) e `RESULTADOS_INVESTIGACAO_GAP_EA0.md` (modo resumo).
Uso:  python investigar_gap_ea0.py rodar [--tempo 5] [--limite 12] [inst ...]   |   python investigar_gap_ea0.py resumo
"""
import os, sys, json, time, random, warnings, tempfile, statistics
import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import ea0_lib as lib
import rodar_ea0 as ea0
import dxf_parser
import heuristic_core as hc
import vns_zhang_pi as vp
from mastri import parse_pcglns

OUT = os.path.join(AQUI, "investigacao_gap_ea0")


def dp_entradas(inst, tour):
    """Mesma ORDEM de pecas do tour; escolhe os vertices de entrada que minimizam a distancia de CHEBYSHEV total (a metrica da FO) (ciclo com a origem). Exato."""
    cid = [c for c in tour if inst["cidades"][c - 1][3] >= 0]
    por_peca = {}
    for i, c in enumerate(inst["cidades"], 1):
        if c[3] >= 0:
            por_peca.setdefault(c[3], []).append(i)
    xy = lambda ids: np.array([[inst["cidades"][i - 1][0], inst["cidades"][i - 1][1]] for i in ids], float)
    camadas = [por_peca[inst["cidades"][c - 1][3]] for c in cid]
    P0 = np.array([[0.0, 0.0]])
    custo = np.abs(xy(camadas[0]) - P0).max(axis=1)
    ant = [None]
    pais = []
    for k in range(1, len(camadas)):
        A, B = xy(camadas[k - 1]), xy(camadas[k])
        M = custo[:, None] + np.abs(A[:, None, :] - B[None, :, :]).max(axis=2)
        pais.append(M.argmin(axis=0))
        custo = M.min(axis=0)
    fim = custo + np.abs(xy(camadas[-1]) - P0).max(axis=1)
    j = int(fim.argmin())
    escolha = [j]
    for k in range(len(camadas) - 1, 0, -1):
        j = int(pais[k - 1][j])
        escolha.append(j)
    escolha.reverse()
    return [1] + [camadas[k][escolha[k]] for k in range(len(camadas))]


def vns_a_partir_de(inst_pi, S0, seed, tempo):
    """Laco do VNS-Pi (Shake + LocalSearch) partindo de S0 em vez do NearestFirst-Pi."""
    rng = random.Random(seed)
    deadline = time.time() + tempo
    S = list(S0)
    custo = vp.vz._custo(S, inst_pi)
    while time.time() < deadline:
        Sp = vp._local_search_pi(vp._shake_pi(S, inst_pi, rng), inst_pi, rng, deadline)
        cp = vp.vz._custo(Sp, inst_pi)
        if cp < custo - 1e-9:
            S, custo = Sp, cp
    return S


def rodar_uma(nome, tempo):
    f = os.path.join(OUT, f"gap_{nome}.json")
    if os.path.exists(f):
        return
    nm, polys, info = dxf_parser.load_instance_dxf(ea0.listar()[nome])
    inst = lib.montar_instancia(polys)
    v_cut, v_air = hc._DEFAULT_CONFIG["v_cut"], hc._DEFAULT_CONFIG["v_air"]
    fo = lambda t: lib.fo_do_tour(polys, inst, t, v_cut, v_air)
    res = hc.run_heuristic(list(polys), {**lib.CFG_BASE, "time_limit": 60, "enforce_precedence": True})
    tourA = lib.tour_de_caminho(polys, inst, res["caminho"])
    r = {"instancia": nome, "n_pecas": len(polys), "fo_nativa": float(res["fo_total"]), "A": fo(tourA), "tempo_heuristica_s": float(res["time_total"])}
    tourB = dp_entradas(inst, tourA)
    r["B"] = fo(tourB)
    r["B_viol"] = lib.violacoes(inst, tourB)
    tmp = tempfile.mkdtemp(prefix="gap_")
    arq = os.path.join(tmp, f"{nome}.pcglns")
    lib.escrever_pcglns(inst, arq, nome)
    inst_pi = vp._InstanciaPi(parse_pcglns(arq))
    melhorC, tC = None, 0.0
    for sd in range(5):
        t0 = time.time()
        S = vp._local_search_pi(list(tourA), inst_pi, random.Random(sd), time.time() + 60)
        tC += time.time() - t0
        c = fo(S)
        if melhorC is None or c < melhorC:
            melhorC, SC = c, S
    r["C"], r["C_tempo_medio_s"], r["C_viol"] = melhorC, tC / 5, lib.violacoes(inst, SC)
    Ds = []
    for sd in range(3):
        SD = vns_a_partir_de(inst_pi, tourA, sd, tempo)
        Ds.append(fo(SD))
        assert lib.violacoes(inst, SD) == 0
    r["D_media"], r["D_melhor"], r["D_tempo_s"] = float(statistics.mean(Ds)), float(min(Ds)), tempo
    for x in os.listdir(tmp):
        os.remove(os.path.join(tmp, x))
    os.rmdir(tmp)
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f + ".tmp", "w"))
    os.replace(f + ".tmp", f)
    print(f"[{time.strftime('%H:%M:%S')}] {nome}: A={r['A']:.1f} B={r['B']:.1f} C={r['C']:.1f} D={r['D_media']:.1f}", flush=True)


def resumo(nomes, tempo_ref=30):
    print("# E-A0 -- investigacao dos ~0,7% (heuristica proposta vs. PCGLNS no nivel de peca)\n")
    print("A = tour da heuristica; B = mesma ordem de pecas com vertices de entrada OTIMOS (DP exata); C = A + busca local do VNS-Pi (descida pura, melhor de 5 sementes); "
          "D = VNS-Pi (Shake + busca local) a partir de A por T s (media de 3 sementes); P = PCGLNS (media do piloto, T=30 s); V = VNS-Pi do piloto (a partir do NearestFirst-Pi). "
          "FO no nivel de peca (`fo_from_path`); 'fecha' = fracao do gap A->P recuperada: (A - x)/(A - P).\n")
    print("| instancia | pecas | A heuristica | B vertices otimos (fecha) | C + busca local (fecha) | D + VNS T s (fecha) | P PCGLNS | V VNS-Pi | gap A vs. P | t heur (s) | t busca local (s) |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    fech = {"B": [], "C": [], "D": []}
    gaps = {"A": [], "B": [], "C": [], "D": []}
    for nome in nomes:
        f = os.path.join(OUT, f"gap_{nome}.json")
        if not os.path.exists(f):
            continue
        r = json.load(open(f))
        d = ea0._coletar(nome, tempo_ref)
        if "pcglns" not in d:
            continue
        P = d["pcglns"]["fo_med"]
        V = d["vns_pi"]["fo_med"] if "vns_pi" in d else float("nan")
        A = r["A"]
        fr = lambda x: (A - x) / (A - P) * 100 if A > P else float("nan")
        for k, x in (("A", A), ("B", r["B"]), ("C", r["C"]), ("D", r["D_media"])):
            gaps[k].append(100 * (x / P - 1))
        for k, x in (("B", r["B"]), ("C", r["C"]), ("D", r["D_media"])):
            fech[k].append(fr(x))
        print(f"| {nome} | {r['n_pecas']} | {A:.1f} | {r['B']:.1f} ({fr(r['B']):.0f}%) | {r['C']:.1f} ({fr(r['C']):.0f}%) | {r['D_media']:.1f} ({fr(r['D_media']):.0f}%) | {P:.1f} | {V:.1f} | "
              f"{100 * (A / P - 1):+.2f}% | {r['tempo_heuristica_s']:.0f} | {r['C_tempo_medio_s']:.1f} |")
    print()
    if gaps["A"]:
        print("Gap medio sobre o PCGLNS (media das instancias): " + "; ".join(f"{k} {statistics.mean(v):+.2f}%" for k, v in gaps.items()) + ".")
        print("Fracao media do gap A->P recuperada: " + "; ".join(f"{k} {statistics.mean([x for x in v if x == x]):.0f}%" for k, v in fech.items()) + ".")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    def _opt(flag, tipo, default):
        return tipo(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default
    com_valor = {"--tempo", "--limite"}
    explicit = [a for i, a in enumerate(sys.argv[2:], 2) if not a.startswith("--") and sys.argv[i - 1] not in com_valor]
    todas = sorted(ea0.listar())
    lim = _opt("--limite", int, 12)
    nomes = explicit or [todas[int(i * len(todas) / lim)] for i in range(lim)]
    nomes = [n for n in nomes if n != "p7xj_4"]           # fora da comparacao (corte em segmentos / tecnicas especiais)
    if modo == "resumo":
        resumo(nomes)
    else:
        tempo = _opt("--tempo", int, 5)
        for n in nomes:
            rodar_uma(n, tempo)
        print("INVESTIGACAO CONCLUIDA", flush=True)
