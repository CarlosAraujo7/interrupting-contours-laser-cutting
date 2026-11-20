"""
recalculo_independente_novos.py  --  RECALCULO INDEPENDENTE dos numeros novos do N1 (19/11/2026, terceira revisao duplo-cega; `docs/53`)
================================================================================================================================
Recomputa, SEM importar o gerador de tabelas e com outra implementacao (postos para o Spearman, tempo total refeito de seus componentes), os numeros das analises acrescentadas depois do
`recalculo_independente_rq1_rq2.py`: (A) a leitura dos 47 layouts reais do CPPLib (macros `rl*`), (B) o ponto de equilibrio exato por iteracao de Newton (`nw*`) e (C) a causa da economia
persistente nos layouts aninhados (`cn*`). Se `manuscrito/N1/numeros_n1.tex` existir, compara com os macros (so o projeto o tem; no repositorio publico o script so imprime os valores).
Uso: python recalculo_independente_novos.py   (codigo de saida 0 se tudo coincide ou se nao ha macros para comparar)
"""
import glob
import json
import os
import re
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
VC, VA = 100.0 / 6.0, 400.0
MAC = os.path.join(os.path.dirname(AQUI), "manuscrito", "N1", "numeros_n1.tex")
macros = {}
if os.path.exists(MAC):
    for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}", open(MAC, encoding="utf-8").read()):
        macros[k] = v
FALHAS = []


