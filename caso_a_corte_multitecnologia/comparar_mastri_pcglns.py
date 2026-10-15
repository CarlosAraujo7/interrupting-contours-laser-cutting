"""
comparar_mastri_pcglns.py
==========================
Primeira comparacao real de dois metodos no Caso A (modo abstrato): roda o
MASTRI (mastri.py, deste projeto) e o PCGLNS (Kudryavtsev & Khachay,
external_tools/pcglns/ do LCPP-main -- ver docs/00_log_cronologico.md,
entrada de 29/08/2026) nas mesmas 48 instancias de
instances/ensigndaniels_cpp/, e registra FO, violacoes de Pi e tempo de cada
um num CSV comparativo.

PCGLNS e' invocado via subprocess (Julia 1.6 -- a versao default do
instalador, 1.12, trava com GC error neste codigo, ver
external_tools/README.md do LCPP-main), seguindo o MESMO padrao ponte
Python->Julia que pcgtsp_comparison/run_comparison.py ja usa no projeto
original (e que o proprio codigo do BnC de Khachay et al. usa: nao
reimplementar o solver, so' fazer a ponte e ler a saida como texto).

Nao ha conversao de unidades aqui (ao contrario de run_comparison.py, que
faz FO_pcglns = (tour_cost/SCALE)/v_air + cut_time_fixed): essa formula e'
especifica do modo GEOMETRICO do LCPP (escala Chebyshev + velocidade de ar +
tempo de corte fixo). Aqui as instancias .pcglns ja trazem a matriz de
distancia em unidades inteiras diretas (sem conversao previa via
converter.py), e mastri.py::resolver_mastri calcula FO somando essa MESMA
matriz diretamente -- ambos FO_mastri e Tour Cost do PCGLNS estao portanto
na mesma unidade, comparaveis sem fator de escala.

Uso:
    python3 comparar_mastri_pcglns.py <pasta_com_pcglns> <max_time_pcglns_seg> <saida.csv> [--append]
"""
from __future__ import annotations

import csv
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mastri import resolver_mastri  # noqa: E402

JULIA_BIN = "/root/.juliaup/bin/julia"
PCGLNS_DIR = Path("/tmp/pcglns_tool")
PCGLNS_SCRIPT = "runPCGLNS.jl"
TMP_OUT = Path("/tmp/pcglns_run_out")
TMP_OUT.mkdir(exist_ok=True)


def run_pcglns(instance_path: Path, max_time: float, mode: str = "default") -> Dict:
    out_path = TMP_OUT / f"{instance_path.stem}.tour"
    t0 = time.time()
    try:
        proc = subprocess.run(
            [JULIA_BIN, "+1.6", "--check-bounds=no", PCGLNS_SCRIPT,
             str(instance_path.resolve()), f"-mode={mode}",
             f"-max_time={int(max_time)}", "-verbose=0",
             f"-output={out_path.resolve()}"],
            capture_output=True, text=True, timeout=max_time + 60,
            cwd=str(PCGLNS_DIR),
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "subprocess timeout"}
    elapsed = time.time() - t0

    if not out_path.exists():
        return {"ok": False, "error": f"sem arquivo de saida (rc={proc.returncode}, "
                                       f"stderr={proc.stderr[-300:]})"}

    text = out_path.read_text(encoding="latin-1")
    m_cost = re.search(r"Tour Cost\s*:\s*([\-\d.]+)", text)
    m_tour = re.search(r"Tour\s*:\s*\[([^\]]+)\]", text)
    m_time = re.search(r"Solver Time\s*:\s*([\d.]+)", text)
    if not m_cost or not m_tour:
        return {"ok": False, "error": f"nao conseguiu parsear saida: {text[:300]!r}"}

    tour = [int(x.strip()) for x in m_tour.group(1).split(",")]
    return {
        "ok": True,
        "tour_cost": float(m_cost.group(1)),
        "tour": tour,
        "solver_time_s": float(m_time.group(1)) if m_time else elapsed,
        "wall_time_s": round(elapsed, 3),
    }


