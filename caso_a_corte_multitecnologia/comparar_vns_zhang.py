"""
comparar_vns_zhang.py
======================
Roda o VNS FIEL de Zhang et al. (2024) (`vns_zhang.py`, reimplementacao independente de 02/10/2026) nas 48 instancias
de `instances/ensigndaniels_cpp/`, com N sementes (padrao 10), e compara com os resultados JA existentes de
MASTRI, PCGLNS e do hibrido proprio (construcao do MASTRI + VNS Reverse/Shift, ex-"TSH+VNS") em `comparacao_3_metodos.csv`.

LEITURA CORRETA DA COMPARACAO
  - O VNS de Zhang et al. NAO modela precedencia: sua ordem e "como esta"; as violacoes de Pi sao CONTADAS (coluna
    `vns_zhang_viol`). O PCGLNS respeita Pi (0 violacoes). Portanto um FO menor que o do PCGLNS com violacoes > 0
    NAO e "melhor": e um problema relaxado. Compare FO so entre metodos com o mesmo status de viabilidade, ou reporte ambos.
  - Orcamento: o artigo usa 1200 s / 10.000 iteracoes sem melhora; aqui `--tempo-limite` (padrao 10 s) por execucao
    (limite de tempo e o criterio efetivo na maioria das instancias). O PCGLNS do CSV de referencia foi rodado com o
    orcamento da rodada original (ver `comparar_mastri_pcglns.py`) -- o orcamento NAO esta igualado aqui.

Saidas (idempotente: pula as (instancia, semente) ja gravadas em `resultado_vns_zhang.csv`):
  resultado_vns_zhang.csv     -- uma linha por (instancia, semente)
  comparacao_vns_zhang.csv    -- uma linha por instancia: melhor/media/dp do VNS-Zhang, violacoes, e gaps vs MASTRI/PCGLNS/hibrido

VARIANTE `--pi` (02/10/2026): usa `vns_zhang_pi.py` (EXTENSAO nossa que respeita Pi; NAO e o metodo do artigo) em vez do
`vns_zhang.py` fiel. Saidas `resultado_vns_zhang_pi.csv` / `comparacao_vns_zhang_pi.csv`. Aqui a comparacao de FO com o
PCGLNS e justa quanto a viabilidade (0 violacoes nos dois); o orcamento continua nao igualado (ver acima).

Uso:  python comparar_vns_zhang.py [--pi] [--seeds 10] [--tempo-limite 10] [--workers 2]
"""
import csv, os, sys, time, statistics, warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

warnings.filterwarnings("ignore")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import vns_zhang
import vns_zhang_pi

PI = "--pi" in sys.argv
SUF = "_pi" if PI else ""
BRUTO = AQUI / f"resultado_vns_zhang{SUF}.csv"
COMP = AQUI / f"comparacao_vns_zhang{SUF}.csv"
REF = AQUI / "comparacao_3_metodos.csv"
REF_PCG = AQUI / "comparacao_mastri_pcglns.csv"   # tempo de solver do PCGLNS por instancia
CAMPOS = ["instance", "seed", "fo", "violacoes", "iteracoes", "tempo_s", "tempo_limite_s", "n_grupos", "n_pares"] + (["fo_direcional"] if PI else [])


def _job(a):
    caminho, seed, tl, pi = a
    r = (vns_zhang_pi.resolver_vns_zhang_pi if pi else vns_zhang.resolver_vns_zhang)(caminho, seed=seed, tempo_limite_s=tl)
    out = {"instance": r["name"], "seed": seed, "fo": r["fo"], "violacoes": r["violacoes"], "iteracoes": r["vns_iteracoes"],
           "tempo_s": round(r["tempo_s"], 3), "tempo_limite_s": tl, "n_grupos": r["n_grupos"], "n_pares": r["n_pares"]}
    if pi:
        out["fo_direcional"] = r["fo_direcional"]
    return out


