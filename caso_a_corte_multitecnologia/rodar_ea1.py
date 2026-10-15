"""
rodar_ea1.py  --  E-A1 NAO TRIVIAL (plano 07 §4.2, H-P1.2): a rota otima de um perfil de tecnologia perde quanto quando usada em outro, com tempo de voo TRAPEZOIDAL?
===================================================================================================================================================================
No nivel de peca, com velocidades constantes, o regret e ZERO por construcao (Proposicao 1 do manuscrito). Com aceleracao limitada o tempo de um movimento em vazio de comprimento d (Chebyshev, unidades do
desenho = mm, k = 1; docs/12 M1) e  tau(d) = d/v + v/a  se d >= v^2/a  e  2*sqrt(d/a)  caso contrario (perfil trapezoidal/triangular, como em Ganganath et al. 2016). Perfis (ordem de grandeza de folhas tecnicas,
docs/12 §9.1; NAO calibrados): LIN (convencao do LCPP: v = 400 mm/s, sem aceleracao), LASER (v = 1667 mm/s ~ 100 m/min, a = 10.000 mm/s^2), PLASMA (v = 423 mm/s ~ 1000 IPM, a = 760 mm/s^2 ~ 30 in/s^2),
PLASMA_A300 (mesma v, a = 300 mm/s^2; sensibilidade). Corte e perfuracao sao constantes por peca e saem da comparacao.
Para cada instancia (84 com >= 2 pecas), perfil P e semente s: PCGLNS com a matriz de custos tau_P (mesma conversao de `ea0_lib.montar_instancia`: mesma peca 0; arcos de precedencia proibidos), T segundos; a rota e avaliada
sob TODOS os perfis. Regret(A -> B) = T_B(melhor rota otimizada para A) / T_B(melhor rota otimizada para B) - 1; piso de ruido = variacao entre sementes no proprio perfil.
Uso: python rodar_ea1.py rodar [--tempo 10] [--sementes 3] [--workers 5]   (resultados em ea1_resultados/, idempotente)  |  python rodar_ea1.py resumo > RESULTADOS_EA1.md
"""
import os
import re
import sys
import json
import time
import tempfile
import subprocess
import statistics
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import ea0_lib as lib                          # noqa: E402
import rodar_ea0 as ea0                        # noqa: E402

OUT = os.path.join(AQUI, "ea1_resultados")
PCGLNS_DIR = ea0.PCGLNS_DIR
PERFIS = {"LIN": ("lin", 400.0, None), "LASER": ("trap", 1667.0, 10000.0), "PLASMA": ("trap", 423.0, 760.0), "PLASMA_A300": ("trap", 423.0, 300.0)}
ESC = 100000


def tau(d, perfil):
    tipo, v, a = perfil
    d = np.asarray(d, float)
    if tipo == "lin":
        return d / v
    dc = v * v / a
    return np.where(d >= dc, d / v + v / a, 2.0 * np.sqrt(np.maximum(d, 0.0) / a))


def matriz_perfil(inst, perfil):
    cid = inst["cidades"]
    xy = np.array([[c[0], c[1]] for c in cid], float)
    dist = np.abs(xy[:, None, :] - xy[None, :, :]).max(axis=2)
    D = np.rint(tau(dist, perfil) * ESC).astype(np.int64)
    grupo = np.array([c[2] for c in cid])
    D[grupo[:, None] == grupo[None, :]] = 0
    D[inst["D"] == -1] = -1                      # arcos de precedencia proibidos (mesma regra do E-A0)
    return D, dist


def custo_tour(tour, dist, perfil):
    idx = np.array(tour) - 1
    nxt = np.roll(idx, -1)
    return float(tau(dist[idx, nxt], perfil).sum())


def _job(a):
    nome, pnome, s, tempo = a
    f = os.path.join(OUT, f"ea1_{nome}_{pnome}_T{tempo}_s{s}.json")
    if os.path.exists(f):
        return nome, pnome, s, "pulado"
    polys = ea0._carregar(nome)
    if len(polys) < 2:
        return nome, pnome, s, "poucas pecas"
    t0 = time.time()
    inst = lib.montar_instancia(polys)
    D, dist = matriz_perfil(inst, PERFIS[pnome])
    inst2 = dict(inst)
    inst2["D"] = D
    tmp = tempfile.mkdtemp(prefix="ea1_")
    arq, saida = os.path.join(tmp, f"{nome}.pcglns"), os.path.join(tmp, "saida.tour")
    lib.escrever_pcglns(inst2, arq, nome)
    p = subprocess.run(["julia", "--threads=1,0", "runPCGLNS.jl", arq, "-mode=default", f"-max_time={tempo}", "-verbose=0", f"-output={saida}", f"-seed={s}"],
                       cwd=PCGLNS_DIR, capture_output=True, text=True, errors="replace")
    txt = open(saida, encoding="latin-1").read() if os.path.exists(saida) else ""
    m = re.search(r"Tour\s*:\s*\[([^\]]+)\]", txt)
    r = {"instancia": nome, "perfil": pnome, "semente": s, "tempo_limite_s": tempo, "n_pecas": len(polys)}
    if m:
        tour = [int(x) for x in m.group(1).split(",")]
        if tour[0] != 1:
            k = tour.index(1)
            tour = tour[k:] + tour[:k]
        r["violacoes"] = lib.violacoes(inst, tour)
        r["T"] = {q: custo_tour(tour, dist, pf) for q, pf in PERFIS.items()}
    else:
        r["erro"] = (p.stdout + p.stderr)[-300:]
    r["tempo_parede_s"] = time.time() - t0
    try:
        for x in os.listdir(tmp):
            os.remove(os.path.join(tmp, x))
        os.rmdir(tmp)
    except OSError:
        pass
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f + ".tmp", "w"))
    os.replace(f + ".tmp", f)
    return nome, pnome, s, f"T_proprio={r['T'][pnome]:.3f}s viol={r.get('violacoes')}" if "T" in r else "ERRO"


