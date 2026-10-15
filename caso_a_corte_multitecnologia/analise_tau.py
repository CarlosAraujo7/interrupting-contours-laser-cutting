"""
analise_tau.py  --  analise PRE-REGISTRADA da reotimizacao dos dois niveis com tempo de voo nao linear (docs/26 §4-5). Escrita ANTES de existir qualquer resultado em tau_resultados/.
=================================================================================================================================================================================
Por instancia (60 da amostra do V3) e curva em {LASER, DEWIL16} (t_av = 0): S = nivel de segmento reotimizado para a curva (melhor das 2 rodadas verificadas), P = nivel de peca reotimizado para a curva;
referencias descritivas: G = rota de segmento ciente do reinicio G(0,25) do V3 avaliada na curva (nao reotimizada), P0 = caminho de peca guardado (otimizado para tempo linear).
Hipoteses (decisao por faixa da mediana; IC bootstrap 95% da mediana relatado; sem teste de significancia):
  H-R1  (DEWIL16)  mediana de S/P - 1 em [-0,15%; +0,05%]   (a vantagem de tempo total do nivel de segmento, com ambos reotimizados, e <= 0,15% e nao e uma perda relevante)
  H-R2  (LASER)    mediana de S/P - 1 em [-0,15%; +0,05%]
  H-R3  (DEWIL16)  S <= G em >= 75% das instancias (reotimizar para a curva ajuda o nivel de segmento)
  H-R4  (descritiva; DEWIL16) nº medio de movimentos em vazio de S <= 40 (H: 60; P: 38)
  H-R5  (descritiva) validacao: o tempo LIN do nivel de peca proprio reproduz o FO honesto guardado do pipeline do LCPP-1 em >= 95% das instancias (|diferenca| <= 0,05%)
  H-R6  (descritiva; DEWIL16) mediana de P/P0 - 1 (reotimizar o nivel de peca para a curva) <= 0 e fracao de instancias com P < P0
Uso: python analise_tau.py > RESULTADOS_TAU_ANALISE.md
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
import analise_voo_nao_linear as vn                                        # noqa: E402

rng = np.random.default_rng(2027)


def boot(x, n=10000):
    x = np.asarray(x, float)
    return np.percentile([np.median(rng.choice(x, size=len(x), replace=True)) for _ in range(n)], (2.5, 97.5))


def ler(nivel, perfil, n):
    f = os.path.join(AQUI, "tau_resultados", f"{nivel}_{perfil}_{n}.json")
    return json.load(open(f)) if os.path.exists(f) else None


def main():
    est = {n: R for n, R, _ in vn.carregar()}
    print("# Reotimização dos dois níveis com tempo de voo não linear (`docs/26`; análise pré-registrada)\n")
    L = {}
    for perfil in ("LASER", "DEWIL16"):
        for n in rv.amostra():
            s, p, p_lin = ler("segmento", perfil, n), ler("peca", perfil, n), ler("peca", "LIN", n)
            if not (s and p and s.get("melhor") and "T" in p and n in est):
                continue
            R = est[n]
            L.setdefault(perfil, []).append({"n": n, "S": s["melhor"]["T"][perfil], "P": p["T"][perfil], "mS": s["melhor"]["n_movimentos"], "mP": p["n_movimentos"], "rS": s["melhor"]["corridas"],
                                             "G": vn.total(R["G0.25"], perfil, 0.0), "P0": vn.total(R["P"], perfil, 0.0), "H": vn.total(R["H"], perfil, 0.0), "viol": p.get("violacoes_pi", 0),
                                             "linP": p_lin["T"]["LIN"] if p_lin and "T" in p_lin else None, "fo0": None})
    print(f"Instâncias com resultado: " + ", ".join(f"{k}: {len(v)}/{len(rv.amostra())}" for k, v in L.items()) + ".\n")
    resumo = {}
    for perfil, S in L.items():
        sp = np.array([100 * (x["S"] / x["P"] - 1) for x in S])
        sg = np.array([100 * (x["S"] / x["G"] - 1) for x in S])
        pp = np.array([100 * (x["P"] / x["P0"] - 1) for x in S])
        hp = np.array([100 * (x["H"] / x["P"] - 1) for x in S])
        gp = np.array([100 * (x["G"] / x["P"] - 1) for x in S])
        i1, i2, i3 = boot(sp), boot(sg), boot(pp)
        print(f"## {perfil} (n = {len(S)}; t_av = 0)\n")
        print(f"- **S/P − 1** (segmento × peça, ambos reotimizados): mediana **{np.median(sp):+.3f}%** (IC 95% [{i1[0]:+.3f}%; {i1[1]:+.3f}%]; mín. {sp.min():+.2f}%, máx. {sp.max():+.2f}%); S < P em **{int((sp < -1e-9).sum())}/{len(S)}**, S > P em {int((sp > 1e-9).sum())}.")
        print(f"- S/G − 1 (reotimizado × rota guardada ciente do reinício, avaliada na curva): mediana {np.median(sg):+.3f}% (IC [{i2[0]:+.3f}%; {i2[1]:+.3f}%]); S ≤ G em {int((sg <= 1e-9).sum())}/{len(S)}.")
        print(f"- P/P0 − 1 (peça reotimizado × peça otimizado para tempo linear): mediana {np.median(pp):+.3f}% (IC [{i3[0]:+.3f}%; {i3[1]:+.3f}%]); P < P0 em {int((pp < -1e-9).sum())}/{len(S)}.")
        print(f"- Referências sem reotimizar: H/P − 1 = {np.median(hp):+.3f}% e G/P − 1 = {np.median(gp):+.3f}% (medianas).")
        print(f"- Movimentos em vazio (mediana): S {np.median([x['mS'] for x in S]):.0f}; P {np.median([x['mP'] for x in S]):.0f}; corridas de S {np.median([x['rS'] for x in S]):.0f}; violações de Π no nível de peça: {sum(x['viol'] for x in S)}.\n")
        resumo[perfil] = {"sp": sp, "sg": sg, "pp": pp, "S": S}
    if "DEWIL16" in resumo:
        v = [x for x in resumo["DEWIL16"]["S"] if x["linP"] is not None]
        ref = {n: fo for n, _, fo in vn.carregar()}
        d = np.array([abs(x["linP"] / ref[x["n"]] - 1) for x in v if ref.get(x["n"])])
        print(f"## Validação do nível de peça próprio (LIN)\n\nTempo LIN do nível de peça próprio × FO honesto guardado do pipeline do LCPP-1: |diferença| mediana {100 * np.median(d):.4f}%, máx. {100 * d.max():.3f}%; dentro de 0,05% em {int((d <= 5e-4).sum())}/{len(d)}.\n")
    print("## Predições (`docs/26`)\n")
    for perfil, tag in (("DEWIL16", "H-R1"), ("LASER", "H-R2")):
        if perfil in resumo:
            m = np.median(resumo[perfil]["sp"])
            print(f"- {tag} ({perfil}: mediana de S/P − 1 em [−0,15%; +0,05%]): {m:+.3f}% → {'SUSTENTADA' if -0.15 <= m <= 0.05 else 'NÃO SUSTENTADA'}.")
    if "DEWIL16" in resumo:
        r = resumo["DEWIL16"]
        frac = float((r["sg"] <= 1e-9).mean())
        print(f"- H-R3 (DEWIL16: S ≤ G em ≥ 75%): {100 * frac:.1f}% → {'SUSTENTADA' if frac >= 0.75 else 'NÃO SUSTENTADA'}.")
        mm = np.mean([x["mS"] for x in r["S"]])
        print(f"- H-R4 (descritiva; DEWIL16: nº médio de movimentos de S ≤ 40): {mm:.1f} → {'dentro' if mm <= 40 else 'fora'}.")
        print(f"- H-R5 (descritiva; validação do nível de peça): {int((d <= 5e-4).sum())}/{len(d)} dentro de 0,05% → {'dentro' if (d <= 5e-4).mean() >= 0.95 else 'fora'}.")
        print(f"- H-R6 (descritiva; DEWIL16: mediana de P/P0 − 1 ≤ 0): {np.median(r['pp']):+.3f}% (P < P0 em {int((r['pp'] < -1e-9).sum())}/{len(r['pp'])}) → {'dentro' if np.median(r['pp']) <= 0 else 'fora'}.")


if __name__ == "__main__":
    main()
