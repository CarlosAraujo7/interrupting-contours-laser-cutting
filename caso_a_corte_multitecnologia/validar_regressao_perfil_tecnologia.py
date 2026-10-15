"""
validar_regressao_perfil_tecnologia.py
========================================
Teste de regressao de ponta a ponta para a integracao de PerfilTecnologia em
heuristic_core.py/local_search_tree.py (ver docs/00_log_cronologico.md,
entrada de 30/08/2026, e a nota "v_cut/v_air/tempo_perfuracao" no docstring
de heuristic_core.py).

Isso e o teste que o docstring de perfil_tecnologia.py:validar_regressao()
ja anunciava como "pendente" (bloqueado por falta de dados de instancia) --
agora possivel com as instancias CPPLib reais.

Tres blocos de verificacao:

  TESTE A (regressao, instancias CPPLib reais, config simples)
    Confirma que run_heuristic(layout, config) SEM v_cut/v_air/tempo_perfuracao
    no config (usa os defaults de _DEFAULT_CONFIG) produz FO IDENTICA
    (delta < 1e-9) a passar esses tres campos explicitamente com os valores
    de LASER_ORIGINAL. E o teste central: garante que nenhum resultado do
    Caso A ja reportado muda de valor por causa desta integracao.

  TESTE B (cobertura de todos os pontos de chamada, layout sintetico)
    O mesmo teste de equivalencia (default vs LASER_ORIGINAL explicito),
    mas variando root_strategy/child_order/mst_strategy/vertex_strategy/
    enforce_precedence+precedence_strategy para forcar a execucao de CADA
    uma das 5 funcoes internas que receberam os novos parametros
    (construir_grafo_mst_edge_swap, enumerar_raiz, compute_child_permutations
    nos dois modos, enumerate_start_vertex, cortar_arvore_com_precedencia_2opt)
    -- nao so o caminho simples (que o Teste A ja cobre em escala real).
    Usa um layout SINTETICO pequeno (nao instancias CPPLib reais) de proposito:
    child_order="permutation"/root_strategy="enumerate" tem custo
    combinatorio (fatorial/quadratico no nº de filhos/nos) e time_limit=None
    roda ate o fim -- em uma instancia CPPLib real (30-250 contornos) isso
    poderia nunca terminar. Um layout de 4 poligonos elimina esse risco
    mantendo a mesma cobertura de codigo.

  TESTE C (sanidade -- confirma que os parametros TEM efeito, nao so que
    o default nao regrediu)
    No mesmo layout sintetico: (1) reduzir v_cut aumenta a FO; (2) aumentar
    tempo_perfuracao aumenta a FO exatamente em n_perfuracoes * delta_tempo,
    onde n_perfuracoes e contado independentemente a partir do caminho
    retornado (nao apenas assumido) -- confirma a formula "uma perfuracao
    por run contiguo maximal de tag='c'" descrita no docstring de calcular_fo.

Uso:
    python3 validar_regressao_perfil_tecnologia.py [--limit N]
    (--limit N controla so' o Teste A; default 20 instancias)
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "src_base"))

from shapely.geometry import Polygon  # noqa: E402

import heuristic_core as hc  # noqa: E402
from dxf_parser import load_all_cpplib, CATEGORIA_COM_PRECEDENCIA  # noqa: E402
from perfil_tecnologia import LASER_ORIGINAL  # noqa: E402

_TOL = 1e-9


def _cfg_laser_original(extra: dict) -> dict:
    return {
        **extra,
        "v_cut": LASER_ORIGINAL.v_cut,
        "v_air": LASER_ORIGINAL.v_air,
        "tempo_perfuracao": LASER_ORIGINAL.tempo_perfuracao,
    }


# ---------------------------------------------------------------------------
# TESTE A -- regressao em instancias CPPLib reais, config simples
# ---------------------------------------------------------------------------

def teste_a_regressao_cpplib(limit: int) -> bool:
    print("=" * 70)
    print("TESTE A -- regressao (default vs LASER_ORIGINAL explicito), CPPLib real")
    print("=" * 70)
    cfg_base = {
        "root_strategy": "nearest",
        "child_order": "num_filhos",
        "mst_strategy": "standard",
        "vertex_strategy": "nearest",
        "enforce_precedence": False,
    }
    root = _HERE / "instances" / "cpplib"
    instances = load_all_cpplib(root, category_dirname=CATEGORIA_COM_PRECEDENCIA)
    if limit:
        instances = instances[:limit]
    print(f"Testando {len(instances)} instancias...")

    n_ok, n_falhou = 0, 0
    max_delta = 0.0
    for name, polys, stats in instances:
        if len(polys) < 2:
            continue
        try:
            res_default = hc.run_heuristic(list(polys), dict(cfg_base))
            res_explicit = hc.run_heuristic(list(polys), _cfg_laser_original(cfg_base))
            delta = abs(res_default["fo_total"] - res_explicit["fo_total"])
            max_delta = max(max_delta, delta)
            if delta < _TOL:
                n_ok += 1
            else:
                n_falhou += 1
                print(f"  DIVERGIU {name}: default={res_default['fo_total']:.6f} "
                      f"explicito={res_explicit['fo_total']:.6f} delta={delta:.3e}")
        except Exception as ex:
            n_falhou += 1
            print(f"  ERRO {name}: {type(ex).__name__}: {ex}")

    print(f"Resultado: {n_ok} OK, {n_falhou} falharam. Delta maximo absoluto: {max_delta:.3e}")
    return n_falhou == 0


# ---------------------------------------------------------------------------
# Layout sintetico usado nos Testes B e C
# ---------------------------------------------------------------------------

def _layout_sintetico():
    outer = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    hole = [(4, 4), (6, 4), (6, 6), (4, 6), (4, 4)]
    A = Polygon(outer, [hole])          # contorno externo + 1 furo -> 2 "runs" de corte
    B = Polygon([(100, 100), (105, 100), (105, 105), (100, 105), (100, 100)])
    C = Polygon([(200, 50), (205, 50), (205, 55), (200, 55), (200, 50)])
    return [A, B, C]


# ---------------------------------------------------------------------------
# TESTE B -- cobertura de todos os pontos de chamada, layout sintetico
# ---------------------------------------------------------------------------

def teste_b_cobertura_pontos_de_chamada() -> bool:
    print()
    print("=" * 70)
    print("TESTE B -- cobertura de todos os pontos de chamada (layout sintetico)")
    print("=" * 70)

    variantes = [
        ("mst_strategy=edge_swap", {"mst_strategy": "edge_swap"}),
        ("root_strategy=enumerate", {"root_strategy": "enumerate"}),
        ("child_order=permutation", {"child_order": "permutation"}),
        ("child_order=2opt", {"child_order": "2opt"}),
        ("vertex_strategy=enumerate", {"vertex_strategy": "enumerate"}),
        ("enforce_precedence+sequential", {"enforce_precedence": True, "precedence_strategy": "sequential"}),
        ("enforce_precedence+sequential_2opt", {"enforce_precedence": True, "precedence_strategy": "sequential_2opt"}),
        ("enforce_precedence+hybrid", {"enforce_precedence": True, "precedence_strategy": "hybrid"}),
    ]
    cfg_base = {
        "root_strategy": "nearest",
        "child_order": "num_filhos",
        "mst_strategy": "standard",
        "vertex_strategy": "nearest",
        "enforce_precedence": False,
        "time_limit": None,
    }

    n_ok, n_falhou = 0, 0
    for label, extra in variantes:
        cfg = {**cfg_base, **extra}
        layout = _layout_sintetico()
        try:
            res_default = hc.run_heuristic(list(layout), dict(cfg))
            res_explicit = hc.run_heuristic(list(layout), _cfg_laser_original(cfg))
            delta = abs(res_default["fo_total"] - res_explicit["fo_total"])
            if delta < _TOL:
                print(f"  OK   {label:38s} fo={res_default['fo_total']:.6f} delta={delta:.2e}")
                n_ok += 1
            else:
                print(f"  FALHOU {label:36s} default={res_default['fo_total']:.6f} "
                      f"explicito={res_explicit['fo_total']:.6f} delta={delta:.3e}")
                n_falhou += 1
        except Exception as ex:
            print(f"  ERRO {label}: {type(ex).__name__}: {ex}")
            n_falhou += 1

    print(f"Resultado: {n_ok} OK, {n_falhou} falharam (de {len(variantes)} variantes).")
    return n_falhou == 0


# ---------------------------------------------------------------------------
# TESTE C -- sanidade: os parametros TEM efeito, e o efeito e o esperado
# ---------------------------------------------------------------------------

def _contar_perfuracoes(caminho) -> int:
    """Reproduz a contagem de calcular_fo de forma independente, para validar."""
    n, tag_anterior = 0, None
    for s, t in caminho:
        if not (hasattr(s, "coords") and len(list(s.coords)) >= 2):
            continue
        if t == "c" and tag_anterior != "c":
            n += 1
        tag_anterior = t
    return n


def teste_c_sanidade_efeito() -> bool:
    print()
    print("=" * 70)
    print("TESTE C -- sanidade: v_cut/tempo_perfuracao tem o efeito esperado")
    print("=" * 70)
    cfg_base = {
        "root_strategy": "nearest",
        "child_order": "num_filhos",
        "mst_strategy": "standard",
        "vertex_strategy": "nearest",
        "enforce_precedence": False,
    }
    layout = _layout_sintetico()
    ok = True

    # (1) reduzir v_cut (corte mais lento) deve AUMENTAR a FO
    res_orig = hc.run_heuristic(list(layout), _cfg_laser_original(cfg_base))
    cfg_lento = _cfg_laser_original(cfg_base)
    cfg_lento["v_cut"] = LASER_ORIGINAL.v_cut / 2.0
    res_lento = hc.run_heuristic(list(layout), cfg_lento)
    if res_lento["fo_total"] > res_orig["fo_total"] + _TOL:
        print(f"  OK   v_cut/2 aumenta FO: {res_orig['fo_total']:.6f} -> {res_lento['fo_total']:.6f}")
    else:
        print(f"  FALHOU v_cut/2 nao aumentou FO como esperado: "
              f"{res_orig['fo_total']:.6f} -> {res_lento['fo_total']:.6f}")
        ok = False

    # (2) tempo_perfuracao > 0 deve aumentar a FO em EXATAMENTE n_perfuracoes * delta
    delta_t = 0.75
    cfg_com_perf = _cfg_laser_original(cfg_base)
    cfg_com_perf["tempo_perfuracao"] = delta_t
    res_com_perf = hc.run_heuristic(list(layout), cfg_com_perf)

    n_perf = _contar_perfuracoes(res_orig["caminho"])
    esperado = res_orig["fo_total"] + n_perf * delta_t
    delta_obs = abs(res_com_perf["fo_total"] - esperado)
    print(f"  n_perfuracoes contado independentemente (ultimo componente): {n_perf}")
    if delta_obs < 1e-6:
        print(f"  OK   FO com perfuracao bate com formula: "
              f"{res_com_perf['fo_total']:.6f} == {res_orig['fo_total']:.6f} + {n_perf}*{delta_t} "
              f"(delta={delta_obs:.2e})")
    else:
        print(f"  FALHOU FO com perfuracao NAO bate com formula: "
              f"obtido={res_com_perf['fo_total']:.6f} esperado={esperado:.6f} (delta={delta_obs:.3e})")
        ok = False

    return ok


if __name__ == "__main__":
    limit = 20
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    ok_a = teste_a_regressao_cpplib(limit)
    ok_b = teste_b_cobertura_pontos_de_chamada()
    ok_c = teste_c_sanidade_efeito()

    print()
    print("=" * 70)
    if ok_a and ok_b and ok_c:
        print("REGRESSAO OK -- integracao de PerfilTecnologia valida em todos os testes.")
        sys.exit(0)
    else:
        print(f"FALHOU -- Teste A: {'OK' if ok_a else 'FALHOU'}, "
              f"Teste B: {'OK' if ok_b else 'FALHOU'}, "
              f"Teste C: {'OK' if ok_c else 'FALHOU'}")
        sys.exit(1)
