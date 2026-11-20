"""
grupo_comum.py  --  LINHA-BASE DE NIVEL DE CONTORNO COM CORTES COMUNS (grupos de perfuracao), certificado e ponto de equilibrio GENERALIZADOS (Proposicoes 2' e 3'; docs/59, Estudo E; 20/11/2026; autorizado por Carlos)
========================================================================================================================================================================================================
Nos layouts em que contornos se tocam ou compartilham arestas, o nivel de contorno do artigo (PCGLNS/DP por contorno) corta toda aresta compartilhada DUAS vezes e cobra um reinicio por contorno; o nivel de
segmento corta cada aresta uma vez e encadeia contornos que se tocam. Parte da vantagem do segmento nesses layouts e portanto de CORTE COMUM (um recurso de CAM, o *pierce group* de Dewil et al.), nao de
interromper contornos. Aqui o efeito e separado com valores EXATOS (so layouts sem furos: o MILP nao tem precedencia):
  R_min   = numero minimo de corridas = soma, por componente do grafo de segmentos requeridos, de max(1, impares/2)  (cobertura minima de arestas por trilhas);
  A_G*    = menor comprimento de ar entre os planos com EXATAMENTE R_min corridas (MILP com a restricao soma y = R_min + 1, a mesma de `milp_r_fixo.py`); G e a linha-base com cortes comuns;
  A*      = ar minimo do RPP sem Pi (valor guardado; conferido contra o MILP em t = 0);  c_G = L/v_c + A_G*/v_a;  T_G(t) = c_G + t R_min.
Proposicao 2' (certificado): todo plano tem R >= R_min corridas; com R = R_min o ar e >= A_G*, com R >= R_min + 1 o ar e >= A*; logo T(t) >= L/v_c + min(A_G*/v_a + t R_min, A*/v_a + t (R_min + 1)) e, para
t >= t_cert^G = (A_G* - A*)/v_a, o plano de A_G* e otimo entre TODOS os planos. (Para contornos disjuntos, R_min = n e G e o plano de nivel de contorno: e a Proposicao 2.)
Proposicao 3' : a economia exata sobre G, S_G(t) = T_G(t) - M(t), M(t) = min_k (c_k + t R_k), e convexa, nao crescente, nula a partir de t_c^G = max_{k: R_k > R_min} (c_G - c_k)/(R_k - R_min) <= t_cert^G, e a iteracao
de Newton de `newton_exato_tc.iterar` (com n -> R_min e P0 -> c_G) a calcula com no maximo R_0 - R_min + 1 MILPs. Decomposicao do ganho do segmento sobre o contorno do artigo, T_P(t) = L_P/v_c + A_P*/v_a + t n:
S_total(t) = T_P(t) - M(t) = [T_P(t) - T_G(t)] (corte comum, sem interromper) + S_G(t) (roteamento interrompido).
Layouts: os de `teto_resultados/` sem furos com R_min < n, origem sem aresta requerida e V <= 70 vertices (regra fixada em docs/59). Previsoes E-S, E-1..E-4: docs/59 (escritas ANTES dos dados).
Uso: python grupo_comum.py autoteste | selecionar | congelar | rodar [--workers 3] [--limite 3600] [--instancias a,b] | verificar | resultados     (`rodar` idempotente; `verificar` ANTES de `resultados`)
"""
import glob
import hashlib
import itertools
import json
import os
import statistics
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy.optimize import LinearConstraint
from scipy.sparse import csr_matrix, lil_matrix

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
import verificar_certificado_milp as vm  # noqa: E402
import newton_exato_tc as nx  # noqa: E402

OUT = os.path.join(AQUI, "grupo_comum_resultados")
MANIFESTO = os.path.join(AQUI, "confirmacao_estudos_manifesto.json")
PROTOCOLO = os.path.join("..", "docs", "59_protocolo_estudos_E_F_G_cortes_comuns_layouts_novos_e_escala_de_fibra.md")
ARQUIVOS_CONGELADOS = ("grupo_comum.py", "confirmacao_novos.py", "escala_fibra_aninhados.py", "verificar_certificado_milp.py", "newton_exato_tc.py", "teto_certificado.py", "tsh_segmento.py", PROTOCOLO)
VC, VA = vm.VC, vm.VA
V_MAX = 70
TS_GRADE = (0.06, 0.25, 1.0)
TOL = nx.TOL


