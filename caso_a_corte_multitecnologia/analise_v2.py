"""
analise_v2.py  --  analise PRE-REGISTRADA do conjunto V2 (docs/17 §5-6). Escrita antes de olhar os resultados de V2 (so os contadores do log tinham sido vistos).
===========================================================================================================================================================
Hipoteses (familia de Holm: H-V2, H-V3, H-V4a; alfa = 0,05):
  H-V1  fracao de layouts (>= 2 contornos) com solucao de segmento verificada em t = 0  >= 95%
  H-V2  mediana da reducao relativa do tempo de AR (segmento vs peca), layouts SEM arestas compartilhadas, >= 20%   (Wilcoxon unilateral sobre log da razao contra log 0,8; IC bootstrap da mediana)
  H-V3  tempo TOTAL do segmento <= o da peca em >= 75% dos layouts (teste dos sinais/binomial unilateral)
  H-V4a mediana do excesso de tempo total ao usar a rota de t = 0 com t = 1 s, sobre a rota de t = 1 s, >= 0,2% (Wilcoxon unilateral contra 0,002; IC bootstrap)
  H-V4b descritiva: vantagem do segmento sobre a peca em tempo total com t = 1 s (mediana e IC)
  Predicao qualitativa: perfuracoes (t = 1 s) < perfuracoes (t = 0) em >= 80% dos layouts.
Controle de orcamento: segmento (t = 0) vs PCGLNS por peca com o mesmo orcamento (descritivo).
Uso: python analise_v2.py > RESULTADOS_V2_ANALISE.md
"""
import os
import sys
import json
import glob
import statistics

import numpy as np
from scipy import stats

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import ea0_lib                                                  # noqa: F401,E402
from heuristic_core import _DEFAULT_CONFIG as D                 # noqa: E402

VC, VA = D["v_cut"], D["v_air"]
rng = np.random.default_rng(2027)


def boot_mediana(x, n=10000, q=(2.5, 97.5)):
    x = np.asarray(x, float)
    m = [np.median(rng.choice(x, size=len(x), replace=True)) for _ in range(n)]
    return np.percentile(m, q)


def carregar():
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "v2_resultados", "v2_*.json")))]
    return R


