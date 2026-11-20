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
try:                                                         # a copia do codigo do artigo irmao (src_base/) NAO esta no repositorio publico
    from heuristic_core import _DEFAULT_CONFIG as D          # noqa: E402
except ImportError:
    import types
    _hc = types.ModuleType("heuristic_core")                 # so as velocidades do benchmark (hipotese A4 do manuscrito): os modulos de analise que o gerador importa
    _hc._DEFAULT_CONFIG = {"v_cut": 100.0 / 6.0, "v_air": 400.0}   # as leem so para ler resultados guardados; nada do codigo da heuristica e reproduzido aqui
    sys.modules["heuristic_core"] = _hc
    D = _hc._DEFAULT_CONFIG
VC, VA = D["v_cut"], D["v_air"]
import avaliar_heuristica_formal as af                       # noqa: E402  (so le caminhos guardados quando chamado; `gerar_figuras_n1.py` usa `gt.af`)
TAB = os.path.join(AQUI, "N1", "tabelas")
os.makedirs(TAB, exist_ok=True)
MACROS = {}
TS = (0.25, 0.5, 1.0)


def pct(a, b):
    return 100.0 * (a / b - 1.0)


def fmt(x, casas=2, sinal=True):
    s = f"{x:+.{casas}f}" if sinal else f"{x:.{casas}f}"
    if float(s) == 0.0:                                                   # arredonda para zero: sem sinal (evita "-0.00%"; revisao de 18/11/2026)
        s = f"{0.0:.{casas}f}"
    return s.replace("-", "$-$") + r"\%"


def fmt_sem_pct(x, casas=2):
    """Como fmt(), mas sem o sinal de percentagem (celulas de tabela com unidade no cabecalho); zero arredondado sai sem sinal."""
    s = f"{x:+.{casas}f}"
    if float(s) == 0.0:
        s = f"{0.0:.{casas}f}"
    return s.replace("-", "$-$")


RESUMO_CAMINHOS = os.path.join(A, "resumos_heuristica_282.json")


def _avaliar_caminhos():
    """Avalia os caminhos guardados da heuristica (que contem a geometria das instancias e NAO e publicado; so existe com o pipeline do artigo irmao):
    -> {nome: so NUMEROS por instancia}. Esse resumo (`resumos_heuristica_282.json`, sem geometria) permite regenerar todas as tabelas sem os caminhos."""
    out = {}                                                  # so aqui sao precisos os caminhos guardados
    for n, r in sorted(af.carregar().items()):
        cam = r["forte"]
        pol = af.fo_poligonal(cam, 0.0)
        t_h = r.get("tempo_s", float("nan"))
        d = {"listada": r["fo_listada_forte"], "poli": pol["fo"], "saltos": pol["saltos"], "t_heur": None if t_h != t_h else t_h}
        for t in (0.0,) + TS:
            f = af.fo_formal(cam, t)
            d[f"H{t}"], d[f"R{t}"], d[f"ret{t}"], d[f"virg{t}"] = f["fo"], f["corridas"], f["retomadas"], f["virgens"]
            if t == 0.0:
                d["ar0"] = f["ar"]                                    # tempo de ar da rota formal da heuristica em t = 0 (Tabela de otimo)
        out[n] = d
    return out


def _resumos_caminhos():
    """Com os caminhos guardados: avalia e (re)grava o resumo; sem eles (ou com N1_SEM_CAMINHOS=1): le o resumo publicado no repositorio."""
    usar_resumo = os.environ.get("N1_SEM_CAMINHOS") == "1" or not os.path.isdir(os.path.join(A, "auditoria_lcpp1", "caminhos_282"))
    if usar_resumo:
        print("modo SEM caminhos guardados: usando", os.path.basename(RESUMO_CAMINHOS))
        return json.load(open(RESUMO_CAMINHOS))
    R = _avaliar_caminhos()
    json.dump(R, open(RESUMO_CAMINHOS, "w", encoding="utf-8", newline="\n"), indent=0, sort_keys=True)
    return R


def carregar_282():
    L = []
    for n, r in sorted(_resumos_caminhos().items()):
        try:
            g = json.load(open(os.path.join(A, "lcpp1_segmento_resultados", f"{n}.json")))
            h = json.load(open(os.path.join(A, "auditoria_lcpp1", "honesta_282", f"{n}.json")))
        except FileNotFoundError:
            continue
        if not g.get("melhor") or "fo_pcglns_honesta" not in h:
            continue
        x = {"nome": n, "listada": r["listada"], "poli": r["poli"], "saltos": r["saltos"], "peca": h["fo_pcglns_honesta"], "gtsp": g["melhor"]["fo"], "R0": g["melhor"]["n_perf"], "nc": g["n_contornos"],
             "t_gtsp": g.get("tempo_total_s", float("nan")), "t_heur": float("nan") if r["t_heur"] is None else r["t_heur"], "ar0": r["ar0"],
             "peca_deles": h.get("fo_pcglns_formula_deles"), "corte_s": h.get("cut_time_fixed")}
        for t in (0.0,) + TS:
            x[f"H{t}"], x[f"R{t}"], x[f"ret{t}"], x[f"virg{t}"] = r[f"H{t}"], r[f"R{t}"], r[f"ret{t}"], r[f"virg{t}"]
        L.append(x)
    return L


def tabela_convencoes(L):
    linhas = [("Heuristic (cost listed by its code) vs.\\ contour-level PCGLNS", "listada", "peca"), ("Heuristic (executable path) vs.\\ contour-level PCGLNS", "poli", "peca"), ("Heuristic (formal objective) vs.\\ contour-level PCGLNS", "H0.0", "peca"),
              ("Heuristic (formal objective) vs.\\ arc-GTSP + PCGLNS", "H0.0", "gtsp"), ("Heuristic (executable path) vs.\\ arc-GTSP + PCGLNS", "poli", "gtsp")]
    T = [r"\begin{table}[t]", r"\centering\small",
         r"\caption{The heuristic of the companion manuscript under three cost conventions on the " + str(len(L)) + r" synthetic instances (restart cost zero). Relative difference of the total objective; negative favours the first method; wins = instances where it is strictly lower. Listed: the value that the code of the heuristic reports, which does not charge the jumps between segments that do not join; executable path: those jumps are counted; formal objective: direct chord between consecutive cutting operations (the objective of the companion manuscript). The contour-level PCGLNS is always costed as an executable path with the legs from and to the origin.}",
         r"\label{tab:n1_conv}", r"\begin{tabular}{lrrr}", r"\toprule", r"Comparison & Median & Mean & Wins \\", r"\midrule"]
    for nome, a, b in linhas:
        d = np.array([pct(x[a], x[b]) for x in L])
        T.append(f"{nome} & {fmt(np.median(d), 3)} & {fmt(d.mean(), 3)} & {int((d < 0).sum())}/{len(d)} " + r"\\")
    T += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_convencoes.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")
    dp = np.array([pct(x["poli"], x["peca"]) for x in L])
    df = np.array([pct(x["H0.0"], x["peca"]) for x in L])
    dg = np.array([pct(x["H0.0"], x["gtsp"]) for x in L])
    dl = np.array([pct(x["listada"], x["peca"]) for x in L])                              # custo listado pelo codigo (como a heuristica foi reportada), mesma referencia de nivel de contorno
    MACROS.update({"winsList": str(int((dl < 0).sum())), "medList": fmt(np.median(dl), 2), "meanList": fmt(dl.mean(), 2)})
    dd = np.array([pct(x["listada"], x["peca_deles"]) for x in L if x.get("peca_deles")])  # idem, com o custo que o artigo irmao atribui ao PCGLNS (sem as pernas da origem)
    if len(dd) == len(L):
        MACROS.update({"winsListDeles": str(int((dd < 0).sum())), "medListDeles": fmt(np.median(dd), 2), "meanListDeles": fmt(dd.mean(), 2)})
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
         r"\caption{Effect of a restart cost $t$ (seconds per interruption of the cut) on the " + str(len(L)) + r" synthetic instances. The heuristic keeps its service order and only its orientations are re-optimised for each $t$; the contour-level cost is the $t=0$ value plus $t$ per contour (an upper bound where contours touch, see the text); the arc-GTSP route is the $t=0$ solution evaluated at $t$ (an upper bound for the restart-aware optimum). Median relative differences of total time (negative favours the first), and instances where the first is lower.}",
         r"\label{tab:n1_t}", r"\begin{tabular}{rrrrrr}", r"\toprule",
         r"$t$ (s) & \shortstack{Runs: heur./\\arc-GTSP/contours} & \shortstack{Heur.\ vs\\contour level} & Wins & \shortstack{Heur.\ vs\\arc-GTSP$_{0}$} & \shortstack{Arc-GTSP$_{0}$ vs\\contour level} \\", r"\midrule"]
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