def _cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def selecionados():
    """Regra do protocolo: layouts de `teto_resultados/` sem furos, R_min < n, origem (vertice 0) sem aresta requerida e V <= V_MAX vertices; do menor para o maior V."""
    L = []
    for f in sorted(glob.glob(os.path.join(AQUI, "teto_resultados", "*.json"))):
        r = json.load(open(f))
        if r["hole"] or not r["R_min"] < r["n_contornos"] or "dp" not in r:
            continue
        coords, req, _ = vm.instancia(r["instancia"])
        if any(u == 0 or v == 0 for u, v in req) or len(coords) > V_MAX:
            continue
        L.append((len(coords), r["instancia"]))
    return [n for _, n in sorted(L)]


def dados(nome):
    """Valores guardados e derivados do layout: n, R_min, L (aresta compartilhada uma vez), L_P (soma dos lados dos contornos = comprimento do nivel de contorno), A* (RPP exato), A_P* (DP exato de contorno), T_P(0)."""
    teto = json.load(open(os.path.join(AQUI, "teto_resultados", f"{nome}.json")))
    coords, req, aneis = vm.instancia(nome)
    L_P = float(sum(_cheb(a[i], a[(i + 1) % len(a)]) for a in aneis for i in range(len(a))))
    return {"nome": nome, "n": teto["n_contornos"], "R_min": teto["R_min"], "componentes": teto["componentes"], "V": len(coords), "L": teto["L_corte"], "L_P": L_P, "As": teto["ar_otimo"],
            "AP": teto["dp"]["ar_otimo_contorno"], "TP0": teto["dp"]["fo"], "coords": coords, "req": req}


def _modelo_fixo(coords, req, R):
    """Modelo do MILP com a cardinalidade FIXA: soma_e y_e = R + 1 (R corridas, origem fora dos contornos). Instancia propria (as restricoes aprendidas valem so para este modelo)."""
    inst = vm.preparar(coords, req)
    m, nv = inst["m"], inst["n"]
    linha = lil_matrix((1, m + nv))
    linha[0, :m] = 1
    inst["cortes"].append(LinearConstraint(csr_matrix(linha), float(R + 1), float(R + 1)))
    return inst


def calcular_G(coords, req, R_min, limite_s):
    """A_G* exato (ar minimo com exatamente R_min corridas). -> dict(otimo, ar_len, n_ar, tempo_s)."""
    inst = _modelo_fixo(coords, req, R_min)
    return vm.resolver_t(inst, req, 0.0, limite_s)


