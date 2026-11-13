r"""
gerar_figuras_n1.py  --  figuras do manuscrito N1 EM TikZ/pgfplots (nada digitado a mao: tudo sai dos arquivos de resultado; a Figura 1 e um layout de brinquedo nosso, resolvido por DP exato)
==========================================================================================================================================================================
Saida: manuscrito/N1/figuras/fig_n1_*.tex  (fragmentos para \input dentro de \begin{figure}; estilo comum em figuras/n1_estilo_figuras.tex) e N1/numeros_figuras.tex
Fig. 1 (fig_n1_brinquedo)   layout de brinquedo (3 retangulos), rota de contornos x rota de segmentos (ambas otimas por enumeracao/DP) e o ponto de equilibrio t* do reinicio
Fig. 2 (fig_n1_convencoes)  distribuicao, por categoria, da diferenca heuristica x PCGLNS por contorno nas convencoes executavel e formal (282 instancias sinteticas)
Fig. 3 (fig_n1_reinicio)    (a) fracao das instancias em que a rota segue melhor que a de contorno em funcao de t; (b) rota cega, (c) rotas cientes do reinicio (mediana de T/T_P - 1 contra t)
Fig. 4 (fig_n1_espessura)   (a) curva EXATA da economia maxima de qualquer plano em funcao de t (MILP); (b) faixas do custo de reinicio por espessura (literatura; retomada derivada)
Fig. 5 (fig_n1_voo)         (a) tempo de um movimento de voo tau(d) nos modelos usados; (b) vantagem do nivel de segmento reotimizado (todas / mesmo corte / arestas compartilhadas)
Uso: python gerar_figuras_n1.py
"""
import itertools
import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
A = os.path.join(RAIZ, "caso_a_corte_multitecnologia")
sys.path.insert(0, A)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "src_base"))
os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
import gerar_tabelas_n1 as gt                                           # noqa: E402
import analise_voo_nao_linear as vn                                     # noqa: E402
import analise_mapa_regimes as am                                       # noqa: E402
import rodar_v3 as rv                                                   # noqa: E402

OUT = os.path.join(AQUI, "N1", "figuras")
os.makedirs(OUT, exist_ok=True)
VCUT, VAIR = 100.0 / 6.0, 400.0


def g(x):
    return f"{x:.5g}"


def cs(xs, ys):
    return " ".join(f"({g(x)},{g(y)})" for x, y in zip(xs, ys))