def macros_corridas_contorno(L):
    """Corridas da rota de contorno x contornos (item de revisao de 19/11/2026): as Tabelas 7 e 9 cobram t por CONTORNO; onde contornos se tocam a rota de contorno pode encadea-los sem reinicio.
    Nas instancias da amostra (as corridas ficaram guardadas em `tau_resultados/`) mede quanto muda o ponto de equilibrio mediano se o reinicio for cobrado por corrida da rota de contorno."""
    import rodar_v3 as rv
    d0 = os.path.join(A, "tau_resultados")
    if not os.path.isdir(d0):
        return
    por_nome = {x["nome"]: x for x in L}
    te_nc, te_run, dif = [], [], []
    for n in rv.amostra():
        x, f = por_nome.get(n), os.path.join(d0, f"peca_LASER_{n}.json")
        if x is None or not os.path.exists(f):
            continue
        runs_p = json.load(open(f))["corridas"]
        dif.append(x["nc"] - runs_p)
        if x["peca"] > x["H0.0"]:
            if x["R0.25"] > x["nc"]:
                te_nc.append((x["peca"] - x["H0.0"]) / (x["R0.25"] - x["nc"]))
            if x["R0.25"] > runs_p:
                te_run.append((x["peca"] - x["H0.0"]) / (x["R0.25"] - runs_p))
    if dif and te_nc and te_run:
        MACROS.update({"nSampleRuns": str(len(dif)), "nDifRuns": str(sum(1 for d in dif if d > 0)), "tEqSampleNc": f"{statistics.median(te_nc):.3f}", "tEqSampleRun": f"{statistics.median(te_run):.3f}"})


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
        except FileNotFoundError:
            continue
        if x is None:
            continue
        cut = r["corte_comprimento"] / VC
        hf = {"ar": x["ar0"], "fo": x["H0.0"]}                           # da rota formal da heuristica em t = 0 (resumo por instancia; nao precisa dos caminhos)
        R.append({"hole": "_hole_" in n, "ar_opt": r["ar_otimo"] / VA, "ar_h": hf["ar"], "ar_g": g["ar"] / VA, "ar_p": x["peca"] - cut, "LB": cut + r["ar_otimo"] / VA, "H": hf["fo"], "G": g["fo"], "P": x["peca"]})
    n_total = len(glob.glob(os.path.join(A, "rpp_lcpp1_resultados", "*.json")))
    T = [r"\begin{table}[t]", r"\centering\footnotesize",
         r"\caption{Distance to the exact optimum of the segment-level problem without precedence (MILP, restart cost zero) on small instances (at most 110 vertices after noding; " + f"{len(R)} of {n_total}" +
         r" solved within the time limit, 600\,s or 900\,s on repeat). Without nesting the exact value is the optimum of the problem of the companion manuscript; for layouts with holes it is a lower bound. Air time gap: median (maximum) over instances (a large maximum is a ratio over an exact air time close to zero); at optimum: gap $\le 0.01\%$.}",
         r"\label{tab:n1_opt}", r"\begin{tabular}{llrrrr}", r"\toprule", r"Layouts & Method & Air gap, median & Air gap, max & At optimum & Total gap, median \\", r"\midrule"]
    for rot, S in (("No nesting\\\\(optimum)", [x for x in R if not x["hole"]]), ("With holes\\\\(lower bound)", [x for x in R if x["hole"]])):
        if not S:
            continue
        for k, (nome, ka, kf) in enumerate((("Heuristic", "ar_h", "H"), ("Arc-GTSP + PCGLNS", "ar_g", "G"), ("Contour-level PCGLNS", "ar_p", "P"))):
            a = np.array([pct(x[ka], x["ar_opt"]) for x in S if x["ar_opt"] > 1e-9])
            fo = np.array([pct(x[kf], x["LB"]) for x in S])
            pre = rf"\multirow{{3}}{{*}}{{\shortstack[l]{{{rot}, $n={len(S)}$}}}}" if k == 0 else ""
            T.append(f"{pre} & {nome} & {fmt(np.median(a), 2)} & {fmt(a.max(), 1)} & {int((a <= 0.01).sum())}/{len(a)} & {fmt(np.median(fo), 3)} " + r"\\")
            if rot.startswith("No"):
                tag = {"ar_h": "Heur", "ar_g": "Gtsp", "ar_p": "Peca"}[ka]
                MACROS[f"otAr{tag}"] = fmt(np.median(a), 2)
                MACROS[f"otFo{tag}"] = fmt(np.median(fo), 3)
                MACROS[f"otN{tag}"] = f"{int((a <= 0.01).sum())}/{len(a)}"
                MACROS[f"otArMax{tag}"] = fmt(a.max(), 1)
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
         r"\label{tab:n1_v2}", r"\begin{tabular}{>{\raggedright\arraybackslash}p{5.2cm}>{\raggedright\arraybackslash}p{3.4cm}>{\raggedright\arraybackslash}p{4.6cm}}", r"\toprule", r"Pre-specified hypothesis & Criterion & Result \\", r"\midrule",
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
        _pular("n1_v3.tex", "as rotas de V3 guardadas nao tem geometria no repositorio publico")
        return
    T = [r"\begin{table}[t]", r"\centering\small",
         r"\caption{Restart-aware routes on a stratified sample of the synthetic instances (protocol fixed before the data). Median relative differences of total time at restart cost $t$; $G(t)$ is the arc-based solution computed with restart cost $t$, $G_0(t)$ the $t=0$ route evaluated at $t$, $B(t)=\min(G,G_0)$ the best verified segment-level solution, $H(t)$ the heuristic of the companion manuscript (formal objective) and $P(t)$ the contour-level reference.}",
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
        if t == 1.0:
            MACROS["vtreeRet"] = f"{100 * sum(x['ret'] for x in U) / sum(x['R'] for x in U):.1f}" + r"\%"      # H-W5: corridas que recomecam em vertice ja cortado (como `analise_v3.py`)
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
        _pular("n1_reparo.tex", "as rotas do reparo guardadas nao tem geometria no repositorio publico")
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
        _pular("n1_voo.tex", "faltam as rotas guardadas (`auditoria_lcpp1/pecas_caminhos/`, com geometria)")
        return
    import analise_voo_nao_linear as vn
    L = vn.carregar()
    if not L:
        _pular("n1_voo.tex", "nenhuma rota guardada pode ser avaliada")
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
        import re
        _m = re.search(r"m\xe1x\. ([\d.]+)%; dentro de 0,05% em (\d+)/(\d+)", open(os.path.join(A, "RESULTADOS_TAU_ANALISE.md"), encoding="utf-8").read())
        if _m:
            MACROS.update({"tauReprMax": f"{float(_m.group(1)):.2f}" + r"\%", "tauReprN": _m.group(2), "tauReprTot": _m.group(3)})
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
        _pular("n1_mapa.tex", "faltam as rotas guardadas (`auditoria_lcpp1/pecas_caminhos/`, com geometria)")
        return
    import analise_mapa_regimes as am
    import analise_voo_nao_linear as vn
    L = vn.carregar()
    perfis = (("FIBRA_1G", r"Reference, 100\,m/min, 1.0\,g"), ("V170_1_4G", r"170\,m/min, 1.4\,g"), ("BLM_2G", r"BLM LS7, 140\,m/min, 2.0\,g"), ("SALV_5G", r"Salvagnini L5, 156\,m/min, 5\,g"), ("DEWIL16", r"CO$_2$, Dewil et al.\ curve"))
    T = [r"\begin{table}[t]", r"\centering\footnotesize",
         r"\caption{Map of regimes anchored in published data (exploratory; " + str(len(L)) + r" synthetic instances; stored routes, not re-optimised). Each cell gives the median of $T/T_P-1$ in percent for the heuristic that ignores the restart cost and for the restart-aware arc-based route ($t=0.25$\,s), against the contour-level route. Motion profiles: trapezoidal, with the speeds and accelerations that manufacturers publish (170\,m/min simultaneous speed of TRUMPF, Bystronic and Salvagnini machines with the 1.4\,g of an Amada machine \citep{trumpf3030fiber,bystronic2025bystarfiber,salvagnini2026l3g4,amada2026ensis}; the BLM LS7 \citep{blm2026ls7}; the Salvagnini L5, whose 5\,g holds on short moves of thin sheet \citep{salvagnini2026l5}), a reference of our own, and the curve of \citet{dewil2016review}. Restart costs: $t=0.01$ and $0.06$\,s bracket the breakthrough time of 2\,mm steel with a fibre laser \citep{hashemzadeh2014piercing}; $t=0.25$ and $1$\,s stand for thicker plate \citep{westmfg2018piercing,prima2015platino,garcia2019piercing}. One drawing unit is taken as one millimetre.}",
         r"\label{tab:n1_mapa}", r"\begin{tabular}{lrrrrr}", r"\toprule", r"Motion profile & $t=0$ & $t=0.01$ & $t=0.06$ & $t=0.25$ & $t=1$ \\", r"\midrule"]
    HMED = {}
    for perfil, nome in perfis:
        cel = []
        for t in am.TS:
            h = np.median([100 * (am.total(R["H"], perfil, t) / am.total(R["P"], perfil, t) - 1) for _, R, _ in L])
            HMED[(perfil, round(t, 2))] = h
            g = np.median([100 * (am.total(R["G0.25"], perfil, t) / am.total(R["P"], perfil, t) - 1) for _, R, _ in L])
            cel.append(f"{fmt_sem_pct(h)} / {fmt_sem_pct(g)}")
        T.append(f"{nome} & " + " & ".join(cel) + r" \\")
    for t_, nm_ in ((0.01, "Ten"), (0.06, "Six"), (0.25, "Quarter"), (1.0, "One")):                      # faixa, entre os perfis de movimento, da perda da heuristica que ignora o reinicio
        v_ = [h_ for (_, tt), h_ in HMED.items() if tt == t_]
        MACROS[f"mapaH{nm_}Lo"], MACROS[f"mapaH{nm_}Hi"] = fmt(min(v_), 2 if t_ == 0.01 else 1, sinal=False), fmt(max(v_), 2 if t_ == 0.01 else 1, sinal=False)
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
            MACROS["trNcont"] = f"{np.median([json.load(open(os.path.join(A, 'lcpp1_segmento_resultados', f'{n}.json')))['n_contornos'] for n in rv.amostra()]):.0f}"       # contornos (nao corridas) da amostra
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
        comuns = [m for m in por_lay.values() if all(t in m for t in grade)]                       # curva exata so nos layouts resolvidos em toda a grade (mesma amostra em todos os pontos)
        for t in grade:
            MACROS[f"com{letra[t]}"] = f"{np.median([m[t] for m in comuns]):.2f}" + r"\%"


def macros_familias(L):
    """Intervalos por FAMILIA (bootstrap por cluster; exploratorio, pos-hoc de 19/11/2026) para as comparacoes nas 282 e numero de familias dos subconjuntos exatos
    (`caso_a_corte_multitecnologia/analise_familias.py`; revisao duplo-cega, R1-M3: as instancias de uma mesma familia nao sao independentes)."""
    import analise_familias as af2
    nomes = [x["nome"] for x in L]
    MACROS["clN"] = str(af2.verificar_estrutura(nomes))
    est = {"w": lambda v: 100.0 * float((v < 0).mean()), "med": lambda v: float(np.median(v)), "mean": lambda v: float(v.mean())}
    for tag, a in (("Poli", "poli"), ("Formal", "H0.0")):
        v = np.array([pct(x[a], x["peca"]) for x in L])
        ci = af2.bootstrap(nomes, v, est)
        MACROS[f"clWins{tag}Lo"], MACROS[f"clWins{tag}Hi"] = f"{ci['w'][0]:.0f}" + r"\%", f"{ci['w'][1]:.0f}" + r"\%"
        MACROS[f"clMed{tag}Lo"], MACROS[f"clMed{tag}Hi"] = fmt(ci["med"][0], 2), fmt(ci["med"][1], 2)
        MACROS[f"clMean{tag}Lo"], MACROS[f"clMean{tag}Hi"] = fmt(ci["mean"][0], 2), fmt(ci["mean"][1], 2)
    S = af2.nomes_de_subconjuntos()
    MACROS.update({"clFamResolvidas": str(af2.contar_familias(S["resolvidas"])), "clFamSemPi": str(af2.contar_familias(S["sem_pi"])),
                   "clFamDisj": str(af2.contar_familias(S["disjuntas"])), "clFamMilp": str(af2.contar_familias(S["milp"]))})


def macros_repositorio_publico():
    """O que o repositorio publico do artigo irmao (versao de congresso) tem em comum com o que o N1 usou (`caso_a_corte_multitecnologia/verificar_repositorio_publico_artigo_irmao.py`;
    conferencia de 19/11/2026: instancias identicas por SHA-256; FO da construcao igual em 267 de 282)."""
    import verificar_repositorio_publico_artigo_irmao as vp
    R = vp.resumo()
    MACROS.update({"pubInst": str(R["n_instancias"]), "pubFoIguais": str(R["fo_iguais"]), "pubFoDif": str(R["fo_diferentes"]), "pubFoDifPack": str(R["diferentes_pack"]),
                   "pubFoDifMax": f"{R['dif_rel_max_pct']:.2f}" + r"\%",
                   # comparacao com o CSV FINAL por instancia do artigo irmao (LCPP-main, somente leitura; constantes reconferidas por `vp.conferir_contra_final()` quando LCPP-main existe)
                   "cmpConsEq": str(R["final_cons_iguais"]), "cmpForteEq": str(R["final_forte_iguais"]), "cmpForteHi": str(R["final_forte_maiores"]),
                   "cmpForteMax": f"{R['final_forte_max_pct']:.2f}" + r"\%", "cmpForteMean": f"{R['final_forte_media_pct']:.2f}" + r"\%", "cmpPubFinalEq": str(R["final_dif_iguais_nosso"])})


def tabela_velocidades():
    """Sensibilidade da economia exata maxima as velocidades de corte e de voo (`caso_a_corte_multitecnologia/analise_escala_velocidades.py`; EXPLORATORIO, POS-HOC de 18/11/2026;
    reprocessa os valores exatos guardados, nenhum solver e rodado; o autoteste do modulo confere o cenario do benchmark com a curva exata da Tabela 12 / Fig. 4)."""
    import analise_escala_velocidades as ev
    D = ev.dados()
    T = [r"\begin{table}[t]", r"\centering\footnotesize",
         r"\caption{Sensitivity of the exact ceiling on the saving of any plan to the cutting speed $v_c$ and the air speed $v_a$, in m/min (exploratory, post hoc: the exact values of Section~\ref{sec:res_esp} are rescaled and nothing is solved again; one drawing unit is one millimetre). The first row is the benchmark; the others are illustrative scenarios, whose cutting speeds are assumptions without a source that we could verify and whose air speed is the lowest manufacturer value of Section~\ref{sec:setup_par}. Air share: air time over total time of the contour-level optimum (median over the layouts of disjoint contours). Ceiling: largest saving of any plan over the contour-level optimum, as a share of the total time, at $t=0$ (median; maximum). Nil at: first restart cost of the exact grid at which the median ceiling is nil. $t_{\mathrm{cert}}$: largest certificate of Proposition~\ref{prop:cert}.}",
         r"\label{tab:n1_vel}", r"\begin{tabular}{lrrrrrr}", r"\toprule",
         r"Scenario & $v_c$ & $v_a$ & Air share & Ceiling at $t=0$ & Nil at (s) & $t_{\mathrm{cert}}$ (s) \\", r"\midrule"]
    for d in D:
        T.append(f"{d['rotulo']} & {d['vc']:g} & {d['va']:g} & {d['voo_med']:.1f}\\% & {d['med'][0.0]:.2f}\\% ({d['max'][0.0]:.2f}\\%) & {d['nil_t']:.2g} & {d['tcert_max']:.2f} " + r"\\")
        k = d["chave"]
        MACROS[f"sc{k}Voo"] = f"{d['voo_med']:.1f}" + r"\%"
        MACROS[f"sc{k}ZMed"] = f"{d['med'][0.0]:.2f}" + r"\%"
        MACROS[f"sc{k}ZMax"] = f"{d['max'][0.0]:.2f}" + r"\%"
        MACROS[f"sc{k}Nil"] = f"{d['nil_t']:.2g}"
        MACROS[f"sc{k}Cert"] = f"{d['tcert_max']:.2f}"
        MACROS[f"sc{k}RI"] = f"{d['r1']:.3f}"
        MACROS[f"sc{k}RIII"] = f"{d['r3']:.2f}"
    if "tEqAirEquil" in MACROS:                                   # o equilibrio mediano da heuristica (distancia de voo equivalente) convertido em tempo a 140 m/min
        MACROS["tEqAirMsFibre"] = f"{float(MACROS['tEqAirEquil']) / (140 * 1000 / 60.0) * 1000:.0f}"
    T += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_velocidades.tex"), "w", encoding="utf-8").write("\n".join(T) + "\n")


def tabela_sem_escala():
    """Leitura SEM ESCALA da economia exata (item 4 de docs/48; EXPLORATORIO, POS-HOC de 19/11/2026; nenhum solver e rodado; so valores exatos guardados).
    A solucao otima so depende de t e de v_a por t*v_a (a distancia de voo que um reinicio vale); em unidades do proprio layout:
    rho = t * v_a / perimetro medio de contorno, com perimetro medio = L/n (comprimento de corte / numero de contornos). Fracao da economia = (T_P - T_otimo) / (tempo de voo do otimo de contorno)."""
    import teto_certificado as tc
    import analise_ancoras_por_espessura as ae
    T = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(A, "teto_resultados", "*.json"))}
    MJ = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(A, "milp_certificado_resultados", "*.json")))]
    if not T or not MJ:
        return
    Dj = [r for r in T.values() if r.get("P0") is not None and tc.disjunta(r)]
    rc = [(r["dp"]["ar_otimo_contorno"] - r["ar_otimo"]) * r["n_contornos"] / r["L_corte"] for r in Dj]                  # rho_cert = (A_P* - A*) / (L/n) = t_cert v_a / (L/n)
    pares = []
    for reg in MJ:
        r = T[reg["instancia"]]
        L_, n_, AP, As = r["L_corte"], r["n_contornos"], r["dp"]["ar_otimo_contorno"], r["ar_otimo"]
        for t in ae.TS_CURVA:
            if t == 0.0:
                Q = min(AP, As) / VA                                       # RPP exato (layout disjunto sem furos)
            else:
                x = reg["t"].get(str(t))
                if not x or not x.get("otimo"):
                    continue
                Q = x["M"] - L_ / VC                                       # tempo sem corte do plano otimo (voo + reinicios), velocidades do benchmark
            QP = AP / VA + t * n_
            pares.append((t * VA * n_ / L_, max(0.0, QP - Q) / (AP / VA)))
    faixas = (("Z", r"$0$ (free restart)", lambda p: p == 0.0), ("A", r"$(0,\,0.1]$", lambda p: 0.0 < p <= 0.1), ("B", r"$(0.1,\,0.3]$", lambda p: 0.1 < p <= 0.3),
              ("C", r"$(0.3,\,1]$", lambda p: 0.3 < p <= 1.0), ("D", r"$>1$", lambda p: p > 1.0))
    bordas = {"A": 0.0, "B": 0.1, "C": 0.3, "D": 1.0}                                    # borda inferior de cada faixa (para o macro sfNilRho)
    Tx = [r"\begin{table}[t]", r"\centering\small",
          r"\caption{Exact saving of any plan in scale-free terms (exploratory, post hoc; stored exact values, nothing is solved again). $\bar\ell$ is the mean contour perimeter of a layout (cutting length over number of contours) and $\rho=t\,v_a/\bar\ell$ the flight distance that one restart is worth, in mean perimeters. Saving: share of the air time of the contour-level optimum that the optimal plan of the mixed-integer programme with restart cost removes; median (maximum) over the " + str(len(pares)) +
          r" programmes (layout, restart cost) of Section~\ref{sec:res_esp}, on " + str(len(MJ)) + r" layouts of disjoint contours without holes.}",
          r"\label{tab:n1_sf}", r"\begin{tabular}{lrrr}", r"\toprule", r"$\rho$ & Programmes & Saving, median & Saving, max \\", r"\midrule"]
    for k, rot, cond in faixas:
        S = [s for p, s in pares if cond(p)]
        if not S:
            continue
        Tx.append(f"{rot} & {len(S)} & {100 * np.median(S):.1f}\\% & {100 * max(S):.1f}\\% " + r"\\")
        MACROS[f"sf{k}Med"], MACROS[f"sf{k}Max"], MACROS[f"sf{k}N"] = f"{100 * np.median(S):.0f}" + r"\%", f"{100 * max(S):.0f}" + r"\%", str(len(S))
        if k in bordas and np.median(S) < 5e-4 and "sfNilRho" not in MACROS:                # primeira faixa de rho em que a mediana da economia e nula
            MACROS["sfNilRho"] = f"{bordas[k]:g}"
    Tx += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_semescala.tex"), "w", encoding="utf-8").write("\n".join(Tx) + "\n")
    MACROS.update({"sfPares": str(len(pares)), "sfLay": str(len(MJ)), "rhoCertMed": f"{np.median(rc):.1f}", "rhoCertLo": f"{min(rc):.1f}", "rhoCertHi": f"{max(rc):.1f}",
                   "sfPerMed": f"{np.median([r['L_corte'] / r['n_contornos'] for r in Dj]):.0f}"})
    # exemplo ilustrativo (premissas, nao dados): reinicio de 10 ms e de 0,1 s numa maquina que voa a 140 m/min, contornos de perimetro medio 300 mm
    v_mm_s, per = 140 * 1000 / 60.0, 300.0
    MACROS.update({"exFlA": f"{0.01 * v_mm_s:.0f}", "exFlB": f"{0.1 * v_mm_s:.0f}", "exRhoA": f"{0.01 * v_mm_s / per:.2f}", "exRhoB": f"{0.1 * v_mm_s / per:.2f}"})


