"""
gerar_figuras_n1.py  --  figuras do manuscrito N1 (nada digitado a mao: tudo sai dos arquivos de resultado; a Figura 1 e um layout de brinquedo nosso, resolvido por DP exato)
==========================================================================================================================================================================
Fig. 1 (fig_n1_brinquedo.pdf)   layout de brinquedo (3 retangulos), rota de contornos x rota de segmentos (ambas otimas por enumeracao/DP) e o ponto de equilibrio t* do reinicio
Fig. 2 (fig_n1_convencoes.pdf)  distribuicao, por categoria, da diferenca heuristica x PCGLNS por contorno nas convencoes executavel e formal (282 instancias sinteticas)
Fig. 3 (fig_n1_reinicio.pdf)    (a) fracao das instancias em que a rota segue melhor que a de contorno em funcao de t; (b) mediana de T/T_P - 1 contra t, rota cega, reparada e ciente do reinicio
Fig. 5 (fig_n1_espessura.pdf)   (a) curva EXATA da economia maxima de qualquer plano em funcao de t (MILP); (b) faixas do custo de reinicio por espessura (literatura; retomada derivada)
Fig. 4 (fig_n1_voo.pdf)         (a) tempo de um movimento de voo tau(d) nos modelos usados; (b) vantagem do nivel de segmento reotimizado (todas / mesmo corte / arestas compartilhadas)
Uso: python gerar_figuras_n1.py        (saida em manuscrito/N1/figuras/)
"""
import itertools
import json
import os
import re
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt                                         # noqa: E402

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
plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"], "mathtext.fontset": "stix", "font.size": 8.5, "axes.titlesize": 9,
                     "axes.labelsize": 8.5, "legend.fontsize": 7.5, "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5})
C_BLUE, C_ORANGE, C_GREEN, C_RED, C_GREY, C_PURPLE = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#555555", "#7B3294"
VCUT, VAIR = 100.0 / 6.0, 400.0


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


def desenhar_rota(ax, polis, O, passos, titulo, cor_corte="#222222"):
    """passos: lista de ('c', p, q) cortes e ('a', p, q) movimentos de ar, em ordem; numera as corridas."""
    for P in polis:
        xs, ys = [p[0] for p in P] + [P[0][0]], [p[1] for p in P] + [P[0][1]]
        ax.fill(xs, ys, color="#eeeeee", zorder=0)
        ax.plot(xs, ys, color="#bbbbbb", lw=0.6, zorder=1)
    corrida = 0
    ant = None
    for tipo, p, q in passos:
        if tipo == "a":
            ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=C_RED, lw=1.0, ls=(0, (3, 2)), shrinkA=0, shrinkB=0, mutation_scale=7), zorder=3)
        else:
            if ant != "c":
                corrida += 1
                ax.text(p[0], p[1], str(corrida), fontsize=7, color="white", ha="center", va="center", zorder=6, bbox=dict(boxstyle="circle,pad=0.18", fc=C_BLUE, ec="none"))
            ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=cor_corte, lw=1.5, shrinkA=0, shrinkB=0, mutation_scale=7), zorder=4)
        ant = tipo
    ax.plot(*O, marker="s", color="black", ms=5, zorder=7)
    ax.text(O[0] + 1.2, O[1] - 2.8, "O", fontsize=8)
    ax.set_title(titulo, loc="left")
    ax.set_aspect("equal")
    ax.set_xlim(-2, 33)
    ax.set_ylim(-4, 28)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)


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


def fig_brinquedo():
    O = (0.0, 0.0)
    polis = [rect(5, 8, 10, 10), rect(20, 4, 10, 8), rect(18, 17, 10, 8)]
    c0 = contorno_exato(polis, O, 0.0)
    s0 = segmento_exato(polis, O, 0.0)
    ar_c, ar_s, R_c, R_s = c0[0], s0[0], len(polis), s0[4]
    tstar = (ar_c - ar_s) / VAIR / (R_s - R_c)
    fig = plt.figure(figsize=(6.8, 3.0))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.15], wspace=0.28)
    a1, a2, a3 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])
    desenhar_rota(a1, polis, O, passos_contorno(polis, O, c0[2]), f"(a) Contour level\n{R_c} runs, air {ar_c:.0f} units")
    desenhar_rota(a2, polis, O, passos_segmento(s0[3], O, s0[2]), f"(b) Segment level, $t=0$\n{R_s} runs, air {ar_s:.0f} units")
    ts = np.linspace(0, 0.07, 100)
    Tc = (ar_c / VAIR) + R_c * ts
    Ts = (ar_s / VAIR) + R_s * ts
    dif = (Ts - Tc) * 1000.0
    a3.plot(ts, dif, color=C_BLUE, lw=1.6)
    a3.axhline(0, color=C_GREY, lw=0.8)
    a3.axvline(tstar, color=C_RED, lw=0.9, ls="--")
    a3.text(tstar + 0.002, dif.max() * 0.85, f"$t^\\ast={tstar:.4f}$ s", color=C_RED, fontsize=7.5, va="top")
    a3.set_xlabel("restart cost $t$ (s per run)")
    a3.set_ylabel("route (b) $-$ route (a), total time (ms)")
    a3.set_title("(c) Which route is faster\n", loc="left")
    a3.text(0.068, dif.min() * 0.55, "(b) faster", fontsize=7.5, color=C_GREY, ha="right", va="center")
    a3.text(0.004, dif.max() * 0.45, "(a) faster", fontsize=7.5, color=C_GREY, ha="left", va="center")
    fig.savefig(os.path.join(OUT, "fig_n1_brinquedo.pdf"), bbox_inches="tight")
    plt.close(fig)
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


