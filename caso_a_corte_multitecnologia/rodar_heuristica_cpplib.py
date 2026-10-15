"""
rodar_heuristica_cpplib.py
===========================
Primeiro teste do pipeline GEOMÉTRICO da heurística LCPP (não mais o modo
abstrato PCGTSP já testado com MASTRI/PCGLNS) nas instâncias REAIS do
CPPLib (Petunin et al., 2020 -- ver instances/cpplib/README.md e
dxf_parser.py). É o teste direto da hipótese H2 do plano de
desenvolvimento: o diferencial QuadTree/LCA da heurística em aninhamento
geométrico de verdade (furo dentro de peça), não apenas em abstrações
PCGTSP.

Reaproveita `src_base/heuristic_core.py` (cópia intocada do LCPP-main --
ver docs/00_log_cronologico.md e README deste projeto para a convenção)
via `run_heuristic(layout, config)`, chamado DUAS VEZES por instância:

  - modo "original" : enforce_precedence=False -- comportamento PADRÃO da
    heurística (mesmo default usado no LCPP-main, `_ORIGINAL_CFG` de
    pcgtsp_comparison/run_comparison.py). Documentado no próprio
    heuristic_core.py como NÃO garantindo Π formalmente.
  - modo "com_pi"   : enforce_precedence=True -- traversal corrigido
    (Seção 11 do plano de pesquisa do LCPP-main), estratégia
    "sequential" (default de precedence_strategy).

Para cada modo, verifica se o caminho de corte gerado respeita a
precedência Π inferida geometricamente (`hc._detectar_precedencia`,
contenção via `Polygon.covers`) -- mesma lógica de verificação
(`_find_polygon_owner` / `check_our_precedence_violations`) já usada em
pcgtsp_comparison/run_comparison.py do LCPP-main, reproduzida aqui (não
importável diretamente: vive num script do LCPP-main, não em src_base/).

IMPORTANTE (ver dxf_parser.py para o detalhe completo): cada instância
CPPLib tem ~50% das entidades .dxf excluídas do parsing (segmentos
degenerados de 2 vértices, achado de 29/08/2026, decisão de escopo
registrada mas não resolvida com a literatura) -- as colunas
n_dxf_entities/n_pieces_used/n_entities_excluded no CSV de saída deixam
isso visível por instância.

Uso:
    python3 rodar_heuristica_cpplib.py <time_limit_seg_por_modo> <saida.csv> [--limit N] [--categoria all]

    --limit N        roda so' as primeiras N instancias (smoke test rapido)
    --categoria all  roda as 148 instancias (4 categorias), nao so' as 85
                     "com precedencia" (default)
"""
from __future__ import annotations

import csv
import statistics
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "src_base"))

import heuristic_core as hc  # noqa: E402
from dxf_parser import load_all_cpplib, CATEGORIA_COM_PRECEDENCIA  # noqa: E402

_CFG_BASE = {
    "root_strategy": "nearest",
    "child_order": "num_filhos",
    "mst_strategy": "standard",
    "vertex_strategy": "nearest",
}


# ---------------------------------------------------------------------------
# Verificacao de violacoes de Pi -- reproduzido de
# pcgtsp_comparison/run_comparison.py (LCPP-main), ver docstring do modulo.
# ---------------------------------------------------------------------------

def _find_polygon_owner(seg, positions) -> Optional[int]:
    def key(a, b):
        a = tuple(round(v, 6) for v in a)
        b = tuple(round(v, 6) for v in b)
        return (min(a, b), max(a, b))
    k = key(seg.coords[0], seg.coords[1])
    for idx, pol in enumerate(positions):
        coords = list(pol.exterior.coords)
        for i in range(len(coords) - 1):
            if key(coords[i], coords[i + 1]) == k:
                return idx
    return None