def carregar(tempo):
    dados = {}
    for f in sorted(os.listdir(OUT)) if os.path.isdir(OUT) else []:
        if f.endswith(f"_T{tempo}_s0.json") or f"_T{tempo}_s" in f:
            r = json.load(open(os.path.join(OUT, f)))
            if "T" in r:
                dados.setdefault(r["instancia"], {}).setdefault(r["perfil"], []).append(r)
    return dados


def resumo(tempo):
    dados = carregar(tempo)
    nomes = sorted(n for n, d in dados.items() if all(p in d and len(d[p]) >= 2 for p in PERFIS))
    pn = list(PERFIS)
    print(f"# E-A1 nao trivial -- regret entre perfis com tempo de voo trapezoidal ({len(nomes)} instancias, PCGLNS T = {tempo} s, sementes por perfil: ate {max(len(d[p]) for d in dados.values() for p in d)})\n")
    print("Perfis (ordem de grandeza de folhas tecnicas; k = 1 mm/unidade): " + "; ".join(f"{k}: " + ("v = %g mm/s, sem aceleracao" % v[1] if v[0] == "lin" else "v = %g mm/s, a = %g mm/s^2" % (v[1], v[2])) for k, v in PERFIS.items()) +
          ". Regret(A -> B) = T_B(melhor rota para A) / T_B(melhor rota para B) - 1 (%), por instancia; mediana [mediana, % de instancias com regret > 0,1% / > 1%].\n")
    melhor = {n: {p: min(dados[n][p], key=lambda r: r["T"][p]) for p in pn} for n in nomes}
    ruido = {p: [] for p in pn}
    for n in nomes:
        for p in pn:
            ts = sorted(r["T"][p] for r in dados[n][p])
            ruido[p].append(100 * (statistics.median(ts) / ts[0] - 1))
    print("| rota otimizada para \\ avaliada em | " + " | ".join(pn) + " |")
    print("|---|" + "---:|" * len(pn))
    for A in pn:
        cel = []
        for B in pn:
            reg = [100 * (melhor[n][A]["T"][B] / melhor[n][B]["T"][B] - 1) for n in nomes]
            cel.append("--" if A == B else f"{statistics.median(reg):+.3f}% [{100 * sum(1 for x in reg if x > 0.1) / len(reg):.0f}% / {100 * sum(1 for x in reg if x > 1) / len(reg):.0f}%]")
        print(f"| {A} | " + " | ".join(cel) + " |")
    print("\nPiso de ruido (variacao entre sementes no proprio perfil: mediana das sementes / melhor - 1): " + "; ".join(f"{p}: mediana {statistics.median(ruido[p]):.3f}%" for p in pn) + ".\n")
    maxs = {(A, B): max(100 * (melhor[n][A]["T"][B] / melhor[n][B]["T"][B] - 1) for n in nomes) for A in pn for B in pn if A != B}
    pior = max(maxs, key=maxs.get)
    print(f"Maior regret observado: {maxs[pior]:+.2f}% ({pior[0]} -> {pior[1]}).")
    viol = sum(r.get("violacoes", 0) for d in dados.values() for p in d.values() for r in p)
    print(f"Violacoes de Pi em todas as rotas: {viol}.")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    tempo = int(sys.argv[sys.argv.index("--tempo") + 1]) if "--tempo" in sys.argv else 10
    if modo == "resumo":
        resumo(tempo)
        sys.exit(0)
    nseeds = int(sys.argv[sys.argv.index("--sementes") + 1]) if "--sementes" in sys.argv else 3
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 5
    nomes = [n for n in sorted(ea0.listar()) if len(ea0._carregar(n)) >= 2]
    jobs = [(n, p, s, tempo) for n in nomes for p in PERFIS for s in range(nseeds)]
    print(f"[{time.strftime('%H:%M:%S')}] E-A1: {len(nomes)} instancias x {len(PERFIS)} perfis x {nseeds} sementes = {len(jobs)} tarefas, {workers} processos, T = {tempo} s", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, p, s, msg in ex.map(_job, jobs, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n} {p} s{s}: {msg}", flush=True)
    print("EA1 CONCLUIDO", flush=True)
