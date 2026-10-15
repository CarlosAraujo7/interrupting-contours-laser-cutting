"""
verificar_certificado_milp.py  --  VERIFICACAO INDEPENDENTE do certificado de ponto de equilibrio (Proposicao 2 do N1) por MILP exato COM custo de reinicio (14/10/2026; autorizada por Carlos)
=====================================================================================================================================================================================
O certificado (`teto_certificado.py`, C3) e um argumento sobre contagem de corridas combinado com dois otimos exatos (RPP sem Pi e DP de nivel de contorno). Aqui ele e conferido por um calculo que
NAO usa o argumento: o MILP do problema de nivel de segmento SEM precedencia e COM custo de reinicio t, resolvido ate a otimalidade (HiGHS).
Modelo: o mesmo do `rpp_exato.resolver_rpp` (y_e em {0,1,2} = usos da aresta de ar e entre dois vertices quaisquer, Chebyshev; paridade; conexidade por cortes preguicosos), com custo por uso de aresta de ar
c_e = d_e / v_a + t. Quando a origem nao tem aresta requerida (grau requerido 0), um plano com R corridas usa R + 1 movimentos de ar (a ida e a volta a origem sao dois movimentos; as demais pausas, um por
corrida seguinte), logo T(t) = L / v_c + sum_e c_e y_e - t. (Pela Proposicao 1 as cordas sao otimas, entao nenhum plano otimo faz dois movimentos de ar seguidos fora da origem.) Layouts em que a origem
toca um contorno ficam de fora (o numero de corridas depende de onde o passeio comeca). O valor e o otimo do relaxamento sem Pi: e <= ao otimo com Pi.
Conferencias (em `resumo`): (a) M(t) <= T_P*(t) (o plano de nivel de contorno e viavel); (b) M(t) >= LB2(t) (o limite da Proposicao 2); (c) para t >= t_cert, M(t) = T_P*(t) (o certificado: o otimo de
nivel de contorno e o otimo de todos os planos); (d) para t < t_cert, a economia exata T_P*(t) - M(t) <= t_cert - t; (e) as solucoes cientes do reinicio do V3 ficam >= M(t).
Historico (honestidade): os 22 MILPs provados (10 layouts) foram obtidos com a formulacao v1 (cortes de conexidade por componente e `corte_sup` = custo do plano de contorno). Depois da rodada acrescentei
duas desigualdades validas (grau de ar da origem >= 2; total de usos de aresta de ar >= n + 1) e as testei em 2 instancias que estouraram o limite (`dighe1_sep`, `art_15_regular_sep`, t = 1 s, 900 s):
NAO provaram a otimalidade nesse tempo, ou seja, nao resolveram o gargalo; ficam no codigo (sao validas e o autoteste passa), mas nenhum resultado guardado depende delas.
Uso: python verificar_certificado_milp.py autoteste | teste <instancia> <t> <limite_s> | rodar [--workers 8] [--limite 900] [--ts 1.0,0.5,0.25] | resumo > RESULTADOS_CERTIFICADO_MILP.md   (idempotente: pula o que tem JSON)
"""
import glob
import json
import os
import sys
import time
import warnings

import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, csr_matrix

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
OUT = os.path.join(AQUI, "milp_certificado_resultados")
VC, VA = 100.0 / 6.0, 400.0
TS = (1.0, 0.5, 0.25)