def fig_convencoes(L):
    cats = ["regular", "irregular", "with holes", "ESICUP-derived"]
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.7), sharey=True)
    for ax, (chave, nome) in zip(axs, (("poli", "Executable path"), ("H0.0", "Formal objective"))):
        dados = [[gt.pct(x[chave], x["peca"]) for x in L if categoria(x["nome"]) == c] for c in cats]
        bp = ax.boxplot(dados, vert=False, widths=0.55, showfliers=False, patch_artist=True, medianprops=dict(color="black", lw=1.2), boxprops=dict(fc="#cfe3f1", ec=C_BLUE),
                        whiskerprops=dict(color=C_BLUE), capprops=dict(color=C_BLUE))
        rng = np.random.default_rng(7)
        for i, d in enumerate(dados, 1):
            ax.scatter(d, i + rng.uniform(-0.18, 0.18, len(d)), s=3, color=C_GREY, alpha=0.45, lw=0, zorder=3)
            ax.text(0.99, i, f"{sum(1 for v in d if v < 0)}/{len(d)}", transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=7, color=C_RED)
        ax.axvline(0, color=C_RED, lw=0.9, ls="--")
        ax.set_yticks(range(1, len(cats) + 1))
        ax.set_yticklabels(cats)
        ax.set_xlabel("heuristic vs contour-level PCGLNS, total time (%)")
        ax.set_title(nome, loc="left")
        ax.set_xlim(-6.5, 3.2)
    axs[0].invert_yaxis()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_n1_convencoes.pdf"), bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------------------------------------------- Fig. 3: reinicio
