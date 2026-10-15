"""
medir_vies_simetrizacao.py
===========================
Quantifica (em vez de supor) o quanto o custo SIMETRIZADO `min(d(a,b), d(b,a))` -- usado por `mastri.escolher_cidades_e_fo`
(herdado do LCPP-main) e por `vns_zhang.py` -- subestima o custo DIRECIONAL que o PCGLNS otimiza, nas 48 instancias
`.pcglns`. Para o tour (deterministico) do MASTRI, calcula:
  fo_sim      -- o FO que o MASTRI reporta (ciclo fechado, simetrizado);
  fo_dir_fin  -- FO usando d(a,b) quando o arco a->b e finito e, so quando e PROIBIDO, d(b,a) (a leitura mais favoravel
                 ao MASTRI que respeita a direcao onde ela existe);
  n_arcos_proibidos -- quantos arcos do ciclo sao proibidos no sentido percorrido (o tour viola a matriz, nao so Pi);
  n_arcos_assim -- quantos arcos tem d(a,b) != d(b,a) (ambos finitos).
Saida: `vies_simetrizacao_mastri.csv` e um resumo. Roda em segundos. Nao altera nada do projeto.
"""
import csv, sys, warnings, statistics
from pathlib import Path

warnings.filterwarnings("ignore")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from mastri import resolver_mastri, parse_pcglns, _dist

INF = float("inf")


def main():
    alvos = sorted((AQUI / "instances" / "ensigndaniels_cpp").rglob("*.pcglns"))
    ref = {r["instance"].replace(".pcglns", ""): r for r in csv.DictReader(open(AQUI / "comparacao_mastri_pcglns.csv", encoding="utf-8"))}
    linhas = []
    for fp in alvos:
        parsed = parse_pcglns(fp)
        m = parsed["matrix"]
        r = resolver_mastri(fp)
        S = r["tour"]
        n = len(S)
        sim = dirf = 0.0
        proib = assim = 0
        for k in range(n):
            a, b = S[k], S[(k + 1) % n]
            f, g = _dist(m, a, b), _dist(m, b, a)
            sim += min(f, g)
            if f == INF:
                proib += 1
                dirf += g
            else:
                dirf += f
                if g != INF and abs(f - g) > 1e-9:
                    assim += 1
        pc = ref.get(fp.stem, {}).get("pcglns_fo")
        pcf = float(pc) if pc not in (None, "", "None") else None
        linhas.append({"instance": fp.stem, "n_grupos": r["n_grupos"], "mastri_fo_sim": round(sim, 2),
                       "mastri_fo_dir_fin": round(dirf, 2), "dif_pct": round(100 * (dirf / sim - 1), 3) if sim else 0.0,
                       "arcos_proibidos_no_tour": proib, "arcos_assimetricos_no_tour": assim, "pcglns_fo": pcf,
                       "gap_pcglns_sim_pct": round(100 * (sim / pcf - 1), 2) if pcf else "",
                       "gap_pcglns_dir_pct": round(100 * (dirf / pcf - 1), 2) if pcf else ""})
    with open(AQUI / "vies_simetrizacao_mastri.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    com = [l for l in linhas if l["arcos_assimetricos_no_tour"] > 0 or l["dif_pct"] > 0]
    print(f"{len(linhas)} instancias; com diferenca sim x dir-finito: {len(com)}")
    print(f"gap medio MASTRI vs PCGLNS: simetrizado {statistics.mean(float(l['gap_pcglns_sim_pct']) for l in linhas if l['gap_pcglns_sim_pct'] != ''):+.2f}% | "
          f"direcional-onde-finito {statistics.mean(float(l['gap_pcglns_dir_pct']) for l in linhas if l['gap_pcglns_dir_pct'] != ''):+.2f}%")
    print(f"arcos proibidos usados pelo tour do MASTRI (total nas 48): {sum(l['arcos_proibidos_no_tour'] for l in linhas)} de {sum(l['n_grupos'] for l in linhas)}")
    for l in sorted(com, key=lambda x: -x["dif_pct"]):
        print(f"  {l['instance']:<14} sim={l['mastri_fo_sim']:>9.1f}  dir={l['mastri_fo_dir_fin']:>9.1f}  (+{l['dif_pct']:.2f}%)  assim={l['arcos_assimetricos_no_tour']}/{l['n_grupos']}")


if __name__ == "__main__":
    main()