def pipeline(d, limite_s, log=print):
    t_ini = time.time()
    nome, coords, req, n, Rm, L = d["nome"], d["coords"], d["req"], d["n"], d["R_min"], d["L"]
    res = {"instancia": nome, "n": n, "R_min": Rm, "componentes": d["componentes"], "V": d["V"], "L": L, "L_P": d["L_P"], "As_guardado": d["As"], "AP": d["AP"], "TP0": d["TP0"], "limite_s": limite_s,
           "pontos": {}, "status": "?"}
    g = calcular_G(coords, req, Rm, limite_s)
    if not g.get("otimo"):
        res.update({"status": "sem_prova_G", "motivo_G": g.get("motivo"), "tempo_total_s": time.time() - t_ini})
        log(f"   {nome}: A_G* SEM PROVA ({g.get('motivo')}, {g.get('tempo_s', 0):.0f}s)")
        return res
    AG = g["ar_len"]
    cG = L / VC + AG / VA
    res.update({"AG": AG, "cG": cG, "tempo_G_s": g["tempo_s"]})
    log(f"   {nome}: V={d['V']} n={n} R_min={Rm} A_G*={AG:.2f} (A_P*={d['AP']:.2f}, A* guardado={d['As']}) ({g['tempo_s']:.0f}s)")
    inst = vm.preparar(coords, req)
    # t = 0: ar minimo (RPP) e o plano de partida
    r0 = vm.resolver_t(inst, req, 0.0, limite_s, corte_sup=AG / VA)
    if not r0.get("otimo"):
        res.update({"status": "sem_prova_t0", "tempo_total_s": time.time() - t_ini})
        log(f"   {nome}: t=0 SEM PROVA ({r0.get('motivo')})")
        return res
    As = r0["ar_len"]
    res.update({"As": As, "t_cert": (AG - As) / VA})
    R0, c0 = r0["n_ar"] - 1, L / VC + r0["ar_len"] / VA
    ponto = lambda t, r: {"t": t, "M": L / VC + r["ar_custo"] - t, "R": r["n_ar"] - 1, "c": L / VC + r["ar_len"] / VA, "tempo_s": r["tempo_s"]}
    p0 = ponto(0.0, r0)
    p0["M"] = L / VC + r0["ar_custo"]
    res["pontos"]["0"] = p0
    for t in TS_GRADE:
        r = vm.resolver_t(inst, req, t, limite_s, corte_sup=AG / VA + t * (Rm + 1))
        if not r.get("otimo"):
            res["pontos"][f"{t:g}"] = {"t": t, "status": "sem_prova", "motivo": r.get("motivo")}
            log(f"   {nome}: t={t}: sem prova ({r.get('motivo')})")
            continue
        res["pontos"][f"{t:g}"] = ponto(t, r)
        log(f"   {nome}: t={t}: R={r['n_ar'] - 1} M={ponto(t, r)['M']:.5f} ({r['tempo_s']:.0f}s)")
    for k, p in res["pontos"].items():
        if "M" in p:
            p["S_G"] = (cG + p["t"] * Rm) - p["M"]
            p["T_P"] = d["TP0"] + p["t"] * n
            p["S_total"] = p["T_P"] - p["M"]
            p["S_cc"] = p["T_P"] - (cG + p["t"] * Rm)
    if res["pontos"]["0"]["S_G"] <= TOL * cG or not R0 > Rm:
        res.update({"status": "exato", "t_c": 0.0, "trilha": [], "tempo_total_s": time.time() - t_ini})
        return res
    dd = {"nome": nome, "L": L, "n": Rm, "AP": AG, "P0": cG}
    trilha, status = nx.iterar(dd, inst, req, limite_s, (0.0, R0, c0), log=log)
    res.update({"status": status, "t_c": trilha[-1]["t"] if status == "exato" else None, "trilha": trilha, "tempo_total_s": time.time() - t_ini})
    return res


def _job(a):
    nome, limite = a
    f = os.path.join(OUT, f"{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    d = dados(nome)
    res = pipeline(d, limite, log=lambda s: print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True))
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(f, "w"), indent=1)
    return nome, f"{res['status']}" + (f" t_c^G={res['t_c']:.5f}" if res.get("t_c") is not None else "") + f" em {res['tempo_total_s']:.0f}s"