def macros_proposicao3():
    """Verificacao numerica da Proposicao 3 (curva exata da economia, convexa e nao crescente; as retas dos planos guardados como cotas inferiores do ponto de equilibrio exato) nos
    valores exatos guardados (EXPLORATORIO, POS-HOC de 19/11/2026; nenhum solver e rodado; layouts de contornos disjuntos sem furos). Conta como violacao: um programa cujo tempo nao
    e L/v_c + A/v_a + t R; uma economia S(t) nao convexa ou crescente na grade; uma reta de plano acima do primeiro ponto da grade com economia nula."""
    import analise_ancoras_por_espessura as ae
    T = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(A, "teto_resultados", "*.json"))}
    MJ = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(A, "milp_certificado_resultados", "*.json")))]
    if not T or not MJ:
        return
    viol = 0
    larg_grade, larg_reta, n_aperta = [], [], 0
    for reg in MJ:
        r = T[reg["instancia"]]
        L_, n_, AP, As = r["L_corte"], r["n_contornos"], r["dp"]["ar_otimo_contorno"], r["ar_otimo"]
        P0 = L_ / VC + AP / VA                                              # otimo EXATO de contorno (DP) em t = 0
        pts = {0.0: (L_ / VC + min(AP, As) / VA, None, None)}               # (M, R, A) por t da grade; em t = 0 o RPP exato (R nao e guardado)
        for t in ae.TS_CURVA[1:]:
            x = reg["t"].get(str(t))
            if x and x.get("otimo"):
                pts[t] = (x["M"], x["R"], x["ar_len"])
                viol += int(abs(x["M"] - (L_ / VC + x["ar_len"] / VA + t * x["R"])) > 1e-6 * x["M"])
        ts = sorted(pts)
        S = {t: (P0 + t * n_) - pts[t][0] for t in ts}
        dec = [(S[b] - S[a]) / (b - a) for a, b in zip(ts, ts[1:])]
        viol += int(any(d2 < d1 - 1e-6 for d1, d2 in zip(dec, dec[1:]))) + int(any(d > 1e-6 for d in dec))
        nulo = [t for t in ts if S[t] <= 1e-5 * (P0 + t * n_)]
        if not nulo:
            continue
        t_zero = min(nulo)
        lo_grade = max([t for t in ts if S[t] > 1e-5 * (P0 + t * n_)] or [0.0])
        raizes = [(P0 - (L_ / VC + Ak / VA)) / (R - n_) for (_, R, Ak) in pts.values() if R is not None and R > n_ and P0 > L_ / VC + Ak / VA]
        viol += sum(1 for x in raizes if x > t_zero + 1e-9)                  # uma reta de plano nao pode ultrapassar o primeiro zero da grade
        lo_reta = max([lo_grade] + raizes)
        larg_grade.append(t_zero - lo_grade)
        larg_reta.append(t_zero - lo_reta)
        n_aperta += int(lo_reta > lo_grade + 1e-9)
    MACROS.update({"pthLay": str(len(MJ)), "pthViol": str(viol), "pthNBr": str(len(larg_grade)), "pthNTight": str(n_aperta),
                   "pthWGrid": f"{np.median(larg_grade):.3f}", "pthWLine": f"{np.median(larg_reta):.3f}"})


