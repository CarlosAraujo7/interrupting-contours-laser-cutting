"""
analise_v3.py  --  analise PRE-REGISTRADA do V3 (docs/19 §5-6). Escrita ANTES de qualquer resultado de V3 existir (v3_resultados/ vazio no momento da escrita).
===========================================================================================================================================================
Comparadores por instancia e t (todos "tempo total" = corte + ar + t * corridas, FO honesta/formal):
  P(t)   PCGLNS por peca (FO a t = 0, `auditoria_lcpp1/honesta_282`) + t * (nº de contornos)            -- a rota de peca nao depende de t (Proposicao 1)
  H(t)   heuristica do LCPP (busca local forte, caminho guardado), FO FORMAL (`avaliar_heuristica_formal.fo_formal`), ordem de servico fixa e orientacao re-otimizada para t
  G0(t)  GTSP de arcos resolvido a t = 0 (`lcpp1_segmento_resultados`) avaliado a t: FO(0) + t * corridas      -- rota CEGA a t
  G(t)   GTSP de arcos resolvido com custo de reinicio t (V3, `v3_resultados`)                                 -- rota CIENTE de t
  B(t)   = min(G(t), G0(t))  melhor solucao verificada conhecida no nivel de segmento
Hipoteses (t primario = 1,0 s; t = 0,25 s descritivo; familia de Holm {H-W1, H-W2, H-W3}; alfa = 0,05):
  H-W1  em >= 80% das instancias, G(1,0) tem MENOS corridas que G0 (teste binomial unilateral contra 0,80)
  H-W2  mediana de G0(1,0)/B(1,0) - 1 >= 0,3%   (Wilcoxon unilateral contra 0,003; IC bootstrap 95% da mediana)       [regret de ignorar o custo de reinicio]
  H-W3  mediana de H(1,0)/B(1,0) - 1 >= 0,5%    (Wilcoxon unilateral contra 0,005; IC bootstrap 95% da mediana)       [a heuristica cega a t perde]
  H-W4  (descritiva) B(1,0)/P(1,0) - 1: mediana, IC e fracao de instancias com B < P; predicao: mediana em [-0,5%; +0,3%]
  H-W5  (descritiva) fracao das corridas de G(1,0) que recomecam em vertice ja cortado (retomadas) e nº de instancias com virgens > nº de contornos; predicao: retomadas < 20% das corridas
Uso: python analise_v3.py > RESULTADOS_V3_ANALISE.md
"""
import os
import sys
import json
import warnings

import numpy as np
from scipy import stats

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import rodar_v3 as rv                                                         # noqa: E402
import avaliar_heuristica_formal as af                                        # noqa: E402

rng = np.random.default_rng(2027)
TS = (0.25, 1.0)


def boot_mediana(x, n=10000, q=(2.5, 97.5)):
    x = np.asarray(x, float)
    return np.percentile([np.median(rng.choice(x, size=len(x), replace=True)) for _ in range(n)], q)


def carregar():
    L = []
    for n in rv.amostra():
        try:
            g0 = json.load(open(os.path.join(AQUI, "lcpp1_segmento_resultados", f"{n}.json")))
            hon = json.load(open(os.path.join(AQUI, "auditoria_lcpp1", "honesta_282", f"{n}.json")))
            cam = json.load(open(os.path.join(af.CAM, f"{n}.json")))["forte"]
        except FileNotFoundError:
            continue
        if not g0.get("melhor") or "fo_pcglns_honesta" not in hon:
            continue
        for t in TS:
            f = os.path.join(AQUI, "v3_resultados", f"{n}__t{t}.json")
            gt = json.load(open(f))["melhor"] if os.path.exists(f) else None
            P = hon["fo_pcglns_honesta"] + t * g0["n_contornos"]
            G0 = g0["melhor"]["fo"] + t * g0["melhor"]["n_perf"]
            H = af.fo_formal(cam, t)["fo"]
            G = gt["fo"] if gt else float("inf")
            L.append({"nome": n, "t": t, "cat": rv.categoria(n), "P": P, "G0": G0, "H": H, "G": G, "B": min(G, G0), "R0": g0["melhor"]["n_perf"], "R": gt["n_perf"] if gt else None,
                      "virg": gt["virgens"] if gt else None, "ret": gt["retomadas"] if gt else None, "nc": g0["n_contornos"]})
    return L


