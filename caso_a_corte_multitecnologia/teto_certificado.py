"""
teto_certificado.py  --  (C1, C3) TETOS CERTIFICADOS do ganho do nivel de segmento e (C2) OTIMO exato do nivel de contorno, nas instancias pequenas do LCPP-1 (14/10/2026; exploratorio, nao planejado antes dos dados)
=====================================================================================================================================================================================================
C1. Para QUALQUER plano (qualquer metodo, com ou sem precedencia): T(t) >= L/v_c + A*/v_a + t*R_min, onde L = comprimento de corte (segmentos compartilhados contados uma vez), A* = ar minimo do RPP exato
SEM precedencia (`rpp_lcpp1.py`; valido tambem com precedencia, que so restringe) e R_min = numero minimo de corridas = soma, por componente conexa do grafo de segmentos requeridos, de max(1, impares/2)
(cobertura minima de arestas por trilhas). Cada termo e limitado separadamente, entao o limite vale para todo t. O teto do ganho sobre a rota de nivel de contorno P (tempo T_P(t) = P0 + t*n_contornos) e
c(t) = (T_P(t) - LB(t)) / T_P(t).
C2. Para o nivel de contorno (a referencia 'peca' = PCGLNS por contorno, cada contorno cortado numa corrida, ciclo origem -> contornos -> origem, distancia de Chebyshev, ponto de entrada livre entre os
vertices do contorno, precedencia ESTRITA nos layouts com furo): programacao dinamica exata (Held-Karp sobre subconjuntos de contornos, estado = cidade de entrada) quando n <= 18 contornos. A FO do tour
otimo e calculada pela MESMA funcao (`heuristic_core.fo_from_path` sobre o caminho de `caminho_de_tour`, copia de `auditar_lcpp1.caminho_de_tour_pcglns`) e comparada com a FO guardada do PCGLNS
(`auditoria_lcpp1/honesta_282`).
C3. Layouts de contornos DISJUNTOS (cada componente conexa do grafo requerido e um contorno; R_min = n): qualquer plano tem R >= n corridas; com R = n cada contorno e cortado numa so corrida, isto e, o plano
e de nivel de contorno e o ar e >= A_P* (otimo do C2); com R >= n + 1 o ar e >= A* (RPP). Logo T(t) >= L/v_c + min(A_P*/v_a + t n, A*/v_a + t (n+1)). Para t >= t_cert = (A_P* - A*)/v_a o otimo de nivel de
contorno e o otimo de todos os planos; para t < t_cert nenhum plano economiza mais que t_cert - t segundos sobre o otimo de nivel de contorno.
Uso: python teto_certificado.py rodar [--workers 6]   |   python teto_certificado.py resumo > RESULTADOS_TETO_CERTIFICADO.md       (idempotente: pula o que ja tem JSON em teto_resultados/)
"""
import glob
import json
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
OUT = os.path.join(AQUI, "teto_resultados")
TS = (0.0, 0.01, 0.06, 0.25, 1.0)
N_MAX_DP = 18


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def r_min(coords, req):
    """Corridas minimas: por componente do grafo requerido, max(1, impares/2)."""
    pai = {}

    def f(x):
        while pai.setdefault(x, x) != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    grau = {}
    for u, v in req:
        pai[f(u)] = f(v)
        grau[u] = grau.get(u, 0) + 1
        grau[v] = grau.get(v, 0) + 1
    impares = {}
    comps = set()
    for x in grau:
        c = f(x)
        comps.add(c)
        if grau[x] % 2:
            impares[c] = impares.get(c, 0) + 1
    return sum(max(1, impares.get(c, 0) // 2) for c in comps), len(comps)


def dp_contornos(pos, pares, origem=(0.0, 0.0)):
    """Held-Karp sobre subconjuntos de contornos com cidade de entrada livre. -> (custo de ar em unidades de desenho, tour [(k, v)])."""
    n = len(pos)
    rings = [list(p.exterior.coords)[:-1] for p in pos]
    cidades = [(k, v) for k in range(n) for v in range(len(rings[k]))]
    C = len(cidades)
    xy = np.array([rings[k][v] for k, v in cidades], dtype=float)
    ck = np.array([k for k, _ in cidades])
    D = np.maximum(np.abs(xy[:, None, 0] - xy[None, :, 0]), np.abs(xy[:, None, 1] - xy[None, :, 1]))
    d0 = np.maximum(np.abs(xy[:, 0] - origem[0]), np.abs(xy[:, 1] - origem[1]))
    dentro = [0] * n                                         # dentro[j] = mascara dos contornos que DEVEM estar cortados antes de j
    for (i, j) in pares:
        dentro[j] |= 1 << i
    idx_k = [np.nonzero(ck == k)[0] for k in range(n)]
    FULL = (1 << n) - 1
    F = np.full((1 << n, C), np.inf)
    for k in range(n):
        if dentro[k] == 0:
            F[1 << k, idx_k[k]] = d0[idx_k[k]]
    for S in range(1, FULL):
        cs = np.nonzero(((S >> ck) & 1) == 1)[0]
        vals = F[S, cs]
        if not np.isfinite(vals).any():
            continue
        h = (vals[:, None] + D[cs]).min(axis=0)
        for j in range(n):
            if (S >> j) & 1 or (dentro[j] & ~S):
                continue
            F[S | (1 << j), idx_k[j]] = h[idx_k[j]]
    fin = F[FULL] + d0
    cfim = int(np.argmin(fin))
    custo = float(fin[cfim])
    tour = [cfim]
    S, c = FULL, cfim
    while bin(S).count("1") > 1:
        Sp = S & ~(1 << int(ck[c]))
        cs = np.nonzero(((Sp >> ck) & 1) == 1)[0]
        cand = F[Sp, cs] + D[cs, c]
        c_prev = int(cs[int(np.argmin(cand))])
        tour.append(c_prev)
        S, c = Sp, c_prev
    tour.reverse()
    return custo, [cidades[c] for c in tour]


def caminho_de_tour(pos, tour):
    from shapely.geometry import LineString
    cam, p = [], (0.0, 0.0)
    for k, v in tour:
        ring = list(pos[k].exterior.coords)[:-1]
        ent = ring[v]
        if tuple(ent) != tuple(p):
            cam.append((LineString([p, ent]), "d"))
        m = len(ring)
        seq = [ring[(v + t) % m] for t in range(m + 1)]
        for a, b in zip(seq[:-1], seq[1:]):
            if tuple(a) != tuple(b):
                cam.append((LineString([a, b]), "c"))
        p = ent
    cam.append((LineString([p, (0.0, 0.0)]), "d"))
    return cam


def _job(nome):
    f = os.path.join(OUT, f"{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    import ea0_lib as lib
    import instancias_lcpp1 as il
    import avaliar_heuristica_formal as af
    from shapely.geometry import Polygon
    hc = lib.hc
    t0 = time.time()
    rpp = json.load(open(os.path.join(AQUI, "rpp_lcpp1_resultados", f"{nome}.json")))
    h = json.load(open(os.path.join(AQUI, "auditoria_lcpp1", "honesta_282", f"{nome}.json")))
    g = json.load(open(os.path.join(AQUI, "lcpp1_segmento_resultados", f"{nome}.json")))
    cam = json.load(open(os.path.join(af.CAM, f"{nome}.json")))["forte"]
    segs = il.ler_segmentos(os.path.join(AQUI, "instancias_lcpp1_dados", f"{nome}.txt"))
    aneis = [a for a in il.agrupar_contornos(segs) if len(a) >= 3]
    coords, req, dono = il.requeridas_com_noding(aneis)
    rmin, ncomp = r_min(coords, req)
    polys = [Polygon(a) for a in aneis]
    pos = hc.clusterizar_quadtree(hc.resolver_intersecoes(hc.tratar_furos(list(polys))))
    pares = hc._detectar_precedencia(list(pos))
    nc = g["n_contornos"]
    r = {"instancia": nome, "hole": "_hole_" in nome, "n_contornos": nc, "n_posicoes": len(pos), "n_pares": len(pares), "R_min": rmin, "componentes": ncomp,
         "L_corte": rpp["corte_comprimento"], "ar_otimo": rpp["ar_otimo"], "P0": h.get("fo_pcglns_honesta"), "R0_gtsp": g["melhor"]["n_perf"], "FO0_gtsp": g["melhor"]["fo"],
         "H": {str(t): af.fo_formal(cam, t)["fo"] for t in TS}}
    if h.get("fo_pcglns_honesta") is not None and len(pos) <= N_MAX_DP and h.get("n_cidades_pcglns") == h.get("n_cidades_posicoes"):
        t1 = time.time()
        custo, tour = dp_contornos(pos, pares)
        fo_dp = float(hc.fo_from_path(caminho_de_tour(pos, tour)))
        r["dp"] = {"ar_otimo_contorno": custo, "fo": fo_dp, "tempo_s": time.time() - t1}
    r["tempo_s"] = time.time() - t0
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f, "w"))
    return nome, f"R_min {rmin} (n {nc}) dp {'sim' if 'dp' in r else 'nao'} {r['tempo_s']:.0f} s"


def nomes_resolvidas():
    L = []
    for f in sorted(glob.glob(os.path.join(AQUI, "rpp_lcpp1_resultados", "*.json"))):
        r = json.load(open(f))
        if r["resolvida"]:
            L.append(r["instancia"])
    return L


def disjunta(r):
    """Cada componente conexa do grafo requerido e um unico contorno (contornos sem vertice em comum) e R_min = n."""
    return r["componentes"] == r["n_contornos"] == r["R_min"] and "dp" in r


def t_cert(r, VA):
    return (r["dp"]["ar_otimo_contorno"] - r["ar_otimo"]) / VA


def teto_refinado(r, t, VC, VA):
    """Layouts disjuntos: LB2(t) = L/v_c + min(A_P*/v_a + t n, A*/v_a + t (n+1)); devolve (LB2, T_P*(t)), T_P* = otimo exato de nivel de contorno."""
    n = r["n_contornos"]
    corte = r["L_corte"] / VC
    tp = corte + r["dp"]["ar_otimo_contorno"] / VA + t * n
    lb2 = corte + min(r["dp"]["ar_otimo_contorno"] / VA + t * n, r["ar_otimo"] / VA + t * (n + 1))
    return lb2, tp


def resumo():
    import statistics as st
    sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
    from heuristic_core import _DEFAULT_CONFIG as D
    VC, VA = D["v_cut"], D["v_air"]
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "*.json")))]
    R = [r for r in R if r.get("P0") is not None]
    print("# Tetos certificados do ganho do nivel de segmento e otimo exato do nivel de contorno (14/10/2026)\n")
    print(f"Instancias com RPP exato e referencia de contorno: {len(R)} ({sum(1 for r in R if not r['hole'])} sem precedencia, {sum(1 for r in R if r['hole'])} com furos). Exploratorio: calculado depois dos resultados principais.\n")
    print("## C1. Teto geral c(t) = (T_P(t) - LB(t)) / T_P(t), LB(t) = L/v_c + A*/v_a + t R_min (qualquer layout; T_P = PCGLNS por contorno guardado)\n")
    print("| t (s) | teto mediano | teto maximo | instancias com teto < 0,1% |\n|---|---:|---:|---:|")
    for t in TS + (0.5,):
        c = []
        for r in R:
            tp = r["P0"] + t * r["n_contornos"]
            lb = r["L_corte"] / VC + r["ar_otimo"] / VA + t * r["R_min"]
            assert lb <= tp + 1e-6, (r["instancia"], t)
            if str(t) in r["H"]:
                assert lb <= r["H"][str(t)] + 1e-6 and lb <= r["FO0_gtsp"] + t * r["R0_gtsp"] + 1e-6, (r["instancia"], t)
            c.append(100 * (tp - lb) / tp)
        print(f"| {t:g} | {st.median(c):.3f}% | {max(c):.2f}% | {sum(1 for x in c if x < 0.1)}/{len(c)} |")
    com = [r for r in R if r["R_min"] < r["n_contornos"]]
    print(f"\nLayouts com R_min < n (contornos que se tocam ou compartilham aresta): {len(com)}/{len(R)}.\n")
    print("## C2. Otimo exato do nivel de contorno (Held-Karp) x PCGLNS por contorno guardado\n")
    D2 = [r for r in R if "dp" in r]
    print(f"Instancias com <= {N_MAX_DP} contornos e mesma instancia abstrata do PCGLNS: {len(D2)}.\n")
    print("| instancia | contornos | PCGLNS (FO) | DP exato (FO) | PCGLNS / DP - 1 |\n|---|---:|---:|---:|---:|")
    gaps = []
    for r in D2:
        gp = 100 * (r["P0"] / r["dp"]["fo"] - 1)
        gaps.append(gp)
        print(f"| {r['instancia']} | {r['n_contornos']} | {r['P0']:.3f} | {r['dp']['fo']:.3f} | {gp:+.4f}% |")
    if gaps:
        print(f"\nMediana {st.median(gaps):+.4f}%, maximo {max(gaps):+.4f}%, minimo {min(gaps):+.4f}%; PCGLNS igual ao otimo (|dif| <= 0,005%) em {sum(1 for x in gaps if abs(x) <= 0.005)}/{len(gaps)}; "
              f"PCGLNS abaixo do DP em {sum(1 for x in gaps if x < -0.005)}.")
    print("\n## C3. Layouts de contornos disjuntos: ponto de equilibrio certificado t_cert = (A_P* - A*) / v_a\n")
    print("Qualquer plano tem R >= n corridas; com R = n o plano e de nivel de contorno (ar >= A_P*, o otimo exato do DP); com R >= n + 1, ar >= A* (RPP exato). "
          "Logo T(t) >= L/v_c + min(A_P*/v_a + t n, A*/v_a + t (n+1)); para t >= t_cert o otimo de nivel de contorno e o otimo de TODOS os planos, e para t < t_cert nenhum plano economiza mais que t_cert - t segundos.\n")
    Dj = [r for r in D2 if disjunta(r)]
    print("| instancia | contornos | A* (RPP) | A_P* (DP) | t_cert (s) |\n|---|---:|---:|---:|---:|")
    for r in Dj:
        print(f"| {r['instancia']} | {r['n_contornos']} | {r['ar_otimo']:.1f} | {r['dp']['ar_otimo_contorno']:.1f} | {t_cert(r, VA):.3f} |")
    tc = [t_cert(r, VA) for r in Dj]
    print(f"\nLayouts disjuntos: {len(Dj)} (mediana de t_cert {st.median(tc):.3f} s; minimo {min(tc):.3f}; maximo {max(tc):.3f}).\n")
    print("| t (s) | economia maxima, mediana | economia maxima, maxima | layouts em que o nivel de contorno e certificadamente otimo |\n|---|---:|---:|---:|")
    for t in (0.0, 0.01, 0.06, 0.25, 0.5, 1.0):
        sv = []
        for r in Dj:
            lb2, tp = teto_refinado(r, t, VC, VA)
            sv.append(100 * (tp - lb2) / tp)
            for key, val in (("H", r["H"].get(str(t))), ("G", r["FO0_gtsp"] + t * r["R0_gtsp"])):
                if val is not None:
                    assert lb2 <= val + 1e-6, (r["instancia"], t, key, lb2, val)
        print(f"| {t:g} | {st.median(sv):.3f}% | {max(sv):.3f}% | {sum(1 for x in sv if x <= 1e-9)}/{len(sv)} |")
    print("\nVerificado: em todos os layouts disjuntos e em todo t, LB2(t) <= heuristica do LCPP e <= rota de arcos de t = 0 avaliada em t.")
    print("\n## C4. Solucoes cientes do reinicio (V3) contra o teto, nos layouts disjuntos em comum\n")
    print("| instancia | t (s) | economia sobre o PCGLNS | economia maxima certificada sobre o otimo de contorno | solucao ciente do reinicio / otimo de contorno - 1 |\n|---|---:|---:|---:|---:|")
    for r in Dj:
        for tt in ("0.25", "1.0"):
            g = os.path.join(AQUI, "v3_resultados", f"{r['instancia']}__t{tt}.json")
            if not os.path.exists(g):
                continue
            B = json.load(open(g))["melhor"]["fo"]
            lb2, tp = teto_refinado(r, float(tt), VC, VA)
            tpp = r["P0"] + float(tt) * r["n_contornos"]
            assert lb2 <= B + 1e-6, (r["instancia"], tt, lb2, B)
            print(f"| {r['instancia']} | {tt} | {100 * (tpp - B) / tpp:.3f}% | {100 * (tp - lb2) / tp:.3f}% | {100 * (B / tp - 1):+.3f}% |")


if __name__ == "__main__":
    if "resumo" in sys.argv:
        resumo()
        sys.exit(0)
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 6
    nomes = sorted(nomes_resolvidas())
    os.makedirs(OUT, exist_ok=True)
    print(f"[{time.strftime('%H:%M:%S')}] teto certificado + DP exato: {len(nomes)} instancias, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, nomes, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("TETO CONCLUIDO", flush=True)
