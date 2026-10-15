"""
gerar_tabelas_n1.py  --  tabelas e macros do manuscrito N1 (nivel de segmento: distancia ao otimo, FO honesta e custo de reinicio), geradas dos arquivos de resultado (nada digitado a mao)
==========================================================================================================================================================================================
Entradas (caso_a_corte_multitecnologia/): auditoria_lcpp1/caminhos_282 (caminhos da heuristica do LCPP), auditoria_lcpp1/honesta_282 (PCGLNS por peca honesto), lcpp1_segmento_resultados (GTSP de arcos, t = 0),
rpp_lcpp1_resultados (RPP exato), v3_resultados (V3; so se existir). Saidas: manuscrito/N1/tabelas/n1_*.tex e manuscrito/N1/numeros_n1.tex.
Uso: python gerar_tabelas_n1.py
"""
import os
import sys
import json
import glob
import statistics

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
A = os.path.join(RAIZ, "caso_a_corte_multitecnologia")
sys.path.insert(0, A)
sys.path.insert(0, os.path.join(RAIZ, "src_base"))
os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
import avaliar_heuristica_formal as af                       # noqa: E402
from heuristic_core import _DEFAULT_CONFIG as D              # noqa: E402

VC, VA = D["v_cut"], D["v_air"]
TAB = os.path.join(AQUI, "N1", "tabelas")
os.makedirs(TAB, exist_ok=True)
MACROS = {}
TS = (0.25, 0.5, 1.0)


def pct(a, b):
    return 100.0 * (a / b - 1.0)


def fmt(x, casas=2, sinal=True):
    s = f"{x:+.{casas}f}" if sinal else f"{x:.{casas}f}"
    return s.replace("-", "$-$") + r"\%"


def carregar_282():
    L = []
    for n, r in sorted(af.carregar().items()):
        try:
            g = json.load(open(os.path.join(A, "lcpp1_segmento_resultados", f"{n}.json")))
            h = json.load(open(os.path.join(A, "auditoria_lcpp1", "honesta_282", f"{n}.json")))
        except FileNotFoundError:
            continue
        if not g.get("melhor") or "fo_pcglns_honesta" not in h:
            continue
        cam = r["forte"]
        pol = af.fo_poligonal(cam, 0.0)
        x = {"nome": n, "listada": r["fo_listada_forte"], "poli": pol["fo"], "saltos": pol["saltos"], "peca": h["fo_pcglns_honesta"], "gtsp": g["melhor"]["fo"], "R0": g["melhor"]["n_perf"], "nc": g["n_contornos"],
             "t_gtsp": g.get("tempo_total_s", float("nan")), "t_heur": r.get("tempo_s", float("nan"))}
        for t in (0.0,) + TS:
            f = af.fo_formal(cam, t)
            x[f"H{t}"], x[f"R{t}"], x[f"ret{t}"], x[f"virg{t}"] = f["fo"], f["corridas"], f["retomadas"], f["virgens"]
        L.append(x)
    return L


def tabela_convencoes(L):
    linhas = [("Heuristic (executable path) vs.\\ contour-level PCGLNS", "poli", "peca"), ("Heuristic (formal objective) vs.\\ contour-level PCGLNS", "H0.0", "peca"),
              ("Heuristic (formal objective) vs.\\ arc-GTSP + PCGLNS", "H0.0", "gtsp"), ("Heuristic (executable path) vs.\\ arc-GTSP + PCGLNS", "poli", "gtsp")]
    T = [r"\begin{table}[t]", r"\centering\small",
         r"\caption{The LCPP heuristic under two cost conventions on the " + str(len(L)) + r" synthetic instances (restart cost zero). Relative difference of the total objective; negative favours the first method; wins = instances where it is strictly lower. Executable path: jumps between non-contiguous segments are counted; formal objective: direct chord between consecutive cutting operations (Eq.~3 of the LCPP-1 model).}",
         r"\label{tab:n1_conv}", r"\begin{tabular}{lrrr}", r"\toprule", r"Comparison & Median & Mean & Wins \\", r"\midrule"]
    for nome, a, b in linhas:
        d = np.array([pct(x[a], x[b]) for x in L])
        T.append(f"{nome} & {fmt(np.median(d), 3)} & {fmt(d.mean(), 3)} & {int((d < 0).sum())}/{len(d)} " + r"\\")
    T += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_convencoes.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")
    dp = np.array([pct(x["poli"], x["peca"]) for x in L])
    df = np.array([pct(x["H0.0"], x["peca"]) for x in L])
    dg = np.array([pct(x["H0.0"], x["gtsp"]) for x in L])
    perd = [x for x, v in zip(L, dp) if v >= 0]
    MACROS["perdasPoli"] = str(len(perd))
    MACROS["perdasPoliHole"] = str(sum(1 for x in perd if "_hole_" in x["nome"]))
    perdf = [x for x, v in zip(L, df) if v >= 0]
    MACROS["perdasFormal"] = str(len(perdf))
    MACROS["perdasFormalHole"] = str(sum(1 for x in perdf if "_hole_" in x["nome"]))
    MACROS["medSaltos"] = f"{np.median([x['saltos'] for x in L]):.0f}"
    MACROS["tempoGtsp"] = f"{np.nanmedian([x['t_gtsp'] for x in L]):.0f}"
    MACROS.update({"nInstL": str(len(L)), "winsPoli": str(int((dp < 0).sum())), "winsFormal": str(int((df < 0).sum())), "winsGtsp": str(int((dg < 0).sum())),
                   "medPoli": fmt(np.median(dp), 2), "medFormal": fmt(np.median(df), 2), "meanPoli": fmt(dp.mean(), 2), "meanFormal": fmt(df.mean(), 2), "medHeurGtsp": fmt(np.median(dg), 2),
                   "listadaSub": fmt(np.median([pct(x["poli"], x["listada"]) for x in L]), 2, sinal=True), "formalVsPoli": fmt(np.median([pct(x["H0.0"], x["poli"]) for x in L]), 3)})