def main():
    R = carregar()
    todos = [r for r in R if r.get("n_contornos", 0) >= 2 and r.get("peca_10s")]
    excl = [r["instancia"] for r in R if r.get("n_contornos", 0) < 2]
    print("# Análise pré-registrada do conjunto V2 (`docs/17`)\n")
    print(f"Arquivos em V2: {len(R)}; com < 2 contornos fechados (excluídos pela regra do protocolo): {len(excl)} ({', '.join(e[-30:] for e in excl)}); **analisados: {len(todos)}**.\n")
    # H-V1
    ok0 = [r for r in todos if r["seg_t0"]["melhor"]]
    print(f"## H-V1 — viabilidade\nSolução de segmento verificada (t = 0): **{len(ok0)}/{len(todos)}** = {100 * len(ok0) / len(todos):.1f}% (critério ≥ 95%). t = 1 s: {sum(1 for r in todos if r['seg_t1']['melhor'])}/{len(todos)}.\n")
    L = []
    for r in ok0:
        Lp = r["L_pecas"]
        ar_peca = r["peca_10s"]["fo_media"] - Lp / VC
        ar_seg = r["seg_t0"]["melhor"]["ar"] / VA
        comp = abs(r["L_segmento"] - Lp) > 1e-6 * Lp
        L.append(dict(nome=r["instancia"], n=r["n_contornos"], pi=r["n_pares_pi"], ar_peca=ar_peca, ar_seg=ar_seg, fo_peca=r["peca_10s"]["fo_media"], fo_seg=r["seg_t0"]["melhor"]["fo"], comp=comp, r=r))
    sem = [x for x in L if not x["comp"] and x["ar_peca"] > 1e-9]
    print(f"Layouts com arestas compartilhadas (o corte do segmento é menor): {sum(1 for x in L if x['comp'])}/{len(L)}; sem: {len(sem)}.\n")
    # H-V2
    p2 = None
    if len(sem) >= 5:
        razao = np.array([x["ar_seg"] / x["ar_peca"] for x in sem])
        red = 100 * (1 - razao)
        d = np.log(razao) - np.log(0.8)
        p2 = stats.wilcoxon(d, alternative="less").pvalue
        ic = boot_mediana(red)
        print(f"## H-V2 — tempo de ar (t = 0; layouts sem arestas compartilhadas, n = {len(sem)})\nRedução relativa do tempo de ar do segmento sobre a peça: mediana **{np.median(red):.1f}%** (média {red.mean():.1f}%), IC 95% bootstrap da mediana [{ic[0]:.1f}%; {ic[1]:.1f}%]. "
              f"Wilcoxon unilateral (H0: redução < 20%): p = {p2:.4g}. Segmento menor em {int((razao < 1).sum())}/{len(razao)}.\n")
    todos_ar = [x for x in L if x["ar_peca"] > 1e-9]
    print(f"(Descritivo, todos os layouts, n = {len(todos_ar)}): redução mediana do ar {np.median([100 * (1 - x['ar_seg'] / x['ar_peca']) for x in todos_ar]):.1f}%.\n")
    # H-V3
    vit = sum(1 for x in L if x["fo_seg"] <= x["fo_peca"] + 1e-9)
    p3 = stats.binomtest(vit, len(L), 0.75, alternative="greater").pvalue
    vit_sem = sum(1 for x in sem if x["fo_seg"] <= x["fo_peca"] + 1e-9)
    print(f"## H-V3 — tempo total (t = 0)\nSegmento ≤ peça em **{vit}/{len(L)}** layouts ({100 * vit / len(L):.1f}%; critério ≥ 75%); binomial unilateral contra 0,75: p = {p3:.4g}. "
          f"Nos layouts sem arestas compartilhadas: {vit_sem}/{len(sem)}. Gap de FO (mediana): {np.median([100 * (x['fo_seg'] / x['fo_peca'] - 1) for x in L]):+.3f}% (sem compartilhadas: {np.median([100 * (x['fo_seg'] / x['fo_peca'] - 1) for x in sem]):+.3f}%).\n")
    # H-V4a / b
    P = [r for r in ok0 if r["seg_t1"]["melhor"]]
    exc, vant = [], []
    for r in P:
        m0, m1 = r["seg_t0"]["melhor"], r["seg_t1"]["melhor"]
        T1_r0 = m0["fo"] + 1.0 * m0["n_perf"]
        T1_r1 = m1["fo"]
        exc.append(T1_r0 / T1_r1 - 1)
        vant.append(m1["fo"] / (r["peca_10s"]["fo_media"] + 1.0 * r["n_contornos"]) - 1)
    exc, vant = np.array(exc), np.array(vant)
    p4 = stats.wilcoxon(exc - 0.002, alternative="greater").pvalue
    ic4 = boot_mediana(100 * exc, q=(5, 95))
    ic4b = boot_mediana(100 * vant)
    print(f"## H-V4a — regret entre tecnologias (n = {len(P)})\nExcesso de tempo total ao usar a rota de t = 0 com t = 1 s: mediana **{100 * np.median(exc):.3f}%** (máx. {100 * exc.max():.2f}%); IC 90% bootstrap [{ic4[0]:.3f}%; {ic4[1]:.3f}%]; "
          f"Wilcoxon unilateral (H0: ≤ 0,2%): p = {p4:.4g}.\n")
    print(f"## H-V4b — vantagem do segmento sobre a peça com t = 1 s (descritiva)\nMediana {100 * np.median(vant):+.3f}% (IC 95% [{ic4b[0]:+.3f}%; {ic4b[1]:+.3f}%]); critério descritivo: entre −0,1% e +0,1%. Segmento menor em {int((vant < 0).sum())}/{len(vant)}.\n")
    menos = sum(1 for r in P if r["seg_t1"]["melhor"]["n_perf"] < r["seg_t0"]["melhor"]["n_perf"])
    print(f"## Predição qualitativa — perfurações\nMenos perfurações com t = 1 s que com t = 0 em **{menos}/{len(P)}** ({100 * menos / len(P):.1f}%; critério ≥ 80%). Mediana de perfurações: t = 0: {statistics.median(r['seg_t0']['melhor']['n_perf'] for r in P):.0f}; t = 1 s: {statistics.median(r['seg_t1']['melhor']['n_perf'] for r in P):.0f}; contornos: {statistics.median(r['n_contornos'] for r in P):.0f}.\n")
    # Holm
    ps = {"H-V2": p2, "H-V3": p3, "H-V4a": p4}
    ordem = sorted([k for k in ps if ps[k] is not None], key=lambda k: ps[k])
    print("## Holm (α = 0,05)\n| hipótese | p | ajustado | decisão |\n|---|---:|---:|---|")
    m = len(ordem)
    prev = 0.0
    for i, k in enumerate(ordem):
        adj = min(1.0, max(prev, ps[k] * (m - i)))
        prev = adj
        print(f"| {k} | {ps[k]:.4g} | {adj:.4g} | {'rejeita H0 (predição sustentada)' if adj < 0.05 else 'não rejeita H0'} |")
    # critérios de tamanho / predicoes
    print("\n## Resumo das predições\n")
    print(f"- H-V1 (≥ 95% viáveis): {'SUSTENTADA' if len(ok0) / len(todos) >= 0.95 else 'REFUTADA'} ({100 * len(ok0) / len(todos):.1f}%).")
    if p2 is not None:
        print(f"- H-V2 (redução mediana do ar ≥ 20%, sem arestas compartilhadas): mediana {np.median(red):.1f}%, limite inferior do IC {ic[0]:.1f}% → {'SUSTENTADA' if ic[0] >= 20 and p2 < 0.05 else 'NÃO SUSTENTADA'} (p Holm: ver tabela).")
    print(f"- H-V3 (≥ 75% dos layouts com segmento ≤ peça): {100 * vit / len(L):.1f}% → {'SUSTENTADA' if vit / len(L) >= 0.75 else 'REFUTADA'} (p bruto {p3:.4g}).")
    print(f"- H-V4a (regret mediano ≥ 0,2%): {100 * np.median(exc):.3f}%, limite inferior do IC 90% {ic4[0]:.3f}% → {'SUSTENTADA' if np.median(exc) >= 0.002 and ic4[0] > 0 and p4 < 0.05 else 'NÃO SUSTENTADA'}.")
    print(f"- H-V4b (descritiva): mediana {100 * np.median(vant):+.3f}% → {'dentro' if abs(np.median(vant)) <= 0.001 else 'fora'} de ±0,1%.")
    print(f"- Predição qualitativa (perfurações): {100 * menos / len(P):.1f}% → {'SUSTENTADA' if menos / len(P) >= 0.8 else 'NÃO SUSTENTADA'}.")
    # controle de orcamento
    ctrl = [100 * (r["seg_t0"]["melhor"]["fo"] / r["peca_ctrl"]["fo"] - 1) for r in ok0 if r.get("peca_ctrl", {}).get("fo")]
    if ctrl:
        print(f"\n## Controle de orçamento\nSegmento (t = 0) sobre o PCGLNS por peça com o MESMO orçamento: tempo total, mediana {np.median(ctrl):+.3f}% (n = {len(ctrl)}); segmento menor em {sum(1 for c in ctrl if c < 0)}/{len(ctrl)}.")
    # por categoria
    print("\n## Por categoria\n| categoria | n | redução mediana do ar (t = 0) | gap de FO mediano |\n|---|---:|---:|---:|")
    for cat in ("Combined_parts", "No_precedence"):
        sub = [x for x in L if cat in x["nome"] and x["ar_peca"] > 1e-9]
        if sub:
            print(f"| {cat} | {len(sub)} | {np.median([100 * (1 - x['ar_seg'] / x['ar_peca']) for x in sub]):.1f}% | {np.median([100 * (x['fo_seg'] / x['fo_peca'] - 1) for x in sub]):+.3f}% |")


if __name__ == "__main__":
    main()
