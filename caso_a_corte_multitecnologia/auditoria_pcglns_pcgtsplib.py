"""
auditoria_pcglns_pcgtsplib.py  --  AUDITORIA DO PCGLNS (docs/AUDITORIA_BASELINES.md; crítica B1 do docs/12): o PCGLNS upstream que usamos reproduz os resultados do próprio PCGLNS
nas instâncias de referência do PCGTSP?
=====================================================================================================================================================================
Instâncias: Ekstedt & Salman (as do artigo de Salman et al., 2020, adaptação de SOPLIB ao PCGTSP; "PCGTSPLIB"), obtidas do repositório público `ukoloff/PCGTSP-BnB`
(pasta `Salman/input`; SEM licença declarada: usadas só para auditoria, NÃO redistribuídas; ver `ferramentas/PCGTSPLIB_ukoloff/FONTE.md`). Esse repositório também guarda a saída
do PCGLNS (`Salman/heuristic`, semente 123, limite 3600 s) para cada instância.
Para cada instância: (i) roda o PCGLNS upstream (`ferramentas/PCGLNS_upstream`, Julia 1.12, `--threads=1,0`) com `-max_time=T` e sementes 123, 0, 1; (ii) lê o custo e a viabilidade do
"Tour Summary"; (iii) compara com o custo da saída guardada; (iv) quando a DP exata (`ea0_otimo_dp.resolver_dp`) cabe no teto de estados, compara também com o ÓTIMO.
Honestidade: o que se confronta é a saída do PCGLNS dos mantenedores do repositório (mesmo solver), NÃO as tabelas dos artigos (inacessíveis aqui).
Uso: python auditoria_pcglns_pcgtsplib.py rodar [--tempo 120] [--workers 4]   |   python auditoria_pcglns_pcgtsplib.py resumo > RESULTADOS_AUDITORIA_PCGLNS.md
"""
import os
import re
import sys
import json
import time
import subprocess
from concurrent.futures import ProcessPoolExecutor

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
DADOS = os.path.join(RAIZ, "ferramentas", "PCGTSPLIB_ukoloff")
PCGLNS_DIR = os.path.join(RAIZ, "ferramentas", "PCGLNS_upstream")
OUT = os.path.join(AQUI, "auditoria_pcglns_resultados")
SEMENTES = (123, 0, 1)


FILTRO = None                                  # lista de nomes (--instancias a,b,c); None = todas


def instancias():
    todas = sorted(f[:-len(".pcglns")] for f in os.listdir(os.path.join(DADOS, "input")) if f.endswith(".pcglns"))
    return [n for n in todas if FILTRO is None or n in FILTRO]


def custo_guardado(nome):
    txt = open(os.path.join(DADOS, "heuristic", f"{nome}.pcglns.result.txt"), encoding="latin-1").read()
    m = re.search(r"Cost\s*:\s*(\d+)", txt[txt.index("Tour Summary"):])
    return int(m.group(1))


def _job(a):
    nome, semente, tempo = a
    f = os.path.join(OUT, f"{nome}_T{tempo}_s{semente}.json")
    if os.path.exists(f):
        return nome, semente, "pulado"
    arq = os.path.join(DADOS, "input", f"{nome}.pcglns")
    t0 = time.time()
    try:
        p = subprocess.run(["julia", "--threads=1,0", "runPCGLNS.jl", arq, "-mode=default", f"-max_time={tempo}", "-verbose=3", f"-seed={semente}"],
                           cwd=PCGLNS_DIR, capture_output=True, text=True, errors="replace", timeout=tempo + 300)
        txt = p.stdout
    except subprocess.TimeoutExpired:
        txt = ""
    r = {"instancia": nome, "semente": semente, "tempo_limite_s": tempo, "tempo_parede_s": time.time() - t0}
    i = txt.rfind("Tour Summary")
    if i >= 0:
        s = txt[i:]
        r["custo"] = int(re.search(r"Cost\s*:\s*(\d+)", s).group(1))
        r["viavel"] = "true" in re.search(r"Tour is Feasible\?\s*:\s*(\w+)", s).group(1).lower()
        r["timeout_solver"] = "true" in re.search(r"Solver Timeout\?\s*:\s*(\w+)", s).group(1).lower()
        m = re.search(r"Tour Ordering\s*:\s*\[([^\]]*)\]", s)
        r["tour"] = [int(x) for x in m.group(1).split(",")] if m else None
    else:
        r["erro"] = (txt + "")[-300:]
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f + ".tmp", "w"))
    os.replace(f + ".tmp", f)
    return nome, semente, f"custo={r.get('custo')} viavel={r.get('viavel')} em {r['tempo_parede_s']:.0f}s"


