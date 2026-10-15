"""
analise_estatistica_ea0.py  --  analise PRE-REGISTRADA do E-A0 completo (docs/11_protocolo_E-A0.md §3-§4)
==============================================================================================================
Unidade = instancia (FO media das sementes por metodo); G_m = FO_m / FO_PCGLNS - 1 (positivo = pior que o PCGLNS), so instancias COMPARAVEIS (a FO nativa da construcao coincide com a
reavaliada no nivel de peca) e viaveis. Hipoteses: H-A0.1 (G_heur_pi > 0; Wilcoxon unilateral), H-A0.2 (equivalencia pratica dos hibridos: IC 95% da mediana de G <= 0,5%),
H-A0.3 (G_vns_pi != 0; bilateral), H-A0.4 (violacoes de Pi), H-A0.5 (Spearman nº de pecas x G_heur_pi > 0), H-A0.6 (razao de tempo); familia de Holm {H-A0.1, H-A0.3}. Extra exploratorio:
Friedman + Wilcoxon/Holm entre os hibridos e o VNS-Pi; perfil de desempenho. Nao altera as hipoteses do protocolo.
Uso: python analise_estatistica_ea0.py [--tempo 30] > RESULTADOS_EA0_COMPLETO.md
"""
import os
import sys
import json
import statistics
import warnings

import numpy as np
from scipy import stats

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import rodar_ea0 as ea0                                        # noqa: E402

METODOS = [("pcglns", "PCGLNS"), ("vns_pi", "VNS-Pi"), ("heur_pi", "Heuristic (construction)"), ("heur_ls", "Heuristic + local search"),
           ("heur_vns", "Heuristic + VNS"), ("mastri", "MASTRI"), ("heur_orig", "Heuristic (original mode)")]
TOL = 5e-4
rng = np.random.default_rng(12345)


def holm(ps):
    ordem = np.argsort(ps)
    m = len(ps)
    aj = np.empty(m)
    mx = 0.0
    for i, k in enumerate(ordem):
        mx = max(mx, (m - i) * ps[k])
        aj[k] = min(1.0, mx)
    return aj


def ic_mediana(x, B=10000):
    x = np.asarray(x, float)
    meds = [np.median(rng.choice(x, size=len(x), replace=True)) for _ in range(B)]
    return float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def carregar(tempo=30, exigir_sementes=10):
    nomes = [n for n in sorted(ea0.listar()) if len(ea0._carregar(n)) >= 2]
    dados = {}
    for n in nomes:
        d = ea0._coletar(n, tempo)
        if "pcglns" not in d or "heur_pi" not in d:
            continue
        dados[n] = d
    completos = {n: d for n, d in dados.items() if all(d.get(m, {}).get("n", 0) >= exigir_sementes for m in ("pcglns", "vns_pi", "heur_ls", "heur_vns"))}
    return nomes, dados, completos


def computar(tempo=30, exigir_sementes=10):
    nomes, dados, comp_all = carregar(tempo, exigir_sementes)
    comp = {n: abs(d["heur_pi"]["nativa_min"] - d["heur_pi"]["fo_min"]) <= TOL * d["heur_pi"]["nativa_min"] and d["heur_pi"]["viol_max"] == 0 for n, d in comp_all.items()}
    usadas = [n for n, c in comp.items() if c]
    npec = {n: json.load(open(ea0.caminho(n, "heur_pi", 0, tempo)))["n_pecas"] for n in comp_all}
    G = {m: np.array([d[m]["fo_med"] / d["pcglns"]["fo_med"] - 1 for n, d in comp_all.items() if n in usadas and m in d]) for m, _ in METODOS if m != "pcglns"}
    res = {"n_instancias": len(nomes), "n_completas": len(comp_all), "n_usadas": len(usadas), "excluidas": [n for n in comp_all if not comp[n]],
           "incompletas": [n for n in nomes if n not in comp_all], "G": G, "npec": [npec[n] for n in usadas], "usadas": usadas, "dados": comp_all}
    # H-A0.1 e H-A0.3
    def wil(x, alt):
        x = x[np.abs(x) > 1e-12]
        return float(stats.wilcoxon(x, alternative=alt).pvalue) if len(x) >= 1 else 1.0
    p1, p3 = wil(G["heur_pi"], "greater"), wil(G["vns_pi"], "two-sided")
    aj = holm([p1, p3])
    res["H1"] = {"mediana": float(np.median(G["heur_pi"])), "ic": ic_mediana(G["heur_pi"]), "p": p1, "p_holm": float(aj[0]), "pos": int((G["heur_pi"] > 1e-12).sum()), "neg": int((G["heur_pi"] < -1e-12).sum())}
    res["H3"] = {"mediana": float(np.median(G["vns_pi"])), "ic": ic_mediana(G["vns_pi"]), "p": p3, "p_holm": float(aj[1]), "pos": int((G["vns_pi"] > 1e-12).sum()), "neg": int((G["vns_pi"] < -1e-12).sum())}
    res["H2"] = {m: {"mediana": float(np.median(G[m])), "ic": ic_mediana(G[m]), "equiv": bool(ic_mediana(G[m])[1] <= 0.005)} for m in ("heur_ls", "heur_vns")}
    rho, p5 = stats.spearmanr(res["npec"], G["heur_pi"], alternative="greater")
    res["H5"] = {"rho": float(rho), "p": float(p5)}
    t = {m: np.array([d[m]["t"] for n, d in comp_all.items() if n in usadas and m in d]) for m, _ in METODOS if any(m in d for d in comp_all.values())}
    res["H6"] = {"razao_mediana_tempo_heur_pi_sobre_pcglns": float(np.median(t["heur_pi"] / t["pcglns"]))}
    viol = {m: sum(1 for d in comp_all.values() if m in d and d[m]["viol_max"] > 0) for m, _ in METODOS}
    res["H4"] = {"instancias_com_violacao": viol}
    # Friedman + Wilcoxon/Holm entre hibridos e VNS-Pi (exploratorio)
    ms = ["heur_ls", "heur_vns", "vns_pi", "pcglns"]
    mat = np.array([[comp_all[n][m]["fo_med"] for m in ms] for n in usadas])
    res["friedman"] = {"estat": float(stats.friedmanchisquare(*[mat[:, k] for k in range(len(ms))]).statistic), "p": float(stats.friedmanchisquare(*[mat[:, k] for k in range(len(ms))]).pvalue), "metodos": ms}
    pares = [(0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3)]
    ps = [wil(mat[:, i] - mat[:, j], "two-sided") for i, j in pares]
    res["pares"] = [(ms[i], ms[j], p, a, float(np.median(mat[:, i] / mat[:, j] - 1))) for (i, j), p, a in zip(pares, ps, holm(ps))]
    # perfil de desempenho (Dolan-More) sobre a melhor FO viavel (media das sementes)
    ms_pd = ["pcglns", "vns_pi", "heur_pi", "heur_ls", "heur_vns"]
    A = np.array([[comp_all[n][m]["fo_med"] for m in ms_pd] for n in usadas])
    rho_pd = A / A.min(axis=1, keepdims=True)
    res["perfil"] = {"metodos": ms_pd, "rho": rho_pd}
    return res


