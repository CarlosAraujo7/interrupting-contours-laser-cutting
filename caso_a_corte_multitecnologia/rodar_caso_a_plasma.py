"""
rodar_caso_a_plasma.py
========================
Primeiro experimento genuinamente multi-tecnologia do Caso A: roda a
heurística geométrica (heuristic_core.run_heuristic, via PerfilTecnologia)
nas instâncias REAIS do CPPLib com o perfil de plasma (PLASMA_ACO_45A_...)
e compara com o perfil original (LASER_ORIGINAL).

Depende da integração de PerfilTecnologia em heuristic_core.py/
local_search_tree.py (ver docs/00_log_cronologico.md, 30/08/2026) e da
investigação de escala documentada em perfil_tecnologia.py (nota
"QUESTÃO DA ESCALA FÍSICA" no topo daquele módulo -- leitura obrigatória
antes de citar qualquer número deste script num rascunho de artigo).

TODO NÚMERO ABSOLUTO deste script depende da suposição
ESCALA_DXF_MM_POR_UNIDADE=1.0 (unidade DXF do CPPLib = mm) -- uma
INFERÊNCIA por consistência dimensional (148/148 instâncias plausíveis
como mm, 0-9% para qualquer alternativa testada), NÃO uma confirmação da
fonte primária (o artigo do CPPLib, Petunin et al. 2020, e os artigos
relacionados do mesmo grupo, estão todos inacessíveis -- 6 tentativas
diferentes, todas bloqueadas, nenhum bypass tentado). Por isso este script
roda DOIS blocos, não um:

  BLOCO 1 -- varredura de espessura: todas as 8 espessuras do
  PLASMA_ACO_45A vs LASER_ORIGINAL, k=1.0 fixo. É o resultado "principal",
  mas AINDA condicionado à suposição de escala.

  BLOCO 2 -- análise de sensibilidade a k (escala DXF->mm) para UMA
  espessura representativa (1/4in, ~6.4mm, aço estrutural comum) --
  caracteriza o quanto a conclusão qualitativa (plasma X% mais lento que
  laser) depende do valor exato de k, já que k não pôde ser confirmado
  pela fonte primária. Testa k em {0.1, 0.5, 1.0, 1.5, 2.0} -- cobre desde
  a segunda hipótese mais plausível encontrada (k=0.1, ver
  perfil_tecnologia.py) até o dobro/metade do valor central.

  Conversão usada: v_cut/v_air são velocidades reais (mm/s); a FO soma
  comprimento_dxf/v -- ou seja, mudar k é equivalente a usar
  v_efetivo = v_mm_s / k (em unidades-DXF/s) SEM alterar a geometria (mais
  simples e exatamente equivalente a escalar as coordenadas por k).
  tempo_perfuracao é um custo de TEMPO (segundos), não de comprimento --
  não depende de k, e portanto NÃO é dividido por k.

Config da heurística mantida FIXA (nearest/num_filhos/standard/nearest,
enforce_precedence=True, precedence_strategy=sequential -- a variante que
GARANTE Π, não a "original" que não garante) em ambos os blocos -- a
variável de interesse aqui é o PERFIL DE TECNOLOGIA, não a estratégia da
heurística (essa comparação já foi feita em rodar_heuristica_cpplib.py).

Uso:
    python3 rodar_caso_a_plasma.py [--limit N]
"""
from __future__ import annotations

import csv
import statistics
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "src_base"))

import heuristic_core as hc  # noqa: E402
from dxf_parser import load_all_cpplib, CATEGORIA_COM_PRECEDENCIA  # noqa: E402
from perfil_tecnologia import (  # noqa: E402
    LASER_ORIGINAL,
    PLASMA_ACO_45A_REFERENCIA_MM_S,
    perfil_plasma_por_espessura,
)

_CFG_BASE = {
    "root_strategy": "nearest",
    "child_order": "num_filhos",
    "mst_strategy": "standard",
    "vertex_strategy": "nearest",
    "enforce_precedence": True,
    "precedence_strategy": "sequential",
}

_ESPESSURA_REPRESENTATIVA = "1/4in (~6.4mm)"
_KS_SENSIBILIDADE = [0.1, 0.5, 1.0, 1.5, 2.0]


def _slug(espessura: str) -> str:
    return espessura.split(" ")[0].replace("/", "_")


def _cfg_perfil(perfil, k: float = 1.0) -> dict:
    """Converte um PerfilTecnologia (em mm/s reais) num config de run_heuristic,
    aplicando o fator de escala k (mm por unidade DXF assumida). v_cut/v_air
    -> velocidade efetiva em unidades-DXF/s = v_mm_s / k. tempo_perfuracao
    NAO e afetado por k (custo de tempo, nao de comprimento)."""
    return {
        **_CFG_BASE,
        "v_cut": perfil.v_cut / k,
        "v_air": perfil.v_air / k,
        "tempo_perfuracao": perfil.tempo_perfuracao,
    }


def carregar_instancias(limit):
    root = _HERE / "instances" / "cpplib"
    instancias = load_all_cpplib(root, category_dirname=CATEGORIA_COM_PRECEDENCIA)
    instancias = [(n, p, s) for (n, p, s) in instancias if len(p) >= 2]
    if limit:
        instancias = instancias[:limit]
    return instancias


