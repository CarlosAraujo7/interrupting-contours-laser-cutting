"""
analise_fendas.py  --  analise PRE-REGISTRADA da inclusao das fendas abertas (docs/28 §3-4). Escrita ANTES de existir qualquer resultado em fendas_resultados/.
=============================================================================================================================================================
Por layout (14 do CPPLib, <= 130 vertices; tempo de voo LINEAR): S0 = segmento SEM fendas (`segmento_resultados/seg_<layout>_t0.json`, t = 0; ar e FO); S = segmento COM fendas (t = 0 e t = 1 s);
P = nivel de peca COM fendas (cada pedaco de fenda e um grupo de 2 cidades; uma corrida por contorno e por pedaco).
Hipoteses (decisao por limiar/faixa da mediana; sem teste de significancia; n pequeno):
  H-F1  viabilidade: o segmento COM fendas tem solucao verificada em 14/14 layouts (t = 0 e t = 1 s)
  H-F2  a inclusao das fendas AUMENTA o tempo de ar do segmento (t = 0): mediana de ar_S / ar_S0 - 1 >= +10%
  H-F3  o segmento COM fendas reduz o tempo de ar do nivel de peca COM fendas (t = 0): mediana da reducao 1 - ar_S / ar_P >= 30%
  H-F4  tempo TOTAL (t = 0): S <= P em >= 75% dos layouts
  H-F5  (descritiva) a t = 1 s: mediana de (FO_S(1) / (FO_P + 1 x corridas_P) - 1) em [-0,3%; +0,3%] (o ganho de roteamento desaparece com o reinicio caro)
  H-F6  (descritiva) nenhum caminho do nivel de peca viola Pi (0 violacoes)
Uso: python analise_fendas.py > RESULTADOS_FENDAS_ANALISE.md
"""
import os
import sys
import json
import warnings

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
rng = np.random.default_rng(2027)


def boot(x, n=10000):
    x = np.asarray(x, float)
    return np.percentile([np.median(rng.choice(x, size=len(x), replace=True)) for _ in range(n)], (2.5, 97.5))


def ler(sub, nome):
    f = os.path.join(AQUI, sub, nome)
    return json.load(open(f)) if os.path.exists(f) else None