def tabela_reinicio(L):
    T = [r"\begin{table}[t]", r"\centering\small",
         r"\caption{Effect of a restart cost $t$ (seconds per interruption of the cut) on the " + str(len(L)) + r" synthetic instances. The heuristic keeps its service order and only its orientations are re-optimised for each $t$; the contour-level cost is the $t=0$ value plus $t$ per contour; the arc-GTSP route is the $t=0$ solution evaluated at $t$ (an upper bound for the restart-aware optimum). Median relative differences of total time (negative favours the first), and instances where the first is lower.}",
         r"\label{tab:n1_t}", r"\begin{tabular}{rrrrrr}", r"\toprule",
         r"$t$ (s) & Runs: heur./arc-GTSP/contours & Heur.\ vs piece & Wins & Heur.\ vs arc-GTSP$_{0}$ & Arc-GTSP$_{0}$ vs piece \\", r"\midrule"]
    for t in (0.0,) + TS:
        hp = np.array([pct(x[f"H{t}"], x["peca"] + t * x["nc"]) for x in L])
        hg = np.array([pct(x[f"H{t}"], x["gtsp"] + t * x["R0"]) for x in L])
        gp = np.array([pct(x["gtsp"] + t * x["R0"], x["peca"] + t * x["nc"]) for x in L])
        runs = f"{np.median([x[f'R{t}'] for x in L]):.0f}/{np.median([x['R0'] for x in L]):.0f}/{np.median([x['nc'] for x in L]):.0f}"
        T.append(f"{t:g} & {runs} & {fmt(np.median(hp), 2)} & {int((hp < 0).sum())}/{len(L)} & {fmt(np.median(hg), 2)} & {fmt(np.median(gp), 2)} " + r"\\")
        letra = {0.0: "Z", 0.25: "A", 0.5: "B", 1.0: "C"}[t]                      # nomes de macro so com letras
        MACROS[f"hg{letra}"] = fmt(np.median(hg), 1)
        MACROS[f"hp{letra}"] = fmt(np.median(hp), 1)
        MACROS[f"hpw{letra}"] = str(int((hp < 0).sum()))
    T += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_reinicio.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")
    # ponto de equilibrio por instancia (heuristica x peca), com as corridas de t = 0,25 s
    te = [(x["peca"] - x["H0.0"]) / (x["R0.25"] - x["nc"]) for x in L if x["R0.25"] > x["nc"] and x["peca"] > x["H0.0"]]
    MACROS["tEquilibrio"] = f"{statistics.median(te):.3f}" if te else "n/a"
    if te:                                                    # custo de reinicio expresso como comprimento de corte equivalente (t x v_corte), em unidades do desenho
        MACROS["tEqEquil"] = f"{statistics.median(te) * VC:.1f}"
        MACROS["tEqAirEquil"] = f"{statistics.median(te) * VA:.0f}"                     # o equilibrio expresso como distancia de voo equivalente (t* x v_voo)
    MACROS["tEqA"] = f"{0.25 * VC:.1f}"
    MACROS["tEqC"] = f"{1.0 * VC:.1f}"
    MACROS["vCutLCPP"] = f"{VC:.1f}"
    MACROS["corridasHeur"] = f"{np.median([x['R0.0'] for x in L]):.0f}"
    MACROS["corridasContornos"] = f"{np.median([x['nc'] for x in L]):.0f}"
    ret = np.array([x["ret0.0"] / max(1, x["ret0.0"] + x["virg0.0"]) for x in L])
    MACROS["fracRetomadas"] = f"{100 * np.median(ret):.1f}\\%"