def macros_layouts_reais():
    """Leitura sem escala nos layouts REAIS do conjunto confirmatorio CPPLib (V2; EXPLORATORIO, POS-HOC de 19/11/2026; so valores guardados em v2_resultados/, nenhum solver e rodado).
    Economia da rota ciente do reinicio a t = 1 s sobre a referencia de contorno, em % do tempo total, com o contorno cobrado um reinicio por contorno (convencao do artigo, limite
    superior onde os contornos se tocam); a versao CONSERVADORA cobra so as corridas da rota onde estas sao menos que os contornos. rho_1 = 1 s * v_a / perimetro medio (L_pecas / n)."""
    from scipy import stats
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(A, "v2_resultados", "v2_*.json")))]
    P = [r for r in R if r.get("n_contornos", 0) >= 2 and r.get("peca_10s") and r["seg_t0"]["melhor"] and r["seg_t1"]["melhor"]]
    if not P:
        return
    X = []
    for r in P:
        n, Lp = r["n_contornos"], r["L_pecas"]
        assert abs(Lp - r["L_segmento"]) <= 1e-6 * Lp, "layout com arestas compartilhadas: o texto diz que nao ha nenhum"
        m1 = r["seg_t1"]["melhor"]
        tot = r["peca_10s"]["fo_media"] + 1.0 * n
        S = 100.0 * (tot - m1["fo"]) / tot
        vies = 100.0 * max(0, n - m1["n_perf"]) / tot                       # reinicios que o nivel de contorno paga a mais se a rota encadeia contornos
        X.append({"n": n, "per": Lp / n, "rho": 1.0 * VA / (Lp / n), "S": S, "vies": vies, "Sc": S - vies, "chain": m1["n_perf"] < n,
                  "ve": m1["viol_estrita"] / n if m1.get("viol_estrita") is not None else None})
    lim = float(MACROS.get("sfNilRho", "0.3"))
    low, high = [x for x in X if x["rho"] <= lim], [x for x in X if x["rho"] > lim]
    chain = [x for x in X if x["chain"]]
    pers = [x for x in high if x["Sc"] > 0.1]
    sem_pct = lambda v: fmt(v, 2).replace(r"\%", "")
    sp = lambda a, b: stats.spearmanr(a, b)[0]
    VE = [x for x in X if x["ve"] is not None]
    MACROS.update({"rlN": str(len(X)), "rlNmin": str(min(x["n"] for x in X)), "rlNmax": str(max(x["n"] for x in X)),
                   "rlPerMed": f"{np.median([x['per'] for x in X]):.0f}", "rlPerMin": f"{min(x['per'] for x in X):.0f}", "rlPerMax": f"{max(x['per'] for x in X):.0f}",
                   "rlRhoMed": f"{np.median([x['rho'] for x in X]):.2f}", "rlRhoMin": f"{min(x['rho'] for x in X):.2f}", "rlRhoMax": f"{max(x['rho'] for x in X):.2f}",
                   "rlNLow": str(len(low)), "rlNHigh": str(len(high)), "rlNChain": str(len(chain)), "rlThr": "0.1" + r"\%",
                   "rlSMed": fmt(np.median([x["S"] for x in X]), 2),
                   "rlSLowMed": fmt(np.median([x["S"] for x in low]), 2), "rlSLowMax": fmt(max(x["S"] for x in low), 2, sinal=False),
                   "rlSHighMed": fmt(np.median([x["S"] for x in high]), 2), "rlSHighMax": fmt(max(x["S"] for x in high), 2, sinal=False),
                   "rlSMaxCor": fmt(max(x["Sc"] for x in X), 2, sinal=False),
                   "rlSpAs": sem_pct(sp([x["rho"] for x in X], [x["S"] for x in X])), "rlSpCor": sem_pct(sp([x["rho"] for x in X], [x["Sc"] for x in X])),
                   "rlSpViol": sem_pct(sp([x["ve"] for x in VE], [x["Sc"] for x in VE])),
                   "rlBiasMed": fmt(np.median([x["vies"] for x in chain]), 2, sinal=False) if chain else "0",
                   "rlPersN": str(len(pers))})
    if pers:
        MACROS.update({"rlPersRhoLo": f"{min(x['rho'] for x in pers):.2f}", "rlPersRhoHi": f"{max(x['rho'] for x in pers):.2f}",
                       "rlPersLo": fmt(min(x["Sc"] for x in pers), 2, sinal=False), "rlPersHi": fmt(max(x["Sc"] for x in pers), 2, sinal=False)})