def main():
    tempo = int(sys.argv[sys.argv.index("--tempo") + 1]) if "--tempo" in sys.argv else 30
    exigir = int(sys.argv[sys.argv.index("--sementes") + 1]) if "--sementes" in sys.argv else 10
    r = computar(tempo, exigir)
    pct = lambda v: f"{100 * v:+.2f}%"
    print(f"# E-A0 completo -- analise pre-registrada (docs/11_protocolo_E-A0.md); T = {tempo} s, >= {exigir} sementes\n")
    print(f"Instancias com >= 2 pecas: {r['n_instancias']}; com todos os metodos estocasticos completos: {r['n_completas']}; usadas na comparacao (mesmo problema e construcao viavel): **{r['n_usadas']}**. "
          f"Fora por nao serem do mesmo problema: {', '.join(r['excluidas']) or 'nenhuma'}. Incompletas (rodada em andamento?): {len(r['incompletas'])}.\n")
    h1, h3 = r["H1"], r["H3"]
    print("## Hipoteses\n")
    print("| hipotese | mediana de G [IC 95%] | instancias pior / melhor que o PCGLNS | p | p (Holm) | leitura |")
    print("|---|---|---|---:|---:|---|")
    print(f"| H-A0.1 construcao > PCGLNS (unilateral) | {pct(h1['mediana'])} [{pct(h1['ic'][0])}; {pct(h1['ic'][1])}] | {h1['pos']} / {h1['neg']} | {h1['p']:.4f} | {h1['p_holm']:.4f} | {'rejeita H0' if h1['p_holm'] < 0.05 else 'nao rejeita'} |")
    print(f"| H-A0.3 VNS-Pi != PCGLNS (bilateral) | {pct(h3['mediana'])} [{pct(h3['ic'][0])}; {pct(h3['ic'][1])}] | {h3['pos']} / {h3['neg']} | {h3['p']:.4f} | {h3['p_holm']:.4f} | {'rejeita H0' if h3['p_holm'] < 0.05 else 'nao rejeita'} |")
    for m, nm in (("heur_ls", "heuristica + busca local"), ("heur_vns", "heuristica + VNS")):
        h = r["H2"][m]
        print(f"| H-A0.2 {nm}: IC superior <= 0,5% | {pct(h['mediana'])} [{pct(h['ic'][0])}; {pct(h['ic'][1])}] | -- | -- | -- | {'equivalencia pratica' if h['equiv'] else 'NAO equivalente'} |")
    print(f"\nH-A0.5 (escala): Spearman entre o nº de pecas e G(construcao) = {r['H5']['rho']:+.2f}, p unilateral = {r['H5']['p']:.4f}. "
          f"H-A0.6: razao mediana de tempo construcao/PCGLNS = {r['H6']['razao_mediana_tempo_heur_pi_sobre_pcglns']:.3f}. "
          f"H-A0.4: instancias com violacao de Pi por metodo = {r['H4']['instancias_com_violacao']}.\n")
    print("## Exploratorio: hibridos e VNS-Pi\n")
    print(f"Friedman sobre {r['friedman']['metodos']}: chi2 = {r['friedman']['estat']:.2f}, p = {r['friedman']['p']:.4g}. Wilcoxon bilateral com Holm (gap mediano do primeiro sobre o segundo):\n")
    print("| par | gap mediano | p | p (Holm) |")
    print("|---|---:|---:|---:|")
    for a, b, p, pa, g in r["pares"]:
        print(f"| {a} x {b} | {pct(g)} | {p:.4f} | {pa:.4f} |")
    print("\n## Gap por metodo sobre o PCGLNS (instancias usadas)\n")
    print("| metodo | mediana | media | melhor / pior que o PCGLNS | tempo medio de parede (s) |")
    print("|---|---:|---:|---:|---:|")
    for m, nm in METODOS[1:5]:
        g = r["G"][m]
        tt = statistics.mean(d[m]["t"] for n, d in r["dados"].items() if n in r["usadas"] and m in d)
        print(f"| {nm} | {pct(np.median(g))} | {pct(np.mean(g))} | {int((g < -1e-12).sum())} / {int((g > 1e-12).sum())} | {tt:.1f} |")


if __name__ == "__main__":
    main()
