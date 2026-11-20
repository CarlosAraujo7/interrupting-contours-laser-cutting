"""
verificar_estudos_ef_corrigido.py  --  VERIFICACAO ESTRUTURAL CORRIGIDA dos estudos E e F (docs/59_desvios.md, D9; 20/11/2026)
=============================================================================================================================
O `verificar` congelado de `grupo_comum.py` e de `confirmacao_novos.py` tem dois alarmes FALSOS (o codigo e mais estrito que as proposicoes; o codigo congelado NAO foi alterado):
  (a) E-S2/F-S2 comparava a economia com `t_cert - t` tambem para t > t_cert (limite negativo): a Proposicao diz `S(t) <= max(0, t_cert - t)` (S = 0 a partir de t_cert);
  (b) E-S4/F-S4 exigia R estritamente decrescente em TODAS as entradas da trilha de Newton, mas a proposicao so garante a reducao estrita de R entre os iterados com S > 0; o ULTIMO passo (S = 0)
      pode devolver um plano com o mesmo R do anterior (o plano anterior e otimo em sua propria raiz).
Aqui as mesmas conferencias sao feitas na forma que as proposicoes enunciam. Tambem confere os hashes do manifesto. Uso: python verificar_estudos_ef_corrigido.py [E|F|ambos]   (codigo de saida 0 se tudo passa)
"""
import glob
import hashlib
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
VC, VA = 100.0 / 6.0, 400.0
TOL = 1e-7


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def trilha_ok(r, n_base, c_base, probs, rotulo):
    """Newton: entre os iterados com S > 0 (a partida e os passos com economia positiva) t cresce e R decresce estritamente; o ultimo (S ~ 0) e o ponto de equilibrio e
    t_c e a raiz da reta do ultimo iterado com S > 0; no maximo R_0 - n_base + 1 MILPs; t_c <= t_cert."""
    tr = r.get("trilha") or []
    if r["status"] != "exato" or not tr:
        return
    pos = [x for x in tr if "R" in x and (x.get("origem") == "partida" or x.get("S", 1) > TOL * (r["P0"] if "P0" in r else r["TP0"]))]
    ts = [x["t"] for x in pos]
    Rs = [x["R"] for x in pos]
    if not all(b > a for a, b in zip(ts, ts[1:])):
        probs.append(f"{rotulo}: t nao cresce entre os iterados com S > 0")
    if not all(b < a for a, b in zip(Rs, Rs[1:])):
        probs.append(f"{rotulo}: R nao decresce estritamente entre os iterados com S > 0")
    if len([x for x in tr if "M" in x]) > tr[0]["R"] - n_base + 1:
        probs.append(f"{rotulo}: mais MILPs que R_0 - n_base + 1")
    ult = pos[-1]
    raiz = (c_base - ult["c"]) / (ult["R"] - n_base)
    if abs(raiz - r["t_c"]) > 1e-9:
        probs.append(f"{rotulo}: t_c nao e a raiz da reta do ultimo iterado com S > 0")
    if r["t_c"] > r["t_cert"] * (1 + 1e-6):
        probs.append(f"{rotulo}: t_c > t_cert")


def grade_ok(pts_S, probs, rotulo):
    pts = sorted(pts_S)
    for (t1, s1), (t2, s2), (t3, s3) in zip(pts, pts[1:], pts[2:]):
        if not (s2 <= s1 + 1e-9 and s3 <= s2 + 1e-9):
            probs.append(f"{rotulo}: S nao decrescente na grade")
        lamb = (t2 - t1) / (t3 - t1)
        if s2 > (1 - lamb) * s1 + lamb * s3 + 1e-7:
            probs.append(f"{rotulo}: S nao convexa na grade")


