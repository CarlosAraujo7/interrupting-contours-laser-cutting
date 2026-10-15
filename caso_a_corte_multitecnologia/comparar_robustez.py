"""
comparar_robustez.py  --  resultados das duas checagens de robustez (docs/24): (a) heuristica do LCPP reexecutada com a maquina livre; (b) referencia de nivel de peca com mais sementes e mais tempo
===========================================================================================================================================================================================
(a) `auditoria_lcpp1/caminhos_282_reexec/*.json` (mesmo pipeline, 3 s, semente 0) contra `auditoria_lcpp1/caminhos_282/*.json` (a rodada gravada sob maquina compartilhada, usada em todo o N1): diferenca relativa da FO
    formal e da poligonal; contagem de vitorias sobre o PCGLNS por peca (referencia `honesta_282`) nas duas rodadas.
(b) `auditoria_lcpp1/pecas_robustez/<inst>__s<semente>.json` (3 sementes x 60 s) contra `honesta_282/<inst>.json` (1 semente x 20 s): quanto a referencia de peca melhora e se as vitorias da heuristica mudam.
Uso: python comparar_robustez.py > RESULTADOS_ROBUSTEZ.md
"""
import os
import sys
import json
import glob
import warnings

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import avaliar_heuristica_formal as af                                  # noqa: E402

A = os.path.join(AQUI, "auditoria_lcpp1")
pct = lambda a, b: 100 * (a / b - 1)


def main():
    print("# Robustez: heurística reexecutada em máquina livre e referência de peça com mais sementes e tempo (`docs/24`)\n")
    # (a)
    novos = {os.path.basename(f)[:-5]: json.load(open(f)) for f in sorted(glob.glob(os.path.join(A, "caminhos_282_reexec", "*.json")))}
    if novos:
        L = []
        for n, r in novos.items():
            try:
                v = json.load(open(os.path.join(A, "caminhos_282", f"{n}.json")))
                h = json.load(open(os.path.join(A, "honesta_282", f"{n}.json")))
            except FileNotFoundError:
                continue
            if "fo_pcglns_honesta" not in h:
                continue
            L.append({"n": n, "peca": h["fo_pcglns_honesta"], "H_v": af.fo_formal(v["forte"], 0.0)["fo"], "H_n": af.fo_formal(r["forte"], 0.0)["fo"],
                      "P_v": af.fo_poligonal(v["forte"], 0.0)["fo"], "P_n": af.fo_poligonal(r["forte"], 0.0)["fo"], "R_v": af.fo_formal(v["forte"], 1.0)["fo"], "R_n": af.fo_formal(r["forte"], 1.0)["fo"]})
        d0 = np.array([pct(x["H_n"], x["H_v"]) for x in L])
        d1 = np.array([pct(x["R_n"], x["R_v"]) for x in L])
        wv = int(sum(1 for x in L if x["H_v"] < x["peca"]))
        wn = int(sum(1 for x in L if x["H_n"] < x["peca"]))
        pv = int(sum(1 for x in L if x["P_v"] < x["peca"]))
        pn = int(sum(1 for x in L if x["P_n"] < x["peca"]))
        print(f"## (a) Heurística reexecutada em máquina livre — {len(L)} instâncias\n")
        print(f"- Diferença da FO formal (reexecução ÷ rodada gravada − 1) em t = 0: mediana **{np.median(d0):+.4f}%**, média {d0.mean():+.4f}%, |máx.| {np.abs(d0).max():.3f}%; nova rodada menor em {int((d0 < -1e-9).sum())}, igual em {int((np.abs(d0) <= 1e-9).sum())}, maior em {int((d0 > 1e-9).sum())}.")
        print(f"- A t = 1 s: mediana {np.median(d1):+.4f}%, |máx.| {np.abs(d1).max():.3f}%.")
        print(f"- **Vitórias sobre o PCGLNS por peça** (t = 0): formal {wv} → {wn}; poligonal {pv} → {pn} (rodada gravada → reexecução).\n")
    else:
        print("## (a) sem reexecução gravada ainda\n")
    # (b)
    rob = {}
    for f in sorted(glob.glob(os.path.join(A, "pecas_robustez", "*.json"))):
        r = json.load(open(f))
        if r.get("fo_pcglns_honesta") is not None:
            rob.setdefault(r["instancia"], []).append(r["fo_pcglns_honesta"])
    if rob:
        L = []
        for n, v in rob.items():
            try:
                h = json.load(open(os.path.join(A, "honesta_282", f"{n}.json")))
                c = json.load(open(os.path.join(A, "caminhos_282", f"{n}.json")))
            except FileNotFoundError:
                continue
            if "fo_pcglns_honesta" not in h:
                continue
            L.append({"n": n, "antes": h["fo_pcglns_honesta"], "melhor": min(v), "media": sum(v) / len(v), "k": len(v), "H": af.fo_formal(c["forte"], 0.0)["fo"], "Hp": af.fo_poligonal(c["forte"], 0.0)["fo"]})
        mel = np.array([pct(x["melhor"], x["antes"]) for x in L])
        dis = np.array([pct(max(rob[x["n"]]), min(rob[x["n"]])) for x in L if len(rob[x["n"]]) > 1])
        print(f"## (b) Referência de peça: 3 sementes × 60 s contra 1 semente × 20 s — {len(L)} instâncias\n")
        print(f"- Melhor das sementes ÷ referência original − 1: mediana **{np.median(mel):+.4f}%**, mín. {mel.min():+.4f}%, máx. {mel.max():+.4f}%; melhor em {int((mel < -1e-9).sum())}, igual em {int((np.abs(mel) <= 1e-9).sum())}, pior em {int((mel > 1e-9).sum())}.")
        if len(dis):
            print(f"- Dispersão entre sementes (máx ÷ mín − 1): mediana {np.median(dis):.4f}%, máx. {dis.max():.3f}%.")
        print(f"- **Vitórias da heurística (formal, t = 0) sobre a referência de peça:** {sum(1 for x in L if x['H'] < x['antes'])} → {sum(1 for x in L if x['H'] < x['melhor'])} de {len(L)} (referência original → melhor das sementes); "
              f"poligonal: {sum(1 for x in L if x['Hp'] < x['antes'])} → {sum(1 for x in L if x['Hp'] < x['melhor'])}.")


if __name__ == "__main__":
    main()