def macros_newton():
    """Ponto de equilibrio EXATO por iteracao de Newton (Proposicao 3; `caso_a_corte_multitecnologia/newton_exato_tc.py`, pre-especificado em docs/52; MILPs novos de 19/11/2026).
    So le os resultados guardados em newton_resultados/ (um JSON por layout, com a trilha completa)."""
    fs = sorted(glob.glob(os.path.join(A, "newton_resultados", "*.json")))
    if not fs:
        return
    R = [json.load(open(f)) for f in fs]
    ex = [r for r in R if r["status"] == "exato"]
    nsp = sum(1 for r in R if r["status"] == "sem_prova")
    sem_prova = ("" if nsp == 0 else ("In the other layout a programme did not finish" if nsp == 1 else f"In the other {nsp} layouts a programme did not finish") + " even with the longest limit, so that only the interval remains.")
    lims = sorted({r["limite_s"] for r in R})                                                      # os limites tentados (1800 s para todos; repeticoes com limites maiores nos que nao fecharam: docs/52 D4, docs/55 parte D)
    lim_sent = f"a limit of {lims[0]:.0f}" + r"\,s per programme"
    for i, L_ in enumerate(lims[1:]):
        n_i = sum(1 for r in R if r["limite_s"] >= L_)                                             # layouts repetidos com o limite L_ (alcancaram o anterior)
        lim_sent += (", extended to " if i == 0 else " and to ") + f"{L_:.0f}" + r"\,s in the " + str(n_i) + (" layouts that reached it" if i == 0 else " that reached that")
    MACROS.update({"nwN": str(len(R)), "nwExact": str(len(ex)), "nwNoProof": str(nsp), "nwNoProofSent": sem_prova, "nwLimSent": lim_sent})
    if not ex:
        return
    novos = [sum(1 for x in r["trilha"] if "M" in x) for r in ex]
    tc = [r["t_c"] for r in ex]
    rho = [r["t_c"] * VA * r["n"] / r["L"] for r in ex]
    razao = [r["t_c"] / r["t_cert"] for r in ex]
    MACROS.update({"nwSolves": str(sum(novos)), "nwSolvesMax": str(max(novos)),
                   "nwTcMed": f"{np.median(tc):.3f}", "nwTcMin": f"{min(tc):.3f}", "nwTcMax": f"{max(tc):.3f}",
                   "nwRhoMed": f"{np.median(rho):.2f}", "nwRhoMin": f"{min(rho):.2f}", "nwRhoMax": f"{max(rho):.2f}", "nwRatioMed": f"{np.median(razao):.2f}", "nwRatioMax": f"{max(razao):.2f}",
                   "nwLimA": f"{min(r['limite_s'] for r in R):.0f}", "nwLimB": f"{max(r['limite_s'] for r in R):.0f}",
                   "nwRetry": str(sum(1 for r in R if r["limite_s"] == max(q["limite_s"] for q in R))) if len({q["limite_s"] for q in R}) > 1 else "0",     # layouts repetidos com o limite maior (docs/52, D4)
                   "nwHfive": "supported" if (0.04 <= np.median(tc) <= 0.15 and max(rho) <= 1) else "not supported",           # previsoes empiricas de docs/52 (H-N5, H-N6)
                   "nwHsix": "supported" if np.median(razao) <= 0.5 else "not supported"})