def escrever(nome, texto):
    with open(os.path.join(OUT, nome + ".tex"), "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


# ---------------------------------------------------------------------------------------------------------------- Fig. 1: layout de brinquedo
def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def contorno_exato(polis, O, t):
    """Rota de contornos otima: ordem x vertice de entrada (cada contorno em uma corrida, saida no vertice de entrada)."""
    best, n = None, len(polis)
    for perm in itertools.permutations(range(n)):
        for ent in itertools.product(range(4), repeat=n):
            ar, pos = 0.0, O
            for ci, e in zip(perm, ent):
                ar += cheb(pos, polis[ci][e])
                pos = polis[ci][e]
            ar += cheb(pos, O)
            T = ar / VAIR + t * n
            if best is None or T < best[1] - 1e-12:
                best = (ar, T, [(ci, e) for ci, e in zip(perm, ent)])
    return best


def segmento_exato(polis, O, t):
    """Rota de segmentos otima por DP em subconjuntos sobre servicos orientados (custo: ar / v_ar + t por corrida)."""
    S = [(P[i], P[(i + 1) % 4], ci) for ci, P in enumerate(polis) for i in range(4)]
    m = len(S)
    orient = [(i, d) for i in range(m) for d in (0, 1)]
    ini = lambda o: S[o[0]][0] if o[1] == 0 else S[o[0]][1]
    fim = lambda o: S[o[0]][1] if o[1] == 0 else S[o[0]][0]
    dp = [dict() for _ in range(1 << m)]
    for k, o in enumerate(orient):
        d = cheb(O, ini(o))
        dp[1 << o[0]][k] = (d / VAIR + t, d, None)
    for mask in range(1, 1 << m):
        for k, (T, ar, _) in list(dp[mask].items()):
            for k2, o2 in enumerate(orient):
                if mask >> o2[0] & 1:
                    continue
                d = cheb(fim(orient[k]), ini(o2))
                T2 = T + d / VAIR + (t if d > 1e-12 else 0.0)
                nm = mask | (1 << o2[0])
                cur = dp[nm].get(k2)
                if cur is None or T2 < cur[0] - 1e-12:
                    dp[nm][k2] = (T2, ar + d, (mask, k))
    full = (1 << m) - 1
    best = None
    for k, (T, ar, _) in dp[full].items():
        d = cheb(fim(orient[k]), O)
        if best is None or T + d / VAIR < best[0] - 1e-12:
            best = (T + d / VAIR, ar + d, k)
    T, ar, k = best
    seq, mask = [], full
    while True:
        seq.append(orient[k])
        pv = dp[mask][k][2]
        if pv is None:
            break
        mask, k = pv
    seq.reverse()
    runs = sum(1 for j, o in enumerate(seq) if j == 0 or cheb(fim(seq[j - 1]), ini(o)) > 1e-12)
    return ar, T, seq, S, runs


def passos_contorno(polis, O, rota):
    out, pos = [], O
    for ci, e in rota:
        P = polis[ci]
        if cheb(pos, P[e]) > 0:
            out.append(("a", pos, P[e]))
        for j in range(4):
            out.append(("c", P[(e + j) % 4], P[(e + j + 1) % 4]))
        pos = P[e]
    if pos != O:
        out.append(("a", pos, O))
    return out


def passos_segmento(S, O, seq):
    out, pos = [], O
    for (i, d) in seq:
        p, q = (S[i][0], S[i][1]) if d == 0 else (S[i][1], S[i][0])
        if cheb(pos, p) > 1e-12:
            out.append(("a", pos, p))
        out.append(("c", p, q))
        pos = q
    if pos != O:
        out.append(("a", pos, O))
    return out


ESTILOS_TOY = (r"x=0.17cm,y=0.17cm,"
               r"cut/.style={line width=1.3pt,black,postaction={decorate},decoration={markings,mark=at position 0.5 with {\arrow{Stealth[length=2.0mm,width=1.6mm]}}}},"
               r"air/.style={line width=0.8pt,fgM,densely dashed,-{Stealth[length=1.6mm,width=1.3mm]},shorten >=1.3mm},"
               r"disc/.style={circle,fill=black,inner sep=0pt,minimum size=2.6mm}")


def tikz_rota(polis, O, passos, titulo, linha2):
    L = [r"\begin{tikzpicture}[" + ESTILOS_TOY + "]"]
    for P in polis:
        cam = " -- ".join(f"({g(x)},{g(y)})" for x, y in P) + " -- cycle"
        L.append(r"\fill[fgXL] " + cam + ";")
        L.append(r"\draw[fgL,line width=0.5pt] " + cam + ";")
    ant = None
    inicios = []
    for tipo, p, q in passos:
        estilo = "air" if tipo == "a" else "cut"
        L.append(r"\draw[" + estilo + "] " + f"({g(p[0])},{g(p[1])}) -- ({g(q[0])},{g(q[1])});")
        if tipo == "c" and ant != "c":
            inicios.append(p)
        ant = tipo
    for p in inicios:
        L.append(r"\node[disc] at " + f"({g(p[0])},{g(p[1])}) {{}};")
    L.append(r"\node[draw,fill=black,minimum size=2.2mm,inner sep=0pt] at (0,0) {};")
    L.append(r"\node[anchor=north west,font=\footnotesize,inner sep=1pt] at (0.8,-0.6) {$O$};")
    L.append(r"\node[anchor=south west,align=left,font=\footnotesize,inner sep=0pt] at (-1,28.8) {\textbf{" + titulo + r"}\\" + linha2 + "};")
    L.append(r"\end{tikzpicture}")
    return "\n".join(L)


def fig_brinquedo():
    O = (0.0, 0.0)
    polis = [rect(5, 8, 10, 10), rect(20, 4, 10, 8), rect(18, 17, 10, 8)]
    c0 = contorno_exato(polis, O, 0.0)
    s0 = segmento_exato(polis, O, 0.0)
    ar_c, ar_s, R_c, R_s = c0[0], s0[0], len(polis), s0[4]
    tstar = (ar_c - ar_s) / VAIR / (R_s - R_c)
    ta = tikz_rota(polis, O, passos_contorno(polis, O, c0[2]), "(a) Contour level", f"{R_c} runs, air moves {ar_c:.0f} units")
    tb = tikz_rota(polis, O, passos_segmento(s0[3], O, s0[2]), "(b) Segment level", f"{R_s} runs, air moves {ar_s:.0f} units")
    ts = np.linspace(0, 0.07, 36)
    dif = ((ar_s / VAIR + R_s * ts) - (ar_c / VAIR + R_c * ts)) * 1000.0
    ymax, ymin = float(dif.max()), float(dif.min())
    y0, y1 = ymin * 1.15, ymax * 1.15
    tc = (r"\begin{tikzpicture}" "\n" r"\begin{axis}[n1axis,width=0.6\textwidth,height=4.4cm,xmin=0,xmax=0.07,ymin=" + g(y0) + ",ymax=" + g(y1) +
          r",xlabel={restart cost $t$ (s per run)},ylabel={time of (b) $-$ time of (a) (ms)},title={(c) Which route is faster?},"
          r"title style={at={(0,1)},anchor=south west,yshift=0.1cm},xtick={0,0.02,0.04,0.06},scaled x ticks=false,xticklabel style={/pgf/number format/fixed}]" "\n"
          r"\addplot[black,line width=1.2pt] coordinates {" + cs(ts, dif) + "};\n"
          r"\draw[black,line width=0.5pt] (axis cs:0,0) -- (axis cs:0.07,0);" "\n"
          r"\draw[fgD,dashed,line width=0.7pt] (axis cs:" + g(tstar) + "," + g(y0) + r") -- (axis cs:" + g(tstar) + "," + g(y1) + ");\n"
          r"\node[anchor=north west,align=left,font=\scriptsize] at (axis cs:" + g(tstar + 0.003) + ",-6) {$t^\\ast=" + f"{tstar:.4f}" + r"$\,s};" "\n"
          r"\node[anchor=north west,align=left,font=\scriptsize,text=fgD] at (axis cs:0.002," + g(y1 * 0.93) + r") {above 0: (a) is faster};" "\n"
          r"\node[anchor=south east,align=right,font=\scriptsize,text=fgD] at (axis cs:0.0685," + g(y0 * 0.93) + r") {below 0: (b) is faster};" "\n"
          r"\end{axis}" "\n" r"\end{tikzpicture}")
    leg = (r"\begin{tikzpicture}[x=1cm,y=1cm,font=\scriptsize]" "\n"
           r"\draw[line width=1.3pt,black,-{Stealth[length=2.0mm,width=1.6mm]}] (0,0) -- (0.9,0); \node[anchor=west] at (1.05,0) {cut move (laser on)};" "\n"
           r"\draw[line width=0.8pt,fgM,densely dashed,-{Stealth[length=1.6mm,width=1.3mm]}] (4.3,0) -- (5.2,0); \node[anchor=west] at (5.35,0) {air move (laser off)};" "\n"
           r"\node[circle,fill=black,inner sep=0pt,minimum size=2.6mm] at (8.9,0) {}; \node[anchor=west] at (9.15,0) {start of a run (a restart)};" "\n"
           r"\node[draw,fill=black,minimum size=2.2mm,inner sep=0pt] at (13.2,0) {}; \node[anchor=west] at (13.45,0) {origin $O$};" "\n"
           r"\end{tikzpicture}")
    texto = (r"\centering" "\n" r"\begin{minipage}[b]{0.47\textwidth}\centering" "\n" + ta + "\n" r"\end{minipage}\hfill" "\n"
             r"\begin{minipage}[b]{0.47\textwidth}\centering" "\n" + tb + "\n" r"\end{minipage}" "\n\n" r"\vspace{8pt}" "\n" + leg + "\n\n" r"\vspace{14pt}" "\n" + tc + "\n")
    escrever("fig_n1_brinquedo", texto)
    return {"toyAirC": f"{ar_c:.0f}", "toyAirS": f"{ar_s:.0f}", "toyAirSave": f"{ar_c - ar_s:.0f}", "toyRunsC": str(R_c), "toyRunsS": str(R_s), "toyTstar": f"{tstar:.4f}"}


# ---------------------------------------------------------------------------------------------------------------- Fig. 2: convencoes por categoria
def categoria(n):
    if "_hole_" in n:
        return "with holes"
    if "_irregular_" in n:
        return "irregular"
    if "_regular_" in n:
        return "regular"
    return "ESICUP-derived"


def resumo5(d):
    d = np.asarray(d, float)
    q1, med, q3 = np.percentile(d, [25, 50, 75])
    iqr = q3 - q1
    return min(x for x in d if x >= q1 - 1.5 * iqr), q1, med, q3, max(x for x in d if x <= q3 + 1.5 * iqr)


def fig_convencoes(L):
    cats = ["regular", "irregular", "with holes", "ESICUP-derived"]
    rng = np.random.default_rng(7)
    partes = []
    for k, (chave, nome) in enumerate((("poli", "(a) Executable-path cost"), ("H0.0", "(b) Formal cost"))):
        dados = [[gt.pct(x[chave], x["peca"]) for x in L if categoria(x["nome"]) == c] for c in cats]
        pos = r"at={(A.east)},anchor=west,xshift=0.35cm,yticklabels={}," if k else ""
        nm = "name=B," if k else "name=A,"
        yl = "" if k else r"yticklabels={regular,irregular,with holes,ESICUP-derived},"
        s = [r"\begin{axis}[n1axis," + nm + pos + yl + r"width=0.43\textwidth,height=5.4cm,xmin=-6.5,xmax=5.6,ymin=0.05,ymax=4.6,y dir=reverse,ytick={1,2,3,4},ymajorgrids=false,xmajorgrids=false,"
             r"xlabel={difference in total time (\%)},title={" + nome + r"},title style={at={(0,1)},anchor=south west,yshift=0.05cm}]"]
        for i, d in enumerate(dados, 1):
            xs = list(d)
            ys = list(i + rng.uniform(-0.17, 0.17, len(d)))
            s.append(r"\addplot[only marks,mark=*,mark size=0.5pt,fgM,opacity=0.6] coordinates {" + cs(xs, ys) + "};")
        for i, d in enumerate(dados, 1):
            lo, q1, med, q3, hi = resumo5(d)
            s.append(r"\draw[black,line width=0.7pt] " + f"(axis cs:{g(lo)},{i}) -- (axis cs:{g(q1)},{i}) (axis cs:{g(q3)},{i}) -- (axis cs:{g(hi)},{i}) "
                     f"(axis cs:{g(lo)},{i - 0.12}) -- (axis cs:{g(lo)},{i + 0.12}) (axis cs:{g(hi)},{i - 0.12}) -- (axis cs:{g(hi)},{i + 0.12});")
            s.append(r"\draw[black,line width=0.7pt] " + f"(axis cs:{g(q1)},{i - 0.27}) rectangle (axis cs:{g(q3)},{i + 0.27});")
            s.append(r"\draw[black,line width=1.4pt] " + f"(axis cs:{g(med)},{i - 0.27}) -- (axis cs:{g(med)},{i + 0.27});")
            s.append(r"\node[anchor=east,font=\scriptsize,inner sep=1pt] at " + f"(axis cs:5.45,{i}) {{{sum(1 for v in d if v < 0)}/{len(d)}}};")
        s.append(r"\draw[black,dashed,line width=0.7pt] (axis cs:0,0.05) -- (axis cs:0,4.6);")
        s.append(r"\node[anchor=east,font=\scriptsize,text=fgD] at (axis cs:-0.5,0.32) {$\leftarrow$ heuristic faster};")
        s.append(r"\node[anchor=west,font=\scriptsize,text=fgD] at (axis cs:0.5,0.32) {slower $\rightarrow$};")
        s.append(r"\node[anchor=east,font=\scriptsize,text=fgD] at (axis cs:5.45,0.32) {wins};")
        s.append(r"\end{axis}")
        partes.append("\n".join(s))
    escrever("fig_n1_convencoes", r"\centering" "\n" r"\begin{tikzpicture}" "\n" + "\n".join(partes) + "\n" r"\end{tikzpicture}" "\n")


# ---------------------------------------------------------------------------------------------------------------- Fig. 3: reinicio
def fig_reinicio(L):
    N = len(L)
    raw = gt.af.carregar()
    tg_a = np.concatenate([[0.0], np.logspace(-3, np.log10(2.0), 60)])
    fh = []
    for t in tg_a:
        wh = 0
        for x in L:
            P = x["peca"] + t * x["nc"]
            wh += gt.af.fo_formal(raw[x["nome"]]["forte"], t)["fo"] < P - 1e-12
        fh.append(100.0 * wh / N)
    xa = np.maximum(tg_a, 1e-3)
    teH = np.array([(x["peca"] - x["H0.0"]) / (x["R0.25"] - x["nc"]) for x in L if x["R0.25"] > x["nc"] and x["peca"] > x["H0.0"]])
    med = float(np.median(teH))
    a = [r"\begin{axis}[n1axis,grid=none,name=A,xmode=log,width=0.295\textwidth,height=5.0cm,xmin=1e-3,xmax=2.2,ymin=0,ymax=100,ytick={0,25,50,75,100},xtick={1e-3,1e-2,1e-1,1},"
         r"xlabel={restart cost $t$ (s per run)},ylabel={\% of the " + str(N) + r" instances},title={(a) How often the\\segment level is faster},"
         r"title style={at={(0,1)},anchor=south west,yshift=0.1cm,align=left}]"]
    a.append(r"\addplot[black,line width=1.3pt] coordinates {" + cs(xa, fh) + "};")
    a.append(r"\draw[fgD,dashed,line width=0.7pt] " + f"(axis cs:{g(med)},0) -- (axis cs:{g(med)},100);")
    a.append(r"\node[anchor=north east,align=right,font=\scriptsize,inner sep=1.5pt] at " + f"(axis cs:2.05,96) {{median\\\\break-even\\\\{med:.3f}\\,s}};")
    a.append(r"\end{axis}")
    Ls = vn.carregar()
    tg = np.logspace(-3, 0, 40)
    serie = {}
    for rota in ("H", "Rep1.0", "G0.25"):
        serie[rota] = [np.median([100 * (am.total(R[rota], "BLM_2G", t) / am.total(R["P"], "BLM_2G", t) - 1) for _, R, _ in Ls]) for t in np.concatenate([[0.0], tg[1:]])]
    xb = tg
    b = [r"\begin{axis}[n1axis,grid=none,name=B,at={(A.north east)},anchor=north west,xshift=1.5cm,xmode=log,width=0.295\textwidth,height=5.0cm,xmin=1e-3,xmax=1.05,ymin=0,ymax=12,xtick={1e-3,1e-2,1e-1,1},"
         r"xlabel={restart cost $t$ (s per run)},ylabel={$\Delta$ total time (\%)},title={(b) Loss of a route that\\ignores the restart cost},"
         r"title style={at={(0,1)},anchor=south west,yshift=0.1cm,align=left}]"]
    b.append(r"\addplot[black,line width=1.3pt] coordinates {" + cs(xb, serie["H"]) + "};")
    b.append(r"\node[anchor=east,font=\scriptsize,inner sep=3pt] at " + f"(axis cs:0.8,{g(serie['H'][-1] + 0.3)}) {{{serie['H'][-1]:+.1f}\\%}};")
    b.append(r"\end{axis}")
    c = [r"\begin{axis}[n1axis,grid=none,name=C,at={(B.north east)},anchor=north west,xshift=1.6cm,xmode=log,width=0.295\textwidth,height=5.0cm,xmin=1e-3,xmax=1.05,ymin=-0.15,ymax=0.25,xtick={1e-3,1e-2,1e-1,1},"
         r"xlabel={restart cost $t$ (s per run)},ylabel={$\Delta$ total time (\%)},title={(c) Restart-aware routes\\(zoomed scale)},"
         r"title style={at={(0,1)},anchor=south west,yshift=0.1cm,align=left}]"]
    c.append(r"\draw[black,line width=0.5pt] (axis cs:1e-3,0) -- (axis cs:1.05,0);")
    c.append(r"\addplot[black,line width=1.2pt,mark=square*,mark size=1.2pt,mark repeat=8] coordinates {" + cs(xb, serie["Rep1.0"]) + "};")
    c.append(r"\addplot[fgD,line width=1.2pt,dashed,mark=triangle*,mark size=1.4pt,mark repeat=8] coordinates {" + cs(xb, serie["G0.25"]) + "};")
    c.append(r"\node[anchor=south west,align=left,font=\scriptsize] at (axis cs:1.5e-3,0.14) {heuristic + repair};")
    c.append(r"\node[anchor=north west,align=left,font=\scriptsize,text=fgD] at (axis cs:1.5e-3,-0.07) {arc-based route};")
    c.append(r"\end{axis}")
    escrever("fig_n1_reinicio", r"\centering" "\n" r"\begin{tikzpicture}" "\n" + "\n".join(a + b + c) + "\n" r"\end{tikzpicture}" "\n")
    out = {"figMedBreakEven": f"{med:.3f}"}
    for nome, t in (("Ten", 0.01), ("Six", 0.06), ("Quarter", 0.25), ("One", 1.0)):
        wh = sum(1 for x in L if gt.af.fo_formal(raw[x["nome"]]["forte"], t)["fo"] < x["peca"] + t * x["nc"] - 1e-12)
        wg = sum(1 for x in L if x["gtsp"] + t * x["R0"] < x["peca"] + t * x["nc"] - 1e-12)
        if t == 1.0:
            out["beatHeurOneN"] = str(wh)
            out["beatHeurOnePack"] = str(sum(1 for x in L if x["nome"].endswith("_pack") and gt.af.fo_formal(raw[x["nome"]]["forte"], t)["fo"] < x["peca"] + t * x["nc"] - 1e-12))
        out[f"beatHeur{nome}"] = f"{100.0 * wh / N:.0f}" + r"\%"
        out[f"beatGtsp{nome}"] = f"{100.0 * wg / N:.0f}" + r"\%"
    return out


# ---------------------------------------------------------------------------------------------------------------- Fig. 4: ancoras por espessura contra a curva exata da economia maxima
def fig_espessura():
    import analise_ancoras_por_espessura as ae
    d = ae.dados()
    F, S = d["faixas"], d["curva"]
    r1, r3 = ae.LIM_R1, ae.LIM_R3
    ts = [t for t in ae.TS_CURVA if S[t]]
    tp = [max(t, 1.6e-3) for t in ts]                                                    # t = 0 desenhado em 1,6e-3 s
    ys_all = []
    for t, x in zip(ts, tp):
        ys_all += [(x, v) for v in S[t]]
    med = [float(np.median(S[t])) for t in ts]
    mx = [float(max(S[t])) for t in ts]
    ytop = max(mx) * 1.62

    def bandas(y0, y1):
        return (r"\fill[black!5] " f"(axis cs:1e-3,{y0}) rectangle (axis cs:{g(r1)},{y1});\n"
                r"\fill[black!12] " f"(axis cs:{g(r1)},{y0}) rectangle (axis cs:{g(r3)},{y1});\n"
                r"\fill[black!22] " f"(axis cs:{g(r3)},{y0}) rectangle (axis cs:30,{y1});\n"
                r"\draw[black,dotted,line width=0.6pt] " f"(axis cs:{g(r1)},{y0}) -- (axis cs:{g(r1)},{y1}) (axis cs:{g(r3)},{y0}) -- (axis cs:{g(r3)},{y1});")
    a = [r"\begin{axis}[n1axis,name=A,xmode=log,width=0.84\textwidth,height=5.6cm,ytick={0,0.5,1},xmin=1e-3,xmax=20,ymin=-0.03,ymax=" + g(ytop) + r",xticklabels={},"
         r"ylabel={largest possible saving (\%)},"
         r"title={(a) The most that any plan can save over contour-level routing (exact)},title style={at={(0,1)},anchor=south west,yshift=0.05cm},"
         r"legend style={at={(0.99,0.58)},anchor=north east,font=\scriptsize,draw=none,fill=none},legend cell align=left]"]
    a.append(bandas("-0.03", g(ytop)))
    a.append(r"\addplot[forget plot,only marks,mark=*,mark size=0.8pt,fgM] coordinates {" + " ".join(f"({g(x)},{g(v)})" for x, v in ys_all) + "};")
    a.append(r"\addplot[black,line width=1.3pt,mark=*,mark size=1.6pt] coordinates {" + cs(tp, med) + r"}; \addlegendentry{median over layouts}")
    a.append(r"\addplot[fgD,line width=1.0pt,dashed,mark=square*,mark size=1.4pt] coordinates {" + cs(tp, mx) + r"}; \addlegendentry{largest layout}")
    a.append(r"\node[anchor=north,font=\scriptsize,align=center] at " + f"(axis cs:0.0075,{g(ytop * 0.99)}) {{R1: $t\\le0.06$\\,s\\\\restart almost free}};")
    a.append(r"\node[anchor=north,font=\scriptsize,align=center] at " + f"(axis cs:0.23,{g(ytop * 0.99)}) {{R2: 0.06 to 0.87\\,s}};")
    a.append(r"\node[anchor=north,font=\scriptsize,align=center] at " + f"(axis cs:5,{g(ytop * 0.99)}) {{R3: $t\\ge0.87$\\,s\\\\no plan beats contour level}};")
    a.append(r"\node[anchor=north west,font=\tiny,text=fgD] at (axis cs:1.2e-3," + g(ytop * 0.15) + r") {one dot per layout};")
    a.append(r"\end{axis}")
    ent = []
    y0 = 0.0
    for k in ("thin", "med", "thick"):
        ent.append((y0, F[k]["rotulo"], F[k]["perf"], F[k]["ret"]))
        y0 += 3.7
    yfim = y0 - 3.7 + 2.05 + 0.7
    b = [r"\begin{axis}[n1axis,name=B,at={(A.south west)},anchor=north west,yshift=-1.0cm,xmode=log,width=0.84\textwidth,height=5.4cm,xmin=1e-3,xmax=20,ymin=-1.0,ymax=" + g(yfim) +
         r",y dir=reverse,ytick={" + ",".join(f"{g(e[0] + 1.15)},{g(e[0] + 2.05)}" for e in ent) + r"},yticklabels={" + ",".join(["piercing", "resumption (derived)"] * 3) +
         r"},ymajorgrids=false,xlabel={restart cost $t$ (s per run)},title={(b) Restart cost by sheet thickness (piercing: literature; resumption: derived)},"
         r"title style={at={(0,1)},anchor=south west,yshift=0.05cm}]"]
    b.append(bandas("-1.0", g(yfim)))
    for y, rot, perf, ret in ent:
        b.append(r"\node[anchor=west,font=\scriptsize\bfseries] at " + f"(axis cs:1.15e-3,{g(y)}) {{{rot}}};")
        b.append(r"\draw[black,fill=fgD,line width=0.5pt] " + f"(axis cs:{g(perf[0])},{g(y + 1.15 - 0.2)}) rectangle (axis cs:{g(perf[1])},{g(y + 1.15 + 0.2)});")
        b.append(r"\draw[black,pattern=north east lines,pattern color=black,line width=0.5pt]" + f"(axis cs:{g(ret[0])},{g(y + 2.05 - 0.2)}) rectangle (axis cs:{g(ret[1])},{g(y + 2.05 + 0.2)});")
    b.append(r"\end{axis}")
    escrever("fig_n1_espessura", r"\centering" "\n" r"\begin{tikzpicture}" "\n" + "\n".join(a + b) + "\n" r"\end{tikzpicture}" "\n")
    return {}


# ---------------------------------------------------------------------------------------------------------------- Fig. 5: tempo de voo e vantagem reotimizada
def pct(a, b):
    return 100.0 * (a / b - 1.0)


def fig_voo():
    d1, d0 = os.path.join(A, "tau_reinicio_resultados"), os.path.join(A, "tau_resultados")
    am0 = rv.amostra()
    linhas = []
    for perfil, nome in (("LASER", "trapezoidal"), ("DEWIL16", "Dewil curve")):
        for t in (0.0, 1.0):
            todos, ig, co = [], [], []
            for n in am0:
                if t == 0.0:
                    s = json.load(open(os.path.join(d0, f"segmento_{perfil}_{n}.json")))["melhor"]
                    p = json.load(open(os.path.join(d0, f"peca_{perfil}_{n}.json")))
                    T_s, T_p, c_s, c_p = s["T"][perfil], p["T"][perfil], s["corte_s"], p["corte_s"]
                else:
                    s = json.load(open(os.path.join(d1, f"segmento_{perfil}_t{t:g}_{n}.json")))["melhor"]
                    p = json.load(open(os.path.join(d0, f"peca_{perfil}_{n}.json")))
                    T_s, T_p, c_s, c_p = s["T"], p["T"][perfil] + t * p["corridas"], s["corte_s"], p["corte_s"]
                v = pct(T_s, T_p)
                todos.append(v)
                (ig if abs(c_s - c_p) <= 1e-6 * max(1.0, c_p) else co).append(v)
            linhas.append((f"{nome}, $t={t:g}$\\,s", float(np.median(todos)), float(np.median(ig)), float(np.median(co)), len(co)))
    dd = np.linspace(0, 330, 67)
    a = [r"\begin{axis}[n1axis,name=A,width=0.37\textwidth,height=5.1cm,xmin=0,xmax=335,ymin=0,ymax=0.88,xlabel={Chebyshev distance of the air move (drawing units = mm)},"
         r"ylabel={time of the air move (s)},title={(a) Time of an air move against its length},title style={at={(0,1)},anchor=south west,yshift=0.05cm},"
         r"legend style={at={(0.5,-0.33)},anchor=north,font=\scriptsize,draw=none,fill=none,/tikz/every even column/.append style={column sep=0.3cm}},legend columns=2,legend cell align=left]"]
    a.append(r"\addplot[black,dashed,line width=0.9pt] coordinates {" + cs(dd, vn.tau(dd, "LIN")) + r"}; \addlegendentry{linear, 400 u/s (benchmark)}")
    a.append(r"\addplot[fgD,line width=1.1pt] coordinates {" + cs(dd, am.tau(dd, "FIBRA_1G")) + r"}; \addlegendentry{trapezoidal, 1.0 g}")
    a.append(r"\addplot[fgM,line width=1.1pt,dash pattern=on 4pt off 1.5pt on 1pt off 1.5pt] coordinates {" + cs(dd, am.tau(dd, "SALV_5G")) + r"}; \addlegendentry{trapezoidal, 5 g (Salvagnini L5)}")
    a.append(r"\addplot[black,line width=1.1pt,mark=o,mark size=1.4pt,mark repeat=1,mark phase=1,only marks] coordinates {" + cs(vn.XS, vn.YS) + r"}; \addlegendentry{Dewil et al.\ (2016), read from plot}")
    a.append(r"\addplot[black,line width=0.9pt,forget plot] coordinates {" + cs(dd, vn.tau(dd, "DEWIL16")) + "};")
    a.append(r"\end{axis}")
    y = [3.0, 2.0, 1.0, 0.0]                                                            # de cima para baixo
    b = [r"\begin{axis}[n1axis,name=B,at={(A.north east)},anchor=north west,xshift=2.8cm,width=0.37\textwidth,height=5.1cm,xmin=-8.2,xmax=3.8,ymin=-0.55,ymax=4.35,"
         r"ytick={3,2,1,0},ytick style={draw=none},yticklabels={" + ",".join("{" + l[0] + "}" for l in linhas) + r"},ymajorgrids=false,xlabel={difference in total time (\%, median)},"
         r"title={(b) What is left after re-optimising both levels},title style={at={(0,1)},anchor=south west,yshift=0.05cm},"
         r"legend style={at={(0.5,-0.33)},anchor=north,font=\scriptsize,draw=none,fill=none},legend columns=1,legend cell align=left]"]
    for yy in y:
        b.append(r"\draw[black!15,line width=0.4pt] " f"(axis cs:-8.2,{yy}) -- (axis cs:3.8,{yy});")
    b.append(r"\draw[black,line width=0.6pt] (axis cs:0,-0.55) -- (axis cs:0,4.35);")
    b.append(r"\node[anchor=east,font=\scriptsize,text=fgD] at (axis cs:-0.45,4.05) {$\leftarrow$ segment level faster};")
    b.append(r"\node[anchor=west,font=\scriptsize,text=fgD] at (axis cs:0.45,4.05) {slower $\rightarrow$};")
    for yy, l in zip(y, linhas):
        b.append(r"\draw[black!45,line width=0.5pt] " f"(axis cs:{g(min(l[1], l[2], l[3]))},{yy}) -- (axis cs:{g(max(l[1], l[2], l[3]))},{yy});")
    b.append(r"\addplot[only marks,mark=*,mark size=2.0pt,black] coordinates {" + cs([l[2] for l in linhas], [yy + 0.2 for yy in y]) + r"}; \addlegendentry{routing only (same cut length)}")
    b.append(r"\addplot[only marks,mark=square*,mark size=2.0pt,mark options={fill=white,draw=black,line width=0.8pt}] coordinates {" + cs([l[3] for l in linhas], y) + r"}; \addlegendentry{shared edges cut once (6 layouts)}")
    b.append(r"\addplot[only marks,mark=diamond*,mark size=2.6pt,fgM] coordinates {" + cs([l[1] for l in linhas], [yy - 0.2 for yy in y]) + r"}; \addlegendentry{all 60 instances}")
    for yy, l in zip(y, linhas):
        txt = (f"{l[3]:+.1f}\\%").replace("-", "$-$")
        if l[3] < -5:
            b.append(r"\node[anchor=south,font=\scriptsize,inner sep=2pt] at " + f"(axis cs:{g(l[3])},{yy + 0.1}) {{{txt}}};")
        else:
            b.append(r"\node[anchor=south east,font=\scriptsize,inner sep=2pt] at " + f"(axis cs:{g(l[3] - 0.1)},{yy + 0.08}) {{{txt}}};")
    b.append(r"\end{axis}")
    escrever("fig_n1_voo", r"\centering" "\n" r"\begin{tikzpicture}" "\n" + "\n".join(a + b) + "\n" r"\end{tikzpicture}" "\n")
    return linhas


def main():
    alvo = set(sys.argv[1:])                                            # ex.: python gerar_figuras_n1.py brinquedo   (so essa figura; nao reescreve as macros)
    tudo = not alvo
    mac = {}
    if tudo or "brinquedo" in alvo:
        mac.update(fig_brinquedo())
    if tudo or alvo & {"convencoes", "reinicio"}:
        L = gt.carregar_282()
        if tudo or "convencoes" in alvo:
            fig_convencoes(L)
        if tudo or "reinicio" in alvo:
            mac.update(fig_reinicio(L))
    if tudo or "voo" in alvo:
        for l in fig_voo():
            print("voo:", l)
    if tudo or "espessura" in alvo:
        mac.update(fig_espessura())
    if tudo:
        with open(os.path.join(AQUI, "N1", "numeros_figuras.tex"), "w", encoding="utf-8") as f:
            f.write("% gerado por gerar_figuras_n1.py (nada digitado a mao)\n")
            for k, v in mac.items():
                assert k.isalpha(), k
                f.write("\\newcommand{\\" + k + "}{" + v + "}\n")
    print({k: v for k, v in mac.items()})


if __name__ == "__main__":
    main()
