"""
analise_tau_reinicio.py  --  analise PRE-REGISTRADA de tau(d) + reinicio t > 0 (docs/27 §3-4). Escrita ANTES de existir qualquer resultado em tau_reinicio_resultados/.
=========================================================================================================================================================================
Por instancia (60) e curva em {DEWIL16, LASER}, t em {0,25; 1,0}: S_t = segmento reotimizado para tau(d) + t; S_0 = segmento reotimizado para tau(d) com t = 0 (`tau_resultados/`) avaliado em t (T0 + t x corridas);
P_t = nivel de peca reotimizado para tau(d) (`tau_resultados/`), T_P(t) = T_P(0) + t x corridas (a rota de peca nao depende de t).
Hipoteses (decisao por faixa/limiar da mediana; IC bootstrap 95% da mediana):
  H-C1  (DEWIL16, t = 1,0)  mediana de S_t/P_t - 1 em [-0,15%; +0,05%]
  H-C2  (LASER, t = 1,0)    idem
  H-C3  (DEWIL16, t = 1,0)  mediana de S_0/S_t - 1 >= 2%   (ignorar o reinicio custa >= 2% mesmo com a curva de voo)
  H-C4  (descritiva; DEWIL16, t = 1,0)  mediana das corridas de S_t <= mediana dos contornos + 2
  H-C5  (descritiva; DEWIL16, t = 0,25) mediana de S_t/P_t - 1 em [-0,15%; +0,05%]
  H-C6  (descritiva; LASER, t = 0,25)   idem
Uso: python analise_tau_reinicio.py > RESULTADOS_TAU_REINICIO_ANALISE.md
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

rng = np.random.default_rng(2027)


def boot(x, n=10000):
    x = np.asarray(x, float)
    return np.percentile([np.median(rng.choice(x, size=len(x), replace=True)) for _ in range(n)], (2.5, 97.5))


def ler(sub, nome):
    f = os.path.join(AQUI, sub, nome)
    return json.load(open(f)) if os.path.exists(f) else None


def carregar(perfil, t):
    L = []
    for n in rv.amostra():
        s = ler("tau_reinicio_resultados", f"segmento_{perfil}_t{t:g}_{n}.json")
        s0 = ler("tau_resultados", f"segmento_{perfil}_{n}.json")
        p = ler("tau_resultados", f"peca_{perfil}_{n}.json")
        if not (s and s.get("melhor") and s0 and s0.get("melhor") and p and "T" in p):
            continue
        S, S0 = s["melhor"], s0["melhor"]
        L.append({"n": n, "nc": s["n_contornos"], "St": S["T"], "rS": S["corridas"], "S0": S0["T"][perfil] + t * S0["corridas"], "rS0": S0["corridas"], "Pt": p["T"][perfil] + t * p["corridas"], "rP": p["corridas"]})
    return L


def main():
    print("# Tempo de voo não linear + custo de reinício: nível de segmento reotimizado (`docs/27`; análise pré-registrada)\n")
    res = {}
    for perfil in ("DEWIL16", "LASER"):
        for t in (0.25, 1.0):
            L = carregar(perfil, t)
            if not L:
                continue
            sp = np.array([100 * (x["St"] / x["Pt"] - 1) for x in L])
            s0 = np.array([100 * (x["S0"] / x["St"] - 1) for x in L])
            i1, i2 = boot(sp), boot(s0)
            print(f"## {perfil}, t = {t:g} s (n = {len(L)})\n")
            print(f"- **S_t/P_t − 1:** mediana **{np.median(sp):+.3f}%** (IC 95% [{i1[0]:+.3f}%; {i1[1]:+.3f}%]; mín. {sp.min():+.2f}%, máx. {sp.max():+.2f}%); S_t < P_t em **{int((sp < -1e-9).sum())}/{len(L)}**.")
            print(f"- **S_0/S_t − 1** (a rota ótima para t = 0, ignorando o reinício, avaliada em t): mediana **{np.median(s0):+.2f}%** (IC [{i2[0]:+.2f}%; {i2[1]:+.2f}%]; máx. {s0.max():+.1f}%).")
            print(f"- Corridas (mediana): S_t {np.median([x['rS'] for x in L]):.0f}; S_0 {np.median([x['rS0'] for x in L]):.0f}; peça {np.median([x['rP'] for x in L]):.0f}; contornos {np.median([x['nc'] for x in L]):.0f}.\n")
            res[(perfil, t)] = {"sp": sp, "s0": s0, "L": L}
    print("## Predições (`docs/27`)\n")
    band = lambda m: -0.15 <= m <= 0.05
    ok = lambda b: "SUSTENTADA" if b else "NÃO SUSTENTADA"
    k = ("DEWIL16", 1.0)
    if k in res:
        print(f"- H-C1 (DEWIL16, t = 1: mediana de S_t/P_t − 1 em [−0,15%; +0,05%]): {np.median(res[k]['sp']):+.3f}% → {ok(band(np.median(res[k]['sp'])))}.")
        print(f"- H-C3 (DEWIL16, t = 1: S_0/S_t − 1 ≥ 2%): {np.median(res[k]['s0']):+.2f}% → {ok(np.median(res[k]['s0']) >= 2.0)}.")
        rS, nc = np.median([x["rS"] for x in res[k]["L"]]), np.median([x["nc"] for x in res[k]["L"]])
        print(f"- H-C4 (descritiva; corridas de S_t ≤ contornos + 2): {rS:.0f} contra {nc:.0f} + 2 → {'dentro' if rS <= nc + 2 else 'fora'}.")
    k = ("LASER", 1.0)
    if k in res:
        print(f"- H-C2 (LASER, t = 1: mediana de S_t/P_t − 1 em [−0,15%; +0,05%]): {np.median(res[k]['sp']):+.3f}% → {ok(band(np.median(res[k]['sp'])))}.")
    for perfil, tag in (("DEWIL16", "H-C5"), ("LASER", "H-C6")):
        k = (perfil, 0.25)
        if k in res:
            print(f"- {tag} (descritiva; {perfil}, t = 0,25: mediana de S_t/P_t − 1 em [−0,15%; +0,05%]): {np.median(res[k]['sp']):+.3f}% → {'dentro' if band(np.median(res[k]['sp'])) else 'fora'}.")


if __name__ == "__main__":
    main()