def tabela_newton():
    """Tabela por layout do ponto de equilibrio exato (Proposicao 3; `caso_a_corte_multitecnologia/newton_resultados/`, pre-especificado em docs/52): so le os resultados guardados (um JSON por layout)."""
    fs = sorted(glob.glob(os.path.join(A, "newton_resultados", "*.json")))
    if not fs:
        return
    R = [json.load(open(f)) for f in fs]
    Tx = [r"\begin{table}[t]", r"\centering\footnotesize",
          r"\caption{Exact break-even restart cost of each layout, by the iteration of Proposition~\ref{prop:curve} (pre-specified; stored values; the mixed-integer programme is the exact solver). $n$: contours; $R_0$: runs of the stored plan of largest root, where the iteration starts; zero on the grid: first grid point at which the exact saving is proved nil; MILPs: exact programmes solved by the iteration; $t_c$: exact break-even restart cost; $t_{\mathrm{cert}}$: certificate of Proposition~\ref{prop:cert}; $\rho_c=t_c v_a n/L$: break-even in mean contour perimeters." + (r" A dash: no programme finished within the longest limit, so that only the interval from the grid remains." if any(r_["status"] != "exato" for r_ in R) else "") + "}",
          r"\label{tab:n1_newton}", r"\begin{tabular}{lrrrrrrrr}", r"\toprule",
          r"Layout & $n$ & $R_0$ & \shortstack{Zero on\\grid (s)} & MILPs & $t_c$ (s) & $t_{\mathrm{cert}}$ (s) & $t_c/t_{\mathrm{cert}}$ & $\rho_c$ \\", r"\midrule"]
    for r in R:
        nome = r["instancia"].replace("_", r"\_")
        novos = sum(1 for x in r["trilha"] if "M" in x)
        if r["status"] == "exato":
            tc, razao, rho = f"{r['t_c']:.3f}", f"{r['t_c'] / r['t_cert']:.2f}", f"{r['t_c'] * VA * r['n'] / r['L']:.2f}"
        else:
            tc = razao = rho = "--"
        Tx.append("\\texttt{" + nome + "} & " + f"{r['n']} & {r['trilha'][0]['R']} & {r['hi_grade']:g} & {novos} & {tc} & {r['t_cert']:.3f} & {razao} & {rho} " + r"\\")
    Tx += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_newton.tex"), "w", encoding="utf-8").write("\n".join(Tx) + "\n")


def macros_causa():
    """Causa da economia persistente nos layouts aninhados com rho_1 > 0,3 (`caso_a_corte_multitecnologia/causa_aninhados_v2.py`; pre-especificado em docs/52; so le os resultados guardados)."""
    import causa_aninhados_v2 as cn
    if not os.path.isdir(cn.OUT):
        return
    V2 = cn.v2_dados()
    nomes = cn.selecionados()
    c, s, gaps = [], [], []
    for nome in nomes:
        r = V2[nome]
        fe, fd = os.path.join(cn.OUT, f"est_{nome}.json"), os.path.join(cn.OUT, f"dp_{nome}.json")
        e = json.load(open(fe))["melhor"] if os.path.exists(fe) else None
        c.append(cn.economia(r, r["seg_t1"]["melhor"]))
        s.append(cn.economia(r, e) if e else None)
        d = json.load(open(fd)) if os.path.exists(fd) else None
        if d and d.get("resolvida"):
            gaps.append(100.0 * (r["peca_10s"]["fo_media"] / d["fo_otimo"] - 1.0))
    ok = [(a, b) for a, b in zip(c, s) if b is not None]
    MACROS.update({"cnN": str(len(nomes)), "cnStrictN": str(len(ok)), "cnDpN": str(len(gaps)),
                   "cnClosLo": fmt(min(c), 2, sinal=False), "cnClosHi": fmt(max(c), 2, sinal=False)})
    if ok:
        MACROS.update({"cnStrLo": fmt(min(b for _, b in ok), 2), "cnStrHi": fmt(max(b for _, b in ok), 2, sinal=False), "cnHalf": str(sum(1 for a, b in ok if b < 0.5 * a)),
                       "cnNil": str(sum(1 for _, b in ok if abs(b) <= 0.01))})                  # economia estrita nula: |S| <= 0,01% do tempo total
        resto = [100.0 * (1.0 - b / a) for a, b in ok if b >= 0.5 * a]                            # os layouts em que a estrita NAO derrubou a economia a menos da metade (previsao P-C1 de docs/52)
        if resto:
            MACROS.update({"cnRest": str(len(resto)), "cnRedLo": f"{min(resto):.0f}" + r"\%", "cnRedHi": f"{max(resto):.0f}" + r"\%"})
    if gaps:
        gmax = max(abs(g) for g in gaps)
        MACROS["cnDpMax"] = ("0.001" if gmax < 1e-3 else f"{gmax:.3f}") + r"\%"                  # cota superior arredondada para cima (0,001% se menor)

    def economia_replica(sem, nome):                                              # replica com sementes novas (docs/52, D3): economia conservadora ou None
        f = os.path.join(cn.OUT, f"rep_{sem}_{nome}.json")
        m = json.load(open(f))["melhor"] if os.path.exists(f) else None
        return cn.economia(V2[nome], m) if m else None
    rc, rs = [economia_replica("fechamento", n) for n in nomes], [economia_replica("estrita", n) for n in nomes]
    if all(x is not None for x in rc + rs):
        MACROS.update({"cnRepClosLo": fmt(min(rc), 2, sinal=False), "cnRepClosHi": fmt(max(rc), 2, sinal=False), "cnRepStrLo": fmt(min(rs), 2), "cnRepStrHi": fmt(max(rs), 2),
                       "cnPTres": str(sum(1 for a, b in zip(c, rc) if b >= 0.75 * a)), "cnPQuatro": str(sum(1 for a, b in zip(s, rs) if abs(a - b) <= 0.05))})


