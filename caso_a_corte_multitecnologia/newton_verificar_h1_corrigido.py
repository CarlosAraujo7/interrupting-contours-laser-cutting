"""
newton_verificar_h1_corrigido.py  --  verificacao CORRIGIDA da previsao estrutural H-N1 (docs/52, desvio D5; 19/11/2026)
=========================================================================================================================
O `verificar` congelado de `newton_exato_tc.py` exigiu R_j estritamente decrescente em TODAS as entradas da trilha, inclusive a ultima (a de economia nula). A Proposicao 3 so afirma isso para os iterados com
S(t_j) > 0: no ultimo passo (S = 0) o MILP pode devolver o proprio plano anterior, empatado com o plano de contorno em t_c, e R fica igual. Este script confere o que a proposicao afirma: t estritamente crescente em
toda a trilha; R estritamente decrescente entre os iterados com S > 0 (a partida inclusa); no maximo R_k - n + 1 MILPs novos. NAO altera o codigo congelado nem os dados. Uso: python newton_verificar_h1_corrigido.py
"""
import glob
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
TOL = 1e-7
ok = True
for f in sorted(glob.glob(os.path.join(AQUI, "newton_resultados", "*.json"))):
    r = json.load(open(f))
    tr = r["trilha"]
    ts = [x["t"] for x in tr]
    pos = [x for x in tr if x.get("origem") == "partida" or (x.get("S") is not None and x["S"] > TOL * (r["P0"] + x["t"] * r["n"]))]
    Rs = [x["R"] for x in pos]
    novos = sum(1 for x in tr if "M" in x)
    probs = []
    if not all(b > a for a, b in zip(ts, ts[1:])):
        probs.append("t nao cresce estritamente")
    if not all(b < a for a, b in zip(Rs, Rs[1:])):
        probs.append("R nao decresce entre os iterados com S > 0")
    if novos > r["partida"][1] - r["n"] + 1:
        probs.append("mais MILPs que R_k - n + 1")
    ok &= not probs
    print(f"  {r['instancia']:22s} {r['status']:10s} R dos iterados com S > 0: {Rs}  | MILPs novos {novos} (limite {r['partida'][1] - r['n'] + 1}) | " + ("; ".join(probs) if probs else "H-N1 OK"))
print("H-N1 CORRIGIDA: " + ("OK" if ok else "COM PROBLEMAS"))
sys.exit(0 if ok else 1)