def verificar_E():
    probs_tot = []
    for f in sorted(glob.glob(os.path.join(AQUI, "grupo_comum_resultados", "*.json"))):
        r = json.load(open(f))
        probs = []
        n, Rm, L = r["n"], r["R_min"], r["L"]
        if abs(r["TP0"] - (r["L_P"] / VC + r["AP"] / VA)) > 1e-6 * r["TP0"]:
            probs.append("E-S5: T_P(0) guardado != L_P/v_c + A_P*/v_a")
        if "As" in r:
            if abs(r["As"] - r["As_guardado"]) > 1e-6 * max(1.0, r["As"]):
                probs.append("E-S5: A* do MILP em t = 0 difere do RPP guardado")
            AG, As, cG = r["AG"], r["As"], r["cG"]
            if AG < As - 1e-9:
                probs.append("E-S1: A_G* < A*")
            for k, p in r["pontos"].items():
                if "M" not in p:
                    continue
                t = p["t"]
                lb = L / VC + min(AG / VA + t * Rm, As / VA + t * (Rm + 1))
                if p["M"] < lb * (1 - 1e-9) - 1e-9:
                    probs.append(f"E-S1: M(t={t}) abaixo do limite inferior (Prop. 2')")
                if p["M"] > cG + t * Rm + 1e-9:
                    probs.append(f"E-S2: M(t={t}) acima de T_G(t)")
                if p["S_G"] > max(0.0, r["t_cert"] - t) + 1e-6:
                    probs.append(f"E-S2: economia sobre G em t={t} maior que max(0, t_cert^G - t)")
                if abs(p["S_total"] - (p["S_cc"] + p["S_G"])) > 1e-9:
                    probs.append(f"E-S6: a decomposicao nao fecha em t={t}")
            grade_ok([(p["t"], p["S_G"]) for p in r["pontos"].values() if "S_G" in p], probs, "E-S3")
            trilha_ok(r, Rm, r["cG"], probs, "E-S4")
        print(f"  E {r['instancia']}: {r['status']}" + (f" t_c^G={r['t_c']:.5f}" if r.get("t_c") is not None else "") + (" | " + "; ".join(probs) if probs else " | estrutura OK"))
        probs_tot += probs
    return probs_tot


def verificar_F():
    probs_tot = []
    for f in sorted(glob.glob(os.path.join(AQUI, "confirmacao_novos_resultados", "*.json"))):
        r = json.load(open(f))
        probs = []
        if "As" in r:
            n, P0, L, AP, As = r["n"], r["P0"], r["L"], r["AP"], r["As"]
            for k, p in r["pontos"].items():
                if "M" not in p:
                    continue
                t = p["t"]
                lb = L / VC + min(AP / VA + t * n, As / VA + t * (n + 1))
                if p["M"] < lb * (1 - 1e-9) - 1e-9:
                    probs.append(f"F-S1: M(t={t}) abaixo do limite inferior")
                if p["M"] > P0 + t * n + 1e-9:
                    probs.append(f"F-S1: M(t={t}) acima do plano de contorno")
                if p["S"] > max(0.0, r["t_cert"] - t) + 1e-6:
                    probs.append(f"F-S2: economia em t={t} maior que max(0, t_cert - t)")
            grade_ok([(p["t"], p["S"]) for p in r["pontos"].values() if "S" in p], probs, "F-S3")
            trilha_ok(r, r["n"], r["P0"], probs, "F-S4")
        print(f"  F {r['instancia']}: {r['status']}" + (f" t_c={r['t_c']:.5f}" if r.get("t_c") is not None else "") + (" | " + "; ".join(probs) if probs else " | estrutura OK"))
        probs_tot += probs
    return probs_tot


if __name__ == "__main__":
    quais = sys.argv[1] if len(sys.argv) > 1 else "ambos"
    man = json.load(open(os.path.join(AQUI, "confirmacao_estudos_manifesto.json")))
    ok = True
    for a, h in man["arquivos"].items():
        igual = sha(os.path.join(AQUI, a)) == h
        ok &= igual
        print(("OK       " if igual else "ALTERADO ") + a)
    probs = []
    if quais in ("E", "ambos"):
        probs += verificar_E()
    if quais in ("F", "ambos"):
        probs += verificar_F()
    ok &= not probs
    print("VERIFICACAO CORRIGIDA " + ("OK" if ok else "COM PROBLEMAS"))
    sys.exit(0 if ok else 1)
