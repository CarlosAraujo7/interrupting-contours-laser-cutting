"""
recalculo_independente_rq1_rq2.py  --  RECALCULO INDEPENDENTE dos numeros centrais do N1 (Tabelas 5 e 6), sem o gerador de tabelas  (19/11/2026)
==========================================================================================================================================
Refaz, so com os arquivos por instancia que o repositorio guarda, os numeros do RQ1 (Tabela 5: heuristica x PCGLNS de nivel de contorno nas 282 instancias,
sob o custo executavel e o formal) e do RQ2 (Tabela 6: distancia ao otimo exato nas instancias pequenas), e compara com o que o manuscrito diz.
Nao importa `manuscrito/gerar_tabelas_n1.py` nem nenhum modulo do projeto: serve para conferir o gerador por outro caminho.

Entradas (todas no repositorio): `resumos_heuristica_282.json` (custos por instancia da rota guardada da heuristica), `auditoria_lcpp1/honesta_282/*.json`
(custo do PCGLNS de nivel de contorno, com as pernas da origem), `rpp_lcpp1_resultados/*.json` (otimo exato de ar), `lcpp1_segmento_resultados/*.json` (arc-GTSP + PCGLNS).
Uso: python recalculo_independente_rq1_rq2.py     (codigo de saida 0 se tudo coincide com o manuscrito; 1 se algo diverge)
"""
import glob
import json
import os
import statistics as st
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
VC, VA = 100.0 / 6.0, 400.0                       # velocidades do benchmark (unidades de desenho por segundo)
ok = True


def confere(rotulo, obtido, esperado, tol):
    global ok
    bom = abs(obtido - esperado) <= tol
    ok = ok and bom
    print(f"  {'ok ' if bom else 'DIVERGE'} {rotulo:52s} obtido {obtido:+.4f} | manuscrito {esperado:+.4f}")


def main():
    R = json.load(open(os.path.join(AQUI, "resumos_heuristica_282.json")))
    H = os.path.join(AQUI, "auditoria_lcpp1", "honesta_282")
    print("== RQ1 (Tabela 5): 282 instancias, t = 0; diferenca relativa da heuristica ao PCGLNS de nivel de contorno ==")
    de, df, dl, dd = [], [], [], []
    for nome, r in sorted(R.items()):
        a = json.load(open(os.path.join(H, nome + ".json")))
        p = a["fo_pcglns_honesta"]
        de.append(r["poli"] / p - 1.0)
        df.append(r["H0.0"] / p - 1.0)
        dl.append(r["listada"] / p - 1.0)                              # custo listado pelo codigo da heuristica (como foi reportada)
        dd.append(r["listada"] / a["fo_pcglns_formula_deles"] - 1.0)   # idem, com o custo que o artigo irmao atribui ao PCGLNS (sem as pernas da origem)
    for rot, d, vit, med, media in (("listado", dl, 282, -0.825, -1.285), ("executavel", de, 253, -0.470, -0.929), ("formal", df, 277, -0.503, -1.012)):
        confere(f"{rot}: instancias em que a heuristica e menor", float(sum(1 for x in d if x < 0)), float(vit), 0)
        confere(f"{rot}: mediana (%)", 100 * st.median(d), med, 5e-4)
        confere(f"{rot}: media (%)", 100 * st.mean(d), media, 5e-4)
    confere("listado x PCGLNS pela formula do artigo irmao: instancias em que a heuristica e menor", float(sum(1 for x in dd if x < 0)), 279.0, 0)
    confere("listado x PCGLNS pela formula do artigo irmao: media (%)", 100 * st.mean(dd), -0.64, 5e-3)
    confere("saltos medianos entre segmentos que nao se unem", float(st.median([r["saltos"] for r in R.values()])), 29.0, 0)
    confere("executavel / listado - 1, mediana (%)", 100 * st.median([r["poli"] / r["listada"] - 1 for r in R.values()]), 0.36, 5e-3)
    confere("formal / executavel - 1, mediana (%)", 100 * st.median([r["H0.0"] / r["poli"] - 1 for r in R.values()]), -0.018, 5e-4)

    print("== RQ2 (Tabela 6): distancia ao otimo exato do problema sem precedencia (tempo de ar e tempo total) ==")
    L = []
    for f in sorted(glob.glob(os.path.join(AQUI, "rpp_lcpp1_resultados", "*.json"))):
        r = json.load(open(f))
        if not r["resolvida"]:
            continue
        n = r["instancia"]
        g = json.load(open(os.path.join(AQUI, "lcpp1_segmento_resultados", n + ".json")))["melhor"]
        p = json.load(open(os.path.join(H, n + ".json")))["fo_pcglns_honesta"]
        corte, ar_otimo = r["corte_comprimento"] / VC, r["ar_otimo"] / VA
        L.append({"hole": "_hole_" in n, "ar_opt": ar_otimo, "LB": corte + ar_otimo, "ar_h": R[n]["ar0"], "H": R[n]["H0.0"], "ar_g": g["ar"] / VA, "G": g["fo"], "ar_p": p - corte, "P": p})
    sem, com = [x for x in L if not x["hole"]], [x for x in L if x["hole"]]
    confere("instancias com otimo exato (de 46)", float(len(L)), 42.0, 0)
    confere("  das quais sem aninhamento (otimo)", float(len(sem)), 33.0, 0)
    confere("  das quais com furos (limite inferior)", float(len(com)), 9.0, 0)
    esperado = {  # (ar: mediana %, ar: maximo %, no otimo, total: mediana %) como na Tabela 6 do manuscrito
        ("sem", "ar_h"): (0.61, 84.6, 14, 0.003), ("sem", "ar_g"): (0.00, 24.9, 17, 0.000), ("sem", "ar_p"): (126.60, 2521.3, 0, 0.745),
        ("com", "ar_h"): (9.66, 44.8, 0, 0.128), ("com", "ar_g"): (12.34, 22.5, 1, 0.107), ("com", "ar_p"): (56.56, 158.7, 0, 0.726)}
    tot = {"ar_h": "H", "ar_g": "G", "ar_p": "P"}
    for rot, S in (("sem", sem), ("com", com)):
        for k in ("ar_h", "ar_g", "ar_p"):
            a = [100 * (x[k] / x["ar_opt"] - 1) for x in S if x["ar_opt"] > 1e-9]
            fo = [100 * (x[tot[k]] / x["LB"] - 1) for x in S]
            m, mx, no, tm = esperado[(rot, k)]
            nome = {"ar_h": "heuristica", "ar_g": "arc-GTSP + PCGLNS", "ar_p": "PCGLNS de contorno"}[k]
            confere(f"{rot} aninhamento, {nome}: ar, mediana (%)", st.median(a), m, 5e-3)
            confere(f"{rot} aninhamento, {nome}: ar, maximo (%)", max(a), mx, 5e-2)
            confere(f"{rot} aninhamento, {nome}: no otimo (gap <= 0,01%)", float(sum(1 for v in a if v <= 0.01)), float(no), 0)
            confere(f"{rot} aninhamento, {nome}: total, mediana (%)", st.median(fo), tm, 5e-4)
    print("\nRESULTADO:", "tudo coincide com o manuscrito" if ok else "HA DIVERGENCIA")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