def num(s):
    s = s.replace("\\%", "").replace("$-$", "-").replace("+", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def confere(nome, valor, casas=2):
    if nome not in macros:
        print(f"      {nome:12s} = {valor:.{casas}f}  (sem macro para comparar)")
        return
    esp = num(macros[nome])
    ok = esp is not None and abs(round(valor, casas) - esp) <= 10 ** (-casas) * 0.51
    print(f"  {'ok ' if ok else 'DIF'} {nome:12s} recalculado {valor:.{casas}f} | manuscrito {macros[nome]}")
    if not ok:
        FALHAS.append(nome)


def postos(x):
    x = np.asarray(x, float)
    o = np.argsort(x, kind="mergesort")
    r = np.empty(len(x))
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[o[j + 1]] == x[o[i]]:
            j += 1
        r[o[i:j + 1]] = (i + j) / 2.0
        i = j + 1
    return r


def spearman(a, b):
    return float(np.corrcoef(postos(a), postos(b))[0, 1])


# ------------------------------------------------------------------------------------------- A. layouts reais do CPPLib (V2)
print("A. 47 layouts reais (v2_resultados)")
L = []
for f in sorted(glob.glob(os.path.join(AQUI, "v2_resultados", "v2_*.json"))):
    r = json.load(open(f))
    if r.get("n_contornos", 0) < 2 or not r.get("peca_10s") or not r["seg_t0"]["melhor"] or not r["seg_t1"]["melhor"]:
        continue
    m1, n, Lp = r["seg_t1"]["melhor"], r["n_contornos"], r["L_pecas"]
    # o tempo total da rota de segmento a t = 1 s refeito dos componentes (corte + voo + reinicios) deve igualar a FO guardada
    refeito = r["L_segmento"] / VC + m1["ar"] / VA + 1.0 * m1["n_perf"]
    assert abs(refeito - m1["fo"]) <= 1e-6 * m1["fo"], "a FO guardada nao e corte + voo + reinicios"
    ref_contorno = r["peca_10s"]["fo_media"] + 1.0 * n                    # o contorno a t = 1 s: valor de t = 0 mais um reinicio por contorno
    S = 100.0 * (ref_contorno - refeito) / ref_contorno
    vies = 100.0 * max(0, n - m1["n_perf"]) / ref_contorno
    L.append(dict(n=n, per=Lp / n, rho=VA / (Lp / n), S=S, Sc=S - vies, vies=vies, cadeia=m1["n_perf"] < n, ve=m1["viol_estrita"] / n, igual=abs(Lp - r["L_segmento"]) <= 1e-6 * Lp))
print(f"      layouts: {len(L)}; comprimento de corte do contorno = o do segmento (nenhuma aresta compartilhada) em todos: {all(x['igual'] for x in L)}")
lim = 0.3
baixo, alto = [x for x in L if x["rho"] <= lim], [x for x in L if x["rho"] > lim]
cadeia = [x for x in L if x["cadeia"]]
pers = [x for x in alto if x["Sc"] > 0.1]
confere("rlN", len(L), 0)
confere("rlNmin", min(x["n"] for x in L), 0)
confere("rlNmax", max(x["n"] for x in L), 0)
confere("rlPerMed", float(np.median([x["per"] for x in L])), 0)
confere("rlRhoMed", float(np.median([x["rho"] for x in L])))
confere("rlNLow", len(baixo), 0)
confere("rlSMed", float(np.median([x["S"] for x in L])))
confere("rlSLowMed", float(np.median([x["S"] for x in baixo])))
confere("rlSLowMax", max(x["S"] for x in baixo))
confere("rlSHighMed", float(np.median([x["S"] for x in alto])))
confere("rlSHighMax", max(x["S"] for x in alto))
confere("rlSMaxCor", max(x["Sc"] for x in L))
confere("rlSpAs", spearman([x["rho"] for x in L], [x["S"] for x in L]))
confere("rlSpCor", spearman([x["rho"] for x in L], [x["Sc"] for x in L]))
confere("rlSpViol", spearman([x["ve"] for x in L], [x["Sc"] for x in L]))
confere("rlNChain", len(cadeia), 0)
confere("rlBiasMed", float(np.median([x["vies"] for x in cadeia])))
confere("rlPersN", len(pers), 0)
confere("rlPersRhoLo", min(x["rho"] for x in pers))
confere("rlPersRhoHi", max(x["rho"] for x in pers))
confere("rlPersLo", min(x["Sc"] for x in pers))
confere("rlPersHi", max(x["Sc"] for x in pers))

# ------------------------------------------------------------------------------------------- B. Newton exato
print("B. Newton exato (newton_resultados)")
R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "newton_resultados", "*.json")))]
ex = []
for r in R:
    teto = json.load(open(os.path.join(AQUI, "teto_resultados", r["instancia"] + ".json")))
    P0 = r["L"] / VC + teto["dp"]["ar_otimo_contorno"] / VA                    # otimo exato de contorno refeito do DP guardado
    assert abs(P0 - r["P0"]) <= 1e-9 * P0, "P0 da trilha difere do DP guardado"
    assert abs((teto["dp"]["ar_otimo_contorno"] - teto["ar_otimo"]) / VA - r["t_cert"]) <= 1e-9, "t_cert da trilha difere do recalculo"
    if r["status"] != "exato":
        continue
    tr = r["trilha"]
    ant = tr[-2]                                                                # o ultimo plano com economia > 0 (ou o de partida)
    raiz = (P0 - ant["c"]) / (ant["R"] - r["n"])
    assert abs(raiz - r["t_c"]) <= 1e-9, "t_c nao e a raiz da reta do plano anterior"
    assert abs(tr[-1]["S"]) <= 1e-7 * (P0 + r["t_c"] * r["n"]), "economia final nao nula"
    ex.append(dict(tc=raiz, rho=raiz * VA * r["n"] / r["L"], razao=raiz / r["t_cert"], novos=sum(1 for x in tr if "M" in x)))
confere("nwN", len(R), 0)
confere("nwExact", len(ex), 0)
confere("nwNoProof", sum(1 for r in R if r["status"] == "sem_prova"), 0)
confere("nwSolves", sum(x["novos"] for x in ex), 0)
confere("nwSolvesMax", max(x["novos"] for x in ex), 0)
confere("nwTcMed", float(np.median([x["tc"] for x in ex])), 3)
confere("nwTcMin", min(x["tc"] for x in ex), 3)
confere("nwTcMax", max(x["tc"] for x in ex), 3)
confere("nwRatioMed", float(np.median([x["razao"] for x in ex])))
confere("nwRatioMax", max(x["razao"] for x in ex))
confere("nwRhoMed", float(np.median([x["rho"] for x in ex])))
confere("nwRhoMax", max(x["rho"] for x in ex))
print(f"      rho_c minimo {min(x['rho'] for x in ex):.2f} (o resumo e a discussao usam 0,3 a 0,5)")