def main():
    V = json.load(open(os.path.join(AQUI, "cpplib_vertices.json")))
    nomes = [n for v, n in V if v <= 130]
    L = []
    for n in nomes:
        s0, s, s1, p = ler("segmento_resultados", f"seg_{n}_t0.json"), ler("fendas_resultados", f"segmento_{n}_t0.json"), ler("fendas_resultados", f"segmento_{n}_t1.json"), ler("fendas_resultados", f"peca_{n}.json")
        L.append({"n": n, "s0": s0, "s": s, "s1": s1, "p": p})
    print("# Fendas abertas incluídas (`docs/28`; análise pré-registrada; exploratório, 14 layouts do CPPLib)\n")
    ok0 = [x for x in L if x["s"] and x["s"].get("melhor")]
    ok1 = [x for x in L if x["s1"] and x["s1"].get("melhor")]
    pk = [x for x in L if x["p"] and "fo" in x["p"]]
    print(f"Layouts: {len(L)}; com solução verificada de segmento COM fendas: t = 0: {len(ok0)}/{len(L)}, t = 1 s: {len(ok1)}/{len(L)}; com nível de peça COM fendas: {len(pk)}/{len(L)}.\n")
    V0 = [x for x in ok0 if x["s0"] and x["s0"].get("melhor")]
    VP = [x for x in ok0 if x["p"] and "fo" in x["p"]]
    if V0:
        a = np.array([100 * (x["s"]["melhor"]["ar_s"] / (x["s0"]["melhor"]["ar"] / 400.0) - 1) for x in V0 if x["s0"]["melhor"]["ar"] > 1e-9])
        i = boot(a)
        print(f"- **Efeito das fendas no ar do segmento** (ar COM / ar SEM − 1; t = 0; n = {len(a)}): mediana **{np.median(a):+.1f}%** (IC 95% [{i[0]:+.1f}%; {i[1]:+.1f}%]; máx. {a.max():+.0f}%).")
        print(f"- Fendas: mediana de {np.median([x['s']['n_fendas'] for x in V0]):.0f} por layout ({np.median([x['s']['n_pedacos'] for x in V0]):.0f} pedaços; contornos {np.median([x['s']['n_contornos'] for x in V0]):.0f}).")
    if VP:
        red = np.array([100 * (1 - x["s"]["melhor"]["ar_s"] / x["p"]["ar_s"]) for x in VP if x["p"]["ar_s"] > 1e-9])
        fo = np.array([100 * (x["s"]["melhor"]["fo"] / x["p"]["fo"] - 1) for x in VP])
        i1, i2 = boot(red), boot(fo)
        print(f"- **Segmento × peça, ambos COM fendas (t = 0; n = {len(VP)}):** redução mediana do ar **{np.median(red):.1f}%** (IC 95% [{i1[0]:.1f}%; {i1[1]:.1f}%]); tempo total mediano **{np.median(fo):+.3f}%** (IC [{i2[0]:+.3f}%; {i2[1]:+.3f}%]); segmento ≤ peça em **{int((fo <= 1e-9).sum())}/{len(fo)}**.")
    V1 = [x for x in ok1 if x["p"] and "fo" in x["p"]]
    if V1:
        f1 = np.array([100 * (x["s1"]["melhor"]["fo"] / (x["p"]["fo"] + 1.0 * x["p"]["corridas"]) - 1) for x in V1])
        i3 = boot(f1)
        print(f"- **A t = 1 s (n = {len(V1)}):** segmento × peça, tempo total mediano **{np.median(f1):+.3f}%** (IC [{i3[0]:+.3f}%; {i3[1]:+.3f}%]); corridas do segmento {np.median([x['s1']['melhor']['corridas'] for x in V1]):.0f} contra {np.median([x['p']['corridas'] for x in V1]):.0f} do nível de peça.")
    print("\n| layout | contornos | fendas (pedaços) | ar SEM (s) | ar COM (s) | ar peça COM (s) | FO COM | FO peça COM |\n|---|---:|---:|---:|---:|---:|---:|---:|")
    for x in L:
        if x["s"] and x["s"].get("melhor"):
            s0a = f"{x['s0']['melhor']['ar'] / 400.0:.2f}" if x["s0"] and x["s0"].get("melhor") else "—"
            pa = f"{x['p']['ar_s']:.2f}" if x["p"] and "fo" in x["p"] else "—"
            pf = f"{x['p']['fo']:.1f}" if x["p"] and "fo" in x["p"] else "—"
            print(f"| {x['n']} | {x['s']['n_contornos']} | {x['s']['n_fendas']} ({x['s']['n_pedacos']}) | {s0a} | {x['s']['melhor']['ar_s']:.2f} | {pa} | {x['s']['melhor']['fo']:.1f} | {pf} |")
    print("\n## Predições (`docs/28`)\n")
    ok = lambda b: "SUSTENTADA" if b else "NÃO SUSTENTADA"
    print(f"- H-F1 (viabilidade 14/14 em t = 0 e t = 1 s): {len(ok0)}/{len(L)} e {len(ok1)}/{len(L)} → {ok(len(ok0) == len(L) and len(ok1) == len(L))}.")
    if V0:
        print(f"- H-F2 (ar COM/SEM − 1 ≥ +10%): {np.median(a):+.1f}% → {ok(np.median(a) >= 10)}.")
    if VP:
        print(f"- H-F3 (redução do ar sobre a peça ≥ 30%): {np.median(red):.1f}% → {ok(np.median(red) >= 30)}.")
        print(f"- H-F4 (segmento ≤ peça em ≥ 75%): {int((fo <= 1e-9).sum())}/{len(fo)} = {100 * (fo <= 1e-9).mean():.0f}% → {ok((fo <= 1e-9).mean() >= 0.75)}.")
        print(f"- H-F6 (descritiva; violações de Π no nível de peça): {sum(x['p']['violacoes_pi'] for x in VP)} → {'dentro' if sum(x['p']['violacoes_pi'] for x in VP) == 0 else 'fora'}.")
    if V1:
        print(f"- H-F5 (descritiva; t = 1 s: tempo total em [−0,3%; +0,3%]): {np.median(f1):+.3f}% → {'dentro' if -0.3 <= np.median(f1) <= 0.3 else 'fora'}.")


if __name__ == "__main__":
    main()
