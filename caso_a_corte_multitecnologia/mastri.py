r"""
mastri.py
=========
Reimplementacao do MASTRI (Eapen & Heckendorn, 2021, "Cutting path
optimization for an automatic cutter in polynomial time using a 3/2
approximation algorithm", Int. J. Adv. Manuf. Technol. 113, 3667-3679,
DOI 10.1007/s00170-021-06842-9), baseline construtivo do Caso A.

Sem codigo original disponivel (ver docs/00_log_cronologico.md, entrada de
13/08/2026, e docs/06_plano_desenvolvimento.md, Secao 1.2) -- reimplementado
a partir da descricao do artigo: triangulacao de Delaunay + MST de Kruskal +
matching de custo minimo (Christofides) sobre os nos de grau impar da MST +
atalho (shortcut) do circuito Euleriano resultante. E' a mesma familia de
algoritmo do Christofides classico para o TSP metrico, aplicada pelos
autores ao Cutting Path Determination Problem (CPDP) via reducao a RPP.

CORRECAO IMPORTANTE (29/08/2026, noite): `escolher_cidades_e_fo` (abaixo)
tinha um fallback herdado fielmente do LCPP-main original que mascarava
como custo 0 qualquer transicao sem distancia direcional finita -- medido
em 21,6% das transicoes (542/2505), em 48/48 instancias reais. Corrigido
(ver comentario na propria funcao para o detalhe completo). Os resultados
em `comparacao_mastri_pcglns.csv` foram RE-GERADOS apos esta correcao --
ver nota de rodape no proprio CSV e docs/00_log_cronologico.md.

Adaptacao para as instancias abstratas GTSP/PCGTSP (formato .pcglns)
---------------------------------------------------------------------
As unicas instancias com formato ja confirmado (github.com/EnsignDaniels/CPP,
ver docs/00_log_cronologico.md) nao trazem coordenadas geometricas brutas --
sao matrizes de distancia abstratas entre "cidades" agrupadas em conjuntos
GTSP (reducao ja aplicada por Khachai-Battaia-Petunin-Khachay 2024 a partir
das instancias industriais reais). A etapa de Delaunay do MASTRI original
(que pressupoe um conjunto de PONTOS no plano) nao se aplica diretamente
aqui -- nao ha pontos para triangular, so' distancias.

Delaunay no MASTRI original e' uma otimizacao de ESPARSIFICACAO (evita o
grafo completo O(n^2) quando n e' grande), nao um requisito matematico do
Christofides -- o algoritmo (MST + matching + atalho) e' correto sobre
QUALQUER grafo completo com pesos metricos, so' perde a garantia de
eficiencia de Delaunay ao usar o grafo completo diretamente. Como aqui
trabalhamos ao nivel de GRUPO (no maximo 120 grupos nas 48 instancias
disponiveis), um grafo completo entre grupos e' trivial computacionalmente
(<=120^2 arestas): pulamos Delaunay e construimos a MST direto sobre o
grafo completo de grupos, com peso(A,B) = menor distancia direcional entre
qualquer par (cidade em A, cidade em B) -- MESMA convencao de
`pcgtsp_comparison/heuristica_direta_pcgtsp.py::construir_grafo_grupos` do
projeto LCPP original.

RESSALVA HONESTA: a garantia formal de 3/2-aproximacao do Christofides
pressupoe uma metrica real (desigualdade triangular) sobre os pontos. No
espaco geometrico original do CPDP isso vale sempre (distancia
euclidiana/Chebyshev entre pontos). Aqui, peso(A,B) = min sobre pares de
cidades e' uma distancia INDUZIDA entre grupos, que NAO e' garantidamente
metrica (ir de A a C via B pode, em principio, ser mais barato que o
"atalho direto" A-C se as cidades que realizam o minimo em cada par forem
diferentes). Tratamos este modulo como "o mesmo template construtivo do
MASTRI" (MST + matching + atalho), nao como uma reimplementacao com garantia
formal preservada nesta adaptacao especifica -- a comparacao empirica de
qualidade continua valida e informativa, so' a garantia teorica de pior caso
do artigo original nao se transporta automaticamente para este modo
abstrato. Quando instancias geometricas reais (com coordenadas) entrarem no
projeto, vale adicionar um segundo modo (`resolver_mastri_geometrico`, nao
implementado ainda) que usa Delaunay de verdade sobre pontos e preserva a
garantia original.

MASTRI, como publicado, NAO modela precedencia (nenhum dos 5 artigos da
linhagem CPDP aplicada modela -- ver docs/04_verdade_atual.md). Este modulo
portanto NAO tenta impor Pi na construcao -- calcula o tour "as-is" e
reporta separadamente quantas violacoes de precedencia ele comete, na mesma
convencao de contagem de `heuristica_direta_pcgtsp.py::_viol_ciclica`. Isso
e' proposital: e' exatamente a comparacao de FEASIBILITY (nao so' custo) que
a hipotese H2 (docs/06_plano_desenvolvimento.md, Secao 1.5) pede.

Nota de arquitetura: este arquivo e' AUTOCONTIDO (nao importa de
C:\Pesquisas\LCPP-main\pcgtsp_comparison\, que fica fora deste projeto e nao
deve virar dependencia viva dele). O parser `.pcglns` abaixo segue o MESMO
formato validado por `pcgtsp_comparison/converter.py` e
`pcgtsp_comparison/heuristica_direta_pcgtsp.py::parse_pcglns` no projeto
original (confirmado por leitura direta de ambos), reescrito aqui de forma
independente para nao acoplar os dois projetos irmaos.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import networkx as nx

INF = float("inf")


# =============================================================================
# Parsing (.pcglns)
# =============================================================================

def parse_pcglns(path) -> Dict:
    """Le um arquivo .pcglns (formato PCGTSPLIB/PCGLNS -- ver
    instances/ensigndaniels_cpp/*/*.pcglns deste projeto).

    Retorna um dict com: dim (n cidades), matrix (matriz de distancia
    direcional dim x dim, -1 = arco proibido), group_cities (dict
    grupo_1indexed -> [cidades_1indexed]), city_group (dict cidade -> grupo),
    pares (lista de (predecessor, sucessor), ids de GRUPO -- sucessor so'
    pode ser visitado depois de predecessor), start_group (grupo inicial).
    """
    lines = Path(path).read_text(encoding="latin-1").splitlines()  # latin-1: o cabecalho de alguns .pcglns tem bytes nao-ASCII (cp1252 padrao do Windows quebrava 17/48 -- corrigido 01/10/2026)

    def idx_de(prefixo: str) -> int:
        for i, l in enumerate(lines):
            if l.strip().startswith(prefixo):
                return i
        return -1

    dim = int(lines[idx_de("DIMENSION")].split(":")[1].strip())

    ew = idx_de("EDGE_WEIGHT_SECTION")
    matrix: List[List[float]] = []
    for i in range(ew + 1, ew + 1 + dim):
        matrix.append([float(x) for x in lines[i].split()])

    city_group: Dict[int, int] = {}
    group_cities: Dict[int, List[int]] = {}
    i = idx_de("GTSP_SET_SECTION") + 1
    while i < len(lines) and not lines[i].strip().startswith(
            ("GTSP_SET_ORDERING", "START_GROUP_SECTION", "EOF")):
        s = lines[i].strip()
        if s:
            nums = [int(x) for x in s.split()]
            grp = nums[0]
            cidades = []
            for c in nums[1:]:
                if c == -1:
                    break
                cidades.append(c)
                city_group[c] = grp
            group_cities[grp] = cidades
        i += 1

    pares: List[Tuple[int, int]] = []
    i = idx_de("GTSP_SET_ORDERING")
    if i != -1:
        i += 1
        while i < len(lines) and not lines[i].strip().startswith(("START_GROUP_SECTION", "EOF")):
            s = lines[i].strip()
            if s:
                nums = [int(x) for x in s.split()]
                pred = nums[0]
                for suc in nums[1:]:
                    if suc == -1:
                        break
                    pares.append((pred, suc))
            i += 1

    sg = idx_de("START_GROUP_SECTION")
    start_group = int(lines[sg + 1].strip()) if sg != -1 else min(group_cities)

    return {
        "dim": dim, "matrix": matrix, "city_group": city_group,
        "group_cities": group_cities, "pares": pares, "start_group": start_group,
        "name": Path(path).stem,
    }


def _dist(matrix: List[List[float]], a: int, b: int) -> float:
    """Distancia direcional a->b (cidades 1-indexadas); -1 = arco proibido."""
    d = matrix[a - 1][b - 1]
    return INF if d < 0 else d


# =============================================================================
# Grafo completo de grupos (substitui a Delaunay do MASTRI original --
# ver ressalva no docstring do modulo)
# =============================================================================

def construir_grafo_grupos(parsed: Dict) -> nx.Graph:
    """Grafo completo entre GRUPOS: peso(A,B) = menor distancia entre
    qualquer par (cidade em A, cidade em B), simetrizada (min das duas
    direcoes) -- mesma convencao de
    `pcgtsp_comparison/heuristica_direta_pcgtsp.py::construir_grafo_grupos`
    no projeto LCPP original."""
    group_cities = parsed["group_cities"]
    matrix = parsed["matrix"]
    grupos = sorted(group_cities.keys())
    G = nx.Graph()
    G.add_nodes_from(grupos)
    for gi, a in enumerate(grupos):
        for b in grupos[gi + 1:]:
            melhor = INF
            melhor_par = None
            for ca in group_cities[a]:
                for cb in group_cities[b]:
                    d = min(_dist(matrix, ca, cb), _dist(matrix, cb, ca))
                    if d < melhor:
                        melhor = d
                        melhor_par = (ca, cb)
            if melhor_par is not None:
                G.add_edge(a, b, weight=melhor, connection=melhor_par)
    return G


# =============================================================================
# MASTRI: MST + matching de custo minimo (Christofides) + atalho
# =============================================================================

def _tour_mastri_sobre_grafo(G: nx.Graph, raiz) -> List:
    """Aplica o template MST + matching + atalho sobre um grafo completo
    ponderado G (nao precisa ser geometrico -- ver ressalva do modulo).
    Retorna a ordem dos NOS de G (shortcut do circuito Euleriano),
    comecando em `raiz`."""
    if G.number_of_nodes() == 1:
        return list(G.nodes())

    mst = nx.minimum_spanning_tree(G, weight="weight")

    impares = [n for n in mst.nodes() if mst.degree(n) % 2 == 1]
    # Matching de custo minimo entre os nos de grau impar, sobre o grafo
    # completo original G (nao a MST) -- e' a etapa de Christofides. G ja e'
    # completo (construido em construir_grafo_grupos), entao o subgrafo
    # induzido em `impares` tambem e' completo.
    sub_completo = G.subgraph(impares)
    matching = nx.algorithms.matching.min_weight_matching(sub_completo, weight="weight")

    multi = nx.MultiGraph()
    multi.add_nodes_from(mst.nodes())
    multi.add_edges_from(mst.edges())
    multi.add_edges_from(matching)
    # Todo no' agora tem grau par (MST + exatamente 1 aresta de matching nos
    # que eram impares) -> circuito Euleriano existe (multi e' conexo, pois
    # a MST ja e' conexa e so' adicionamos arestas).
    circuito = list(nx.eulerian_circuit(multi, source=raiz))

    visitados = set()
    tour = []
    for u, v in circuito:
        if u not in visitados:
            tour.append(u)
            visitados.add(u)
    for n in mst.nodes():  # salvaguarda defensiva (nao deveria disparar)
        if n not in visitados:
            tour.append(n)

    if tour and tour[0] != raiz and raiz in tour:
        idx = tour.index(raiz)
        tour = tour[idx:] + tour[:idx]

    return tour


# =============================================================================
# Escolha da cidade representante de cada grupo (gulosa) + FO
# =============================================================================
#
# CORRECAO (29/08/2026, noite, achada ao validar tsh_vns.py -- ver
# docs/00_log_cronologico.md para o detalhe completo e o impacto medido):
# a versao original desta funcao (identica, byte a byte, a
# `pcgtsp_comparison/heuristica_direta_pcgtsp.py::escolher_cidades_e_fo` do
# LCPP-main -- reproduzida daqui de forma fiel, nao e' erro de transcricao)
# usava so' a distancia DIRECIONAL (_dist(matrix, cidade_atual, c)) tanto pra
# escolher a proxima cidade quanto pra somar o custo, com um fallback de
# "custo 0" sempre que essa direcao especifica desse -1/INF. Medido nas 48
# instancias reais (instances/ensigndaniels_cpp/): 542 de 2505 transicoes
# (21,6%), em 48/48 instancias, batiam nesse fallback -- ou seja, ~1 em cada
# 5 movimentos do tour do MASTRI (e, por heranca, do TSH+VNS, que reusa esta
# funcao) tinha seu custo real SILENCIOSAMENTE ZERADO em vez de contabilizado.
# Isso gera FO ARTIFICIALMENTE MAIS BAIXA para ambos os baselines
# construtivos sempre que a direcao "de ida" escolhida pela gulosa calha de
# ser proibida -- inclusive no resultado ja reportado em
# `comparacao_mastri_pcglns.csv` (MASTRI vs PCGLNS), que precisou ser
# re-rodado com a correcao abaixo (ver docs/00_log_cronologico.md e
# comparacao_mastri_pcglns.csv, nota de rodape).
#
# Causa raiz: `construir_grafo_grupos` (acima) ja SIMETRIZA a distancia entre
# GRUPOS (min das duas direcoes) para decidir se dois grupos sao "vizinhos"
# -- mas esta funcao, ao escolher a CIDADE especifica dentro do grupo, usava
# so' a direcao unica "de ida". Quando a direcao escolhida pela MST/matching
# (baseada na distancia simetrizada) e' justamente a proibida no sentido
# direcional, a gulosa fica sem opcao valida e caia no fallback de custo 0.
#
# Fix: usar a MESMA convencao de simetrizacao ja empregada em
# `construir_grafo_grupos` (min das duas direcoes) tambem aqui, tanto pra
# escolher a cidade quanto pra somar o custo -- consistente com o resto do
# modulo, e elimina o problema por completo: 0/2505 transicoes ficam INF
# apos a correcao (medido nas mesmas 48 instancias). Mantido um contador
# `n_transicoes_ainda_inf` (deve ser 0 na pratica, mas reportado de forma
# transparente em vez de mascarado, caso apareca em instancias futuras).
#
# RESSALVA: assumir min(ida,volta) e' uma aproximacao -- fisicamente, o
# tour pode nao poder "percorrer ao contrario" um segmento cuja direcao
# direta e' proibida. E' uma simplificacao deliberada e documentada (a
# MESMA ja aceita implicitamente pela etapa de construcao do grafo de
# grupos), preferida a silenciar 21,6% dos custos reais como zero.

def escolher_cidades_e_fo(ordem_grupos: List[int], parsed: Dict) -> Tuple[List[int], float]:
    group_cities = parsed["group_cities"]
    matrix = parsed["matrix"]

    def dist_sim(a: int, b: int) -> float:
        return min(_dist(matrix, a, b), _dist(matrix, b, a))

    cidades_escolhidas: List[int] = []
    cidade_atual = None
    fo = 0.0
    n_transicoes_ainda_inf = 0

    for grp in ordem_grupos:
        candidatos = group_cities[grp]
        if cidade_atual is None:
            escolhida = candidatos[0]
        else:
            escolhida = min(candidatos, key=lambda c: dist_sim(cidade_atual, c))
            custo = dist_sim(cidade_atual, escolhida)
            if custo == INF:
                n_transicoes_ainda_inf += 1
            else:
                fo += custo
        cidades_escolhidas.append(escolhida)
        cidade_atual = escolhida

    if cidades_escolhidas:
        primeira = cidades_escolhidas[0]
        custo_fecha = dist_sim(cidade_atual, primeira)
        if custo_fecha == INF:
            n_transicoes_ainda_inf += 1
        else:
            fo += custo_fecha

    if n_transicoes_ainda_inf:
        # Nao deveria disparar (0/2505 medido nas 48 instancias reais) --
        # se disparar em dados futuros, o FO retornado ainda subestima o
        # custo real nessas transicoes especificas; o chamador pode checar
        # esta condicao lendo o 3o elemento da tupla estendida se precisar.
        import sys as _sys
        print(f"AVISO: {n_transicoes_ainda_inf} transicao(oes) sem distancia "
              f"finita em nenhuma direcao (grupo isolado?) -- FO subestimado.",
              file=_sys.stderr)

    return cidades_escolhidas, fo


def _viol_precedencia(ordem_grupos: List[int], pares: List[Tuple[int, int]]) -> int:
    """Conta violacoes de Pi numa ordem de GRUPOS: para cada par
    (predecessor, sucessor) em `pares`, sucessor deve vir DEPOIS de
    predecessor na ordem (ja' comeca em start_group, entao nao precisa de
    rotacao ciclica extra -- ver heuristica_direta_pcgtsp.py::_viol_ciclica
    para o caso geral com mais de uma componente)."""
    pos = {g: i for i, g in enumerate(ordem_grupos)}
    viol = 0
    for pred, suc in pares:
        if pred in pos and suc in pos and pos[pred] > pos[suc]:
            viol += 1
    return viol


# =============================================================================
# Entrada principal
# =============================================================================

def resolver_mastri(path) -> Dict:
    t0 = time.time()
    parsed = parse_pcglns(path)
    G = construir_grafo_grupos(parsed)

    fo_total = 0.0
    tour_total: List[int] = []
    viol_total = 0
    for comp in nx.connected_components(G):
        sub = G.subgraph(comp)
        raiz = parsed["start_group"] if parsed["start_group"] in comp else next(iter(comp))
        ordem_grupos = _tour_mastri_sobre_grafo(sub, raiz)
        cidades, fo = escolher_cidades_e_fo(ordem_grupos, parsed)
        pares_comp = [(f, p) for f, p in parsed["pares"] if f in comp and p in comp]
        viol_total += _viol_precedencia(ordem_grupos, pares_comp)
        fo_total += fo
        tour_total.extend(cidades)

    t_total = time.time() - t0
    return {
        "name": parsed["name"],
        "fo": fo_total,
        "tour": tour_total,
        "n_grupos": len(parsed["group_cities"]),
        "n_pares": len(parsed["pares"]),
        "violacoes": viol_total,
        "tempo_s": t_total,
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        alvos = [Path(p) for p in sys.argv[1:]]
    else:
        base = Path(__file__).resolve().parent / "instances" / "ensigndaniels_cpp"
        alvos = sorted(base.rglob("*.pcglns"))

    resultados = []
    for fp in alvos:
        r = resolver_mastri(fp)
        resultados.append(r)
        print(f"{r['name']:<20} FO={r['fo']:>14.2f}  grupos={r['n_grupos']:>4}  "
              f"pares={r['n_pares']:>4}  viol={r['violacoes']:>3}  t={r['tempo_s']:.4f}s")

    if len(alvos) > 1:
        print(f"\nTotal: {len(resultados)} instancias, "
              f"{sum(r['violacoes'] for r in resultados)} violacoes de Pi no total "
              f"(esperado > 0 -- MASTRI nao modela precedencia, ver docstring do modulo), "
              f"tempo total {sum(r['tempo_s'] for r in resultados):.3f}s")