# ------------------------------------------------------------------------------------------- C. causa nos layouts aninhados
print("C. causa nos layouts aninhados (causa_aninhados_resultados)")
V2 = {os.path.basename(f)[3:-5]: json.load(open(f)) for f in glob.glob(os.path.join(AQUI, "v2_resultados", "v2_*.json"))}


def economia(r, m):
    n = r["n_contornos"]
    tot = r["peca_10s"]["fo_media"] + n
    return 100.0 * (tot - m["fo"]) / tot - 100.0 * max(0, n - m["n_perf"]) / tot


nomes = sorted(os.path.basename(f)[4:-5] for f in glob.glob(os.path.join(AQUI, "causa_aninhados_resultados", "est_*.json")))
fech, estr, rep_f, rep_e = [], [], [], []
for n in nomes:
    r = V2[n]
    fech.append(economia(r, r["seg_t1"]["melhor"]))
    estr.append(economia(r, json.load(open(os.path.join(AQUI, "causa_aninhados_resultados", f"est_{n}.json")))["melhor"]))
    rep_f.append(economia(r, json.load(open(os.path.join(AQUI, "causa_aninhados_resultados", f"rep_fechamento_{n}.json")))["melhor"]))
    rep_e.append(economia(r, json.load(open(os.path.join(AQUI, "causa_aninhados_resultados", f"rep_estrita_{n}.json")))["melhor"]))
confere("cnN", len(nomes), 0)
confere("cnClosLo", min(fech))
confere("cnClosHi", max(fech))
confere("cnStrLo", min(estr))
confere("cnStrHi", max(estr))
confere("cnHalf", sum(1 for a, b in zip(fech, estr) if b < 0.5 * a), 0)
confere("cnNil", sum(1 for b in estr if abs(b) <= 0.01), 0)
confere("cnPTres", sum(1 for a, b in zip(fech, rep_f) if b >= 0.75 * a), 0)
confere("cnPQuatro", sum(1 for a, b in zip(estr, rep_e) if abs(a - b) <= 0.05), 0)
print(f"      media do fechamento {np.mean(fech):.3f}% -> estrita {np.mean(estr):.3f}% (queda de {100 * (1 - np.mean(estr) / np.mean(fech)):.0f}%)")

