"""
comparar_3_metodos.py
======================
AVISO (01/10/2026): o "TSH+VNS" de `tsh_vns.py` NAO e o metodo de Zhang et al. (2024) -- e um hibrido proprio
(construcao do MASTRI + VNS Reverse/Shift); ver o aviso no docstring de `tsh_vns.py`. Os resultados desta
comparacao valem para esse hibrido, nao para o artigo.

Roda o TSH+VNS (tsh_vns.py) com N sementes independentes nas 48 instancias
de `instances/ensigndaniels_cpp/`, e junta o resultado (melhor FO entre as
sementes, por instancia) com os resultados JA CORRIGIDOS de MASTRI e PCGLNS
em `comparacao_mastri_pcglns.csv` (ver mastri.py, correcao de 29/08/2026
noite, e docs/00_log_cronologico.md) -- NAO re-roda PCGLNS (precisa de
Julia, ~20s/instancia): os numeros do PCGLNS ja gravados nesse CSV nao
dependem da correcao (ela afeta so' `escolher_cidades_e_fo`, usada por
MASTRI e TSH+VNS, nao pelo solver PCGLNS externo).

Convencao de relato: reporta o MELHOR FO entre as `--seeds` sementes por
instancia (convencao padrao pra metaheuristicas estocasticas), mas tambem
guarda media e desvio padrao entre sementes pra transparencia sobre a
variancia.

HISTORICO: rodado primeiro em modo exploratorio (3 sementes, 29/08/2026
noite) -- resultados arquivados em `*_exploratorio_3seeds.csv` para
referencia. Rodado depois com o protocolo estatistico completo do projeto
(minimo 10 sementes, ver docs/06_plano_desenvolvimento.md Secao 1.6,
29/08/2026 noite, ~1186s/20min) -- ESTE e' o resultado atual/canonico em
`comparacao_3_metodos.csv`/`resultado_tsh_vns.csv` (sem sufixo). As
conclusoes nao mudaram entre as duas rodadas (mesmo ranking de custo,
significancia estatistica igual ou mais forte com 10 sementes) -- a rodada
de 3 sementes ja era representativa, mas 10 e' o que o protocolo exige
antes de tratar os numeros como finais de artigo. `--seeds 10` e' o default
agora; use um valor menor so' para testes rapidos/iteracao de codigo.

Uso: python3 comparar_3_metodos.py [--seeds N] [--tempo-limite S]
     [--pasta instances/ensigndaniels_cpp] [--referencia comparacao_mastri_pcglns.csv]
"""
from __future__ import annotations

import argparse
import csv
import statistics
import time
from collections import defaultdict
from pathlib import Path

from scipy import stats

from tsh_vns import resolver_tsh_vns

FIELDNAMES = [
    "instance", "n_grupos", "n_pares",
    "tshvns_fo_melhor", "tshvns_fo_media", "tshvns_fo_std", "tshvns_viol_melhor",
    "mastri_fo", "mastri_viol",
    "pcglns_fo", "pcglns_viol",
    "gap_pct_tshvns_vs_mastri", "gap_pct_tshvns_vs_pcglns",
]


def rodar_tsh_vns_lote(pasta: Path, seeds: int, tempo_limite: float) -> dict:
    """Roda resolver_tsh_vns em todas as .pcglns de `pasta`, `seeds` vezes
    cada (sementes 0..seeds-1). Retorna dict nome_instancia -> lista de
    resultados (1 por semente)."""
    alvos = sorted(pasta.rglob("*.pcglns"))
    por_instancia: dict = defaultdict(list)
    t0 = time.time()
    for i, fp in enumerate(alvos, 1):
        for s in range(seeds):
            r = resolver_tsh_vns(fp, seed=s, tempo_limite_s=tempo_limite)
            por_instancia[r["name"]].append(r)
        print(f"[{i}/{len(alvos)}] {fp.name}: "
              f"FOs={[round(x['fo'], 1) for x in por_instancia[fp.stem]]} "
              f"t_acumulado={time.time() - t0:.1f}s", flush=True)
    print(f"TSH+VNS: {len(alvos)} instancias x {seeds} sementes = "
          f"{len(alvos) * seeds} execucoes em {time.time() - t0:.1f}s")
    return por_instancia


def montar_comparacao(por_instancia: dict, referencia_csv: Path) -> list:
    with open(referencia_csv, newline="", encoding="utf-8") as f:
        ref = {r["instance"].replace(".pcglns", ""): r for r in csv.DictReader(f)}

    linhas = []
    for nome, execs in por_instancia.items():
        r = ref.get(nome)
        if r is None:
            print(f"AVISO: sem referencia MASTRI/PCGLNS para {nome}, pulando.")
            continue
        fos = [e["fo"] for e in execs]
        viols = [e["violacoes"] for e in execs]
        idx_melhor = fos.index(min(fos))
        linha = {
            "instance": nome,
            "n_grupos": r["n_grupos"],
            "n_pares": r["n_pares"],
            "tshvns_fo_melhor": fos[idx_melhor],
            "tshvns_fo_media": round(statistics.mean(fos), 2),
            "tshvns_fo_std": round(statistics.pstdev(fos), 2) if len(fos) > 1 else 0.0,
            "tshvns_viol_melhor": viols[idx_melhor],
            "mastri_fo": float(r["mastri_fo"]),
            "mastri_viol": int(r["mastri_viol"]),
            "pcglns_fo": float(r["pcglns_fo"]) if r["pcglns_ok"] == "True" else None,
            "pcglns_viol": int(r["pcglns_viol"]) if r["pcglns_ok"] == "True" else None,
        }
        linha["gap_pct_tshvns_vs_mastri"] = round(
            100.0 * (linha["tshvns_fo_melhor"] - linha["mastri_fo"]) / linha["mastri_fo"], 2
        ) if linha["mastri_fo"] else None
        linha["gap_pct_tshvns_vs_pcglns"] = round(
            100.0 * (linha["tshvns_fo_melhor"] - linha["pcglns_fo"]) / linha["pcglns_fo"], 2
        ) if linha["pcglns_fo"] else None
        linhas.append(linha)
    return linhas