def fig_reinicio(L):
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.8))
    ax = axs[0]
    ts = np.logspace(-3, np.log10(2.0), 300)
    N = len(L)
    raw = gt.af.carregar()
    tg_a = np.concatenate([[0.0], np.logspace(-3, np.log10(2.0), 60)])
    fh, fg = [], []
    for t in tg_a:
        wh = wg = 0
        for x in L:
            P = x["peca"] + t * x["nc"]
            wh += gt.af.fo_formal(raw[x["nome"]]["forte"], t)["fo"] < P - 1e-12
            wg += (x["gtsp"] + t * x["R0"]) < P - 1e-12
        fh.append(100.0 * wh / N)
        fg.append(100.0 * wg / N)
    teH = np.array([(x["peca"] - x["H0.0"]) / (x["R0.25"] - x["nc"]) for x in L if x["R0.25"] > x["nc"] and x["peca"] > x["H0.0"]])
    ax.axvspan(0.01, 0.06, color=C_GREEN, alpha=0.13, lw=0)
    ax.axvspan(0.25, 1.0, color=C_ORANGE, alpha=0.13, lw=0)
    ax.text(0.0245, 99, "thin sheet\n(fibre, 2 mm)", fontsize=6.3, ha="center", va="top", color="#2f6f4f")
    ax.text(0.5, 99, "thicker\nplate", fontsize=6.3, ha="center", va="top", color="#8a5a00")
    xp = np.maximum(tg_a, 1e-3)
    ax.plot(xp, fh, color=C_BLUE, lw=1.6, label="heuristic route (blind; directions re-optimised)")
    ax.plot(xp, fg, color=C_PURPLE, lw=1.3, ls="--", label="arc-GTSP route of $t=0$")
    med = float(np.median(teH))
    ax.axvline(med, color=C_RED, lw=0.8, ls=":")
    ax.text(med * 1.1, 80, f"median per-instance\nbreak-even {med:.3f} s", color=C_RED, fontsize=6.8, va="top", ha="left")
    ax.set_xscale("log")
    ax.set_xlim(1e-3, 2)
    ax.set_ylim(0, 102)
    ax.set_xlabel("restart cost $t$ (s per run)")
    ax.set_ylabel(f"% of the {N} instances where the\nroute is faster than contour level")
    ax.set_title("(a) Break-even over the instances", loc="left")
    ax.legend(loc="lower left", frameon=False, bbox_to_anchor=(0.0, 0.02), fontsize=6.6)
    ax = axs[1]
    Ls = vn.carregar()
    tg = np.concatenate([[0.0], np.logspace(-3, 0, 40)])
    for perfil, ls_, nm in (("BLM_2G", "-", "BLM LS7, 140 m/min, 2 g"), ("DEWIL16", ":", "Dewil et al. curve")):
        for rota, cor, rotulo in (("H", C_BLUE, "heuristic (blind)"), ("Rep1.0", C_ORANGE, "heuristic + repair ($t=1$)"), ("G0.25", C_GREEN, "restart-aware arc-GTSP ($t=0.25$)")):
            y = [np.median([100 * (am.total(R[rota], perfil, t) / am.total(R["P"], perfil, t) - 1) for _, R, _ in Ls]) for t in tg]
            ax.plot(np.maximum(tg, 1e-3), y, color=cor, lw=1.4, ls=ls_, label=f"{rotulo}" if perfil == "BLM_2G" else None)
    ax.axhline(0, color=C_GREY, lw=0.7)
    ax.axvspan(0.01, 0.06, color=C_GREEN, alpha=0.13, lw=0)
    ax.axvspan(0.25, 1.0, color=C_ORANGE, alpha=0.13, lw=0)
    ax.set_xscale("log")
    ax.set_xlim(1e-3, 1.05)
    ax.set_xlabel("restart cost $t$ (s per run)")
    ax.set_ylabel("total time vs contour level (%, median)")
    ax.set_title(f"(b) Stored routes, {len(Ls)} instances", loc="left")
    ax.legend(loc="upper left", frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_n1_reinicio.pdf"), bbox_inches="tight")
    plt.close(fig)
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


# ---------------------------------------------------------------------------------------------------------------- Fig. 4: tempo de voo e vantagem reotimizada
def pct(a, b):
    return 100.0 * (a / b - 1.0)


def fig_voo():
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.3), gridspec_kw={"width_ratios": [1, 1.15]})
    ax = axs[0]
    d = np.linspace(0, 330, 400)
    ax.plot(d, vn.tau(d, "LIN"), color=C_GREY, lw=1.2, ls="--", label="linear, 400 u/s (benchmark)")
    ax.plot(d, am.tau(d, "FIBRA_1G"), color=C_BLUE, lw=1.4, label="trapezoidal, 1667 mm/s, 1.0 g")
    ax.plot(d, am.tau(d, "SALV_5G"), color=C_PURPLE, lw=1.2, label="trapezoidal, 2600 mm/s, 5 g (Salvagnini L5)")
    ax.plot(d, vn.tau(d, "DEWIL16"), color=C_RED, lw=1.4, label="Dewil et al. (2016), read from plot")
    ax.plot(vn.XS, vn.YS, "o", color=C_RED, ms=3)
    ax.set_xlabel("Chebyshev distance of the air move (drawing units = mm)")
    ax.set_ylabel("air-move time (s)")
    ax.set_title("(a) Air-move time models", loc="left")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False, fontsize=6.6, ncol=1)
    ax = axs[1]
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
            linhas.append((f"{nome}, $t={t:g}$ s", np.median(todos), np.median(ig), np.median(co), len(co)))
    y = np.arange(len(linhas))[::-1]
    w = 0.26
    ax.barh(y + w, [l[2] for l in linhas], height=w, color=C_BLUE, label="same cut length (routing only)")
    ax.barh(y, [l[3] for l in linhas], height=w, color=C_ORANGE, label="shared edges (6 layouts)")
    ax.barh(y - w, [l[1] for l in linhas], height=w, color="#999999", label="all 60 instances")
    ax.set_yticks(y)
    ax.set_yticklabels([l[0] for l in linhas])
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("segment level vs contour level, total time (%, median)")
    ax.set_title("(b) Both levels re-optimised", loc="left")
    for yy, l in zip(y, linhas):
        for off, v in ((w, l[2]), (0.0, l[3]), (-w, l[1])):
            txt = (f"{v:+.2f}" if abs(v) < 1 else f"{v:+.1f}").replace("-", "\u2212")
            ax.text(v - 0.12 if v < -0.5 else 0.12, yy + off, txt, va="center", ha="right" if v < -0.5 else "left", fontsize=6.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False, fontsize=6.6, ncol=1)
    ax.set_xlim(-7.4, 1.4)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_n1_voo.pdf"), bbox_inches="tight")
    plt.close(fig)
    return linhas