# ------------------------------------------------------------------------------------------- D. orcamento e esforco de busca do PCGLNS (docs/55, docs/55_desvios.md)
SL = os.path.join(AQUI, "causa_aninhados_resultados_slow")
if glob.glob(os.path.join(SL, "orc_*.json")):
    print("\nD. orcamento e esforco de busca do PCGLNS nos aninhados (orc_* em causa_aninhados_resultados e em causa_aninhados_resultados_slow)")
    OUTD = os.path.join(AQUI, "causa_aninhados_resultados")
    reg = []
    for n in nomes:
        r = V2[n]
        orig = {"fechamento": r["seg_t1"]["melhor"], "estrita": json.load(open(os.path.join(OUTD, f"est_{n}.json")))["melhor"]}
        for sem in ("fechamento", "estrita"):
            c, s = json.load(open(os.path.join(OUTD, f"orc_{sem}_{n}.json"))), json.load(open(os.path.join(SL, f"orc_{sem}_{n}.json")))
            reg.append({"sem": sem, "so": economia(r, orig[sem]), "sc": economia(r, c["melhor"]), "ss": economia(r, s["melhor"]),
                        "dfc": 100.0 * (c["melhor"]["fo"] / orig[sem]["fo"] - 1.0), "dfs": 100.0 * (s["melhor"]["fo"] / orig[sem]["fo"] - 1.0), "tcap": c["tempo_total_s"], "torig": c["tempo_original_s"]})
    CL, ST = [x for x in reg if x["sem"] == "fechamento"], [x for x in reg if x["sem"] == "estrita"]
    confere("bgN", len(CL), 0)
    confere("bgTasks", len(reg), 0)
    confere("bgBound", sum(1 for x in reg if x["tcap"] > 2 * x["torig"] + 15), 0)
    confere("bgFree", sum(1 for x in reg if x["tcap"] <= 2 * x["torig"] + 15), 0)
    confere("bgRatioLo", 600.0 / max(x["torig"] for x in reg), 0)
    confere("bgRatioHi", 600.0 / min(x["torig"] for x in reg), 0)
    for k, L_, campo in (("bgClosOrig", CL, "so"), ("bgClosCap", CL, "sc"), ("bgClosSlow", CL, "ss"), ("bgStrOrig", ST, "so"), ("bgStrCap", ST, "sc"), ("bgStrSlow", ST, "ss")):
        confere(k + "Lo", min(x[campo] for x in L_))
        confere(k + "Hi", max(x[campo] for x in L_))
    confere("bgDSavCap", max(abs(x["sc"] - x["so"]) for x in reg), 3)
    confere("bgDSavSlow", max(abs(x["ss"] - x["so"]) for x in reg), 3)
    confere("bgDSavMax", max(max(abs(x["sc"] - x["so"]), abs(x["ss"] - x["so"])) for x in reg), 3)
    confere("bgDFoCap", max(abs(x["dfc"]) for x in reg), 3)
    confere("bgDFoSlow", max(abs(x["dfs"]) for x in reg), 3)
    confere("bgDFoSlowUp", max(x["dfs"] for x in reg), 3)
    confere("bgOa", sum(1 for x in CL if abs(x["sc"] - x["so"]) <= 0.05), 0)
    confere("bgOb", sum(1 for x in ST if abs(x["sc"] - x["so"]) <= 0.05), 0)
    confere("bgOc", sum(1 for x in ST if x["sc"] <= 0.10), 0)
    confere("bgSa", sum(1 for x in CL if abs(x["ss"] - x["so"]) <= 0.05), 0)
    confere("bgSb", sum(1 for x in ST if abs(x["ss"] - x["so"]) <= 0.05), 0)
    confere("bgSc", sum(1 for x in ST if x["ss"] <= 0.10), 0)
    tudo = (all(c_["sc"] >= s_["sc"] - 1e-9 and c_["ss"] >= s_["ss"] - 1e-9 for c_, s_ in zip(CL, ST)) and min(sum(1 for x in CL if abs(x["dfc"]) <= 0.01), sum(1 for x in ST if abs(x["dfc"]) <= 0.01)) >= 3
            and min(sum(1 for x in CL if x["dfs"] <= 0.01), sum(1 for x in ST if x["dfs"] <= 0.01)) >= 3 and min(sum(1 for x in CL if abs(x["sc"] - x["so"]) <= 0.05), sum(1 for x in ST if abs(x["sc"] - x["so"]) <= 0.05),
                                                                                                         sum(1 for x in ST if x["sc"] <= 0.10), sum(1 for x in CL if abs(x["ss"] - x["so"]) <= 0.05),
                                                                                                         sum(1 for x in ST if abs(x["ss"] - x["so"]) <= 0.05), sum(1 for x in ST if x["ss"] <= 0.10)) >= 3)
    if "bgOkAll" in macros:
        ok = (macros["bgOkAll"] == "supported") == tudo
        print(f"  {'ok ' if ok else 'DIF'} todas as previsoes sustentadas (bgOkAll)  recalculado {'supported' if tudo else 'not supported'} | manuscrito {macros['bgOkAll']}")
        if not ok:
            FALHAS.append("bgOkAll")

# ------------------------------------------------------------------------------------------- E. estudos E, F e G (docs/59): cortes comuns, layouts novos, escala de fibra
import statistics as st