def main():
    L = carregar()
    n_amostra = len(rv.amostra())
    print("# Análise pré-registrada do V3 (`docs/19`)\n")
    print(f"Amostra: {n_amostra} instâncias; com todos os insumos: {len({x['nome'] for x in L})}; com solução de V3 verificada em t = 1,0: {len({x['nome'] for x in L if x['t'] == 1.0 and x['R'] is not None})}.\n")
    ps = {}
    for t in TS:
        S = [x for x in L if x["t"] == t and x["R"] is not None]
        if not S:
            continue
        reg = np.array([x["G0"] / x["B"] - 1 for x in S])
        hx = np.array([x["H"] / x["B"] - 1 for x in S])
        bp = np.array([x["B"] / x["P"] - 1 for x in S])
        menos = sum(1 for x in S if x["R"] < x["R0"])
        gp = np.array([x["G"] / x["P"] - 1 for x in S])
        print(f"## t = {t} s (n = {len(S)})\n")
        print(f"- Corridas: G(t) < G0 em **{menos}/{len(S)}** ({100 * menos / len(S):.1f}%); mediana de corridas G0 = {np.median([x['R0'] for x in S]):.0f}, G(t) = {np.median([x['R'] for x in S]):.0f}, contornos = {np.median([x['nc'] for x in S]):.0f}.")
        ic = boot_mediana(100 * reg)
        print(f"- **Regret da rota cega a t** G0(t)/B(t) − 1: mediana **{100 * np.median(reg):.3f}%** (IC 95% [{ic[0]:.3f}%; {ic[1]:.3f}%]; máx. {100 * reg.max():.2f}%).")
        ic = boot_mediana(100 * hx)
        print(f"- **Heurística do LCPP (formal) sobre B(t):** mediana **{100 * np.median(hx):+.3f}%** (IC 95% [{ic[0]:+.3f}%; {ic[1]:+.3f}%]); heurística ≤ B em {int((hx <= 1e-9).sum())}/{len(S)}.")
        ic = boot_mediana(100 * bp)
        print(f"- **Segmento (melhor conhecido) × peça** B(t)/P(t) − 1: mediana **{100 * np.median(bp):+.3f}%** (IC 95% [{ic[0]:+.3f}%; {ic[1]:+.3f}%]); B < P em {int((bp < 0).sum())}/{len(S)}. Só G(t) × peça: mediana {100 * np.median(gp[np.isfinite(gp)]):+.3f}%.")
        tot = sum(x["R"] for x in S)
        ret = sum(x["ret"] for x in S)
        dup = sum(1 for x in S if x["virg"] > x["nc"])
        print(f"- Retomadas (corridas que recomeçam em vértice já cortado): **{100 * ret / tot:.1f}%** das corridas; instâncias com mais inícios virgens que contornos: {dup}/{len(S)}.\n")
        if t == 1.0:
            ps["H-W1"] = stats.binomtest(menos, len(S), 0.8, alternative="greater").pvalue
            ps["H-W2"] = stats.wilcoxon(reg - 0.003, alternative="greater").pvalue
            ps["H-W3"] = stats.wilcoxon(hx - 0.005, alternative="greater").pvalue
            res = {"reg": reg, "hx": hx, "bp": bp, "menos": menos, "n": len(S), "ret": ret / tot}
    if ps:
        print("## Holm (α = 0,05; t = 1,0 s)\n| hipótese | p | ajustado | decisão |\n|---|---:|---:|---|")
        ordem = sorted(ps, key=lambda k: ps[k])
        prev, m = 0.0, len(ordem)
        for i, k in enumerate(ordem):
            adj = min(1.0, max(prev, ps[k] * (m - i)))
            prev = adj
            print(f"| {k} | {ps[k]:.4g} | {adj:.4g} | {'rejeita H0 (predição sustentada)' if adj < 0.05 else 'não rejeita H0'} |")
        print("\n## Resumo das predições (t = 1,0 s)\n")
        print(f"- H-W1 (≥ 80% com menos corridas): {100 * res['menos'] / res['n']:.1f}% → {'SUSTENTADA' if res['menos'] / res['n'] >= 0.8 and ps['H-W1'] < 0.05 else 'NÃO SUSTENTADA'} (p bruto {ps['H-W1']:.4g}).")
        print(f"- H-W2 (regret mediano ≥ 0,3%): {100 * np.median(res['reg']):.3f}% → {'SUSTENTADA' if np.median(res['reg']) >= 0.003 and ps['H-W2'] < 0.05 else 'NÃO SUSTENTADA'} (p bruto {ps['H-W2']:.4g}).")
        print(f"- H-W3 (heurística ≥ 0,5% acima de B): {100 * np.median(res['hx']):+.3f}% → {'SUSTENTADA' if np.median(res['hx']) >= 0.005 and ps['H-W3'] < 0.05 else 'NÃO SUSTENTADA'} (p bruto {ps['H-W3']:.4g}).")
        print(f"- H-W4 (descritiva; predição: mediana de B/P − 1 em [−0,5%; +0,3%]): {100 * np.median(res['bp']):+.3f}% → {'dentro' if -0.005 <= np.median(res['bp']) <= 0.003 else 'fora'}.")
        print(f"- H-W5 (descritiva; predição: retomadas < 20% das corridas): {100 * res['ret']:.1f}% → {'dentro' if res['ret'] < 0.2 else 'fora'}.")
    print("\n## Por categoria (t = 1,0 s)\n| categoria | n | regret G0 | heurística sobre B | B sobre peça |\n|---|---:|---:|---:|---:|")
    for cat in ("regular", "irregular", "hole", "esicup"):
        S = [x for x in L if x["t"] == 1.0 and x["R"] is not None and x["cat"] == cat]
        if S:
            print(f"| {cat} | {len(S)} | {100 * np.median([x['G0'] / x['B'] - 1 for x in S]):.3f}% | {100 * np.median([x['H'] / x['B'] - 1 for x in S]):+.3f}% | {100 * np.median([x['B'] / x['P'] - 1 for x in S]):+.3f}% |")


if __name__ == "__main__":
    main()