def autoteste():
    """Layout de brinquedo com corte comum: dois retangulos que compartilham uma aresta (grafo 'theta': 2 vertices impares => 1 trilha) e um terceiro separado: n = 3, R_min = 2. (1) R_min e L calculados
    batem com a mao; (2) A_G* do MILP de cardinalidade fixa = forca bruta sobre (ordem, direcao, vertice de entrada do terceiro); (3) a iteracao generalizada termina em S_G = 0 com t_c^G <= t_cert^G e
    conferencia independente em t_c(1 -+ 1e-3); (4) a decomposicao S_total = S_cc + S_G fecha."""
    from shapely.geometry import box
    import tsh_segmento as tsh
    import teto_certificado as tc
    polys = [box(5, 8, 15, 18), box(15, 8, 25, 18), box(20, 28, 30, 38)]
    coords, req = tsh.construir_requeridas(polys)
    Rm, ncomp = tc.r_min(coords, req)
    assert (Rm, ncomp) == (2, 2), (Rm, ncomp)
    L = float(sum(_cheb(coords[u], coords[v]) for u, v in req))
    assert abs(L - (7 * 10 + 40)) < 1e-9, L                                       # aresta compartilhada uma vez: 7 arestas de 10 no par + 40 no terceiro = 110
    # forca bruta de A_G*
    O, u, v = (0, 0), (15, 8), (15, 18)
    w3 = [(20, 28), (30, 28), (30, 38), (20, 38)]
    melhor = 1e18
    for w in w3:
        for ent, sai in ((u, v), (v, u)):
            melhor = min(melhor, _cheb(O, ent) + _cheb(sai, w) + _cheb(w, O),            # par primeiro, depois o terceiro
                         _cheb(O, w) + _cheb(w, ent) + _cheb(sai, O))                     # terceiro primeiro
    g = calcular_G(coords, req, Rm, 120)
    assert g["otimo"] and abs(g["ar_len"] - melhor) < 1e-6, (g, melhor)
    print(f"A_G* = {g['ar_len']} (forca bruta {melhor}) OK")
    d = {"nome": "brinquedo_cc", "n": 3, "R_min": Rm, "componentes": ncomp, "V": len(coords), "L": L, "L_P": 100.0, "As": None, "AP": None, "TP0": None, "coords": coords, "req": req}
    # valores de contorno do brinquedo: DP sobre os 3 contornos (cada um cortado inteiro) e L_P = soma dos 3 perimetros (a aresta compartilhada duas vezes)
    AP, _ = tc.dp_contornos(polys, [])
    L_P = 40 + 40 + 40
    d.update({"AP": AP, "L_P": float(L_P), "TP0": L_P / VC + AP / VA})
    res = pipeline(d, 120, log=lambda s: print("  ", s))
    assert res["status"] == "exato", res["status"]
    assert res["t_c"] <= res["t_cert"] + 1e-9
    inst = vm.preparar(coords, req)
    cG = res["cG"]
    if res["t_c"] > 0:
        for t, esperado in ((res["t_c"] * (1 - 1e-3), True), (res["t_c"] * (1 + 1e-3), False)):
            r = vm.resolver_t(inst, req, t, 120)
            S = (cG + t * Rm) - (L / VC + r["ar_custo"] - t)
            assert (S > TOL * (cG + t * Rm)) == esperado, (t, S)
    for k, p in res["pontos"].items():
        if "M" in p:
            assert abs(p["S_total"] - (p["S_cc"] + p["S_G"])) < 1e-9
    print("pipeline OK: t_c^G =", res["t_c"], "t_cert^G =", res["t_cert"], "| S_cc(1) =", res["pontos"]["1"].get("S_cc"))
    print("AUTOTESTE OK")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def congelar():
    man = {"data": time.strftime("%Y-%m-%d %H:%M:%S"), "arquivos": {os.path.normpath(a): sha(os.path.join(AQUI, a)) for a in ARQUIVOS_CONGELADOS}}
    json.dump(man, open(MANIFESTO, "w"), indent=1)
    print("congelado:", json.dumps(man, indent=1))