print("E1. cortes comuns (grupo_comum_resultados)")
RE = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "grupo_comum_resultados", "*.json")))]
if RE:
    exE = []
    for r in RE:
        assert abs(r["TP0"] - (r["L_P"] / VC + r["AP"] / VA)) <= 1e-9 * r["TP0"], "T_P(0) guardado difere de L_P/v_c + A_P/v_a"
        if r["status"] != "exato":
            continue
        cG = r["L"] / VC + r["AG"] / VA
        assert abs(cG - r["cG"]) <= 1e-9 * cG
        tc = r["t_c"]
        if r["trilha"]:
            ant = r["trilha"][-2] if len(r["trilha"]) > 1 else r["trilha"][0]
            assert abs((cG - ant["c"]) / (ant["R"] - r["R_min"]) - tc) <= 1e-9, "t_c^G nao e a raiz da reta do plano anterior"
        pts = {}
        for k, p in r["pontos"].items():
            if "M" in p:
                TP = r["TP0"] + p["t"] * r["n"]
                assert abs(p["T_P"] - TP) <= 1e-9 * TP
                pts[k] = dict(SG=100 * ((cG + p["t"] * r["R_min"]) - p["M"]) / TP, Scc=100 * (TP - (cG + p["t"] * r["R_min"])) / TP, St=100 * (TP - p["M"]) / TP)
        exE.append(dict(tc=tc, rho=tc * VA * r["R_min"] / r["L"], razao=tc / ((r["AG"] - r["As"]) / VA) if r["AG"] > r["As"] else None, pts=pts))
    confere("gcN", len(RE), 0)
    confere("gcExact", len(exE), 0)
    confere("gcNoProof", len(RE) - len(exE), 0)
    if exE:
        confere("gcTcMed", st.median(x["tc"] for x in exE), 3)
        confere("gcTcMax", max(x["tc"] for x in exE), 3)
        confere("gcRhoMed", st.median(x["rho"] for x in exE))
        confere("gcRhoMax", max(x["rho"] for x in exE))
        confere("gcRatioMed", st.median(x["razao"] for x in exE if x["razao"] is not None))
        confere("gcSgZMed", st.median(x["pts"]["0"]["SG"] for x in exE))
        confere("gcSgZMax", max(x["pts"]["0"]["SG"] for x in exE))
        confere("gcSccCMed", st.median(x["pts"]["1"]["Scc"] for x in exE if "1" in x["pts"]), 1)
        confere("gcSccCMin", min(x["pts"]["1"]["Scc"] for x in exE if "1" in x["pts"]), 1)
        confere("gcSccCMax", max(x["pts"]["1"]["Scc"] for x in exE if "1" in x["pts"]), 1)
        confere("gcSccZMed", st.median(x["pts"]["0"]["Scc"] for x in exE), 1)
        confere("gcSgANil", sum(1 for x in exE if "0.25" in x["pts"] and x["pts"]["0.25"]["SG"] <= 1e-5), 0)
        # decomposicao: S_total = S_cc + S_G em cada ponto
        assert all(abs(p["St"] - (p["Scc"] + p["SG"])) <= 1e-9 for x in exE for p in x["pts"].values()), "a decomposicao nao fecha"
print("E2. layouts novos (confirmacao_novos_resultados)")
RF = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "confirmacao_novos_resultados", "*.json")))]
if RF:
    exF = []
    for r in RF:
        if r["status"] != "exato":
            continue
        P0 = r["L"] / VC + r["AP"] / VA
        assert abs(P0 - r["P0"]) <= 1e-9 * P0
        tc = r["t_c"]
        S = {k: 100 * (P0 + p["t"] * r["n"] - p["M"]) / (P0 + p["t"] * r["n"]) for k, p in r["pontos"].items() if "M" in p}
        if r["trilha"]:
            ant = r["trilha"][-2] if len(r["trilha"]) > 1 else r["trilha"][0]
            assert abs((P0 - ant["c"]) / (ant["R"] - r["n"]) - tc) <= 1e-9, "t_c nao e a raiz da reta do plano anterior"
        exF.append(dict(tc=tc, rho=tc * VA * r["n"] / r["L"], razao=tc / r["t_cert"], S=S, cert=r["t_cert"]))
    confere("nlN", len(RF), 0)
    confere("nlExact", len(exF), 0)
    if exF:
        confere("nlTcMed", st.median(x["tc"] for x in exF), 3)
        confere("nlTcMin", min(x["tc"] for x in exF), 3)
        confere("nlTcMax", max(x["tc"] for x in exF), 3)
        confere("nlRhoMed", st.median(x["rho"] for x in exF))
        confere("nlRhoMin", min(x["rho"] for x in exF))
        confere("nlRhoMax", max(x["rho"] for x in exF))
        confere("nlRatioMed", st.median(x["razao"] for x in exF))
        confere("nlRatioMax", max(x["razao"] for x in exF))
        confere("nlCertMed", st.median(x["cert"] for x in exF))
        confere("nlSZMed", st.median(x["S"]["0"] for x in exF))
        confere("nlSZMax", max(x["S"]["0"] for x in exF))
        confere("nlSVMed", st.median(x["S"]["0.03"] for x in exF if "0.03" in x["S"]))
        confere("nlSANil", sum(1 for x in exF if "0.25" in x["S"] and x["S"]["0.25"] <= 1e-5), 0)
