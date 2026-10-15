"""
ea0_sensibilidade_pcglns.py  --  SENSIBILIDADE AO ORCAMENTO NAS LAYOUTS GRANDES (critica B3 do docs/12; achado da auditoria do PCGLNS em 10/10/2026)
====================================================================================================================================================
A auditoria do PCGLNS nas instancias grandes da PCGTSPLIB mostrou que, a partir de ~250 clusters, o PCGLNS NAO converge em 300 s (a saida dos mantenedores usou 3600 s e ficou 4-7% melhor).
No E-A0 (T = 30 s) o PCGLNS parou por tempo em poucas layouts grandes (tempo de parede medio >= 40 s, i.e. 30 s + ~12 s de partida do Julia). Aqui: rodar SO o PCGLNS com T maior
(padrao 120 s, 3 sementes) nas layouts em que o tempo medio de parede do E-A0 foi >= `--corte` s (padrao 25 s), e comparar com o PCGLNS a 30 s do E-A0 (10 sementes) e
com as demais metodologias do E-A0 (FO media de 10 sementes, T = 30 s). Os JSON novos entram em `ea0_resultados/` com `T<tempo>` no nome e NAO alteram a analise pre-registrada
(`analise_estatistica_ea0.py` filtra T = 30).
Uso: python ea0_sensibilidade_pcglns.py rodar [--tempo 120] [--corte 25] [--workers 5]   |   python ea0_sensibilidade_pcglns.py resumo [--tempo 120] [--corte 25] > RESULTADOS_EA0_SENSIBILIDADE_PCGLNS.md
"""
import os
import sys
import json
import time
import glob
import statistics
import collections
from concurrent.futures import ProcessPoolExecutor

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import rodar_ea0 as ea0                                       # noqa: E402

PASTA = os.path.join(AQUI, "ea0_resultados")
METODOS_30 = ["pcglns", "vns_pi", "heur_pi", "heur_ls", "heur_vns"]


def layouts_grandes(corte):
    d = collections.defaultdict(list)
    for f in glob.glob(os.path.join(PASTA, "ea0_*_pcglns_T30_s*.json")):
        r = json.load(open(f))
        d[r["instancia"]].append(r["tempo_parede_s"])
    return sorted(n for n, v in d.items() if statistics.mean(v) >= corte)


def media_fo(nome, metodo, tempo, sementes):
    v = []
    for s in sementes:
        f = os.path.join(PASTA, f"ea0_{nome}_{metodo}_T{tempo}_s{s}.json")
        if os.path.exists(f):
            r = json.load(open(f))
            if "fo" in r:
                v.append(r["fo_reavaliada"] if metodo.startswith("heur") and "fo_reavaliada" in r else r["fo"])
    return (statistics.mean(v), len(v)) if v else (None, 0)


def resumo(tempo, corte):
    nomes = layouts_grandes(corte)
    print(f"# E-A0 — sensibilidade do PCGLNS ao orçamento nas {len(nomes)} layouts em que o PCGLNS a 30 s levou ≥ {corte} s de parede\n")
    print(f"FO média (s; menor é melhor). PCGLNS a 30 s: 10 sementes (E-A0); PCGLNS a {tempo} s: 3 sementes (esta rodada). 'G30' = gap da construção (heurística com Π) sobre o PCGLNS a 30 s; "
          f"'G{tempo}' = sobre o PCGLNS a {tempo} s; 'ganho' = quanto o PCGLNS melhora com o orçamento maior.\n")
    print(f"| layout | peças | PCGLNS 30 s | PCGLNS {tempo} s | ganho | VNS-Π 30 s | constr. | G30 | G{tempo} | VNS-Π vs PCGLNS {tempo} s |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    ganhos, g30, glong, vns_long = [], [], [], []
    for n in nomes:
        p30, _ = media_fo(n, "pcglns", 30, range(10))
        pl, k = media_fo(n, "pcglns", tempo, range(3))
        v30, _ = media_fo(n, "vns_pi", 30, range(10))
        hc, _ = media_fo(n, "heur_pi", 30, [0])
        npec = json.load(open(os.path.join(PASTA, f"ea0_{n}_pcglns_T30_s0.json")))["n_pecas"]
        if pl is None or p30 is None or hc is None:
            continue
        ganhos.append(100 * (1 - pl / p30))
        g30.append(100 * (hc / p30 - 1))
        glong.append(100 * (hc / pl - 1))
        vns_long.append(100 * (v30 / pl - 1))
        print(f"| {n} | {npec} | {p30:.2f} | {pl:.2f} (n={k}) | {ganhos[-1]:+.2f}% | {v30:.2f} | {hc:.2f} | {g30[-1]:+.2f}% | {glong[-1]:+.2f}% | {vns_long[-1]:+.2f}% |")
    if ganhos:
        print(f"\nMediana do ganho do PCGLNS com {tempo} s: {statistics.median(ganhos):+.2f}% (máx. {max(ganhos):+.2f}%). Gap mediano da construção: {statistics.median(g30):+.2f}% sobre o PCGLNS a 30 s "
              f"e {statistics.median(glong):+.2f}% sobre o PCGLNS a {tempo} s. VNS-Π (30 s) sobre o PCGLNS a {tempo} s: mediana {statistics.median(vns_long):+.2f}% (máx. {max(vns_long):+.2f}%).")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    arg = lambda f, t, d: t(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    tempo, corte, workers = arg("--tempo", int, 120), arg("--corte", float, 25.0), arg("--workers", int, 5)
    if modo == "resumo":
        resumo(tempo, corte)
        sys.exit(0)
    nomes = layouts_grandes(corte)
    jobs = [(n, "pcglns", s, tempo) for n in nomes for s in range(3)]
    print(f"[{time.strftime('%H:%M:%S')}] sensibilidade PCGLNS: {len(nomes)} layouts ({', '.join(nomes)}) x 3 sementes, T = {tempo} s, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, m, s, msg in ex.map(ea0._job, jobs, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n} {m} s{s}: {msg}", flush=True)
    print("SENSIBILIDADE CONCLUIDA", flush=True)
