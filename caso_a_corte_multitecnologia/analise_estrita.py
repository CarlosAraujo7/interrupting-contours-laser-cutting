"""
analise_estrita.py  --  analise da sensibilidade ESTRITA x FECHAMENTO no nivel de segmento (docs/21). Escrita ANTES de existir qualquer resultado em estrita_resultados/.
=================================================================================================================================================================
Por layout (30, `lista_varredura_t.txt`) e t em {0, 1,0 s}:
  FECHAMENTO  `segmento_resultados/seg_<inst>_t<t>.json`  (ja existente; mesmos parametros)       ESTRITA  `estrita_resultados/est_<inst>_t<t>.json`
  PECA        PCGLNS do E-A0 (media de 10 sementes, T = 30 s) + t x nº de contornos; ar = FO - L_pecas/v_cut
Medidas: preco da estrita no ar e no tempo total (estrita/fechamento - 1); estrita x peca no ar e no tempo total.
Predicoes registradas em docs/21 (exploratorio; sem teste de hipotese formal, so medianas e IC bootstrap 95% da mediana):
  P-S1  fechamento <= estrita em >= 90% dos layouts (o conjunto viavel da estrita esta contido no do fechamento; so o ruido do solver pode inverter)
  P-S2  preco da estrita no AR (t = 0): mediana >= +30%     [ajustada de "+2% a +30%" depois de um teste funcional em p1xe_7: ar 885 (estrita) x 235 (fechamento); declarado em docs/21 §1]
  P-S3  preco da estrita no tempo TOTAL (t = 0): mediana <= +1%   [idem: no teste, +0,53%]
  P-S4  a estrita ainda reduz o AR em relacao a peca: mediana da reducao >= 10% (t = 0)
Uso: python analise_estrita.py > RESULTADOS_ESTRITA.md
"""
import os
import sys
import json
import glob
import statistics
import warnings

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from heuristic_core import _DEFAULT_CONFIG as D                     # noqa: E402

VC, VA = D["v_cut"], D["v_air"]
rng = np.random.default_rng(2027)


def boot(x, n=10000):
    x = np.asarray(x, float)
    return np.percentile([np.median(rng.choice(x, size=len(x), replace=True)) for _ in range(n)], (2.5, 97.5))


def media_peca(nome):
    v = []
    for f in glob.glob(os.path.join(AQUI, "ea0_resultados", f"ea0_{nome}_pcglns_T30_s*.json")):
        d = json.load(open(f))
        if d.get("fo") is not None:
            v.append(d["fo"])
    return statistics.mean(v) if v else None


def carregar(t):
    L = []
    for n in open(os.path.join(AQUI, "lista_varredura_t.txt"), encoding="utf-8").read().strip().split(","):
        fe = os.path.join(AQUI, "estrita_resultados", f"est_{n}_t{t:g}.json")
        fc = os.path.join(AQUI, "segmento_resultados", f"seg_{n}_t{t:g}.json")
        fa = os.path.join(AQUI, "ar_resultados", f"ar_{n}.json")
        if not (os.path.exists(fe) and os.path.exists(fc) and os.path.exists(fa)):
            continue
        e, c, a = json.load(open(fe)), json.load(open(fc)), json.load(open(fa))
        pg = media_peca(n)
        if not c["melhor"] or pg is None:
            continue
        r = {"nome": n, "E": c["E"], "pares": c["n_pares_pi"], "fo_c": c["melhor"]["fo"], "ar_c": c["melhor"]["ar"] / VA, "R_c": c["melhor"]["n_perf"],
             "fo_p": pg + t * c["n_pecas"], "ar_p": pg - a["L_pecas"] / a["v_cut"], "fo_e": None, "ar_e": None, "R_e": None}
        if e["melhor"]:
            r.update(fo_e=e["melhor"]["fo"], ar_e=e["melhor"]["ar"] / VA, R_e=e["melhor"]["n_perf"])
        L.append(r)
    return L