def tabela_orcamento():
    """Orcamento e esforco de busca do PCGLNS no teste da causa nos 4 layouts aninhados (`caso_a_corte_multitecnologia/causa_aninhados_orcamento.py` e `causa_aninhados_slow.py`; pre-especificado em docs/55 e
    docs/55_desvios.md; so le os resultados guardados): economia conservadora a t = 1 s com o orcamento original, com o teto de 600 s no modo default e no modo slow; macros e tabela."""
    import causa_aninhados_v2 as cn
    SL = os.path.join(A, "causa_aninhados_resultados_slow")
    if not (os.path.isdir(cn.OUT) and os.path.isdir(SL)):
        return
    V2 = cn.v2_dados()
    F = []
    for nome in cn.selecionados():
        r = V2[nome]
        orig = {"fechamento": r["seg_t1"]["melhor"], "estrita": json.load(open(os.path.join(cn.OUT, f"est_{nome}.json")))["melhor"]}
        for sem in ("fechamento", "estrita"):
            fc, fs = os.path.join(cn.OUT, f"orc_{sem}_{nome}.json"), os.path.join(SL, f"orc_{sem}_{nome}.json")
            if not (os.path.exists(fc) and os.path.exists(fs)):
                return                                                           # incompleto: nem macros nem tabela
            rc, rs = json.load(open(fc)), json.load(open(fs))
            mo, mc, ms = orig[sem], rc["melhor"], rs["melhor"]
            if not (mo and mc and ms):
                return
            F.append({"nome": nome, "curto": nome.split("__")[-1], "n": r["n_contornos"], "E": rc["E"], "sem": sem, "t_orig": rc["tempo_original_s"], "t_cap": rc["tempo_total_s"], "t_slow": rs["tempo_total_s"],
                      "s_o": cn.economia(r, mo), "s_c": cn.economia(r, mc), "s_s": cn.economia(r, ms),
                      "d_c": 100.0 * (mc["fo"] / mo["fo"] - 1.0), "d_s": 100.0 * (ms["fo"] / mo["fo"] - 1.0)})
    Tx = [r"\begin{table}[t]", r"\centering\footnotesize\setlength{\tabcolsep}{3.5pt}",
          r"\caption{PCGLNS budget and search effort in the test of the cause on the four nested layouts (pre-specified; protocol and deviations in the repository). Saving of the segment-level route over the contour-level reference at $t=1$\,s (conservative, in \% of the total time), under the closing and the strict precedence. Original: the budget of the main experiment ($\min(120,\,20+E/4)$\,s per round, default mode of the solver); cap 600\,s: default mode with a cap of 600\,s per round; slow: slow mode of the solver (more iterations and trials), same cap. $\Delta$FO: change of the best total time against the original, in \%. Seeds 0 and 1, two rounds, in every case. Times: both rounds, in seconds. $n$: contours; $E$: arcs.}",
          r"\label{tab:n1_orcamento}", r"\begin{tabular}{llrrrrrrrrr}", r"\toprule",
          r"Layout & Precedence & $n$ & $E$ & Original & Cap 600\,s & Slow & $\Delta$FO slow & Time original & Time cap & Time slow \\", r"\midrule"]
    for x in F:
        Tx.append(f"\\texttt{{{x['curto'].replace('_', chr(92) + '_')}}} & {'closing' if x['sem'] == 'fechamento' else 'strict'} & {x['n']} & {x['E']} & {fmt_sem_pct(x['s_o'], 3)} & {fmt_sem_pct(x['s_c'], 3)} & {fmt_sem_pct(x['s_s'], 3)} & {fmt_sem_pct(x['d_s'], 3)} & $\\le{2 * x['t_orig']}$ & {x['t_cap']:.0f} & {x['t_slow']:.0f} " + r"\\")
    Tx += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_orcamento.tex"), "w", encoding="utf-8").write("\n".join(Tx) + "\n")
    C, S = [x for x in F if x["sem"] == "fechamento"], [x for x in F if x["sem"] == "estrita"]
    rng = lambda L_, k, casas=2: (fmt(min(y[k] for y in L_), casas, sinal=False), fmt(max(y[k] for y in L_), casas, sinal=False))
    n_lay = len(C)
    dsav = lambda L_, a, b: max(abs(y[a] - y[b]) for y in L_)
    ligado = sum(1 for x in F if x["t_cap"] > 2 * x["t_orig"] + 15)                # o teto original limitava a execucao (a nova levou mais que as duas rodadas do orcamento original)
    p1a, p1b = sum(1 for x in C if abs(x["s_c"] - x["s_o"]) <= 0.05), sum(1 for x in S if abs(x["s_c"] - x["s_o"]) <= 0.05)
    p3 = sum(1 for x in S if x["s_c"] <= 0.10)
    q1, q2 = sum(1 for x in C if abs(x["s_s"] - x["s_o"]) <= 0.05), sum(1 for x in S if abs(x["s_s"] - x["s_o"]) <= 0.05)
    q3 = sum(1 for x in S if x["s_s"] <= 0.10)
    sup = lambda ok: "supported" if ok else "not supported"
    est_c = all(c_["s_c"] >= s_["s_c"] - 1e-9 for c_, s_ in zip(C, S))                          # P-O2: com o teto de 600 s, fechamento >= estrita em todos os layouts
    est_s = all(c_["s_s"] >= s_["s_s"] - 1e-9 for c_, s_ in zip(C, S))                          # P-S4: idem no modo slow
    conv_c = min(sum(1 for x in C if abs(x["d_c"]) <= 0.01), sum(1 for x in S if abs(x["d_c"]) <= 0.01)) >= 3     # P-O4: o melhor FO muda <= 0,01% em >= 3 de 4, por semantica
    diag_s = min(sum(1 for x in C if x["d_s"] <= 0.01), sum(1 for x in S if x["d_s"] <= 0.01)) >= 3               # P-S5: o modo slow nao e pior que o original em mais de 0,01% em >= 3 de 4, por semantica
    MACROS.update({"bgOStr": sup(est_c), "bgOConv": sup(conv_c), "bgSStr": sup(est_s), "bgSDiag": sup(diag_s)})
    MACROS.update({"bgN": str(n_lay), "bgTasks": str(len(F)), "bgBound": str(ligado), "bgFree": str(len(F) - ligado),
                   "bgRatioLo": f"{600 / max(x['t_orig'] for x in F):.0f}", "bgRatioHi": f"{600 / min(x['t_orig'] for x in F):.0f}",
                   "bgClosOrigLo": rng(C, "s_o")[0], "bgClosOrigHi": rng(C, "s_o")[1], "bgClosCapLo": rng(C, "s_c")[0], "bgClosCapHi": rng(C, "s_c")[1], "bgClosSlowLo": rng(C, "s_s")[0], "bgClosSlowHi": rng(C, "s_s")[1],
                   "bgStrOrigLo": fmt(min(x["s_o"] for x in S), 2), "bgStrOrigHi": fmt(max(x["s_o"] for x in S), 2, sinal=False), "bgStrCapLo": fmt(min(x["s_c"] for x in S), 2), "bgStrCapHi": fmt(max(x["s_c"] for x in S), 2, sinal=False),
                   "bgStrSlowLo": fmt(min(x["s_s"] for x in S), 2), "bgStrSlowHi": fmt(max(x["s_s"] for x in S), 2, sinal=False),
                   "bgDSavCap": f"{max(dsav(C, 's_c', 's_o'), dsav(S, 's_c', 's_o')):.3f}", "bgDSavSlow": f"{max(dsav(C, 's_s', 's_o'), dsav(S, 's_s', 's_o')):.3f}",
                   "bgDSavMax": f"{max(dsav(C, 's_c', 's_o'), dsav(S, 's_c', 's_o'), dsav(C, 's_s', 's_o'), dsav(S, 's_s', 's_o')):.3f}",
                   "bgDFoCap": f"{max(abs(x['d_c']) for x in F):.3f}" + r"\%", "bgDFoSlow": f"{max(abs(x['d_s']) for x in F):.3f}" + r"\%",
                   "bgDFoSlowUp": f"{max(x['d_s'] for x in F):.3f}" + r"\%",                                  # a maior piora do modo slow sobre o original (se > 0)
                   "bgOa": str(p1a), "bgOb": str(p1b), "bgOc": str(p3), "bgSa": str(q1), "bgSb": str(q2), "bgSc": str(q3),
                   "bgOkAll": sup(min(p1a, p1b, p3, q1, q2, q3) >= 3)})
    assert MACROS["bgOkAll"] == "supported" and all(MACROS[k] == "supported" for k in ("bgOStr", "bgOConv", "bgSStr", "bgSDiag")), \
        "alguma previsao do teste de orcamento (docs/55) nao foi sustentada: reescreva a secao D.4 e a frase da secao 6.7, que dizem 'sustentadas'"      # o texto afirma que todas foram sustentadas