def check_pcglns_precedence_violations(pcglns_path: Path, tour: List[int]) -> Tuple[int, int]:
    """Mesma logica de pcgtsp_comparison/run_comparison.py::
    check_pcglns_precedence_violations do LCPP-main: le GTSP_SET_SECTION +
    GTSP_SET_ORDERING do .pcglns e verifica se o tour devolvido respeita a
    ordem de GRUPO exigida."""
    text = pcglns_path.read_text(encoding="latin-1")
    lines = text.split("\n")
    city_group: Dict[int, int] = {}
    prec: List[Tuple[int, int]] = []
    state = None
    for line in lines:
        s = line.strip()
        if s.startswith("GTSP_SET_SECTION"):
            state = "sets"; continue
        if s.startswith("GTSP_SET_ORDERING"):
            state = "order"; continue
        if s.startswith("START_GROUP_SECTION") or s.startswith("EOF"):
            state = None; continue
        if state == "sets" and s:
            nums = [int(x) for x in s.split()]
            grp = nums[0]
            for c in nums[1:]:
                if c == -1:
                    break
                city_group[c] = grp
        elif state == "order" and s:
            nums = [int(x) for x in s.split()]
            pred = nums[0]
            for suc in nums[1:]:
                if suc == -1:
                    break
                prec.append((pred, suc))
    group_pos: Dict[int, int] = {}
    for pos, city in enumerate(tour):
        if city in city_group:
            group_pos[city_group[city]] = pos
    violacoes = 0
    for pred, suc in prec:
        if pred in group_pos and suc in group_pos and group_pos[pred] > group_pos[suc]:
            violacoes += 1
    return len(prec), violacoes


def compare_one(instance_path: Path, max_time_pcglns: float) -> Dict:
    name = instance_path.name
    row: Dict = {"instance": name}

    mastri = resolver_mastri(instance_path)
    row.update({
        "n_grupos": mastri["n_grupos"],
        "n_pares": mastri["n_pares"],
        "mastri_fo": round(mastri["fo"], 2),
        "mastri_viol": mastri["violacoes"],
        "mastri_tempo_s": round(mastri["tempo_s"], 4),
    })

    pc = run_pcglns(instance_path, max_time_pcglns)
    if not pc["ok"]:
        row.update({"pcglns_ok": False, "pcglns_error": pc.get("error")})
        return row

    n_prec, n_viol = check_pcglns_precedence_violations(instance_path, pc["tour"])
    gap_pct = (
        round(100.0 * (mastri["fo"] - pc["tour_cost"]) / pc["tour_cost"], 2)
        if pc["tour_cost"] else None
    )
    row.update({
        "pcglns_ok": True,
        "pcglns_fo": pc["tour_cost"],
        "pcglns_solver_time_s": pc["solver_time_s"],
        "pcglns_wall_time_s": pc["wall_time_s"],
        "pcglns_pares_checados": n_prec,
        "pcglns_viol": n_viol,
        "gap_pct_mastri_vs_pcglns": gap_pct,
    })
    return row


def main():
    folder = Path(sys.argv[1])
    max_time = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
    out_csv = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("comparacao_mastri_pcglns.csv")
    append = "--append" in sys.argv

    files = sorted(folder.glob("*.pcglns"))
    print(f"{len(files)} instancias em {folder}, orcamento PCGLNS={max_time}s cada, "
          f"saida={out_csv} (append={append})")

    fieldnames = ["instance", "n_grupos", "n_pares", "mastri_fo", "mastri_viol",
                  "mastri_tempo_s", "pcglns_ok", "pcglns_fo", "pcglns_solver_time_s",
                  "pcglns_wall_time_s", "pcglns_pares_checados", "pcglns_viol",
                  "gap_pct_mastri_vs_pcglns", "pcglns_error"]

    mode = "a" if append and out_csv.exists() else "w"
    with open(out_csv, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if mode == "w":
            writer.writeheader()
        for i, fp in enumerate(files, 1):
            t0 = time.time()
            try:
                row = compare_one(fp, max_time)
            except Exception as e:
                row = {"instance": fp.name, "pcglns_ok": False, "pcglns_error": f"EXCEPTION: {e}"}
            writer.writerow(row)
            f.flush()
            print(f"[{i}/{len(files)}] {fp.name}: {row.get('mastri_fo')=} "
                  f"{row.get('pcglns_fo')=} {row.get('gap_pct_mastri_vs_pcglns')=} "
                  f"({time.time()-t0:.1f}s)", flush=True)

    print(f"\nResultados salvos em {out_csv}")


if __name__ == "__main__":
    main()
