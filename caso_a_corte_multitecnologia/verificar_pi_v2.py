"""
verificar_pi_v2.py
===================
Checagem REFINADA de violacoes de Pi para o modo enforce_precedence=True,
rodada em cima dos resultados de rodar_heuristica_cpplib.py (ver
docs/00_log_cronologico.md, entrada de 29/08/2026, para o achado completo).

Achado: o checker original (check_precedence_violations, reproduzido de
pcgtsp_comparison/run_comparison.py do LCPP-main) reportou 21/4596 "violacoes"
no modo com_pi. Investigacao exaustiva (as 21 janelas de violacao, TODAS
inspecionadas segmento a segmento) mostrou que TODAS sao causadas pelo mesmo
mecanismo: quando um furo esta encostado na borda do seu pai (poligonos se
tocam, distance=0), o(s) segmento(s) da aresta de CONTATO pertencem
simultaneamente aos dois contornos (a mesma aresta faz parte do perimetro de
ambos). O checker original usa `_find_polygon_owner`, que devolve so' o
PRIMEIRO indice de poligono cuja borda bate com o segmento -- como pai tem
indice menor que furo (efeito colateral de como `_detectar_precedencia`
ordena os pares), toda aresta compartilhada e' creditada a pai, mesmo
quando faz parte de um trecho de corte contiguo que na verdade pertence ao
bloco de furo. Isso faz `primeiro[pai]` "comecar cedo demais", criando uma
violacao falsa.

Este script implementa a correcao: uma aresta compartilhada conta pra AMBOS
os poligonos; so' e' violacao de verdade se existir um segmento EXCLUSIVO de
pai (bate na borda de pai, NAO bate na borda de furo) antes do ultimo
segmento de furo (exclusivo ou compartilhado). Roda de novo o modo com_pi
(so' esse -- nao precisa repetir o modo original) em todas as instancias e
reporta a contagem corrigida.

Uso:
    python3 verificar_pi_v2.py <time_limit_seg> [--limit N]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import List, Tuple

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "src_base"))

import heuristic_core as hc  # noqa: E402
from dxf_parser import load_all_cpplib, CATEGORIA_COM_PRECEDENCIA  # noqa: E402
from rodar_heuristica_cpplib import _CFG_BASE  # noqa: E402


def _key(a, b, tol=6):
    a = tuple(round(v, tol) for v in a)
    b = tuple(round(v, tol) for v in b)
    return (min(a, b), max(a, b))


def _edge_keys(poly):
    coords = list(poly.exterior.coords)
    return {_key(coords[i], coords[i + 1]) for i in range(len(coords) - 1)}


def check_v2(caminho, positions, precedence_pairs) -> Tuple[int, int]:
    """(n_pares_checados, n_violacoes_v2).

    Achado adicional (29/08/2026, ver docs/00_log_cronologico.md): a
    primeira versao deste checker (que so subtraia de pai_edges as arestas
    compartilhadas com O PROPRIO furo do par) ainda dava 1 falso positivo
    residual (p1xj_9, par furo=38/pai=37) -- causa: pai=37 tem DOIS furos
    (35 e 38), e a aresta de contato entre o IRMAO (35) e pai(37) tambem
    bate na busca por "aresta exclusiva de pai" do par (38,37), mesmo nao
    tendo nenhuma relacao com furo=38. Corrigido subtraindo de pai_edges as
    arestas compartilhadas com QUALQUER filho de pai (todos os pares onde
    esse mesmo pai_idx aparece), nao so' o furo do par sendo checado."""
    # cache de segmentos 'c' validos com sua key, na ordem do caminho
    seg_keys: List[Tuple[int, tuple]] = []
    for pos_idx, (seg, tag) in enumerate(caminho):
        if tag != "c" or seg.length < 1e-6:
            continue
        seg_keys.append((pos_idx, _key(seg.coords[0], seg.coords[1])))

    checados = 0
    violacoes = 0
    edge_cache = {}

    def edges_of(idx):
        if idx not in edge_cache:
            edge_cache[idx] = _edge_keys(positions[idx])
        return edge_cache[idx]

    # todos os filhos de cada pai (nao so' o par sendo checado no momento)
    filhos_de: dict = {}
    for f, p in precedence_pairs:
        filhos_de.setdefault(p, []).append(f)

    for furo_idx, pai_idx in precedence_pairs:
        furo_edges = edges_of(furo_idx)
        pai_edges = edges_of(pai_idx)
        arestas_de_algum_filho = set()
        for irmao_idx in filhos_de.get(pai_idx, []):
            arestas_de_algum_filho |= edges_of(irmao_idx)
        pai_exclusive = pai_edges - arestas_de_algum_filho

        ultimo_furo = None
        primeiro_pai_exclusivo = None
        for pos_idx, k in seg_keys:
            if k in furo_edges:
                ultimo_furo = pos_idx  # inclui compartilhadas -- furo "usa" essa aresta tambem
            if k in pai_exclusive and primeiro_pai_exclusivo is None:
                primeiro_pai_exclusivo = pos_idx

        if ultimo_furo is None or primeiro_pai_exclusivo is None:
            continue
        checados += 1
        if ultimo_furo >= primeiro_pai_exclusivo:
            violacoes += 1

    return checados, violacoes


def main():
    time_limit = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
    args = sys.argv[2:]
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None

    root = _HERE / "instances" / "cpplib"
    instances = load_all_cpplib(root, category_dirname=CATEGORIA_COM_PRECEDENCIA)
    if limit:
        instances = instances[:limit]
    print(f"Reverificando modo com_pi (checker v2) em {len(instances)} instancias...")

    tot_checados = 0
    tot_viol = 0
    n_skipped = 0
    n_crash = 0
    t0 = time.time()
    for i, (name, polys, stats) in enumerate(instances, 1):
        if len(polys) < 2:
            n_skipped += 1
            continue
        try:
            positions = hc.clusterizar_quadtree(
                hc.resolver_intersecoes(hc.tratar_furos(list(polys)))
            )
            prec_pairs = hc._detectar_precedencia(positions)
            cfg = {**_CFG_BASE, "time_limit": time_limit, "enforce_precedence": True}
            res = hc.run_heuristic(list(polys), cfg)
            checados, viol = check_v2(res["caminho"], positions, prec_pairs)
            tot_checados += checados
            tot_viol += viol
            marca = "" if viol == 0 else f"  <<< {viol} VIOLACAO(OES) REAL(IS)"
            print(f"[{i}/{len(instances)}] {name}: checados={checados} violacoes_v2={viol}{marca}")
        except Exception as ex:
            n_crash += 1
            print(f"[{i}/{len(instances)}] {name}: ERRO {type(ex).__name__}: {ex}")

    print(f"\nTempo total: {time.time()-t0:.1f}s")
    print(f"Puladas: {n_skipped}  Erros: {n_crash}")
    print(f"\n=== RESULTADO FINAL (checker v2, corrige atribuicao de aresta compartilhada) ===")
    print(f"Pares checados: {tot_checados}")
    print(f"Violacoes reais: {tot_viol}")


if __name__ == "__main__":
    main()