def _componentes(n, arestas):
    pai = list(range(n))

    def f(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x
    for u, v in arestas:
        a, b = f(u), f(v)
        if a != b:
            pai[a] = b
    return [f(x) for x in range(n)]


def preparar(coords, req):
    n = len(coords)
    P = np.array(coords, float)
    D = np.abs(P[:, None, :] - P[None, :, :]).max(axis=2)
    pares = [(u, v) for u in range(n) for v in range(u + 1, n)]
    m = len(pares)
    grau_req = np.zeros(n, int)
    for u, v in req:
        grau_req[u] += 1
        grau_req[v] += 1
    A = lil_matrix((n, m + n))
    for k, (u, v) in enumerate(pares):
        A[u, k] = 1
        A[v, k] = 1
    for v in range(n):
        A[v, m + v] = -2
    b = -grau_req.astype(float)
    cons = LinearConstraint(csr_matrix(A), b, b)
    # cortes de conexidade iniciais: cada componente do grafo requerido que nao contem a origem precisa de >= 2 usos de aresta de ar saindo dela (valido para qualquer t)
    raiz = _componentes(n, list(req))
    comps = {}
    for v in range(n):
        if grau_req[v] > 0:
            comps.setdefault(raiz[v], set()).add(v)
    cortes = []
    for r, S in comps.items():
        if 0 in S:
            continue
        row = lil_matrix((1, m + n))
        for k, (u, v) in enumerate(pares):
            if (u in S) != (v in S):
                row[0, k] = 1
        cortes.append(LinearConstraint(csr_matrix(row), 2.0, np.inf))
    if grau_req[0] == 0:
        # (v2, 14/10/2026) desigualdades validas que fortalecem a relaxacao: a origem, sem aresta requerida, tem grau de ar >= 2 (o passeio parte e volta a ela), e o total de usos de aresta de ar e
        # >= (numero de componentes requeridas) + 1, porque cada componente e a origem tem >= 2 pontas de aresta de ar e cada aresta tem 2 pontas.
        row = lil_matrix((1, m + n))
        for k, (u, v) in enumerate(pares):
            if u == 0 or v == 0:
                row[0, k] = 1
        cortes.append(LinearConstraint(csr_matrix(row), 2.0, np.inf))
        row = lil_matrix((1, m + n))
        row[0, :m] = 1
        cortes.append(LinearConstraint(csr_matrix(row), float(len(comps) + 1), np.inf))
    return {"n": n, "D": D, "pares": pares, "m": m, "cons": cons, "cortes": cortes, "grau_req": grau_req}


def resolver_t(inst, req, t, limite_s, max_rodadas=300, corte_sup=None):
    """-> dict(ar_custo = sum c_e y_e, ar_len, n_ar (usos), rodadas, tempo, otimo) ou {'otimo': False, ...}. Os cortes aprendidos ficam em inst['cortes'] (validos para todo t).
    `corte_sup`: limite superior valido do objetivo (o custo do plano de nivel de contorno, que e viavel): vira uma restricao c.x <= corte_sup + 1e-6 e poda a busca; nao altera o otimo
    (o plano de contorno satisfaz a restricao), so acelera a prova."""
    n, D, pares, m = inst["n"], inst["D"], inst["pares"], inst["m"]
    c = np.concatenate([np.array([D[u, v] / VA + t for u, v in pares]), np.zeros(n)])
    lb = np.zeros(m + n)
    ub = np.concatenate([np.full(m, 2.0), np.full(n, 2.0 * n)])
    extra = [LinearConstraint(csr_matrix(c.reshape(1, -1)), -np.inf, corte_sup + 1e-6)] if corte_sup is not None else []
    t0 = time.time()
    for rodada in range(1, max_rodadas + 1):
        restante = limite_s - (time.time() - t0)
        if restante <= 1:
            return {"otimo": False, "motivo": "limite", "rodadas": rodada, "tempo_s": time.time() - t0}
        res = milp(c, constraints=[inst["cons"]] + inst["cortes"] + extra, integrality=np.ones(m + n), bounds=Bounds(lb, ub),
                   options={"time_limit": restante, "disp": False, "mip_rel_gap": 1e-9})
        if res.x is None or res.status != 0:
            return {"otimo": False, "motivo": f"status {res.status}", "rodadas": rodada, "tempo_s": time.time() - t0}
        y = np.rint(res.x[:m]).astype(int)
        ar = [(pares[k][0], pares[k][1], int(y[k])) for k in range(m) if y[k] > 0]
        arestas = list(req) + [(u, v) for u, v, _ in ar]
        raiz = _componentes(n, arestas)
        ativos = set(x for e in arestas for x in e) | {0}
        comps = {}
        for v in ativos:
            comps.setdefault(raiz[v], set()).add(v)
        if len(comps) == 1:
            return {"otimo": True, "ar_custo": float(sum((D[u, v] / VA + t) * yy for u, v, yy in ar)), "ar_len": float(sum(D[u, v] * yy for u, v, yy in ar)),
                    "n_ar": int(sum(yy for _, _, yy in ar)), "rodadas": rodada, "tempo_s": time.time() - t0, "ar": ar}
        r0 = raiz[0]
        for r, S in comps.items():
            if r == r0:
                continue
            row = lil_matrix((1, m + n))
            for k, (u, v) in enumerate(pares):
                if (u in S) != (v in S):
                    row[0, k] = 1
            inst["cortes"].append(LinearConstraint(csr_matrix(row), 2.0, np.inf))
    return {"otimo": False, "motivo": "rodadas", "rodadas": max_rodadas, "tempo_s": time.time() - t0}


def instancia(nome):
    import instancias_lcpp1 as il
    segs = il.ler_segmentos(os.path.join(AQUI, "instancias_lcpp1_dados", f"{nome}.txt"))
    aneis = [a for a in il.agrupar_contornos(segs) if len(a) >= 3]
    coords, req, dono = il.requeridas_com_noding(aneis)
    return coords, req, aneis


def candidatas():
    """Layouts disjuntos sem furos (o MILP nao tem precedencia) e com a origem fora dos contornos."""
    import teto_certificado as tc
    L = []
    for f in sorted(glob.glob(os.path.join(AQUI, "teto_resultados", "*.json"))):
        r = json.load(open(f))
        if not tc.disjunta(r) or r["hole"]:
            continue
        coords, req, _ = instancia(r["instancia"])
        if any(u == 0 or v == 0 for u, v in req):
            continue
        L.append((len(coords), r["instancia"]))
    return [n for _, n in sorted(L)]


def _job(a):
    nome, ts, limite = a
    f = os.path.join(OUT, f"{nome}.json")
    reg = json.load(open(f)) if os.path.exists(f) else {"instancia": nome, "t": {}}
    coords, req, _ = instancia(nome)
    inst = preparar(coords, req)
    corte = sum(max(abs(coords[u][0] - coords[v][0]), abs(coords[u][1] - coords[v][1])) for u, v in req)
    reg["L_corte"] = corte
    reg["vertices"] = len(coords)
    teto = json.load(open(os.path.join(AQUI, "teto_resultados", f"{nome}.json")))
    msgs = []
    for t in ts:
        if str(t) in reg["t"] and reg["t"][str(t)].get("otimo"):
            continue
        sup = teto["dp"]["ar_otimo_contorno"] / VA + t * (teto["n_contornos"] + 1)            # custo (em tempo de ar + t por uso) do plano de nivel de contorno
        r = resolver_t(inst, req, t, limite, corte_sup=sup)
        r["corte_sup_usado"] = True
        if r.get("otimo"):
            r["M"] = corte / VC + r["ar_custo"] - t
            r["R"] = r["n_ar"] - 1
        reg["t"][str(t)] = r
        os.makedirs(OUT, exist_ok=True)
        json.dump(reg, open(f, "w"))
        msgs.append(f"t={t}: " + (f"M={r['M']:.4f} R={r['R']} ({r['rodadas']} rod., {r['tempo_s']:.0f}s)" if r.get("otimo") else f"sem prova ({r.get('motivo')}, {r['tempo_s']:.0f}s)"))
    return nome, "; ".join(msgs) if msgs else "pulado"


def autoteste():
    """Duas caixas disjuntas: M(t) deve igualar o DP de contorno para t grande e o RPP (t = 0) para t = 0; e uma conferencia por enumeracao dos planos de nivel de contorno."""
    from shapely.geometry import box
    import rpp_exato as rx
    import tsh_segmento as tsh
    import teto_certificado as tc
    polys = [box(10, 10, 20, 20), box(40, 10, 50, 20), box(10, 40, 20, 50)]
    coords, req = tsh.construir_requeridas(polys)
    inst = preparar(coords, req)
    corte = sum(max(abs(coords[u][0] - coords[v][0]), abs(coords[u][1] - coords[v][1])) for u, v in req)
    r0 = rx.resolver_rpp(coords, req)
    rt0 = resolver_t(inst, req, 0.0, 120)
    print("RPP (ar, unidades)", r0[0], "| MILP t=0 (ar_len)", rt0["ar_len"])
    assert abs(r0[0] - rt0["ar_len"]) < 1e-6
    pos = [p for p in polys]
    custo_dp, _ = tc.dp_contornos(pos, [])
    for t in (5.0, 1.0):
        r = resolver_t(inst, req, t, 120)
        M = corte / VC + r["ar_custo"] - t
        TP = corte / VC + custo_dp / VA + t * len(polys)
        print(f"t={t}: MILP {M:.6f}  contorno-DP {TP:.6f}  R={r['n_ar'] - 1}")
        assert abs(M - TP) < 1e-6
    print("autoteste OK")


def resumo():
    import statistics as st
    import teto_certificado as tc
    R = {os.path.basename(f)[:-5]: json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "*.json")))}
    T = {os.path.basename(f)[:-5]: json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "teto_resultados", "*.json")))}
    print("# Verificacao independente do certificado por MILP exato com custo de reinicio (14/10/2026)\n")
    print("MILP do problema de nivel de segmento SEM precedencia e COM custo de reinicio t (HiGHS, otimo provado); layouts disjuntos sem furos e com a origem fora dos contornos. "
          "T_P* = otimo exato de nivel de contorno (DP); LB2 = limite da Proposicao 2; B = melhor solucao ciente do reinicio do V3 (quando existe).\n")
    print("| instancia | vertices | t (s) | M(t) (MILP) | T_P*(t) (DP) | M / T_P* - 1 | LB2(t) | R no MILP | t_cert (s) | economia exata (s) | B(t) (V3) | B / M - 1 |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    viol, igual, n_ok, n_tot = [], [], 0, 0
    por_t = {}
    for nome, reg in R.items():
        r = T[nome]
        tcert = tc.t_cert(r, VA)
        for ts in sorted(reg["t"], key=float, reverse=True):
            x = reg["t"][ts]
            t = float(ts)
            n_tot += 1
            if not x.get("otimo"):
                print(f"| {nome} | {reg['vertices']} | {t:g} | sem prova ({x.get('motivo')}) | | | | | {tcert:.3f} | | | |")
                continue
            n_ok += 1
            lb2, tp = tc.teto_refinado(r, t, VC, VA)
            M = x["M"]
            tol = 1e-6 * tp
            ok_a, ok_b = M <= tp + tol, M >= lb2 - tol
            if not (ok_a and ok_b):
                viol.append((nome, t, M, tp, lb2))
            if t >= tcert:
                igual.append(abs(M - tp) <= tol)
            sav = tp - M
            if t < tcert and sav > (tcert - t) + 1e-6:
                viol.append((nome, t, "economia > t_cert - t", sav, tcert - t))
            gB = os.path.join(AQUI, "v3_resultados", f"{nome}__t{ts}.json")
            B = json.load(open(gB))["melhor"]["fo"] if os.path.exists(gB) else None
            por_t.setdefault(t, []).append((100 * (M / tp - 1), sav, tcert, None if B is None else 100 * (B / M - 1)))
            print(f"| {nome} | {reg['vertices']} | {t:g} | {M:.4f} | {tp:.4f} | {100 * (M / tp - 1):+.5f}% | {lb2:.4f} | {x['R']} | {tcert:.3f} | {sav:.4f} | {'' if B is None else f'{B:.4f}'} | {'' if B is None else f'{100 * (B / M - 1):+.3f}%'} |")
    print(f"\nMILPs resolvidos ate a otimalidade: {n_ok} de {n_tot}.\n")
    print("| t (s) | layouts | M = T_P* (certificado) | economia exata, mediana (s) | economia exata, maxima (s) | economia maxima permitida pelo certificado, mediana (s) | B / M - 1, mediana (V3) |\n|---|---:|---:|---:|---:|---:|---:|")
    for t in sorted(por_t, reverse=True):
        v = por_t[t]
        eq = sum(1 for a in v if abs(a[0]) <= 1e-4)
        bs = [a[3] for a in v if a[3] is not None]
        print(f"| {t:g} | {len(v)} | {eq}/{len(v)} | {st.median(a[1] for a in v):.4f} | {max(a[1] for a in v):.4f} | {st.median(max(0.0, a[2] - t) for a in v):.4f} | {'' if not bs else f'{st.median(bs):+.3f}% (n={len(bs)})'} |")
    print()
    print("**Violacoes do certificado (esperado: nenhuma):** " + ("nenhuma" if not viol else str(viol)))
    if igual:
        print(f"\nPara t >= t_cert, M(t) = T_P*(t) (tolerancia 1e-6 relativa) em {sum(igual)} de {len(igual)} casos.")


def teste(nome, t, limite):
    """Um unico MILP (para medir o efeito de mudancas na formulacao): python verificar_certificado_milp.py teste <instancia> <t> <limite_s>"""
    coords, req, _ = instancia(nome)
    inst = preparar(coords, req)
    teto = json.load(open(os.path.join(AQUI, "teto_resultados", f"{nome}.json")))
    corte = sum(max(abs(coords[u][0] - coords[v][0]), abs(coords[u][1] - coords[v][1])) for u, v in req)
    sup = teto["dp"]["ar_otimo_contorno"] / VA + t * (teto["n_contornos"] + 1)
    r = resolver_t(inst, req, t, limite, corte_sup=sup)
    tp = corte / VC + teto["dp"]["ar_otimo_contorno"] / VA + t * teto["n_contornos"]
    if r.get("otimo"):
        M = corte / VC + r["ar_custo"] - t
        print(f"{nome} t={t}: M={M:.6f} T_P*={tp:.6f} dif={M - tp:+.2e} R={r['n_ar'] - 1} rodadas={r['rodadas']} tempo={r['tempo_s']:.0f}s", flush=True)
    else:
        print(f"{nome} t={t}: sem prova ({r.get('motivo')}) em {r['tempo_s']:.0f}s", flush=True)


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    if modo == "teste":
        teste(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))
    elif modo == "autoteste":
        autoteste()
    elif modo == "resumo":
        resumo()
    else:
        workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 8
        limite = float(sys.argv[sys.argv.index("--limite") + 1]) if "--limite" in sys.argv else 900.0
        ts = tuple(float(x) for x in sys.argv[sys.argv.index("--ts") + 1].split(",")) if "--ts" in sys.argv else TS
        nomes = candidatas()
        if "--resolvidas-a" in sys.argv:                              # so os layouts cujo MILP ja foi provado nesse t (curva exata da economia em t pequeno)
            ref = sys.argv[sys.argv.index("--resolvidas-a") + 1]
            def _ok(n):
                f = os.path.join(OUT, f"{n}.json")
                return os.path.exists(f) and json.load(open(f))["t"].get(ref, {}).get("otimo", False)
            nomes = [n for n in nomes if _ok(n)]
        os.makedirs(OUT, exist_ok=True)
        print(f"[{time.strftime('%H:%M:%S')}] verificacao MILP do certificado: {len(nomes)} layouts x t = {ts}, {workers} processos, limite {limite:g} s por MILP", flush=True)
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for n, msg in ex.map(_job, [(n, ts, limite) for n in nomes], chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
        print("MILP CERTIFICADO CONCLUIDO", flush=True)