def tabela_tamanho(L):
    """Tamanho do layout (numero de contornos) nas 282 sinteticas (item 5 de docs/48; EXPLORATORIO, POS-HOC): parcela de voo, ganho da heuristica a t = 0 e ponto de equilibrio, so de valores guardados."""
    from scipy import stats
    X = []
    for x in L:
        if not x.get("corte_s"):
            return
        ar_p = x["peca"] - x["corte_s"]
        per = x["corte_s"] * VC / x["nc"]
        te = (x["peca"] - x["H0.0"]) / (x["R0.25"] - x["nc"]) if (x["R0.25"] > x["nc"] and x["peca"] > x["H0.0"]) else None
        X.append({"n": x["nc"], "per": per, "alpha": 100 * ar_p / x["peca"], "ganho": 100 * (x["peca"] - x["H0.0"]) / x["peca"], "ganho_ar": 100 * (x["peca"] - x["H0.0"]) / ar_p, "te": te, "rho": te * VA / per if te else None})
    faixas = ((10, 20, "10 to 20"), (21, 40, "21 to 40"), (41, 80, "41 to 80"), (81, 10 ** 6, "81 to " + str(max(x["n"] for x in X))))
    Tx = [r"\begin{table}[t]", r"\centering\small",
          r"\caption{Layout size on the " + str(len(X)) + r" synthetic instances (exploratory, post hoc; stored values). Air share: air time over total time of the contour-level route, at $t=0$. Gain: reduction of the total time and of the air time of the contour-level route that the heuristic obtains under the formal cost, at $t=0$. Break-even: restart cost at which the heuristic stops being ahead (Eq.~\eqref{eq:tstar}), in seconds and in mean contour perimeters ($\rho^\ast=t^\ast v_a/\bar\ell$), over the instances in which it is ahead at $t=0$ and cuts more runs than contours. $\bar\ell$: mean contour perimeter in drawing units. Medians.}",
          r"\label{tab:n1_size}", r"\begin{tabular}{lrrrrrrr}", r"\toprule",
          r"Contours & Instances & $\bar\ell$ & Air share & \shortstack{Gain,\\total} & \shortstack{Gain,\\air} & \shortstack{Break-even\\(s)} & $\rho^\ast$ \\", r"\midrule"]
    for lo, hi, rot in faixas:
        S = [x for x in X if lo <= x["n"] <= hi]
        if not S:
            continue
        B = [x for x in S if x["te"]]
        Tx.append(f"{rot} & {len(S)} & {np.median([x['per'] for x in S]):.0f} & {np.median([x['alpha'] for x in S]):.2f}\\% & {np.median([x['ganho'] for x in S]):.2f}\\% & {np.median([x['ganho_ar'] for x in S]):.0f}\\% & {np.median([x['te'] for x in B]):.3f} & {np.median([x['rho'] for x in B]):.2f} " + r"\\")
    Tx += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    open(os.path.join(TAB, "n1_tamanho.tex"), "w", encoding="utf-8").write("\n".join(Tx) + "\n")
    n_ = [x["n"] for x in X]
    B = [x for x in X if x["rho"]]
    MACROS.update({"sizeNmin": str(min(n_)), "sizeNmed": f"{np.median(n_):.0f}", "sizeNmax": str(max(n_)),
                   "sizeSpAir": fmt(stats.spearmanr(n_, [x["alpha"] for x in X])[0], 2), "sizeSpGain": fmt(stats.spearmanr(n_, [x["ganho"] for x in X])[0], 2),
                   "sizeSpRho": fmt(stats.spearmanr([x["n"] for x in B], [x["rho"] for x in B])[0], 2), "sizeRhoMed": f"{np.median([x['rho'] for x in B]):.2f}"})
    for k in ("SpAir", "SpGain", "SpRho"):                                    # coeficientes de Spearman: sem o sinal de percentagem
        MACROS["size" + k] = MACROS["size" + k].replace(r"\%", "")


def legendas_abaixo():
    r"""Move \caption e \label de cada tabela gerada para depois do \end{tabular} (estilo do LCPP-1: legenda abaixo). Idempotente."""
    import glob
    for f in sorted(glob.glob(os.path.join(TAB, "n1_*.tex"))):
        t = open(f, encoding="utf-8").read()
        i = t.find("\\caption{")
        if i < 0 or t.find("\\end{tabular}") < i:
            continue                                                     # sem legenda ou ja esta abaixo
        j, nivel = i + len("\\caption"), 0
        while True:                                                      # casa as chaves da legenda
            c = t[j]
            nivel += (c == "{") - (c == "}")
            j += 1
            if nivel == 0:
                break
        k = j
        while t[k] in " \n":
            k += 1
        if not t.startswith("\\label{", k):
            raise SystemExit("legenda sem \\label logo depois em " + f)
        k = t.index("}", k) + 1
        bloco = t[i:k].strip()
        t = t[:i] + t[k:].lstrip("\n")
        fim = t.rindex("\\end{table}")
        t = t[:fim] + bloco + "\n" + t[fim:]
        open(f, "w", encoding="utf-8").write(t)


TABELAS_PULADAS = []


def _pular(tabela, motivo):
    """Registra e avisa uma tabela que nao pode ser regenerada neste ambiente (as que avaliam rotas guardadas, que contem geometria de instancias, exigem as rotas)."""
    TABELAS_PULADAS.append(tabela)
    print(f"AVISO: {tabela} NAO foi regenerada: {motivo}")


def _garantir_amostra_v3():
    """Sem os arquivos de instancia (repositorio publico) `rodar_v3.amostra()` devolve vazio; usa os 60 nomes guardados (`auditoria_lcpp1/nomes_amostra_v3.txt`) e,
    quando as instancias existem, confere que o sorteio de semente 2027 reproduz exatamente a lista guardada."""
    import rodar_v3 as rv
    arq = os.path.join(A, "auditoria_lcpp1", "nomes_amostra_v3.txt")
    guardados = [s for s in open(arq, encoding="utf-8").read().strip().split(",") if s]
    sorteados = rv.amostra()
    if sorteados:
        assert sorted(sorteados) == sorted(guardados), "a amostra sorteada difere da guardada"
    else:
        rv.amostra = lambda: list(guardados)
        print("amostra V3: usando os nomes guardados (sem os arquivos de instancia)")


def main():
    _garantir_amostra_v3()
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
    macros_corridas_contorno(L)
    tabela_otimo(L)
    tabela_v2()
    tabela_v3()
    tabela_reparo()
    tabela_teto(L)
    tabela_espessura()
    tabela_velocidades()
    tabela_sem_escala()
    macros_proposicao3()
    macros_layouts_reais()
    macros_newton()
    tabela_newton()
    macros_causa()
    tabela_orcamento()
    tabela_tamanho(L)
    macros_familias(L)
    macros_repositorio_publico()
    legendas_abaixo()
    out = ["% gerado por manuscrito/gerar_tabelas_n1.py -- nao editar a mao"]
    out += [r"\newcommand{\%s}{%s}" % (k, v) for k, v in sorted(MACROS.items())]
    open(os.path.join(AQUI, "N1", "numeros_n1.tex"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("macros:", len(MACROS), "| instancias:", len(L))
    if TABELAS_PULADAS:
        print("tabelas NAO regeneradas (precisam das rotas guardadas, que contem geometria):", ", ".join(TABELAS_PULADAS))
    for k, v in sorted(MACROS.items()):
        print(f"  {k} = {v}")


if __name__ == "__main__":
    main()