def verificar():
    """(1) codigo e protocolo iguais aos congelados; (2) previsoes ESTRUTURAIS E-S1..E-S5 em cada resultado (violar uma e erro de codigo ou da teoria: investigar, nao relatar como achado)."""
    ok = True
    man = json.load(open(MANIFESTO))
    for a, h in man["arquivos"].items():
        igual = sha(os.path.join(AQUI, a)) == h
        ok &= igual
        print(("OK       " if igual else "ALTERADO ") + a)
    fs = sorted(glob.glob(os.path.join(OUT, "*.json")))
    print(f"{len(fs)} layouts com resultado")
    for f in fs:
        r = json.load(open(f))
        probs = []
        n, Rm, L = r["n"], r["R_min"], r["L"]
        if abs(r["TP0"] - (r["L_P"] / VC + r["AP"] / VA)) > 1e-6 * r["TP0"]:
            probs.append("E-S5: T_P(0) guardado != L_P/v_c + A_P*/v_a")
        if "As" in r:
            if abs(r["As"] - r["As_guardado"]) > 1e-6 * max(1.0, r["As"]):
                probs.append("E-S5: A* do MILP em t = 0 difere do RPP guardado")
            AG, As, cG = r["AG"], r["As"], r["cG"]
            if AG < As - 1e-9:
                probs.append("E-S1: A_G* < A*")
            for k, p in r["pontos"].items():
                if "M" not in p:
                    continue
                t = p["t"]
                lb = L / VC + min(AG / VA + t * Rm, As / VA + t * (Rm + 1))
                if p["M"] < lb * (1 - 1e-9) - 1e-9:
                    probs.append(f"E-S1: M(t={t}) abaixo do limite inferior (Prop. 2')")
                if p["M"] > cG + t * Rm + 1e-9:
                    probs.append(f"E-S2: M(t={t}) acima de T_G(t)")
                if p["S_G"] > r["t_cert"] - t + 1e-6:
                    probs.append(f"E-S2: economia sobre G em t={t} maior que t_cert^G - t")
            pts = sorted((p["t"], p["S_G"]) for p in r["pontos"].values() if "S_G" in p)
            for (t1, s1), (t2, s2), (t3, s3) in zip(pts, pts[1:], pts[2:]):
                if not (s2 <= s1 + 1e-9 and s3 <= s2 + 1e-9):
                    probs.append("E-S3: S_G nao decrescente na grade")
                lamb = (t2 - t1) / (t3 - t1)
                if s2 > (1 - lamb) * s1 + lamb * s3 + 1e-7:
                    probs.append("E-S3: S_G nao convexa na grade")
        if r["status"] == "exato" and r.get("trilha"):
            tr = r["trilha"]
            ts = [x["t"] for x in tr]
            Rs = [x["R"] for x in tr if "R" in x]
            if not all(b > a for a, b in zip(ts, ts[1:])) or not all(b < a for a, b in zip(Rs, Rs[1:])):
                probs.append("E-S4: t nao cresce ou R nao decresce estritamente")
            if len([x for x in tr if "M" in x]) > Rs[0] - Rm + 1:
                probs.append("E-S4: mais MILPs que R_0 - R_min + 1")
            if r["t_c"] > r["t_cert"] * (1 + 1e-6):
                probs.append("E-S4: t_c^G > t_cert^G")
        ok &= not probs
        print(f"  {r['instancia']}: {r['status']}" + (f" t_c^G={r['t_c']:.5f}" if r.get("t_c") is not None else "") + (" | " + "; ".join(probs) if probs else " | estrutura OK"))
    print("VERIFICACAO " + ("OK" if ok else "COM PROBLEMAS"))
    sys.exit(0 if ok else 1)