def ler_instancia(nome):
    """.pcglns -> dict no formato de ea0_lib.montar_instancia (cidades [(x, y, grupo, peca, vertice)], D, pares) para a DP exata."""
    linhas = open(os.path.join(DADOS, "input", f"{nome}.pcglns"), encoding="latin-1").read().split("\n")
    n = int(next(l for l in linhas if l.startswith("DIMENSION")).split(":")[1])
    i = next(k for k, l in enumerate(linhas) if l.startswith("EDGE_WEIGHT_SECTION")) + 1
    D = np.array([[int(x) for x in linhas[i + r].split()] for r in range(n)], dtype=np.int64)
    j = next(k for k, l in enumerate(linhas) if l.startswith("GTSP_SET_SECTION")) + 1
    grupo = {}
    while not linhas[j].startswith("GTSP_SET_ORDERING") and not linhas[j].startswith("START_GROUP"):
        t = [int(x) for x in linhas[j].split()]
        for v in t[1:-1]:
            grupo[v] = t[0]
        j += 1
    pares = []
    if linhas[j].startswith("GTSP_SET_ORDERING"):
        j += 1
        while not linhas[j].startswith("START_GROUP"):
            t = [int(x) for x in linhas[j].split()]
            pares += [(t[0], s) for s in t[1:-1]]
            j += 1
    cid = [(0.0, 0.0, grupo[v], 0, 0) for v in range(1, n + 1)]
    return {"cidades": cid, "D": D, "pares": pares}


def otimo_dp(nome, teto):
    import ea0_otimo_dp as dp
    inst = ler_instancia(nome)
    r, est = dp.resolver_dp(inst, teto)
    if r is None:
        return None, est
    custo, tour = r
    return custo, est


def carregar():
    d = {}
    for f in sorted(os.listdir(OUT)) if os.path.isdir(OUT) else []:
        if f.endswith(".json"):
            r = json.load(open(os.path.join(OUT, f)))
            if "custo" in r:
                d.setdefault(r["instancia"], []).append(r)
    return d


def resumo(tempo, teto_dp):
    d = carregar()
    L = [f"# Auditoria do PCGLNS nas instâncias de Ekstedt & Salman (PCGTSPLIB) — T = {tempo} s, sementes {SEMENTES}", "",
         "Custo do PCGLNS upstream (nosso) × custo da saída do PCGLNS guardada no repositório `ukoloff/PCGTSP-BnB` (semente 123, limite 3600 s) × ótimo exato (DP; só onde cabe em "
         f"{teto_dp} estados). **O que se confronta é a saída do PCGLNS dos mantenedores do repositório (mesmo solver), não as tabelas dos artigos.**", "",
         "| instância | guardado | nosso s123 | nosso melhor (3 sem.) | nosso pior | ótimo (DP) | viável | s123 = guardado | melhor ≤ guardado |", "|---|---:|---:|---:|---:|---:|:--:|:--:|:--:|"]
    iguais = melhores = pior_que = total = viol = 0
    estrito = igual_melhor = n_opt = n_opt_ok = 0
    max_pior = 0.0
    for nome in instancias():
        rs = [r for r in d.get(nome, []) if r["tempo_limite_s"] == tempo]
        if not rs:
            continue
        g = custo_guardado(nome)
        c = {r["semente"]: r["custo"] for r in rs}
        best, worst = min(c.values()), max(c.values())
        s123 = c.get(123)
        opt, est = otimo_dp(nome, teto_dp)
        total += 1
        viavel = all(r["viavel"] for r in rs)
        viol += 0 if viavel else 1
        iguais += 1 if s123 == g else 0
        melhores += 1 if best <= g else 0
        pior_que += 1 if best > g else 0
        estrito += 1 if best < g else 0
        igual_melhor += 1 if best == g else 0
        max_pior = max(max_pior, 100 * (best / g - 1))
        if opt is not None:
            n_opt += 1
            n_opt_ok += 1 if best == opt else 0
        L.append(f"| {nome} | {g} | {s123} | {best} | {worst} | {opt if opt is not None else '--'} | {'sim' if viavel else 'NÃO'} | {'sim' if s123 == g else 'não'} | {'sim' if best <= g else 'NÃO'} |")
    L += ["", f"Instâncias: {total}. Semente 123 igual ao custo guardado em {iguais}; nosso melhor de 3 sementes ≤ guardado em {melhores}; pior que o guardado em {pior_que}; soluções inviáveis: {viol}."]
    json.dump({"n": total, "s123_igual": iguais, "melhor_menor_ou_igual": melhores, "melhor_estritamente_menor": estrito, "melhor_igual": igual_melhor, "melhor_pior": pior_que,
               "max_pior_pct": max_pior, "inviaveis": viol, "n_otimo_dp": n_opt, "n_otimo_atingido": n_opt_ok, "tempo_s": tempo, "teto_dp": teto_dp},
              open(os.path.join(AQUI, f"auditoria_pcglns_resumo_T{tempo}.json"), "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    tempo = int(sys.argv[sys.argv.index("--tempo") + 1]) if "--tempo" in sys.argv else 120
    if "--instancias" in sys.argv:
        FILTRO = sys.argv[sys.argv.index("--instancias") + 1].split(",")
    if modo == "resumo":
        teto = int(sys.argv[sys.argv.index("--teto") + 1]) if "--teto" in sys.argv else 60000
        resumo(tempo, teto)
        sys.exit(0)
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    jobs = [(n, s, tempo) for n in instancias() for s in SEMENTES]
    print(f"[{time.strftime('%H:%M:%S')}] auditoria PCGLNS: {len(instancias())} instâncias x {len(SEMENTES)} sementes = {len(jobs)} tarefas, {workers} processos, T = {tempo} s", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, s, msg in ex.map(_job, jobs, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n} s{s}: {msg}", flush=True)
    print("AUDITORIA CONCLUIDA", flush=True)