def tabela_otimo(L):
    R = []
    for f in sorted(glob.glob(os.path.join(A, "rpp_lcpp1_resultados", "*.json"))):
        r = json.load(open(f))
        n = r["instancia"]
        if not r["resolvida"]:
            continue
        x = next((y for y in L if y["nome"] == n), None)
        try:
            g = json.load(open(os.path.join(A, "lcpp1_segmento_resultados", f"{n}.json")))["melhor"]
            cam = json.load(open(os.path.join(af.CAM, f"{n}.json")))["forte"]
        except FileNotFoundError:
            continue
        if x is None:
            continue
        cut = r["corte_comprimento"] / VC
        hf = af.fo_formal(cam, 0.0)
        R.append({"hole": "_hole_" in n, "ar_opt": r["ar_otimo"] / VA, "ar_h": hf["ar"], "ar_g": g["ar"] / VA, "ar_p": x["peca"] - cut, "LB": cut + r["ar_otimo"] / VA, "H": hf["fo"], "G": g["fo"], "P": x["peca"]})
    n_total = len(glob.glob(os.path.join(A, "rpp_lcpp1_resultados", "*.json")))
    T = [r"\begin{table}[t]", r"\centering\footnotesize",
         r"\caption{Distance to the exact optimum of the segment-level problem without precedence (MILP, restart cost zero) on small instances (at most 110 vertices after noding; " + f"{len(R)} of {n_total}" +
         r" solved within 600\,s). Without nesting the exact value is the optimum of the LCPP-1 problem; for layouts with holes it is a lower bound. Air time gap: median (maximum) over instances; at optimum: gap $\le 0.01\%$.}",
         r"\label{tab:n1_opt}", r"\begin{tabular}{llrrrr}", r"\toprule", r"Layouts & Method & Air gap, median & Air gap, max & At optimum & Total gap, median \\", r"\midrule"]
    for rot, S in (("No nesting\\\\(optimum)", [x for x in R if not x["hole"]]), ("With holes\\\\(lower bound)", [x for x in R if x["hole"]])):
        if not S:
            continue
        for k, (nome, ka, kf) in enumerate((("LCPP heuristic", "ar_h", "H"), ("Arc-GTSP + PCGLNS", "ar_g", "G"), ("Contour-level PCGLNS", "ar_p", "P"))):
            a = np.array([pct(x[ka], x["ar_opt"]) for x in S if x["ar_opt"] > 1e-9])
            fo = np.array([pct(x[kf], x["LB"]) for x in S])
            pre = rf"\multirow{{3}}{{*}}{{\shortstack[l]{{{rot}, $n={len(S)}$}}}}" if k == 0 else ""
            T.append(f"{pre} & {nome} & {fmt(np.median(a), 2)} & {fmt(a.max(), 1)} & {int((a <= 0.01).sum())}/{len(a)} & {fmt(np.median(fo), 3)} " + r"\\")
            if rot.startswith("No"):
                tag = {"ar_h": "Heur", "ar_g": "Gtsp", "ar_p": "Peca"}[ka]
                MACROS[f"otAr{tag}"] = fmt(np.median(a), 2)
                MACROS[f"otFo{tag}"] = fmt(np.median(fo), 3)
                MACROS[f"otN{tag}"] = f"{int((a <= 0.01).sum())}/{len(a)}"
        T.append(r"\midrule")
    T[-1] = r"\bottomrule"
    T += [r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_otimo.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")
    MACROS["nRppResolvidas"] = str(len(R))
    MACROS["nRppTotal"] = str(n_total)
    MACROS["nRppTotalMinusSolved"] = str(n_total - len(R))
    MACROS["nRppSemPi"] = str(len([x for x in R if not x["hole"]]))


def tabela_v2():
    """V2 (CPPLib, confirmatorio, docs/17): numeros extraidos de RESULTADOS_V2_ANALISE.md (gerado por analise_v2.py, escrito antes dos dados)."""
    import re
    txt = open(os.path.join(A, "RESULTADOS_V2_ANALISE.md"), encoding="utf-8").read()
    g = lambda pat, k=1: re.search(pat, txt).group(k)
    n = g(r"\*\*analisados: (\d+)\*\*")
    viab = g(r"\*\*(\d+/\d+)\*\* = [\d.]+%")
    lo, hi = g(r"IC 95% bootstrap da mediana \[([\d.]+)%; ([\d.]+)%\]", 1), g(r"IC 95% bootstrap da mediana \[([\d.]+)%; ([\d.]+)%\]", 2)
    ar = re.search(r"H-V2 .*?mediana \*\*([\d.]+)%\*\*", txt, re.S).group(1)
    wins_ar = re.search(r"Segmento menor em (\d+/\d+)", txt).group(1)
    tot = g(r"Segmento ≤ peça em \*\*(\d+/\d+)\*\*")
    gap = g(r"Gap de FO \(mediana\): ([-\d.]+)%")
    reg, regmax = re.search(r"mediana \*\*([\d.]+)%\*\* \(máx\. ([\d.]+)%\)", txt).groups()
    vant = g(r"Mediana ([+\-\d.]+)% \(IC 95%")
    perf0, perf1, nc = re.search(r"Mediana de perfurações: t = 0: (\d+); t = 1 s: (\d+); contornos: (\d+)", txt).groups()
    menos = g(r"Menos perfurações com t = 1 s que com t = 0 em \*\*(\d+/\d+)\*\*")
    MACROS.update({"nVtwo": n, "vtwoViab": viab, "vtwoAr": ar + r"\%", "vtwoArLo": lo + r"\%", "vtwoArHi": hi + r"\%", "vtwoArWins": wins_ar, "vtwoTot": tot, "vtwoGap": fmt(float(gap), 2),
                   "vtwoRegret": reg + r"\%", "vtwoRegretMax": regmax + r"\%", "vtwoVant": fmt(float(vant), 2), "vtwoPerfZero": perf0, "vtwoPerfUm": perf1, "vtwoContornos": nc, "vtwoMenos": menos})
    T = [r"\begin{table}[t]", r"\centering\small",
         r"\caption{Confirmatory CPPLib set (pre-specified before any data was generated; " + n + r" layouts of categories never used in development). Segment-level routes with closing precedence against the contour-level PCGLNS reference. Restart cost $t$ in seconds.}",
         r"\label{tab:n1_v2}", r"\begin{tabular}{p{5.2cm}p{3.4cm}p{4.6cm}}", r"\toprule", r"Pre-specified hypothesis & Criterion & Result \\", r"\midrule",
         rf"Feasible verified solutions & $\ge 95\%$ & {viab} \\",
         rf"Air-time reduction vs.\ contour level ($t=0$) & median $\ge 20\%$ & {ar}\% (95\% CI [{lo}\%; {hi}\%]); lower in {wins_ar} \\",
         rf"Total time vs.\ contour level ($t=0$) & lower in $\ge 75\%$ & lower in {tot}; median {fmt(float(gap), 2)} \\",
         rf"Regret of the $t=0$ route used at $t=1$ & median $\ge 0.2\%$ & {reg}\% (max {regmax}\%) \\",
         rf"Fewer restarts when $t=1$ (descriptive) & $\ge 80\%$ of layouts & {menos}; median {perf0} $\to$ {perf1} (contours: {nc}) \\",
         rf"Advantage over contour level at $t=1$ (descriptive) & within $\pm 0.1\%$ & median {fmt(float(vant), 2)} \\",
         r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_v2.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")


def tabela_v3():
    """V3 (docs/19): tabela e macros a partir de analise_v3.carregar(); so se houver resultados de V3 em t = 1,0 (caso contrario nao gera nada e o texto mantem o \\pending)."""
    import analise_v3 as av
    L = [x for x in av.carregar() if x["R"] is not None]
    S = [x for x in L if x["t"] == 1.0]
    if not S:
        for f in ("n1_v3.tex",):
            p = os.path.join(TAB, f)
            if os.path.exists(p):
                os.remove(p)
        return
    T = [r"\begin{table}[t]", r"\centering\small",
         r"\caption{Restart-aware routes on a stratified sample of the synthetic instances (protocol fixed before the data). Median relative differences of total time at restart cost $t$; $G(t)$ is the arc-based solution computed with restart cost $t$, $G_0(t)$ the $t=0$ route evaluated at $t$, $B(t)=\min(G,G_0)$ the best verified segment-level solution, $H(t)$ the LCPP heuristic (formal objective) and $P(t)$ the contour-level reference.}",
         r"\label{tab:n1_v3}", r"\begin{tabular}{rrrrrr}", r"\toprule", r"$t$ (s) & $n$ & runs $G_0\to G$ & $G_0/B-1$ & $H/B-1$ & $B/P-1$ \\", r"\midrule"]
    for t in (0.25, 1.0):
        U = [x for x in L if x["t"] == t]
        if not U:
            continue
        reg = np.array([pct(x["G0"], x["B"]) for x in U])
        hx = np.array([pct(x["H"], x["B"]) for x in U])
        bp = np.array([pct(x["B"], x["P"]) for x in U])
        runs = f"{np.median([x['R0'] for x in U]):.0f}$\\to${np.median([x['R'] for x in U]):.0f}"
        T.append(f"{t:g} & {len(U)} & {runs} & {fmt(np.median(reg), 2)} & {fmt(np.median(hx), 2)} & {fmt(np.median(bp), 2)} " + r"\\")
        letra = "A" if t == 0.25 else "C"
        MACROS[f"vtreeReg{letra}"] = fmt(np.median(reg), 2)
        MACROS[f"vtreeHeur{letra}"] = fmt(np.median(hx), 2)
        MACROS[f"vtreeBP{letra}"] = fmt(np.median(bp), 2)
        MACROS[f"vtreeBPwins{letra}"] = f"{int((bp < 0).sum())}/{len(U)}"
    T += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_v3.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")
    MACROS["nVtree"] = str(len(S))


def tabela_reparo():
    """Reparo ciente do reinicio da heuristica (docs/23): tabela e macros a partir de analise_reparo.carregar()."""
    import analise_reparo as ar
    L = ar.carregar()
    if not [x for x in L if x["t"] == 1.0]:
        p = os.path.join(TAB, "n1_reparo.tex")
        if os.path.exists(p):
            os.remove(p)
        return
    T = [r"\begin{table}[t]", r"\centering\small",
         r"\caption{Restart-aware repair of the heuristic (pre-specified; same sample as Table~\ref{tab:n1_v3}). Median relative differences of total time at restart cost $t$: the heuristic (H) and the repaired route (Rep) against the best verified segment-level solution $B$ and against the contour-level reference $P$; the fraction of the excess $H-B$ that the repair removes; median search time of the repair (the heuristic itself takes 3\,s).}",
         r"\label{tab:n1_rep}", r"\begin{tabular}{rrrrrrrr}", r"\toprule", r"$t$ (s) & $n$ & runs H$\to$Rep & $H/B-1$ & Rep$/B-1$ & excess removed & Rep$/P-1$ & search (s) \\", r"\midrule"]
    for t in (0.25, 1.0):
        U = [x for x in L if x["t"] == t]
        if not U:
            continue
        hb = np.array([pct(x["Hr"], x["B"]) for x in U])
        rb = np.array([pct(x["Rep"], x["B"]) for x in U])
        rp = np.array([pct(x["Rep"], x["P"]) for x in U])
        rec = np.array([100 * (x["Hr"] - x["Rep"]) / (x["Hr"] - x["B"]) for x in U if x["Hr"] - x["B"] > 1e-9])
        runs = f"{np.median([x['Rh'] for x in U]):.0f}$\\to${np.median([x['Rrep'] for x in U]):.0f}"
        tb = np.median([x["tb"] for x in U])
        T.append(f"{t:g} & {len(U)} & {runs} & {fmt(np.median(hb), 2)} & {fmt(np.median(rb), 2)} & {np.median(rec):.0f}\\% & {fmt(np.median(rp), 2)} & {tb:.1f} " + r"\\")
        letra = "A" if t == 0.25 else "C"
        MACROS[f"rep{letra}"] = fmt(np.median(rb), 2)
        MACROS[f"repHb{letra}"] = fmt(np.median(hb), 2)
        MACROS[f"repRec{letra}"] = f"{np.median(rec):.0f}" + r"\%"
        MACROS[f"repP{letra}"] = fmt(np.median(rp), 2)
        MACROS[f"repT{letra}"] = f"{tb:.1f}"
        MACROS[f"repOk{letra}"] = f"{sum(1 for x in U if x['ok'])}/{len(U)}"
        MACROS[f"repConv{letra}"] = f"{sum(1 for x in U if x['conv'])}/{len(U)}"
    T += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_reparo.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")


def tabela_voo():
    """Rotas guardadas sob tempos de voo nao lineares (docs/25): tabela e macros a partir de analise_voo_nao_linear (sem reotimizar)."""
    p = os.path.join(A, "auditoria_lcpp1", "pecas_caminhos")
    if not os.path.isdir(p) or not os.listdir(p):
        return
    import analise_voo_nao_linear as vn
    L = vn.carregar()
    if not L:
        return
    nomes = {"H": "Heuristic", "Rep1.0": "Heuristic + repair ($t=1$)", "G1.0": "Restart-aware arc-GTSP ($t=1$)"}
    perfis = (("LIN", "Linear"), ("LASER", "Trapezoidal, fast"), ("DEWIL16", "Dewil et al.\\ curve"))
    T = [r"\begin{table}[t]", r"\centering\small",
         r"\caption{Stored routes under different air-move time models, restart cost zero, without re-optimisation (exploratory; " + str(len(L)) + r" synthetic instances). Median of the relative difference of the total time of each segment-level route to the contour-level route ($T/T_P-1$). Linear: 400 drawing units per second, the convention of the benchmark; trapezoidal: $v=1667$, $a=10^4$ units per second (squared); Dewil et al.\ curve: time of an air move read off, approximately, from the plot of \citet{dewil2016review} for a 4\,kW CO$_2$ machine, taking one drawing unit as one millimetre.}",
         r"\label{tab:n1_voo}", r"\begin{tabular}{lrrr}", r"\toprule", r"Route & " + " & ".join(n for _, n in perfis) + r" \\", r"\midrule"]
    for r, nm in nomes.items():
        cel = []
        for perfil, _ in perfis:
            x = np.array([100 * (vn.total(R[r], perfil, 0.0) / vn.total(R["P"], perfil, 0.0) - 1) for _, R, _ in L])
            cel.append(fmt(np.median(x), 2))
            MACROS[f"voo{r.replace('.', '').replace('Rep10', 'Rep').replace('G10', 'Gc')}{perfil[:3]}"] = fmt(np.median(x), 2)
        T.append(f"{nm} & " + " & ".join(cel) + r" \\")
    nm_ = lambda r: np.median([len(R[r][1]) for _, R, _ in L])
    MACROS.update({"vooMovP": f"{nm_('P'):.0f}", "vooMovH": f"{nm_('H'):.0f}", "vooMovG": f"{nm_('G1.0'):.0f}",
                   "vooArLinP": f"{np.median([float(vn.tau(R['P'][1], 'LIN').sum()) for _, R, _ in L]):.1f}", "vooArDewP": f"{np.median([float(vn.tau(R['P'][1], 'DEWIL16').sum()) for _, R, _ in L]):.1f}",
                   "vooNvoo": str(len(L))})
    T += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_voo.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")


def tabela_tau():
    """Os dois niveis reotimizados para a curva de voo (docs/26): tabela e macros a partir de tau_resultados/ (a decomposicao por corte compartilhado e exploratoria, nao pre-registrada)."""
    d = os.path.join(A, "tau_resultados")
    if not os.path.isdir(d) or len(os.listdir(d)) < 300:
        return
    import rodar_v3 as rv
    T = [r"\begin{table}[t]", r"\centering\small",
         r"\caption{Both levels re-optimised for the air-move time model (restart cost zero; " + "60" + r" synthetic instances; PCGLNS). Median of the relative difference of the total time of the segment-level solution to the contour-level solution ($S/P-1$), over all instances, over those in which both levels cut the same length (routing effect only), and over those with shared edges, where the segment level cuts each shared edge once (a modelling effect, decided before any routing). Air time is that of the same-length group.}",
         r"\label{tab:n1_tau}", r"\begin{tabular}{lrrrr}", r"\toprule", r"Air-move time model & All & Same cut length & Shared edges & Air time (same cut) \\", r"\midrule"]
    for perfil, nome, sfx in (("LASER", "Trapezoidal, fast", "Las"), ("DEWIL16", "Dewil et al.\\ curve", "Dew")):
        S = []
        for n in rv.amostra():
            s = json.load(open(os.path.join(d, f"segmento_{perfil}_{n}.json")))["melhor"]
            p = json.load(open(os.path.join(d, f"peca_{perfil}_{n}.json")))
            S.append((s["T"][perfil], p["T"][perfil], s["corte_s"], p["corte_s"], s["n_movimentos"], p["n_movimentos"]))
        todos = [pct(a, b) for a, b, *_ in S]
        ig = [x for x in S if abs(x[2] - x[3]) <= 1e-6 * max(1.0, x[3])]
        co = [x for x in S if x not in ig]
        r_ig = [pct(a, b) for a, b, *_ in ig]
        r_co = [pct(a, b) for a, b, *_ in co]
        ar = [pct(a - c, b - e) for a, b, c, e, *_ in ig if b - e > 1e-9]
        T.append(f"{nome} & {fmt(np.median(todos), 2)} & {fmt(np.median(r_ig), 2)} ({sum(1 for x in r_ig if x < -1e-9)}/{len(ig)}) & {fmt(np.median(r_co), 2)} ({len(co)}) & {fmt(np.median(ar), 1)} " + r"\\")
        MACROS.update({f"tau{sfx}All": fmt(np.median(todos), 2), f"tau{sfx}Same": fmt(np.median(r_ig), 2), f"tau{sfx}SameWins": f"{sum(1 for x in r_ig if x < -1e-9)}/{len(ig)}",
                       f"tau{sfx}Shared": fmt(np.median(r_co), 1), f"tau{sfx}Ar": fmt(np.median(ar), 1), f"tau{sfx}Wins": f"{sum(1 for x in todos if x < -1e-9)}/{len(S)}",
                       f"tau{sfx}MovS": f"{np.median([x[4] for x in S]):.0f}", f"tau{sfx}MovP": f"{np.median([x[5] for x in S]):.0f}"})
        MACROS["tauNShared"] = str(len(co))
        MACROS["tauNSame"] = str(len(ig))
    T += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_tau.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")


def macros_fendas_resultados():
    """Fendas abertas incluidas (docs/28 §3): numeros extraidos de RESULTADOS_FENDAS_ANALISE.md (analise_fendas.py, escrita antes dos dados)."""
    import re
    p = os.path.join(A, "RESULTADOS_FENDAS_ANALISE.md")
    if not os.path.exists(p):
        return
    t = open(p, encoding="utf-8").read()
    m1 = re.search(r"mediana \*\*([+\-\d.]+)%\*\* \(IC 95% \[([+\-\d.]+)%; ([+\-\d.]+)%\]; máx\. ([+\-\d.]+)%\)\.\n- Fendas", t)
    m2 = re.search(r"redução mediana do ar \*\*([\d.]+)%\*\*.*?tempo total mediano \*\*([+\-\d.]+)%\*\*.*?segmento ≤ peça em \*\*(\d+/\d+)\*\*", t, re.S)
    m3 = re.search(r"A t = 1 s \(n = \d+\):\*\* segmento × peça, tempo total mediano \*\*([+\-\d.]+)%\*\*", t)
    m4 = re.search(r"COM fendas: t = 0: (\d+/\d+), t = 1 s: (\d+/\d+)", t)
    if not (m1 and m2 and m3 and m4):
        return
    MACROS.update({"fdAr": f"{float(m1.group(1)):.0f}" + r"\%", "fdRed": m2.group(1) + r"\%", "fdTot": fmt(float(m2.group(2)), 2), "fdWins": m2.group(3), "fdTc": fmt(float(m3.group(1)), 2),
                   "fdViabZ": m4.group(1), "fdViabC": m4.group(2)})


def macros_rpp_cpplib():
    """RPP exato nas layouts pequenas do CPPLib (docs/28 §2): limite inferior do problema com Pi de fechamento contra o ar do GTSP de arcos (t = 0)."""
    d = os.path.join(A, "rpp_cpplib_resultados")
    if not os.path.isdir(d):
        return
    R = [json.load(open(os.path.join(d, f))) for f in sorted(os.listdir(d))]
    ok, gaps = [], []
    for r in R:
        g = os.path.join(A, "segmento_resultados", f"seg_{r['instancia']}_t0.json")
        if r["resolvida"] and os.path.exists(g):
            s = json.load(open(g))
            if s.get("melhor") and r["ar_otimo"] > 1e-9:
                ok.append(r)
                gaps.append(100 * (s["melhor"]["ar"] / r["ar_otimo"] - 1))
    if not gaps:
        return
    MACROS.update({"cppRppTotal": str(len(R)), "cppRppSolved": str(len(ok)), "cppRppCert": str(sum(1 for g in gaps if g <= 0.01)), "cppRppMaxGap": f"{max(gaps):.1f}" + r"\%",
                   "cppRppMaxV": str(max(r["vertices"] for r in ok))})


def tabela_mapa():
    """Mapa de regimes ancorado em fontes (docs/28): rotas guardadas em perfis de movimento de fichas de maquinas e custos de reinicio da literatura."""
    p = os.path.join(A, "auditoria_lcpp1", "pecas_caminhos")
    if not os.path.isdir(p) or not os.listdir(p):
        return
    import analise_mapa_regimes as am
    import analise_voo_nao_linear as vn
    L = vn.carregar()
    perfis = (("FIBRA_1G", r"Reference, 100\,m/min, 1.0\,g"), ("V170_1_4G", r"170\,m/min, 1.4\,g"), ("BLM_2G", r"BLM LS7, 140\,m/min, 2.0\,g"), ("SALV_5G", r"Salvagnini L5, 156\,m/min, 5\,g"), ("DEWIL16", r"CO$_2$, Dewil et al.\ curve"))
    T = [r"\begin{table}[t]", r"\centering\footnotesize",
         r"\caption{Map of regimes anchored in published data (exploratory; " + str(len(L)) + r" synthetic instances; stored routes, not re-optimised). Each cell gives the median of $T/T_P-1$ in percent for the heuristic that ignores the restart cost and for the restart-aware arc-based route ($t=0.25$\,s), against the contour-level route. Motion profiles: trapezoidal, with the speeds and accelerations that manufacturers publish (170\,m/min simultaneous speed of TRUMPF, Bystronic and Salvagnini machines with the 1.4\,g of an Amada machine \citep{trumpf3030fiber,bystronic2025bystarfiber,salvagnini2026l3g4,amada2026ensis}; the BLM LS7 \citep{blm2026ls7}; the Salvagnini L5, whose 5\,g holds on short moves of thin sheet \citep{salvagnini2026l5}), a reference of our own, and the curve of \citet{dewil2016review}. Restart costs: $t=0.01$ and $0.06$\,s bracket the breakthrough time of 2\,mm steel with a fibre laser \citep{hashemzadeh2014piercing}; $t=0.25$ and $1$\,s stand for thicker plate \citep{westmfg2018piercing,prima2015platino,garcia2019piercing}. One drawing unit is taken as one millimetre.}",
         r"\label{tab:n1_mapa}", r"\begin{tabular}{lrrrrr}", r"\toprule", r"Motion profile & $t=0$ & $t=0.01$ & $t=0.06$ & $t=0.25$ & $t=1$ \\", r"\midrule"]
    for perfil, nome in perfis:
        cel = []
        for t in am.TS:
            h = np.median([100 * (am.total(R["H"], perfil, t) / am.total(R["P"], perfil, t) - 1) for _, R, _ in L])
            g = np.median([100 * (am.total(R["G0.25"], perfil, t) / am.total(R["P"], perfil, t) - 1) for _, R, _ in L])
            cel.append(f"{h:+.2f} / {g:+.2f}".replace("-", "$-$"))
        T.append(f"{nome} & " + " & ".join(cel) + r" \\")
    fr = np.median([float(am.tau(R["P"][1], "SALV_5G").sum()) / am.total(R["P"], "SALV_5G", 0.0) for _, R, _ in L])
    fr2 = np.median([float(am.tau(R["P"][1], "FIBRA_1G").sum()) / am.total(R["P"], "FIBRA_1G", 0.0) for _, R, _ in L])
    MACROS["mapaArFrMin"] = f"{100 * fr:.1f}" + r"\%"
    MACROS["mapaArFrMax"] = f"{100 * fr2:.1f}" + r"\%"
    T += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_mapa.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")


def tabela_tau_reinicio():
    """Segmento reotimizado para tau(d) + t (docs/27): tabela e macros a partir de tau_reinicio_resultados/ e tau_resultados/ (peca, T_P(t) = T_P(0) + t x corridas)."""
    d1, d0 = os.path.join(A, "tau_reinicio_resultados"), os.path.join(A, "tau_resultados")
    if not os.path.isdir(d1) or len(os.listdir(d1)) < 240:
        return
    import rodar_v3 as rv
    T = [r"\begin{table}[t]", r"\centering\small",
         r"\caption{Segment level re-optimised for the air-move time model and for the restart cost $t$ (pre-specified; 60 synthetic instances). Median of $S_t/P_t-1$, the total time of the segment-level solution relative to the contour-level one, over all instances, over those in which both cut the same length (routing only) and over those with shared edges; wins: instances where the segment level is strictly lower; and the median excess of the route optimised for $t=0$ over the one optimised for $t$.}",
         r"\label{tab:n1_taur}", r"\begin{tabular}{llrrrr}", r"\toprule", r"Air-move model & $t$ (s) & All & Same cut (wins) & Shared edges & Excess of the $t=0$ route \\", r"\midrule"]
    for perfil, nome, sfx in (("DEWIL16", "Dewil et al.\\ curve", "Dew"), ("LASER", "Trapezoidal, fast", "Las")):
        for t, tg in ((0.25, "A"), (1.0, "C")):
            R = []
            for n in rv.amostra():
                s = json.load(open(os.path.join(d1, f"segmento_{perfil}_t{t:g}_{n}.json")))["melhor"]
                s0 = json.load(open(os.path.join(d0, f"segmento_{perfil}_{n}.json")))["melhor"]
                p = json.load(open(os.path.join(d0, f"peca_{perfil}_{n}.json")))
                R.append((s["T"], p["T"][perfil] + t * p["corridas"], s["corte_s"], p["corte_s"], s0["T"][perfil] + t * s0["corridas"], s["corridas"]))
            todos = [pct(a, b) for a, b, *_ in R]
            ig = [x for x in R if abs(x[2] - x[3]) <= 1e-6 * max(1.0, x[3])]
            co = [x for x in R if x not in ig]
            r_ig = [pct(x[0], x[1]) for x in ig]
            r_co = [pct(x[0], x[1]) for x in co]
            ex = [pct(x[4], x[0]) for x in R]
            T.append(f"{nome} & {t:g} & {fmt(np.median(todos), 3)} & {fmt(np.median(r_ig), 3)} ({sum(1 for x in r_ig if x < -1e-9)}/{len(ig)}) & {fmt(np.median(r_co), 1)} & {fmt(np.median(ex), 2)} " + r"\\")
            MACROS.update({f"tr{sfx}{tg}All": fmt(np.median(todos), 3), f"tr{sfx}{tg}Same": fmt(np.median(r_ig), 3), f"tr{sfx}{tg}Shared": fmt(np.median(r_co), 1), f"tr{sfx}{tg}Ex": fmt(np.median(ex), 2),
                           f"tr{sfx}{tg}ExMax": fmt(max(ex), 0), f"tr{sfx}{tg}Runs": f"{np.median([x[5] for x in R]):.0f}"})
    T += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_taur.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")


def macros_robustez():
    """Robustez e escala (docs/24): numeros extraidos de RESULTADOS_ROBUSTEZ.md e RESULTADOS_ESCALA.md (comparar_robustez.py e rodar_escala.py resumo)."""
    import re
    pr, pe = os.path.join(A, "RESULTADOS_ROBUSTEZ.md"), os.path.join(A, "RESULTADOS_ESCALA.md")
    if os.path.exists(pr):
        t = open(pr, encoding="utf-8").read()
        m = re.search(r"em t = 0: mediana \*\*([+\-\d.]+)%\*\*, média ([+\-\d.]+)%, \|máx\.\| ([\d.]+)%; nova rodada menor em (\d+), igual em (\d+), maior em (\d+)", t)
        if m:
            MACROS.update({"rbMax": f"{float(m.group(3)):.2f}" + r"\%", "rbMenor": m.group(4), "rbIgual": m.group(5), "rbMaior": m.group(6)})
        m = re.search(r"formal (\d+) → (\d+); poligonal (\d+) → (\d+)", t)
        if m:
            MACROS.update({"rbFormalA": m.group(1), "rbFormalB": m.group(2), "rbPoliA": m.group(3), "rbPoliB": m.group(4)})
        m = re.search(r"Melhor das sementes ÷ referência original − 1: mediana \*\*([+\-\d.]+)%\*\*, mín\. ([+\-\d.]+)%, máx\. ([+\-\d.]+)%; melhor em (\d+), igual em (\d+), pior em (\d+)", t)
        if m:
            MACROS.update({"rbPecaMin": f"{abs(float(m.group(2))):.2f}" + r"\%", "rbPecaMelhor": m.group(4), "rbPecaIgual": m.group(5)})
        m = re.search(r"sobre a referência de peça:\*\* (\d+) → (\d+) de (\d+)", t)
        if m:
            MACROS.update({"rbPecaWinsA": m.group(1), "rbPecaWinsB": m.group(2), "rbPecaN": m.group(3)})
    if os.path.exists(pe):
        t = open(pe, encoding="utf-8").read()
        m = re.search(r"Tempo total \(FO\): 600 s contra 120 s, mediana \*\*([+\-\d.]+)%\*\* \(mín\. ([+\-\d.]+)%, máx\. ([+\-\d.]+)%\); 600 s melhor em (\d+)/(\d+)", t)
        if m:
            MACROS.update({"esFo": f"{abs(float(m.group(1))):.2f}" + r"\%", "esMelhor": m.group(4), "esN": m.group(5)})
        m = re.search(r"Tempo de \*\*ar\*\*: mediana \*\*([+\-\d.]+)%\*\* \(mín\. ([+\-\d.]+)%, máx\. ([+\-\d.]+)%\)", t)
        if m:
            MACROS.update({"esAr": f"{abs(float(m.group(1))):.0f}" + r"\%", "esArLo": f"{abs(float(m.group(3))):.0f}" + r"\%", "esArHi": f"{abs(float(m.group(2))):.0f}" + r"\%"})
        arcos = re.findall(r"\| (?:p\w+) \| (\d+) \|", t)
        if arcos:
            MACROS.update({"esArcosMin": str(min(map(int, arcos))), "esArcosMax": str(max(map(int, arcos)))})


def macros_estrita():
    """Sensibilidade estrita x fechamento (docs/21): numeros extraidos de RESULTADOS_ESTRITA.md (analise_estrita.py, escrito antes dos dados)."""
    import re
    p = os.path.join(A, "RESULTADOS_ESTRITA.md")
    if not os.path.exists(p):
        return
    txt = open(p, encoding="utf-8").read()
    ar = re.findall(r"Preço da estrita no ar\*\* \(estrita/fechamento − 1\): mediana \*\*([+\-\d.]+)%\*\*", txt)
    fo = re.findall(r"Preço da estrita no tempo total:\*\* mediana \*\*([+\-\d.]+)%\*\*", txt)
    red = re.findall(r"Estrita × peça:\*\* redução mediana do ar \*\*([\-\d.]+)%\*\*", txt)
    fp = re.findall(r"tempo total mediano ([+\-\d.]+)% \(menor em (\d+/\d+)\)", txt)
    cl = re.findall(r"fechamento ≤ estrita em \*\*(\d+/\d+)\*\*", txt)
    if len(ar) < 2 or len(fo) < 2:
        return
    for i, letra in enumerate(("Z", "C")):                       # Z = t 0, C = t 1 s
        MACROS[f"stAr{letra}"] = fmt(float(ar[i]), 1)
        MACROS[f"stFo{letra}"] = fmt(float(fo[i]), 2)
        MACROS[f"stRed{letra}"] = fmt(float(red[i]), 1, sinal=False)[:-2] + r"\%"
        MACROS[f"stPeca{letra}"] = fmt(float(fp[i][0]), 2)
        MACROS[f"stClose{letra}"] = cl[i]


def macros_fendas():
    """Fendas (entidades de 2 vertices) do CPPLib: numeros extraidos de RESULTADOS_FENDAS_CPPLIB.md (explorar_fendas.py)."""
    import re
    txt = open(os.path.join(A, "RESULTADOS_FENDAS_CPPLIB.md"), encoding="utf-8").read()
    nf = re.search(r"fendas: (\d+); contornos fechados: (\d+)", txt).groups()
    dentro = re.search(r"\| dentro \| \d+ \| ([\d.]+)%", txt).group(1)
    cruza = re.search(r"\| cruza \| \d+ \| ([\d.]+)%", txt).group(1)
    razao = re.search(r"mediana ([\d.]+), m", txt).group(1)
    MACROS.update({"nFendas": nf[0], "nContornosFechados": nf[1], "fendaDentro": dentro + r"\%", "fendaCruza": cruza + r"\%", "fendaRazao": f"{100 * float(razao):.0f}" + r"\%"})


def tabela_teto(L):
    """Tetos certificados e otimo exato do nivel de contorno (`teto_certificado.py`; exploratorio, calculado depois dos resultados principais)."""
    import teto_certificado as tc
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(A, "teto_resultados", "*.json")))]
    R = [r for r in R if r.get("P0") is not None]
    if not R:
        return
    Dj = [r for r in R if tc.disjunta(r)]
    letra = {0.0: "Z", 0.01: "U", 0.06: "S", 0.25: "A", 0.5: "B", 1.0: "C"}
    T = [r"\begin{table}[t]", r"\centering\small",
         r"\caption{Certified ceilings on what any segment-level method can save in total time over the contour level, by restart cost $t$ (exploratory; computed after the main results). Left: the " + str(len(Dj)) +
         r" layouts of disjoint contours, where the saving is bounded by $\max(0,t_{\mathrm{cert}}-t)$ seconds over the exact contour-level optimum (Proposition~\ref{prop:cert}); the last column counts the layouts in which the contour level is certified optimal. Right: all " + str(len(R)) +
         r" layouts with an exact rural-postman value, ceiling $c(t)=(T_P(t)-LB(t))/T_P(t)$ over the PCGLNS contour-level route, with $LB(t)=L/v_c+A^\ast/v_a+t\,R_{\min}$; it is large only where contours share edges.}",
         r"\label{tab:n1_teto}", r"\begin{tabular}{rrrrrr}", r"\toprule",
         r" & \multicolumn{3}{c}{Disjoint contours} & \multicolumn{2}{c}{All layouts} \\", r"\cmidrule(lr){2-4}\cmidrule(lr){5-6}",
         r"$t$ (s) & Ceiling, median & Ceiling, max & Certified optimal & Ceiling, median & Ceiling, max \\", r"\midrule"]
    for t in (0.0, 0.01, 0.06, 0.25, 0.5, 1.0):
        sv = []
        for r in Dj:
            lb2, tp = tc.teto_refinado(r, t, VC, VA)
            sv.append(100 * (tp - lb2) / tp)
        c = []
        for r in R:
            tp = r["P0"] + t * r["n_contornos"]
            lb = r["L_corte"] / VC + r["ar_otimo"] / VA + t * r["R_min"]
            c.append(100 * (tp - lb) / tp)
        T.append(f"{t:g} & {np.median(sv):.2f}\\% & {max(sv):.2f}\\% & {sum(1 for x in sv if x <= 1e-9)}/{len(sv)} & {np.median(c):.2f}\\% & {max(c):.1f}\\% " + r"\\")
        MACROS[f"tetoDj{letra[t]}"] = f"{np.median(sv):.2f}" + r"\%"
        MACROS[f"tetoDjMax{letra[t]}"] = f"{max(sv):.2f}" + r"\%"
        MACROS[f"tetoMed{letra[t]}"] = f"{np.median(c):.2f}" + r"\%"
        MACROS[f"tetoMax{letra[t]}"] = f"{max(c):.1f}" + r"\%"
    T += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_teto.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")
    tcs = [tc.t_cert(r, VA) for r in Dj]
    MACROS.update({"tetoN": str(len(R)), "tetoNcomp": str(sum(1 for r in R if r["R_min"] < r["n_contornos"])), "tetoNdj": str(len(Dj)),
                   "tcertMed": f"{np.median(tcs):.2f}", "tcertMin": f"{min(tcs):.2f}", "tcertMax": f"{max(tcs):.2f}"})
    # verificacao independente por MILP exato com custo de reinicio (`verificar_certificado_milp.py`)
    MJ = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(A, "milp_certificado_resultados", "*.json")))]
    if MJ:
        por_t, lay, tot, ok, dmax = {}, set(), 0, 0, 0.0
        sm_tot, sm_ok, sm_lay = 0, 0, set()
        for reg in MJ:
            r = next(x for x in R if x["instancia"] == reg["instancia"])
            for ts, x in reg["t"].items():
                t = float(ts)
                small = t < 0.2                                                                                 # t pequeno: a economia exata e positiva (curva exata, Fig. espessura)
                if small:
                    sm_tot += 1
                else:
                    tot += 1
                if not x.get("otimo"):
                    continue
                lb2, tp = tc.teto_refinado(r, t, VC, VA)
                assert lb2 - 1e-6 * tp <= x["M"] <= tp + 1e-6 * tp, (reg["instancia"], t, lb2, x["M"], tp)          # o certificado nao pode ser violado
                if small:
                    sm_ok += 1
                    sm_lay.add(reg["instancia"])
                    continue
                ok += 1
                lay.add(reg["instancia"])
                dmax = max(dmax, abs(x["M"] / tp - 1.0))
                por_t[t] = por_t.get(t, 0) + 1
        assert dmax < 1e-6, dmax                                                                                 # todo MILP provado em t >= 0,25 iguala o otimo de contorno
        MACROS.update({"milpNlay": str(len(MJ)), "milpTot": str(tot), "milpOk": str(ok), "milpLay": str(len(lay)), "milpAtC": str(por_t.get(1.0, 0)), "milpAtB": str(por_t.get(0.5, 0)), "milpAtA": str(por_t.get(0.25, 0)),
                       "milpSmTot": str(sm_tot), "milpSmOk": str(sm_ok), "milpSmLay": str(len(sm_lay))})
    # layouts com aresta compartilhada: solucao ciente do reinicio contra o teto geral (V3, t = 1 s)
    com = []
    for r in R:
        g = os.path.join(A, "v3_resultados", f"{r['instancia']}__t1.0.json")
        if r["R_min"] < r["n_contornos"] and os.path.exists(g):
            B = json.load(open(g))["melhor"]["fo"]
            tp = r["P0"] + r["n_contornos"]
            lb = r["L_corte"] / VC + r["ar_otimo"] / VA + r["R_min"]
            com.append((r["instancia"], 100 * (tp - lb) / tp, 100 * (tp - B) / tp))
    for tt, lt in (("0.25", "A"), ("1.0", "C")):                              # solucoes cientes do reinicio (V3) contra o otimo exato de contorno, nos layouts disjuntos
        gv = []
        for r in Dj:
            g = os.path.join(A, "v3_resultados", f"{r['instancia']}__t{tt}.json")
            if os.path.exists(g):
                B = json.load(open(g))["melhor"]["fo"]
                _, tp = tc.teto_refinado(r, float(tt), VC, VA)
                gv.append(100 * (B / tp - 1))
        MACROS[f"tetoVrN{lt}"] = str(len(gv))
        if gv:
            MACROS[f"tetoVrMed{lt}"] = fmt(np.median(gv), 2)
            MACROS[f"tetoVrMax{lt}"] = fmt(max(gv), 2)
            MACROS[f"tetoVrMin{lt}"] = fmt(min(gv), 2)
    MACROS["tetoComN"] = str(len(com))
    if com:
        MACROS["tetoComCeil"] = f"{np.median([x[1] for x in com]):.1f}" + r"\%"
        MACROS["tetoComBest"] = f"{np.median([x[2] for x in com]):.1f}" + r"\%"
        MACROS["tetoComMaxCeil"] = f"{max(x[1] for x in com):.1f}" + r"\%"
        MACROS["tetoComMaxBest"] = f"{max(x[2] for x in com):.1f}" + r"\%"
    # PCGLNS por contorno contra o otimo exato de nivel de contorno; heuristica contra esse otimo
    D2 = [r for r in R if "dp" in r]
    byname = {x["nome"]: x for x in L}
    gaps = np.array([100 * (r["P0"] / r["dp"]["fo"] - 1) for r in D2])
    hp = np.array([pct(byname[r["instancia"]]["poli"], r["dp"]["fo"]) for r in D2])
    hf = np.array([pct(byname[r["instancia"]]["H0.0"], r["dp"]["fo"]) for r in D2])
    hpP = np.array([pct(byname[r["instancia"]]["poli"], r["P0"]) for r in D2])
    hfP = np.array([pct(byname[r["instancia"]]["H0.0"], r["P0"]) for r in D2])
    pior = D2[int(np.argmax(gaps))]
    MACROS.update({"dpN": str(len(D2)), "dpMaxN": str(max(r["n_contornos"] for r in D2)), "dpIgual": f"{int((np.abs(gaps) <= 0.005).sum())}/{len(D2)}",
                   "dpMed": f"{np.median(gaps):.3f}" + r"\%", "dpMax": f"{gaps.max():.2f}" + r"\%", "dpMaxName": pior["instancia"].replace("_", r"\_"), "dpAbaixo": str(int((gaps < -0.005).sum())),
                   "dpWinsPoli": f"{int((hp < 0).sum())}/{len(D2)}", "dpWinsFormal": f"{int((hf < 0).sum())}/{len(D2)}", "dpMedPoli": fmt(np.median(hp), 2), "dpMedFormal": fmt(np.median(hf), 2),
                   "dpWinsPoliP": f"{int((hpP < 0).sum())}/{len(D2)}", "dpWinsFormalP": f"{int((hfP < 0).sum())}/{len(D2)}", "dpMedPoliP": fmt(np.median(hpP), 2), "dpMedFormalP": fmt(np.median(hfP), 2)})