def bloco1_varredura_espessura(instancias, fo_laser_cache: dict):
    print("=" * 70)
    print("BLOCO 1 -- varredura de espessura de plasma vs laser (k=1.0)")
    print("=" * 70)
    linhas = []
    t0 = time.time()
    for i, (nome, polys, stats) in enumerate(instancias, 1):
        try:
            res_laser = hc.run_heuristic(list(polys), _cfg_perfil(LASER_ORIGINAL))
            fo_laser = res_laser["fo_total"]
            fo_laser_cache[nome] = fo_laser
        except Exception as ex:
            print(f"  [{i}/{len(instancias)}] {nome}: ERRO laser {type(ex).__name__}: {ex}")
            continue
        linha = {"instance": nome, "fo_laser": round(fo_laser, 4)}
        for espessura in PLASMA_ACO_45A_REFERENCIA_MM_S:
            perfil = perfil_plasma_por_espessura(espessura)
            chave = _slug(espessura)
            try:
                res_p = hc.run_heuristic(list(polys), _cfg_perfil(perfil))
                fo_p = res_p["fo_total"]
                linha[f"fo_plasma_{chave}"] = round(fo_p, 4)
                linha[f"gap_pct_{chave}"] = round(100 * (fo_p - fo_laser) / fo_laser, 3) if fo_laser > 0 else None
            except Exception as ex:
                linha[f"fo_plasma_{chave}"] = None
                print(f"    ERRO plasma {espessura} em {nome}: {type(ex).__name__}: {ex}")
        linhas.append(linha)
        if i % 10 == 0 or i == len(instancias):
            print(f"  [{i}/{len(instancias)}] processadas ({time.time() - t0:.1f}s)...", flush=True)
    return linhas


def bloco2_sensibilidade_k(instancias, fo_laser_cache: dict):
    print()
    print("=" * 70)
    print(f"BLOCO 2 -- sensibilidade a k (escala DXF->mm), espessura={_ESPESSURA_REPRESENTATIVA}")
    print("=" * 70)
    perfil = perfil_plasma_por_espessura(_ESPESSURA_REPRESENTATIVA)
    linhas = []
    t0 = time.time()
    for i, (nome, polys, stats) in enumerate(instancias, 1):
        fo_laser = fo_laser_cache.get(nome)
        if fo_laser is None:
            try:
                fo_laser = hc.run_heuristic(list(polys), _cfg_perfil(LASER_ORIGINAL))["fo_total"]
            except Exception:
                continue
        linha = {"instance": nome, "fo_laser": round(fo_laser, 4)}
        for k in _KS_SENSIBILIDADE:
            try:
                res_p = hc.run_heuristic(list(polys), _cfg_perfil(perfil, k=k))
                fo_p = res_p["fo_total"]
                linha[f"fo_plasma_k{k}"] = round(fo_p, 4)
                linha[f"gap_pct_k{k}"] = round(100 * (fo_p - fo_laser) / fo_laser, 3) if fo_laser > 0 else None
            except Exception as ex:
                linha[f"fo_plasma_k{k}"] = None
                print(f"    ERRO k={k} em {nome}: {type(ex).__name__}: {ex}")
        linhas.append(linha)
        if i % 10 == 0 or i == len(instancias):
            print(f"  [{i}/{len(instancias)}] processadas ({time.time() - t0:.1f}s)...", flush=True)
    return linhas


def resumir(linhas, chaves_gap, titulo):
    print(f"\n--- Resumo: {titulo} ---")
    for chave in chaves_gap:
        gaps = [l[chave] for l in linhas if l.get(chave) is not None]
        if gaps:
            print(f"  {chave:20s}: n={len(gaps):3d}  media={statistics.mean(gaps):9.2f}%  "
                  f"mediana={statistics.median(gaps):9.2f}%  min={min(gaps):9.2f}%  max={max(gaps):9.2f}%")
        else:
            print(f"  {chave:20s}: sem dados")


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    # Bloco 2 (sensibilidade a k) e' um teste de robustez suplementar, nao o
    # resultado principal -- roda num subconjunto menor por padrao para nao
    # dobrar o tempo total (5 valores de k x N instancias). Default 30,
    # sobrepoe com --limit-b2 se quiser rodar no mesmo conjunto do Bloco 1.
    limit_b2 = 30
    if "--limit-b2" in sys.argv:
        limit_b2 = int(sys.argv[sys.argv.index("--limit-b2") + 1])

    instancias = carregar_instancias(limit)
    print(f"Carregadas {len(instancias)} instancias validas (categoria=com_precedencia).")

    fo_laser_cache: dict = {}

    linhas1 = bloco1_varredura_espessura(instancias, fo_laser_cache)
    campos1 = ["instance", "fo_laser"] + sorted({k for l in linhas1 for k in l if k not in ("instance", "fo_laser")})
    with open(_HERE / "resultado_caso_a_plasma_por_espessura.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos1)
        w.writeheader()
        w.writerows(linhas1)
    resumir(linhas1, [f"gap_pct_{_slug(e)}" for e in PLASMA_ACO_45A_REFERENCIA_MM_S],
            "gap % plasma vs laser por espessura (k=1.0)")

    instancias_b2 = instancias[:limit_b2] if limit_b2 else instancias
    linhas2 = bloco2_sensibilidade_k(instancias_b2, fo_laser_cache)
    campos2 = ["instance", "fo_laser"] + sorted({k for l in linhas2 for k in l if k not in ("instance", "fo_laser")})
    with open(_HERE / "resultado_caso_a_plasma_sensibilidade_k.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos2)
        w.writeheader()
        w.writerows(linhas2)
    resumir(linhas2, [f"gap_pct_k{k}" for k in _KS_SENSIBILIDADE],
            f"gap % plasma vs laser por k ({_ESPESSURA_REPRESENTATIVA})")

    print("\nCSVs salvos: resultado_caso_a_plasma_por_espessura.csv, resultado_caso_a_plasma_sensibilidade_k.csv")
    print("LEMBRETE: todo numero acima assume ESCALA_DXF_MM_POR_UNIDADE=1.0 (inferencia, nao confirmacao -- ver perfil_tecnologia.py).")


if __name__ == "__main__":
    main()
