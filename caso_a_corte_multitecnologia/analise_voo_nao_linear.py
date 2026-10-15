"""
analise_voo_nao_linear.py  --  as rotas guardadas (amostra do V3) sob TEMPOS DE VOO NAO LINEARES, sem reotimizar (docs/25 §3; exploratorio; predicoes fixadas antes)
=====================================================================================================================================================================
Curvas de tempo de voo por movimento (Chebyshev; 1 unidade = 1 mm, NAO confirmado): LIN (400 u/s, a do LCPP), LASER (trapezoidal v = 1667 mm/s, a = 10000 mm/s^2; o perfil do E-A1) e DEWIL16 (curva lida, de forma aproximada,
da Fig. 3 de Dewil et al. 2016: maquina CO2 4 kW). Rotas: P (PCGLNS por peca, caminho reconstituido, 20 s, semente 1), H (heuristica, ordem guardada), Rep(t) (heuristica reparada), G(t) (GTSP de arcos ciente do reinicio).
Tempo total = corte/v_corte + soma tau(d) dos movimentos em vazio (inclui as pernas de/para a origem) + t_av * corridas. Corte medido sobre a propria rota (o nivel de peca corta duas vezes as arestas compartilhadas).
Predicoes (docs/25 §3): P-A1 (DEWIL16, t_av = 0: H nao e mais rapida que P em >= 50% das instancias); P-A2 (DEWIL16, t_av = 0: G(0,25) mais perto de P que H em mediana, e dentro de +-1%);
P-A3 (LASER, t_av = 0: |H/P - 1| mediano <= 0,5%).
Uso: python analise_voo_nao_linear.py > RESULTADOS_VOO_NAO_LINEAR.md   (precisa de auditoria_lcpp1/pecas_caminhos/)
"""
import os
import sys
import json
import warnings

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
import rodar_v3 as rv                                                      # noqa: E402
import avaliar_heuristica_formal as af                                     # noqa: E402

VC = af.VC
rng = np.random.default_rng(2027)
XS = [0, 10, 50, 100, 150, 200, 250, 300, 330]
YS = [0, 0.20, 0.34, 0.50, 0.56, 0.60, 0.65, 0.69, 0.71]


def tau(d, perfil):
    d = np.asarray(d, float)
    if perfil == "LIN":
        return d / 400.0
    if perfil == "LASER":
        v, a = 1667.0, 10000.0
        return np.where(d >= v * v / a, d / v + v / a, 2.0 * np.sqrt(np.maximum(d, 0.0) / a))
    return np.interp(d, XS, YS) + np.where(d > 330, (d - 330) * 0.00091, 0.0)          # DEWIL16 (extrapola com a ultima inclinacao)


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def de_servicos(sv, t):
    """[(a, b)] na ordem dada -> (corte/v_corte, array de movimentos em vazio, corridas) com orientacoes por DP para o custo linear + t."""
    n = len(sv)
    INF = 1e18

    def ends(i, o):
        a, b = sv[i]
        return (a, b) if o == 0 else (b, a)
    c = [[INF, INF] for _ in range(n)]
    pa = [[0, 0] for _ in range(n)]
    for o in (0, 1):
        c[0][o] = cheb((0, 0), ends(0, o)[0]) / 400.0
    for i in range(1, n):
        for o in (0, 1):
            for q in (0, 1):
                d = cheb(ends(i - 1, q)[1], ends(i, o)[0])
                v = c[i - 1][q] + ((d / 400.0 + t) if d > 1e-7 else 0.0)
                if v < c[i][o]:
                    c[i][o], pa[i][o] = v, q
    fin = [c[n - 1][o] + cheb(ends(n - 1, o)[1], (0, 0)) / 400.0 for o in (0, 1)]
    o = 0 if fin[0] <= fin[1] else 1
    ori = [0] * n
    for i in range(n - 1, -1, -1):
        ori[i] = o
        if i > 0:
            o = pa[i][o]
    d = [cheb((0, 0), ends(0, ori[0])[0])] + [cheb(ends(i - 1, ori[i - 1])[1], ends(i, ori[i])[0]) for i in range(1, n)] + [cheb(ends(n - 1, ori[n - 1])[1], (0, 0))]
    d = np.array([x for x in d if x > 1e-7])
    corte = sum(cheb(a, b) for a, b in sv) / VC
    return corte, d, max(len(d) - 1, 1)


def de_caminho(cam):
    """caminho com tags: corte = soma dos 'c'; movimentos = os 'd'; corridas = nº de corridas de 'c'."""
    corte = sum(cheb((s[0], s[1]), (s[2], s[3])) for s in cam if s[4] == "c") / VC
    d = np.array([cheb((s[0], s[1]), (s[2], s[3])) for s in cam if s[4] == "d" and cheb((s[0], s[1]), (s[2], s[3])) > 1e-7])
    runs, ant = 0, None
    for s in cam:
        if s[4] == "c" and ant != "c":
            runs += 1
        ant = s[4]
    return corte, d, runs


def total(rota, perfil, tav):
    corte, d, runs = rota
    return corte + float(tau(d, perfil).sum()) + tav * runs


def boot(x, n=10000):
    x = np.asarray(x, float)
    return np.percentile([np.median(rng.choice(x, size=len(x), replace=True)) for _ in range(n)], (2.5, 97.5))


