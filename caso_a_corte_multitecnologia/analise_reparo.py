"""
analise_reparo.py  --  analise PRE-REGISTRADA do reparo ciente do reinicio (docs/23 §4-5). Escrita ANTES de existir qualquer resultado em reparo_resultados/ para a amostra do V3.
=============================================================================================================================================================
Por instancia (60 da amostra do V3) e t em {0,25; 1,0}:
  H     heuristica do LCPP (FO formal, ordem de servico fixa, orientacoes por DP)         Rep   heuristica + reparo (`reparo_reinicio.py`)
  B     = min(G(t), G0(t)): melhor solucao verificada de nivel de segmento (V3)            G     GTSP de arcos + PCGLNS com custo de reinicio t (V3)        P   nivel de peca (PCGLNS por peca + t x contornos)
Hipoteses (t primario = 1,0 s; t = 0,25 s descritivo; familia de Holm {H-P1, H-P2}; alfa = 0,05):
  H-P1  mediana de Rep/B - 1 <= 3%                      (Wilcoxon unilateral de (Rep/B - 1 - 0,03) < 0; IC bootstrap 95% da mediana)       [o reparo fecha a maior parte do excesso de ~10% da heuristica]
  H-P2  mediana da reducao (H - Rep)/H >= 5%             (Wilcoxon unilateral de (reducao - 0,05) > 0; IC bootstrap)
  H-P3  100% das solucoes finais verificadas: contiguas, partem e voltam a origem, cobertura geometrica OK, 0 violacoes de Pi de fechamento (geometrica e do verificador), e nenhuma pior que a inicial (Rep <= H)   (deterministica)
  H-P4  (descritiva) fracao do excesso recuperada, (H - Rep)/(H - B), mediana >= 50%
  H-P5  (descritiva) >= 95% das buscas convergem (sem atingir max_iter nem o limite de tempo); tempo mediano da busca <= 5 s
  H-P6  (descritiva) Rep/P - 1 (P = nivel de peca) com mediana em [-0,5%; +1,0%]; relatar a fracao de instancias com Rep < P e Rep < B
Uso: python analise_reparo.py > RESULTADOS_REPARO_ANALISE.md
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
import analise_v3 as av                                                      # noqa: E402

rng = np.random.default_rng(2027)


def boot(x, n=10000):
    x = np.asarray(x, float)
    return np.percentile([np.median(rng.choice(x, size=len(x), replace=True)) for _ in range(n)], (2.5, 97.5))


def carregar():
    L = []
    for x in av.carregar():
        if x["R"] is None:
            continue
        f = os.path.join(AQUI, "reparo_resultados", f"{x['nome']}__t{x['t']}.json")
        if not os.path.exists(f):
            continue
        r = json.load(open(f))
        x = dict(x)
        x.update(Rep=r["Rep_fo"], Hr=r["H_fo"], Rrep=r["Rep_corridas"], Rh=r["H_corridas"], conv=r["convergiu"] and not r["por_tempo"], tb=r["tempo_busca_s"], it=r["iteracoes"],
                 ok=bool(r.get("verif_contiguo") and r.get("verif_origem") and r.get("verif_geo_ok") and r.get("verif_viol_fechamento") == 0 and r["fim_viavel"] and r["inicio_viavel"] and r["Rep_fo"] <= r["H_fo"] + 1e-9))
        L.append(x)
    return L


def main():
    L = carregar()
    n_am = len(av.rv.amostra())
    print("# Análise pré-registrada do reparo ciente do reinício (`docs/23`)\n")
    print(f"Amostra: {n_am} instâncias; resultados do reparo: {len({x['nome'] for x in L})}.\n")
    ps, res = {}, {}
    for t in av.TS:
        S = [x for x in L if x["t"] == t]
        if not S:
            continue
        rb = np.array([x["Rep"] / x["B"] - 1 for x in S])
        hb = np.array([x["Hr"] / x["B"] - 1 for x in S])
        red = np.array([(x["Hr"] - x["Rep"]) / x["Hr"] for x in S])
        rec = np.array([(x["Hr"] - x["Rep"]) / (x["Hr"] - x["B"]) for x in S if x["Hr"] - x["B"] > 1e-9])
        rp = np.array([x["Rep"] / x["P"] - 1 for x in S])
        ok = sum(1 for x in S if x["ok"])
        conv = sum(1 for x in S if x["conv"])
        print(f"## t = {t} s (n = {len(S)})\n")
        i1, i2 = boot(100 * rb), boot(100 * red)
        print(f"- **Rep/B − 1:** mediana **{100 * np.median(rb):+.3f}%** (IC 95% [{i1[0]:+.3f}%; {i1[1]:+.3f}%]); antes do reparo H/B − 1: {100 * np.median(hb):+.3f}%; Rep ≤ B em {int((rb <= 1e-9).sum())}/{len(S)}.")
        print(f"- **Redução (H − Rep)/H:** mediana **{100 * np.median(red):.2f}%** (IC 95% [{i2[0]:.2f}%; {i2[1]:.2f}%]); Rep < H em {int((red > 1e-9).sum())}/{len(S)}; corridas: H {np.median([x['Rh'] for x in S]):.0f} → Rep {np.median([x['Rrep'] for x in S]):.0f}.")
        print(f"- **Fração do excesso recuperada** (H − Rep)/(H − B): mediana **{100 * np.median(rec):.1f}%** (n = {len(rec)}).")
        print(f"- **Verificação (H-P3):** {ok}/{len(S)} soluções verificadas e não piores que a inicial. **Convergência:** {conv}/{len(S)}; tempo mediano da busca {np.median([x['tb'] for x in S]):.2f} s (máx. {max(x['tb'] for x in S):.1f} s); iterações medianas {np.median([x['it'] for x in S]):.0f}.")
        ip = boot(100 * rp)
        print(f"- **Rep × nível de peça:** mediana **{100 * np.median(rp):+.3f}%** (IC 95% [{ip[0]:+.3f}%; {ip[1]:+.3f}%]); Rep < P em {int((rp < 0).sum())}/{len(S)}.\n")
        if t == 1.0:
            ps["H-P1"] = stats.wilcoxon(rb - 0.03, alternative="less").pvalue
            ps["H-P2"] = stats.wilcoxon(red - 0.05, alternative="greater").pvalue
            res = {"rb": rb, "red": red, "rec": rec, "rp": rp, "ok": ok, "n": len(S), "conv": conv, "tb": np.median([x["tb"] for x in S])}
    if ps:
        print("## Holm (α = 0,05; t = 1,0 s)\n| hipótese | p | ajustado | decisão |\n|---|---:|---:|---|")
        ordem = sorted(ps, key=lambda k: ps[k])
        prev, m = 0.0, len(ordem)
        for i, k in enumerate(ordem):
            adj = min(1.0, max(prev, ps[k] * (m - i)))
            prev = adj
            print(f"| {k} | {ps[k]:.4g} | {adj:.4g} | {'rejeita H0 (predição sustentada)' if adj < 0.05 else 'não rejeita H0'} |")
        print("\n## Resumo das predições (t = 1,0 s)\n")
        print(f"- H-P1 (mediana de Rep/B − 1 ≤ 3%): {100 * np.median(res['rb']):+.3f}% → {'SUSTENTADA' if np.median(res['rb']) <= 0.03 and ps['H-P1'] < 0.05 else 'NÃO SUSTENTADA'} (p bruto {ps['H-P1']:.4g}).")
        print(f"- H-P2 (redução mediana ≥ 5%): {100 * np.median(res['red']):.2f}% → {'SUSTENTADA' if np.median(res['red']) >= 0.05 and ps['H-P2'] < 0.05 else 'NÃO SUSTENTADA'} (p bruto {ps['H-P2']:.4g}).")
        print(f"- H-P3 (100% verificadas e não piores): {res['ok']}/{res['n']} → {'SUSTENTADA' if res['ok'] == res['n'] else 'NÃO SUSTENTADA'}.")
        print(f"- H-P4 (descritiva; fração recuperada ≥ 50%): {100 * np.median(res['rec']):.1f}% → {'dentro' if np.median(res['rec']) >= 0.5 else 'fora'}.")
        print(f"- H-P5 (descritiva; ≥ 95% convergem; tempo mediano ≤ 5 s): {100 * res['conv'] / res['n']:.1f}%; {res['tb']:.2f} s → {'dentro' if res['conv'] / res['n'] >= 0.95 and res['tb'] <= 5 else 'fora'}.")
        print(f"- H-P6 (descritiva; Rep/P − 1 em [−0,5%; +1,0%]): {100 * np.median(res['rp']):+.3f}% → {'dentro' if -0.005 <= np.median(res['rp']) <= 0.01 else 'fora'}.")
    print("\n## Por categoria (t = 1,0 s)\n| categoria | n | Rep/B − 1 | H/B − 1 | redução | Rep/P − 1 |\n|---|---:|---:|---:|---:|---:|")
    for cat in ("regular", "irregular", "hole", "esicup"):
        S = [x for x in L if x["t"] == 1.0 and x["cat"] == cat]
        if S:
            print(f"| {cat} | {len(S)} | {100 * np.median([x['Rep'] / x['B'] - 1 for x in S]):+.3f}% | {100 * np.median([x['Hr'] / x['B'] - 1 for x in S]):+.3f}% | "
                  f"{100 * np.median([(x['Hr'] - x['Rep']) / x['Hr'] for x in S]):.2f}% | {100 * np.median([x['Rep'] / x['P'] - 1 for x in S]):+.3f}% |")


if __name__ == "__main__":
    main()