# ---------------------------------------------------------------------------------------------------------------- Fig. 5: ancoras por espessura contra a curva exata da economia maxima
def fig_espessura():
    import analise_ancoras_por_espessura as ae
    d = ae.dados()
    F, S, lay = d["faixas"], d["curva"], d["layouts"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.6, 4.9), sharex=True, gridspec_kw={"height_ratios": [1.15, 1.0], "hspace": 0.30})
    for ax in (ax1, ax2):
        ax.axvspan(1e-3, ae.LIM_R1, color=C_GREEN, alpha=0.10, lw=0)
        ax.axvspan(ae.LIM_R1, ae.LIM_R3, color=C_ORANGE, alpha=0.10, lw=0)
        ax.axvspan(ae.LIM_R3, 30, color=C_RED, alpha=0.10, lw=0)
        ax.axvline(ae.LIM_R1, color=C_GREY, lw=0.7, ls=":")
        ax.axvline(ae.LIM_R3, color=C_GREY, lw=0.7, ls=":")
    ts = [t for t in ae.TS_CURVA if S[t]]
    tp = [max(t, 1.6e-3) for t in ts]                                                    # t = 0 desenhado em 1,6e-3 s
    for t, x in zip(ts, tp):
        ax1.plot([x] * len(S[t]), S[t], ".", color=C_GREY, ms=2.5, alpha=0.6)
    ax1.plot(tp, [np.median(S[t]) for t in ts], "-o", color=C_BLUE, lw=1.5, ms=3.5, label="median over layouts")
    ax1.plot(tp, [max(S[t]) for t in ts], "--s", color=C_RED, lw=1.1, ms=3, label="largest layout")
    ax1.set_ylabel("exact largest saving of any plan\nover the contour-level optimum (%)")
    ax1.set_title("(a) Exact computation (mixed-integer programme with restart cost)", loc="left")
    ax1.legend(loc="upper right", frameon=False)
    ax1.set_ylim(bottom=-0.02)
    ax1.text(1.3e-3, ax1.get_ylim()[1] * 0.04, "R1", color=C_GREEN, fontsize=8, weight="bold")
    ax1.text(0.12, ax1.get_ylim()[1] * 0.04, "R2", color="#A66A00", fontsize=8, weight="bold")
    ax1.text(1.8, ax1.get_ylim()[1] * 0.04, "R3", color=C_RED, fontsize=8, weight="bold")
    ys, lab = [], []
    for i, k in enumerate(("thin", "med", "thick")):
        f = F[k]
        for j, (tipo, cor) in enumerate((("perf", C_BLUE), ("ret", C_ORANGE))):
            y = -(i * 2.6 + j)
            lo, hi = f[tipo]
            ax2.plot([lo, hi], [y, y], "-", color=cor, lw=6, solid_capstyle="butt")
            ys.append(y)
            lab.append(("piercing" if tipo == "perf" else "resumption (derived)"))
        ax2.text(1.2e-3, -(i * 2.6 + 0.5) + 0.95, f["rotulo"], fontsize=7.4, va="bottom", weight="bold")
    ax2.set_yticks(ys)
    ax2.set_yticklabels(lab, fontsize=7)
    ax2.set_ylim(-7.4, 1.2)
    ax2.set_xscale("log")
    ax2.set_xlim(1e-3, 20)
    ax2.set_xlabel("restart cost $t$ (s per run)")
    ax2.set_title("(b) Ranges of the restart cost by sheet thickness (literature; resumption derived)", loc="left")
    ax2.grid(axis="y", alpha=0)
    fig.savefig(os.path.join(OUT, "fig_n1_espessura.pdf"), bbox_inches="tight")
    plt.close(fig)
    return {}


def main():
    mac = {}
    mac.update(fig_brinquedo())
    L = gt.carregar_282()
    fig_convencoes(L)
    mac.update(fig_reinicio(L))
    for l in fig_voo():
        print("voo:", l)
    mac.update(fig_espessura())
    with open(os.path.join(AQUI, "N1", "numeros_figuras.tex"), "w", encoding="utf-8") as f:
        f.write("% gerado por gerar_figuras_n1.py (nada digitado a mao)\n")
        for k, v in mac.items():
            assert k.isalpha(), k
            f.write("\\newcommand{\\" + k + "}{" + v + "}\n")
    print({k: v for k, v in mac.items()})


if __name__ == "__main__":
    main()