def carregar():
    L = []
    for n in rv.amostra():
        try:
            P = json.load(open(os.path.join(AQUI, "auditoria_lcpp1", "pecas_caminhos", f"{n}.json")))
            h = json.load(open(os.path.join(AQUI, "auditoria_lcpp1", "caminhos_282", f"{n}.json")))["forte"]
        except FileNotFoundError:
            continue
        if "caminho" not in P:
            continue
        sv0 = [((s[0], s[1]), (s[2], s[3])) for s in h if s[4] == "c"]
        R = {"P": de_caminho(P["caminho"]), "H": de_servicos(sv0, 0.0)}
        for t in ("0.25", "1.0"):
            rp = json.load(open(os.path.join(AQUI, "reparo_resultados", f"{n}__t{t}.json")))
            sv = [sv0[k - 1] for k in rp["ordem"]]
            R[f"Rep{t}"] = de_servicos(sv, float(t))
            g = json.load(open(os.path.join(AQUI, "v3_resultados", f"{n}__t{t}.json")))["melhor"]["caminho"]
            R[f"G{t}"] = de_caminho(g)
        L.append((n, R, P.get("fo_pcglns_honesta")))
    return L


def main():
    L = carregar()
    print("# Rotas guardadas sob tempos de voo não lineares (`docs/25` §3; exploratório; sem reotimizar)\n")
    print(f"Instâncias com todas as rotas: {len(L)} de {len(rv.amostra())}. Curvas: **LIN** (400 u/s), **LASER** (trapezoidal, v = 1667 mm/s, a = 10 000 mm/s²), **DEWIL16** (curva lida da Fig. 3 de Dewil et al. 2016, aproximada; 4 kW CO₂). 1 u = 1 mm (não confirmado).\n")
    chk = [abs(total(R["P"], "LIN", 0.0) / fo - 1) for _, R, fo in L if fo]
    print(f"Validação: o tempo LIN do caminho de peça reconstituído difere do FO honesto guardado em mediana {100 * np.median(chk):.4f}% (máx. {100 * max(chk):.3f}%).\n")
    rotas = ["H", "Rep0.25", "Rep1.0", "G0.25", "G1.0"]
    res = {}
    for perfil in ("LIN", "LASER", "DEWIL16"):
        print(f"## Perfil {perfil}: mediana de T(rota)/T(peça) − 1 [IC 95% da mediana] e nº de instâncias com a rota mais rápida que a peça\n")
        print("| rota | t_av = 0 | t_av = 0,25 s | t_av = 1 s |\n|---|---:|---:|---:|")
        for r in rotas:
            cel = []
            for tav in (0.0, 0.25, 1.0):
                x = np.array([total(R[r], perfil, tav) / total(R["P"], perfil, tav) - 1 for _, R, _ in L])
                ic = boot(100 * x)
                cel.append(f"{100 * np.median(x):+.2f}% [{ic[0]:+.2f}; {ic[1]:+.2f}] ({int((x < 0).sum())}/{len(x)})")
                res[(perfil, r, tav)] = x
            print(f"| {r} | " + " | ".join(cel) + " |")
        print()
    med = lambda k: float(np.median(res[k]))
    print("## Movimentos em vazio (mediana)\n")
    print("| rota | nº de movimentos | ar LIN (s) | ar DEWIL16 (s) | razão DEWIL16/LIN |\n|---|---:|---:|---:|---:|")
    for r in ["P"] + rotas:
        nm = [len(R[r][1]) for _, R, _ in L]
        al = [float(tau(R[r][1], "LIN").sum()) for _, R, _ in L]
        ad = [float(tau(R[r][1], "DEWIL16").sum()) for _, R, _ in L]
        print(f"| {r} | {np.median(nm):.0f} | {np.median(al):.2f} | {np.median(ad):.2f} | {np.median(np.array(ad) / np.array(al)):.1f}× |")
    print("\n## Predições (`docs/25` §3)\n")
    hd = res[("DEWIL16", "H", 0.0)]
    gd = res[("DEWIL16", "G0.25", 0.0)]
    print(f"- P-A1 (DEWIL16, t_av = 0: H não é mais rápida que P em ≥ 50%): H ≥ P em {int((hd >= 0).sum())}/{len(hd)} ({100 * (hd >= 0).mean():.1f}%) → {'SUSTENTADA' if (hd >= 0).mean() >= 0.5 else 'NÃO SUSTENTADA'}.")
    print(f"- P-A2 (DEWIL16: G(0,25) mais perto de P que H, e dentro de ±1%): |G/P − 1| mediano {100 * np.median(np.abs(gd)):.2f}% contra |H/P − 1| {100 * np.median(np.abs(hd)):.2f}%; mediana de G/P − 1 {100 * np.median(gd):+.2f}% → "
          f"{'SUSTENTADA' if np.median(np.abs(gd)) < np.median(np.abs(hd)) and abs(np.median(gd)) <= 0.01 else 'NÃO SUSTENTADA'}.")
    hl = res[("LASER", "H", 0.0)]
    print(f"- P-A3 (LASER, t_av = 0: |H/P − 1| mediano ≤ 0,5%): {100 * np.median(np.abs(hl)):.2f}% (mediana de H/P − 1 {100 * np.median(hl):+.2f}%) → {'SUSTENTADA' if np.median(np.abs(hl)) <= 0.005 else 'NÃO SUSTENTADA'}.")


if __name__ == "__main__":
    main()