def main():
    print("# Sensibilidade: Π estrita × Π de fechamento no nível de segmento (`docs/21`; exploratório)\n")
    for t in (0.0, 1.0):
        L = carregar(t)
        if not L:
            print(f"## t = {t:g} s\nsem resultados.\n")
            continue
        S = [x for x in L if x["fo_e"] is not None]
        print(f"## t = {t:g} s — {len(L)} layouts com fechamento e referência de peça; estrita viável e verificada em **{len(S)}/{len(L)}**\n")
        if not S:
            continue
        pa = np.array([100 * (x["ar_e"] / x["ar_c"] - 1) for x in S if x["ar_c"] > 1e-9])
        pf = np.array([100 * (x["fo_e"] / x["fo_c"] - 1) for x in S])
        ep = np.array([100 * (1 - x["ar_e"] / x["ar_p"]) for x in S if x["ar_p"] > 1e-9])
        ef = np.array([100 * (x["fo_e"] / x["fo_p"] - 1) for x in S])
        cp = np.array([100 * (x["fo_c"] / x["fo_p"] - 1) for x in S])
        cl = sum(1 for x in S if x["fo_c"] <= x["fo_e"] + 1e-9)
        i1, i2, i3 = boot(pa), boot(pf), boot(ep)
        print(f"- **Preço da estrita no ar** (estrita/fechamento − 1): mediana **{np.median(pa):+.2f}%** (IC 95% [{i1[0]:+.2f}%; {i1[1]:+.2f}%]; máx. {pa.max():+.1f}%); fechamento ≤ estrita em **{cl}/{len(S)}** layouts no tempo total.")
        print(f"- **Preço da estrita no tempo total:** mediana **{np.median(pf):+.3f}%** (IC 95% [{i2[0]:+.3f}%; {i2[1]:+.3f}%]).")
        print(f"- **Estrita × peça:** redução mediana do ar **{np.median(ep):.1f}%** (IC 95% [{i3[0]:.1f}%; {i3[1]:.1f}%]); tempo total mediano {np.median(ef):+.3f}% (menor em {int((ef < 0).sum())}/{len(S)}); para comparação, fechamento × peça no tempo total: {np.median(cp):+.3f}% (menor em {int((cp < 0).sum())}/{len(S)}).")
        print(f"- Corridas (mediana): estrita {statistics.median(x['R_e'] for x in S):.0f}, fechamento {statistics.median(x['R_c'] for x in S):.0f}.\n")
        if t == 0.0:
            print("### Predições registradas (`docs/21`, t = 0)\n")
            print(f"- P-S1 (fechamento ≤ estrita em ≥ 90%): {100 * cl / len(S):.1f}% → {'SUSTENTADA' if cl / len(S) >= 0.9 else 'NÃO SUSTENTADA'}.")
            print(f"- P-S2 (preço no ar ≥ +30%): {np.median(pa):+.2f}% → {'SUSTENTADA' if np.median(pa) >= 30 else 'NÃO SUSTENTADA'}.")
            print(f"- P-S3 (preço no tempo total ≤ +1%): {np.median(pf):+.3f}% → {'SUSTENTADA' if np.median(pf) <= 1.0 else 'NÃO SUSTENTADA'}.")
            print(f"- P-S4 (estrita ainda reduz o ar ≥ 10% sobre a peça): {np.median(ep):.1f}% → {'SUSTENTADA' if np.median(ep) >= 10 else 'NÃO SUSTENTADA'}.\n")
        print("| layout | arcos | pares Π | ar fechamento | ar estrita | ar peça | FO fecham. | FO estrita | FO peça |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for x in sorted(S, key=lambda x: x["E"]):
            print(f"| {x['nome']} | {x['E']} | {x['pares']} | {x['ar_c']:.3f} | {x['ar_e']:.3f} | {x['ar_p']:.3f} | {x['fo_c']:.2f} | {x['fo_e']:.2f} | {x['fo_p']:.2f} |")
        print()


if __name__ == "__main__":
    main()