def imprimir_resumo(linhas: list) -> None:
    tshvns_fo = [l["tshvns_fo_melhor"] for l in linhas]
    mastri_fo = [l["mastri_fo"] for l in linhas]
    pcglns_fo = [l["pcglns_fo"] for l in linhas if l["pcglns_fo"] is not None]
    n = len(linhas)

    n_vs_mastri = sum(1 for l in linhas if l["tshvns_fo_melhor"] < l["mastri_fo"])
    n_vs_pcglns = sum(1 for l in linhas if l["pcglns_fo"] and l["tshvns_fo_melhor"] < l["pcglns_fo"])
    gaps_m = [l["gap_pct_tshvns_vs_mastri"] for l in linhas if l["gap_pct_tshvns_vs_mastri"] is not None]
    gaps_p = [l["gap_pct_tshvns_vs_pcglns"] for l in linhas if l["gap_pct_tshvns_vs_pcglns"] is not None]

    stat_m, p_m = stats.wilcoxon(tshvns_fo, mastri_fo)
    stat_p, p_p = stats.wilcoxon(tshvns_fo, pcglns_fo)

    viol_tshvns = sum(l["tshvns_viol_melhor"] for l in linhas)
    viol_mastri = sum(l["mastri_viol"] for l in linhas)
    viol_pcglns = sum(l["pcglns_viol"] for l in linhas if l["pcglns_viol"] is not None)
    n_pares_total = sum(int(l["n_pares"]) for l in linhas)

    print(f"\n=== TSH+VNS (melhor de N sementes) vs MASTRI (corrigido, {n} instancias) ===")
    print(f"TSH+VNS mais barato em: {n_vs_mastri}/{n}")
    print(f"gap medio: {statistics.mean(gaps_m):+.2f}%  mediana: {statistics.median(gaps_m):+.2f}%")
    print(f"Wilcoxon pareado: stat={stat_m:.4g}  p={p_m:.4g}")

    print(f"\n=== TSH+VNS (melhor de N sementes) vs PCGLNS ===")
    print(f"TSH+VNS mais barato em: {n_vs_pcglns}/{n}")
    print(f"gap medio: {statistics.mean(gaps_p):+.2f}%  mediana: {statistics.median(gaps_p):+.2f}%")
    print(f"Wilcoxon pareado: stat={stat_p:.4g}  p={p_p:.4g}")

    print(f"\n=== Feasibility (violacoes de Pi -- nenhum dos 3 metodos modela precedencia) ===")
    print(f"MASTRI:   {viol_mastri}/{n_pares_total} pares violados")
    print(f"TSH+VNS:  {viol_tshvns}/{n_pares_total} pares violados")
    print(f"PCGLNS:   {viol_pcglns}/{n_pares_total} pares violados")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=10, help="sementes independentes por instancia (default 10, o minimo do protocolo estatistico do projeto; reduzir so' para testes rapidos)")
    ap.add_argument("--tempo-limite", type=float, default=3.0, help="segundos de VNS por componente conexo por semente")
    ap.add_argument("--pasta", type=Path, default=Path("instances/ensigndaniels_cpp"))
    ap.add_argument("--referencia", type=Path, default=Path("comparacao_mastri_pcglns.csv"))
    ap.add_argument("--saida-bruta", type=Path, default=Path("resultado_tsh_vns.csv"))
    ap.add_argument("--saida-comparacao", type=Path, default=Path("comparacao_3_metodos.csv"))
    args = ap.parse_args()

    por_instancia = rodar_tsh_vns_lote(args.pasta, args.seeds, args.tempo_limite)

    with open(args.saida_bruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name", "seed", "fo", "n_grupos", "n_pares", "violacoes", "tempo_s", "vns_iteracoes"])
        w.writeheader()
        for execs in por_instancia.values():
            for e in execs:
                w.writerow({k: e[k] for k in w.fieldnames})
    print(f"Resultado bruto (todas as sementes) salvo em {args.saida_bruta}")

    linhas = montar_comparacao(por_instancia, args.referencia)
    with open(args.saida_comparacao, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        for l in linhas:
            w.writerow({k: l.get(k, "") for k in FIELDNAMES})
    print(f"Comparacao de 3 metodos salva em {args.saida_comparacao}")

    imprimir_resumo(linhas)


if __name__ == "__main__":
    main()