def main():
    def _opt(f, tp, df):
        return tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else df
    seeds, tl, workers = _opt("--seeds", int, 10), _opt("--tempo-limite", float, 10.0), _opt("--workers", int, 2)
    alvos = sorted((AQUI / "instances" / "ensigndaniels_cpp").rglob("*.pcglns"))
    feitos = set()
    if BRUTO.exists():
        for r in csv.DictReader(open(BRUTO, encoding="utf-8")):
            feitos.add((r["instance"], int(r["seed"])))
    jobs = [(str(f), s, tl, PI) for f in alvos for s in range(seeds) if (f.stem, s) not in feitos]
    novo = not BRUTO.exists()
    if jobs:
        with open(BRUTO, "a", newline="", encoding="utf-8") as fh, ProcessPoolExecutor(max_workers=workers) as ex:
            w = csv.DictWriter(fh, fieldnames=CAMPOS)
            if novo:
                w.writeheader()
            for r in ex.map(_job, jobs, chunksize=1):
                w.writerow(r)
                fh.flush()
    # --- consolidacao
    por = {}
    for r in csv.DictReader(open(BRUTO, encoding="utf-8")):
        por.setdefault(r["instance"], []).append(r)
    ref = {r["instance"].replace(".pcglns", ""): r for r in csv.DictReader(open(REF, encoding="utf-8"))}
    linhas = []
    for nome in sorted(por):
        fos = [float(r["fo"]) for r in por[nome]]
        viol = [int(r["violacoes"]) for r in por[nome]]
        rf = ref.get(nome, {})
        pcg = float(rf["pcglns_fo"]) if rf.get("pcglns_fo") not in (None, "", "None") else None
        mas = float(rf["mastri_fo"]) if rf.get("mastri_fo") not in (None, "", "None") else None
        hib = float(rf["tshvns_fo_melhor"]) if rf.get("tshvns_fo_melhor") not in (None, "", "None") else None
        melhor = min(fos)
        g = lambda ref_: f"{100 * (melhor / ref_ - 1):+.2f}" if ref_ else ""
        linhas.append({"instance": nome, "n_grupos": por[nome][0]["n_grupos"], "n_pares": por[nome][0]["n_pares"],
                       "n_sementes": len(fos), "vns_zhang_fo_melhor": melhor, "vns_zhang_fo_media": round(statistics.mean(fos), 2),
                       "vns_zhang_fo_dp": round(statistics.pstdev(fos), 2) if len(fos) > 1 else 0.0,
                       "vns_zhang_viol_media": round(statistics.mean(viol), 2), "vns_zhang_viol_min": min(viol),
                       "pcglns_fo": pcg, "mastri_fo": mas, "hibrido_mastri_vns_fo_melhor": hib,
                       "gap_pct_vs_pcglns": g(pcg), "gap_pct_vs_mastri": g(mas), "gap_pct_vs_hibrido": g(hib)})
    with open(COMP, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    if PI:                                                   # verificacoes da variante viavel
        brutos = [r for rs in por.values() for r in rs]
        assert all(int(r["violacoes"]) == 0 for r in brutos), "VNS-Pi devolveu solucao com violacao de Pi"
        assert all(abs(float(r["fo_direcional"]) - float(r["fo"])) < 1e-6 for r in brutos), "fo direcional != fo simetrizado"
    gp = [float(l["gap_pct_vs_pcglns"]) for l in linhas if l["gap_pct_vs_pcglns"] != ""]
    gh = [float(l["gap_pct_vs_hibrido"]) for l in linhas if l["gap_pct_vs_hibrido"] != ""]
    rotulo = "VNS-Zhang-Pi (extensao)" if PI else "VNS-Zhang"
    print(f"{len(linhas)} instancias; {rotulo} (melhor de {seeds}, {tl:g}s): gap medio vs PCGLNS = {statistics.mean(gp):+.2f}% "
          f"(vence/empata em {sum(1 for x in gp if x <= 0)}/{len(gp)}; violacoes medias de Pi = {statistics.mean(float(l['vns_zhang_viol_media']) for l in linhas):.1f}); "
          f"gap medio vs hibrido antigo = {statistics.mean(gh):+.2f}%")


if __name__ == "__main__":
    main()