def check_precedence_violations(caminho, positions, precedence_pairs) -> Tuple[int, int]:
    """(n_pares_checados, n_violacoes). Segmentos de comprimento ~0 sao
    ignorados (ruido de ponto flutuante em cantos que se tocam -- ver nota
    completa em run_comparison.py, funcao check_our_precedence_violations)."""
    primeiro, ultimo = {}, {}
    for pos_idx, (seg, tag) in enumerate(caminho):
        if tag != "c":
            continue
        if seg.length < 1e-6:
            continue
        owner = _find_polygon_owner(seg, positions)
        if owner is not None:
            primeiro.setdefault(owner, pos_idx)
            ultimo[owner] = pos_idx
    violacoes = 0
    checados = 0
    for furo_idx, pai_idx in precedence_pairs:
        if furo_idx not in ultimo or pai_idx not in primeiro:
            continue
        checados += 1
        if ultimo[furo_idx] >= primeiro[pai_idx]:
            violacoes += 1
    return checados, violacoes


# ---------------------------------------------------------------------------
# Uma instancia
# ---------------------------------------------------------------------------

def compare_one(name: str, polys: List, stats: Dict, time_limit: float) -> Dict:
    result = {
        "instance": name,
        "n_dxf_entities": stats["n_dxf_entities"],
        "n_pieces_used": stats["n_pieces_used"],
        "n_entities_excluded": stats["n_entities_excluded"],
    }
    if len(polys) < 2:
        result["skipped"] = "menos de 2 pecas validas apos parsing"
        return result

    try:
        positions = hc.clusterizar_quadtree(
            hc.resolver_intersecoes(hc.tratar_furos(list(polys)))
        )
        prec_pairs = hc._detectar_precedencia(positions)
    except Exception as ex:
        result["skipped"] = f"falha no preprocessamento: {type(ex).__name__}: {ex}"
        return result

    result["n_groups_pos_quadtree"] = len(positions)
    result["n_precedence_pairs"] = len(prec_pairs)

    for label, extra_cfg in (("original", {}), ("com_pi", {"enforce_precedence": True})):
        cfg = {**_CFG_BASE, "time_limit": time_limit, **extra_cfg}
        t0 = time.time()
        try:
            res = hc.run_heuristic(list(polys), cfg)
            wall = time.time() - t0
            checados, viol = check_precedence_violations(res["caminho"], positions, prec_pairs)
            result[f"{label}_ok"] = True
            result[f"{label}_fo"] = round(res["fo_total"], 4)
            result[f"{label}_time_s"] = round(wall, 3)
            result[f"{label}_timeout"] = res["timeout"]
            result[f"{label}_prec_checked"] = checados
            result[f"{label}_prec_violations"] = viol
        except Exception as ex:
            result[f"{label}_ok"] = False
            result[f"{label}_error"] = f"{type(ex).__name__}: {ex}"

    if result.get("original_ok") and result.get("com_pi_ok") and result["original_fo"] > 0:
        result["gap_pct_pi_vs_original"] = round(
            100 * (result["com_pi_fo"] - result["original_fo"]) / result["original_fo"], 4
        )
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3:
        print("Uso: python3 rodar_heuristica_cpplib.py <time_limit_seg_por_modo> <saida.csv> [--limit N] [--categoria all]")
        sys.exit(1)
    time_limit = float(sys.argv[1])
    out_csv = Path(sys.argv[2])
    args = sys.argv[3:]
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
    categoria = None if ("--categoria" in args and args[args.index("--categoria") + 1] == "all") else CATEGORIA_COM_PRECEDENCIA

    root = _HERE / "instances" / "cpplib"
    instances = load_all_cpplib(root, category_dirname=categoria)
    if limit:
        instances = instances[:limit]
    print(f"Carregadas {len(instances)} instancias (categoria={categoria or 'TODAS'}, time_limit={time_limit}s/modo).")

    rows = []
    t_batch0 = time.time()
    for i, (name, polys, stats) in enumerate(instances, 1):
        print(f"[{i}/{len(instances)}] {name} ...", end=" ", flush=True)
        row = compare_one(name, polys, stats, time_limit)
        rows.append(row)
        if row.get("original_ok") and row.get("com_pi_ok"):
            print(f"ok (fo_orig={row['original_fo']:.1f} fo_pi={row['com_pi_fo']:.1f} "
                  f"viol_orig={row['original_prec_violations']}/{row['original_prec_checked']} "
                  f"viol_pi={row['com_pi_prec_violations']}/{row['com_pi_prec_checked']})")
        else:
            print(f"FALHOU: {row}")
    print(f"\nTempo total do lote: {time.time() - t_batch0:.1f}s")

    fieldnames = ["instance"] + sorted({k for r in rows for k in r.keys()} - {"instance"})
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"CSV salvo em {out_csv}")

    # ---- resumo agregado ----
    ok_rows = [r for r in rows if r.get("original_ok") and r.get("com_pi_ok")]
    skipped_rows = [r for r in rows if "skipped" in r]
    crash_rows = [r for r in rows if r not in ok_rows and r not in skipped_rows]

    print(f"\n=== RESUMO ({len(ok_rows)}/{len(rows)} instancias OK em ambos os modos) ===")
    print(f"Puladas (pre-processamento/poucas pecas): {len(skipped_rows)}")
    print(f"Falhas em run_heuristic: {len(crash_rows)}")

    if ok_rows:
        tot_pairs_orig = sum(r["original_prec_checked"] for r in ok_rows)
        tot_viol_orig = sum(r["original_prec_violations"] for r in ok_rows)
        tot_pairs_pi = sum(r["com_pi_prec_checked"] for r in ok_rows)
        tot_viol_pi = sum(r["com_pi_prec_violations"] for r in ok_rows)
        print(f"Violacoes Pi (original): {tot_viol_orig}/{tot_pairs_orig}")
        print(f"Violacoes Pi (com_pi):   {tot_viol_pi}/{tot_pairs_pi}")

        n_timeout_orig = sum(1 for r in ok_rows if r["original_timeout"])
        n_timeout_pi = sum(1 for r in ok_rows if r["com_pi_timeout"])
        print(f"Timeouts (original): {n_timeout_orig}  Timeouts (com_pi): {n_timeout_pi}")

        gaps = [r["gap_pct_pi_vs_original"] for r in ok_rows if "gap_pct_pi_vs_original" in r]
        if gaps:
            print(f"Gap FO (com_pi vs original): media={statistics.mean(gaps):.3f}%  mediana={statistics.median(gaps):.3f}%")
            n_pior = sum(1 for g in gaps if g > 1e-9)
            n_igual = sum(1 for g in gaps if abs(g) <= 1e-9)
            n_melhor = sum(1 for g in gaps if g < -1e-9)
            print(f"com_pi pior em {n_pior}, igual em {n_igual}, melhor em {n_melhor} (de {len(gaps)})")
            try:
                from scipy.stats import wilcoxon
                orig_fos = [r["original_fo"] for r in ok_rows if "gap_pct_pi_vs_original" in r]
                pi_fos = [r["com_pi_fo"] for r in ok_rows if "gap_pct_pi_vs_original" in r]
                stat, p = wilcoxon(pi_fos, orig_fos)
                print(f"Wilcoxon (com_pi vs original): stat={stat:.2f} p={p:.4e}")
            except Exception as ex:
                print(f"Wilcoxon nao calculado: {ex}")

        tot_entities = sum(r["n_dxf_entities"] for r in ok_rows)
        tot_used = sum(r["n_pieces_used"] for r in ok_rows)
        tot_excl = sum(r["n_entities_excluded"] for r in ok_rows)
        print(f"\nEntidades DXF (instancias OK): {tot_entities}  usadas: {tot_used}  "
              f"excluidas: {tot_excl} ({100*tot_excl/tot_entities:.1f}%)")

    if crash_rows:
        print("\nInstancias com falha em run_heuristic:")
        for r in crash_rows:
            print(f"  {r['instance']}: {r.get('original_error') or r.get('com_pi_error')}")
    if skipped_rows:
        print("\nInstancias puladas:")
        for r in skipped_rows:
            print(f"  {r['instance']}: {r['skipped']}")


if __name__ == "__main__":
    main()
