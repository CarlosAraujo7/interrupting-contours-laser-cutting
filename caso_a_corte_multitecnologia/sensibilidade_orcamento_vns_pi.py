"""
sensibilidade_orcamento_vns_pi.py
==================================
O VNS-Pi (`vns_zhang_pi.py`) e escrito em Python puro e, com 10 s por execucao, faz poucas dezenas de iteracoes (o artigo
original usa ate 1200 s / 10.000 iteracoes sem melhora). Este script mede QUANTO o orcamento importa: roda um subconjunto
de instancias com um tempo MAIOR (padrao 120 s, 3 sementes) e compara com (a) o resultado de 10 s do `resultado_vns_zhang_pi.csv`
e (b) o FO do PCGLNS em `comparacao_mastri_pcglns.csv`. Idempotente (pula (instancia, semente, tempo) ja gravadas).

Uso:  python sensibilidade_orcamento_vns_pi.py [--tempo 120] [--seeds 3] [--workers 3] [inst ...]
Saidas: `sensibilidade_orcamento_vns_pi.csv` (bruto) e resumo impresso (markdown).
"""
import csv, os, sys, warnings, statistics
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

warnings.filterwarnings("ignore")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import vns_zhang_pi

SAIDA = AQUI / "sensibilidade_orcamento_vns_pi.csv"
PADRAO = ["P5XJ_9-n-m", "p7xj_5-m", "pl-75-m", "ph-110-m", "pm-47-m", "e1x_7_m"]
CAMPOS = ["instance", "seed", "tempo_limite_s", "fo", "violacoes", "iteracoes"]


def _job(a):
    caminho, seed, tl = a
    r = vns_zhang_pi.resolver_vns_zhang_pi(caminho, seed=seed, tempo_limite_s=tl)
    return {"instance": r["name"], "seed": seed, "tempo_limite_s": tl, "fo": r["fo"], "violacoes": r["violacoes"],
            "iteracoes": r["vns_iteracoes"]}


def main():
    def _opt(f, tp, df):
        return tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else df
    tl, seeds, workers = _opt("--tempo", float, 120.0), _opt("--seeds", int, 3), _opt("--workers", int, 3)
    com_valor = {"--tempo", "--seeds", "--workers"}
    nomes = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] not in com_valor] or PADRAO
    todos = {f.stem: f for f in (AQUI / "instances" / "ensigndaniels_cpp").rglob("*.pcglns")}
    feitos = set()
    if SAIDA.exists():
        for r in csv.DictReader(open(SAIDA, encoding="utf-8")):
            feitos.add((r["instance"], int(r["seed"]), float(r["tempo_limite_s"])))
    jobs = [(str(todos[n]), s, tl) for n in nomes for s in range(seeds) if (n, s, tl) not in feitos]
    novo = not SAIDA.exists()
    if jobs:
        with open(SAIDA, "a", newline="", encoding="utf-8") as fh, ProcessPoolExecutor(max_workers=workers) as ex:
            w = csv.DictWriter(fh, fieldnames=CAMPOS)
            if novo:
                w.writeheader()
            for r in ex.map(_job, jobs, chunksize=1):
                w.writerow(r)
                fh.flush()
    # --- resumo
    bruto = list(csv.DictReader(open(SAIDA, encoding="utf-8")))
    curto = {}
    p10 = AQUI / "resultado_vns_zhang_pi.csv"
    if p10.exists():
        for r in csv.DictReader(open(p10, encoding="utf-8")):
            curto.setdefault(r["instance"], []).append(float(r["fo"]))
    pcg = {r["instance"].replace(".pcglns", ""): r for r in csv.DictReader(open(AQUI / "comparacao_mastri_pcglns.csv", encoding="utf-8"))}
    print(f"| instancia | VNS-Pi 10 s (melhor de 10) | VNS-Pi {tl:g} s (melhor de {seeds}) | media {tl:g} s | iteracoes ({tl:g} s) | PCGLNS | gap {tl:g} s vs PCGLNS |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for n in nomes:
        rs = [r for r in bruto if r["instance"] == n and float(r["tempo_limite_s"]) == tl]
        if not rs:
            continue
        fo = [float(r["fo"]) for r in rs]
        p = pcg.get(n, {}).get("pcglns_fo")
        pf = float(p) if p not in (None, "", "None") else None
        c10 = min(curto[n]) if n in curto else None
        print(f"| {n} | {c10:.0f} | {min(fo):.0f} | {statistics.mean(fo):.1f} | {statistics.mean(int(r['iteracoes']) for r in rs):.0f} | "
              f"{pf:.0f} | {100 * (min(fo) / pf - 1):+.2f}% |" if (c10 and pf) else f"| {n} | -- | {min(fo):.0f} | {statistics.mean(fo):.1f} | -- | -- | -- |")


if __name__ == "__main__":
    main()