def resultados():
    fs = sorted(glob.glob(os.path.join(OUT, "*.json")))
    R = [json.load(open(f)) for f in fs]
    ex = [r for r in R if r["status"] == "exato"]
    f2 = lambda x, d=3: "--" if x is None else f"{x:.{d}f}"
    pc = lambda r, k, c: (100 * r["pontos"][k][c] / r["pontos"][k]["T_P"]) if k in r["pontos"] and c in r["pontos"][k] else None
    L = ["# Linha-base com cortes comuns (grupos de perfuracao): certificado e ponto de equilibrio generalizados (docs/59, Estudo E)", "",
         "| layout | n | R_min | V | A_P* | A_G* | A* | t_cert^G (s) | t_c^G (s) | rho_G | S_G(0) % | S_G(0,25) % | S_G(1) % | S_cc(1) % | S_total(1) % | status |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    linhas = []
    for r in R:
        rho = r["t_c"] * VA * r["R_min"] / r["L"] if r.get("t_c") is not None else None
        linhas.append((r, rho))
        L.append(f"| {r['instancia']} | {r['n']} | {r['R_min']} | {r['V']} | {r['AP']:.1f} | {f2(r.get('AG'), 1)} | {f2(r.get('As'), 1)} | {f2(r.get('t_cert'))} | {f2(r.get('t_c'), 5)} | {f2(rho)} | "
                 f"{f2(pc(r, '0', 'S_G'))} | {f2(pc(r, '0.25', 'S_G'))} | {f2(pc(r, '1', 'S_G'))} | {f2(pc(r, '1', 'S_cc'))} | {f2(pc(r, '1', 'S_total'))} | {r['status']} |")
    L += ["", f"Layouts: {len(R)}; com ponto de equilibrio exato sobre G: {len(ex)}."]
    if len(ex) >= 5:
        s25 = [pc(r, "0.25", "S_G") for r in ex if pc(r, "0.25", "S_G") is not None]
        s1 = [r for r in ex if "1" in r["pontos"] and "S_G" in r["pontos"]["1"]]
        tcs = [r["t_c"] for r in ex]
        rhos = [rho for r, rho in linhas if rho is not None and r["status"] == "exato"]
        E1 = bool(s25) and all(x <= 1e-5 for x in s25)
        E2 = max(tcs) <= 0.2 and 0.2 <= statistics.median(rhos) <= 0.8
        E3 = bool(s1) and all(r["pontos"]["1"]["S_G"] <= TOL * r["pontos"]["1"]["T_P"] and abs(r["pontos"]["1"]["S_total"] - r["pontos"]["1"]["S_cc"]) <= 1e-6 * r["pontos"]["1"]["T_P"] for r in s1)
        cc1 = [r["pontos"]["1"]["S_cc"] for r in s1]
        E4 = bool(cc1) and all(x > 0 for x in cc1)
        fmt = lambda b: "SUSTENTADA" if b else "NAO SUSTENTADA"
        L += ["", f"E-1 (nulo em 0,25 s sobre G): {sum(1 for x in s25 if x <= 1e-5)} de {len(s25)} layouts; previsao: todos: **{fmt(E1)}**.",
              f"E-2 (t_c^G <= 0,2 s e rho_G mediano em [0,2; 0,8]): maior t_c^G = {max(tcs):.4f} s; rho_G mediano = {statistics.median(rhos):.3f} (min {min(rhos):.3f}, max {max(rhos):.3f}): **{fmt(E2)}**.",
              f"E-3 (a 1 s o ganho total do segmento e todo de corte comum: S_G(1) = 0 e S_total(1) = S_cc(1)): {len(s1)} layouts com M(1) provado: **{fmt(E3)}**.",
              f"E-4 (S_cc(1) > 0): " + (f"minimo {min(cc1) / 1:.4g} s ({len(cc1)} layouts): **{fmt(E4)}**." if cc1 else "sem dados.")]
    else:
        L += ["", f"Menos de 5 layouts com ponto de equilibrio exato sobre G ({len(ex)}): as previsoes E-1..E-4 NAO sao avaliadas (regra de decisao do protocolo); relatar so a tabela."]
    open(os.path.join(AQUI, "RESULTADOS_GRUPO_COMUM.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "autoteste"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "autoteste":
        autoteste()
    elif modo == "selecionar":
        for nome in selecionados():
            d = dados(nome)
            print(f"{nome}: n={d['n']} R_min={d['R_min']} V={d['V']} L={d['L']:.1f} L_P={d['L_P']:.1f} A*={d['As']:.1f} A_P*={d['AP']:.1f}")
    elif modo == "congelar":
        congelar()
    elif modo == "verificar":
        verificar()
    elif modo == "resultados":
        resultados()
    elif modo == "rodar":
        workers, limite = arg("--workers", int, 3), arg("--limite", float, 3600.0)
        nomes = arg("--instancias", str, "").split(",") if "--instancias" in sys.argv else selecionados()
        print(f"[{time.strftime('%H:%M:%S')}] Cortes comuns: {len(nomes)} layouts, {workers} processos, limite {limite:g} s por MILP: {', '.join(nomes)}", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for n_, msg in ex.map(_job, [(x, limite) for x in nomes], chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {n_}: {msg}", flush=True)
        print("CORTES COMUNS CONCLUIDO", flush=True)