print("E3. escala de fibra (fibra_aninhados_resultados)")
G1 = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "fibra_aninhados_resultados", "g1_*.json")))]
G2 = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "fibra_aninhados_resultados", "g2_*.json")))]


def eco_fibra(r, tpp, vc_mmin):
    vc, va = vc_mmin * 1000.0 / 60.0, 140.0 * 1000.0 / 60.0
    tl = float(tpp) * VA / va
    m = r["seg"][tpp]
    Ts = r["L_segmento"] / vc + m["ar"] / va + tl * m["n_perf"]
    AP = (r["fo_contorno_media"] - r["L_pecas"] / VC) * VA
    Tc = r["L_pecas"] / vc + AP / va + tl * min(r["n_contornos"], m["n_perf"])
    return 100 * (Tc - Ts) / Tc, 100 * (AP / va) / Tc


if G1 and all(all(k in r["seg"] and r["seg"][k] for k in ("0", "0.06", "0.25", "1")) for r in G1):
    confere("fbN", len(G1), 0)
    for vc_m, tag in ((15, ""), (30, "Th")):
        for tpp, s in (("0", "Z"), ("0.06", "S"), ("0.25", "A"), ("1", "C")):
            e = [eco_fibra(r, tpp, vc_m)[0] for r in G1]
            confere(f"fbMed{tag}{s}", st.median(e), 3)
            confere(f"fbMax{tag}{s}", max(e), 3)
    confere("fbAirS", st.median(eco_fibra(r, "0.06", 15)[1] for r in G1))
if G2 and all(all(k in r["seg"] and r["seg"][k] for k in ("0", "0.06", "0.25", "1")) for r in G2):
    confere("fbNdense", len(G2), 0)
    for tpp, s in (("0", "Z"), ("0.06", "S"), ("0.25", "A"), ("1", "C")):
        e = [eco_fibra(r, tpp, 15)[0] for r in G2]
        confere(f"fbDenMed{s}", st.median(e), 3)
        confere(f"fbDenMax{s}", max(e), 3)
    confere("fbDenAirS", st.median(eco_fibra(r, "0.06", 15)[1] for r in G2))

print("E4. PCGLNS de arcos contra o exato (heuristica_vs_exato_resultados)")
RH = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "heuristica_vs_exato_resultados", "*.json")))]
exc, lac, cap = [], [], []
for r in RH:
    for t, c in r["casos"].items():
        h = c["h"]
        if not h:
            continue
        nc_h, nc_x = h["fo"] - r["L_segmento"] / VC, c["M"] - r["L_segmento"] / VC
        exc.append(100 * (nc_h - nc_x) / nc_x)
        lac.append(100 * (h["fo"] - c["M"]) / c["T_P"])
        S = c["T_P"] - c["M"]
        if S > 1e-3 * c["T_P"]:
            cap.append((c["T_P"] - h["fo"]) / S)
if exc:
    confere("hvLay", len(RH), 0)
    confere("hvN", len(exc), 0)
    confere("hvMed", st.median(exc), 2)
    confere("hvMax", max(exc), 2)
    confere("hvWfive", sum(1 for x in exc if x <= 5.0), 0)
    confere("hvOpt", sum(1 for x in exc if x <= 1e-6), 0)
    confere("hvGapMed", st.median(lac), 3)
    confere("hvGapMax", max(lac), 3)
    if cap:
        confere("hvCapN", len(cap), 0)
        confere("hvCapMed", st.median(cap), 2)

print("\nRESULTADO: " + ("tudo coincide com o manuscrito" if not FALHAS else "DIFERENCAS em " + ", ".join(FALHAS)))
sys.exit(0 if not FALHAS else 1)