def tabela_espessura():
    """Ancoras de reinicio por espessura (literatura + derivacao) e curva exata da economia maxima (`analise_ancoras_por_espessura.py`; exploratorio, plano B sem maquina)."""
    import analise_ancoras_por_espessura as ae
    d = ae.dados()
    F, S, lay = d["faixas"], d["curva"], d["layouts"]
    nome = {"thin": r"Thin sheet (up to 3\,mm)", "med": r"Medium plate (9 to 12\,mm)", "thick": r"Thick plate (20 to 25\,mm)"}
    fonte = {"thin": r"\citep{hashemzadeh2014piercing}", "med": r"\citep{westmfg2018piercing,prima2015platino,garcia2019piercing}", "thick": r"\citep{piranha2026rapidpierce,garcia2019piercing}"}

    def ints(lo, hi):
        return f"{lo:.2g} to {hi:.2g}"

    T = [r"\begin{table}[t]", r"\centering\footnotesize",
         r"\caption{Restart costs by sheet thickness (seconds). Piercing at an uncut point: ranges from the sources cited, whose upper end adds up to 0.15\,s for lifting and lowering the head. Resumption in a kerf already cut: \emph{derived by us}, because we found no source that measures it, as a pre-cut of 2\,mm at the cutting speed plus the stop and start at the vertex plus the lift of the head, and never above the cost of a piercing. Regimes: R1, $t\le0.06$\,s; R2, $0.06<t<0.87$\,s; R3, $t\ge0.87$\,s (Section~\ref{sec:res_cert}). Sources of the piercing ranges: thin sheet \citep{hashemzadeh2014piercing}; medium plate \citep{westmfg2018piercing,prima2015platino,garcia2019piercing}; thick plate \citep{piranha2026rapidpierce,garcia2019piercing}.}",
         r"\label{tab:n1_esp}", r"\begin{tabular}{llcll}", r"\toprule", r"Sheet & Piercing & Regimes & Resumption (derived) & Regimes \\", r"\midrule"]
    for k in ("thin", "med", "thick"):
        f = F[k]
        T.append(f"{nome[k]} & {ints(*f['perf'])} & {', '.join(ae.regimes(*f['perf']))} & {ints(*f['ret'])} & {', '.join(ae.regimes(*f['ret']))} " + r"\\")
        MACROS[f"esp{k.capitalize()}PerfLo"] = f"{f['perf'][0]:.2g}"
        MACROS[f"esp{k.capitalize()}PerfHi"] = f"{f['perf'][1]:.2g}"
        MACROS[f"esp{k.capitalize()}RetLo"] = f"{f['ret'][0]:.2g}"
        MACROS[f"esp{k.capitalize()}RetHi"] = f"{f['ret'][1]:.2g}"
    T += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_espessura.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")
    letra = {0.0: "Z", 0.01: "U", 0.03: "V", 0.06: "S", 0.1: "W", 0.25: "A", 0.5: "B", 1.0: "C"}
    for t, v in S.items():
        if v:
            MACROS[f"exMed{letra[t]}"] = f"{np.median(v):.2f}" + r"\%"
            MACROS[f"exMax{letra[t]}"] = f"{max(v):.2f}" + r"\%"
            MACROS[f"exN{letra[t]}"] = str(len(v))
    gletra = {0.0: "Z", 0.01: "U", 0.06: "S", 0.25: "A", 1.0: "C"}
    for t, g in d["gaps"].items():
        if not g["P"]:
            continue
        MACROS[f"gapN{gletra[t]}"] = str(len(g["P"]))
        for chave, nome_m in (("H", "H"), ("G", "G"), ("P", "P")):
            if g[chave]:
                MACROS[f"gap{nome_m}Med{gletra[t]}"] = f"{np.median(g[chave]):.2f}" + r"\%"
                MACROS[f"gap{nome_m}Max{gletra[t]}"] = f"{max(g[chave]):.1f}" + r"\%"
    # ponto de equilibrio exato por layout: maior t da grade com economia > 1e-3 % e menor t com economia <= 1e-3 % (so layouts com MILP provado em toda a grade ate 0,25 s)
    grade = [t for t in ae.TS_CURVA if t <= 0.25]
    por_lay = {}
    for t in grade:
        for nome_l, s in zip(lay[t], S[t]):
            por_lay.setdefault(nome_l, {})[t] = s
    lo, hi = [], []
    for nome_l, m in por_lay.items():
        if all(t in m for t in grade):
            pos = [t for t in grade if m[t] > 1e-3]
            zero = [t for t in grade if m[t] <= 1e-3]
            lo.append(max(pos) if pos else 0.0)
            hi.append(min(zero) if zero else float("inf"))
    if lo:
        MACROS["tbeN"] = str(len(lo))
        MACROS["tbeLoMed"] = f"{np.median(lo):.3g}"
        MACROS["tbeHiMed"] = f"{np.median(hi):.3g}"
        MACROS["tbeHiMax"] = f"{max(hi):.3g}"
        MACROS["tbeLoMax"] = f"{max(lo):.3g}"


def main():
    macros_fendas_resultados()
    macros_rpp_cpplib()
    tabela_mapa()
    tabela_tau_reinicio()
    tabela_tau()
    tabela_voo()
    macros_robustez()
    macros_estrita()
    macros_fendas()
    L = carregar_282()
    tabela_convencoes(L)
    tabela_reinicio(L)
    tabela_otimo(L)
    tabela_v2()
    tabela_v3()
    tabela_reparo()
    tabela_teto(L)
    tabela_espessura()
    out = ["% gerado por manuscrito/gerar_tabelas_n1.py -- nao editar a mao"]
    out += [r"\newcommand{\%s}{%s}" % (k, v) for k, v in sorted(MACROS.items())]
    open(os.path.join(AQUI, "N1", "numeros_n1.tex"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("macros:", len(MACROS), "| instancias:", len(L))
    for k, v in sorted(MACROS.items()):
        print(f"  {k} = {v}")


if __name__ == "__main__":
    main()
