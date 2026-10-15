"""
tsh_vns.py
==========
AVISO (auditoria de 01/10/2026, PDF de Zhang et al. 2024 em `Artigos/` lido): ESTE MODULO NAO E O METODO
DO ARTIGO. No artigo, TSH (heuristica de dois passos do metodo de ARESTAS/RPP: MstConnet + McfEven
+ circuito euleriano, familia Christofides, proxima do MASTRI) e VNS (metodo SEPARADO do modelo de
NOS/GTSP: 7 operadores Change/Swap/Reverse/Shift/Nearest/Double/Farthest replace, NearestFirst,
Shake de ate 10 aplicacoes, LocalSearch em ordem aleatoria, parada em 10.000 iteracoes sem melhora
ou 1200 s, sem precedencia) sao metodos distintos. Este arquivo e um HIBRIDO PROPRIO (construcao do
MASTRI + VNS Reverse/Shift em ordem de grupos), escrito antes de o artigo estar disponivel. NAO
atribuir seus resultados a "Zhang et al. (2024)". O LCPP-main tem `pcgtsp_comparison/vns_zhang_fiel.py`
(VNS fiel, escrito a partir do mesmo PDF) -- o remedio e portar uma copia adaptada para `src_base/`
(nunca importar) e refazer a comparacao. Ver docs/00_log_cronologico.md, continuacao 64, item 4.

Reimplementacao do TSH+VNS (Tai Zhang, Shaowen Yao, Qiang Liu, Lijun Wei &
Hao Zhang, 2024, "Heuristic approaches for the cutting path problem",
Expert Systems With Applications, 237, 121567, DOI 10.1016/j.eswa.2023.121567),
terceiro baseline do Caso A (ao lado de MASTRI e PCGLNS, ja comparados em
comparacao_mastri_pcglns.csv).

ACESSO AO PAPER: bloqueado nesta sessao -- 6 rotas legitimas tentadas em
29/08/2026 (noite) e todas falharam (DOI -> Elsevier linkinghub:
PROVENANCE_REQUIRED; ResearchGate: 429; mirror ACM: 403; OpenAlex API:
PROVENANCE_REQUIRED; Unpaywall: PROVENANCE_REQUIRED; busca web geral por
PDF/preprint: nada encontrado). Ver docs/06_plano_desenvolvimento.md Secao 4
e docs/00_log_cronologico.md para o detalhe completo. Isso NAO e um bloqueio
para este modulo -- o plano do projeto sempre pryeviu reimplementar TSH+VNS
"a partir da descricao do artigo" (06_plano_desenvolvimento.md, Secao 1.4,
item 2, desde 13/08/2026), o mesmo caminho ja usado com sucesso para o
MASTRI. A descricao disponivel nos documentos do projeto (05_fontes_por_caso.md
item 7; 06_plano_desenvolvimento.md Secao 1.2, tabela de baselines) e:

    "Construtivo (MST+matching+Euler) + metaheuristica (VNS)... MST na
    construcao; VNS com operadores Reverse/Shift analogos a 2-opt/Or-opt na
    melhoria."

ACHADO DE DESIGN (relevante para a redacao do artigo): a construcao "TSH"
(MST + matching + circuito Euleriano + atalho) e, pela propria descricao
disponivel, o MESMO template de Christofides usado pelo MASTRI (Eapen &
Heckendorn 2021 descrevem sua propria construcao como "MST + matching +
atalho" -- seccao 1.2 deste mesmo `06_plano_desenvolvimento.md`). A unica
diferenca estruturalmente documentada entre os dois metodos e a fase de
melhoria: Zhang et al. adicionam VNS (Reverse/Shift) depois da construcao;
Eapen & Heckendorn nao tem nenhuma fase de melhoria (MASTRI e puramente
construtivo). Por isso este modulo REAPROVEITA a construcao de `mastri.py`
(import direto -- mesmo arquivo/projeto, nao e a dependencia-viva-entre-
projetos-irmaos que o resto do codebase evita; ver docstring de mastri.py)
em vez de duplicar o mesmo algoritmo, e implementa so a parte que
distingue os dois metodos: a fase VNS. Isso isola exatamente o efeito
marginal do VNS sobre uma construcao identica -- uma comparacao mais limpa
do que teria se as duas construcoes fossem reimplementadas de forma
levemente diferente por acidente.

RESSALVA HONESTA (mesmo espirito da ressalva em mastri.py): sem o texto
completo do artigo, os seguintes detalhes NAO estao verificados contra a
fonte original -- sao escolhas de engenharia razoaveis, documentadas aqui,
nao uma reproducao fiel confirmada:
  - Se a construcao TSH do artigo tem alguma diferenca nao capturada pela
    descricao curta acima (ex.: uma restricao geometrica tipo Delaunay,
    igual ao MASTRI original -- nao aplicavel aqui pelo mesmo motivo: as
    instancias disponiveis sao matrizes de distancia abstratas, sem
    coordenadas).
  - A ordem de exploracao das vizinhancas Reverse/Shift dentro do VNS, o
    mecanismo exato de shake, o criterio de parada e quaisquer parametros
    numericos (tamanho de bloco do Or-opt, profundidade da busca local)
    nao sao especificados nos documentos do projeto. Usamos uma variante
    "VNS basico" padrao da literatura (Mladenovic & Hansen) com parametros
    default documentados abaixo, nao os do artigo original.
Se o Carlos conseguir acesso ao paper depois, vale revisar este modulo
contra o texto real e ajustar o que divergir.

Adaptacao ao modo abstrato: identica a de mastri.py -- vizinhancas operam
sobre a ORDEM DE GRUPOS (nao cidades), avaliadas com o mesmo grafo completo
de grupos (`construir_grafo_grupos`, peso = menor distancia entre pares de
cidades). A seleccao final de cidade representante por grupo (e o FO real
reportado) usa `escolher_cidades_e_fo`, so uma vez, no final -- durante a
busca local usamos o custo PROXY (soma dos pesos de grupo ao longo do
ciclo) por velocidade, a mesma convencao ja usada pela construcao MST tanto
do MASTRI quanto deste modulo. Precedencia: TSH+VNS, como o MASTRI e como
os outros 4 artigos da linhagem CPDP aplicada (ver docs/04_verdade_atual.md),
NAO modela Pi -- calculamos a ordem "as-is" e reportamos violacoes
separadamente, mesma convencao de `mastri.py::_viol_precedencia`.

Nota de arquitetura: autocontido dentro deste projeto (so importa de
`mastri.py`, mesmo diretorio -- nao de C:\Pesquisas\LCPP-main).
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import networkx as nx

from mastri import (
    INF,
    parse_pcglns,
    _dist,
    construir_grafo_grupos,
    _tour_mastri_sobre_grafo,
    escolher_cidades_e_fo,
    _viol_precedencia,
)

# Parametros default do VNS -- engenharia propria (ver RESSALVA HONESTA
# acima), nao extraidos do paper original.
_TEMPO_LIMITE_PADRAO_S = 5.0
_MAX_SEM_MELHORA_PADRAO = 30
_TAM_BLOCO_OR_OPT = (1, 2, 3)  # tamanhos de bloco testados pelo operador Shift


# =============================================================================
# Custo proxy (mesma convencao de peso de `construir_grafo_grupos`)
# =============================================================================

def _peso(G: nx.Graph, a, b) -> float:
    if a == b:
        return 0.0
    if G.has_edge(a, b):
        return G[a][b]["weight"]
    return INF


def custo_ciclo(ordem: List, G: nx.Graph) -> float:
    """Soma dos pesos de grupo ao longo do ciclo fechado (volta ao inicio) --
    mesmo proxy usado implicitamente pela etapa de MST/matching da
    construcao. E' o objetivo otimizado pela busca local -- o FO REAL
    (baseado em cidades escolhidas) so' e' recalculado uma vez no final,
    via `escolher_cidades_e_fo`."""
    if len(ordem) < 2:
        return 0.0
    total = 0.0
    for i in range(len(ordem)):
        total += _peso(G, ordem[i], ordem[(i + 1) % len(ordem)])
    return total


# =============================================================================
# Vizinhanca N1: Reverse (2-opt classico)
# =============================================================================

def _delta_2opt(ordem: List, G: nx.Graph, i: int, j: int) -> float:
    """Delta de custo ao reverter o segmento ordem[i+1..j] (2-opt padrao,
    i<j). Substitui as arestas (i,i+1) e (j,j+1) por (i,j) e (i+1,j+1)."""
    n = len(ordem)
    a, b = ordem[i], ordem[(i + 1) % n]
    c, d = ordem[j], ordem[(j + 1) % n]
    antes = _peso(G, a, b) + _peso(G, c, d)
    depois = _peso(G, a, c) + _peso(G, b, d)
    return depois - antes


def busca_local_2opt(ordem: List, G: nx.Graph, deadline: float) -> Tuple[List, float]:
    """Descida por melhor-melhora (best-improvement) em 2-opt ate' otimo
    local ou deadline. O(n^2) por passada -- trivial para n<=120 (maior
    contagem de grupos vista nas 48 instancias, ver 06_plano_desenvolvimento.md
    Secao 1.3)."""
    n = len(ordem)
    melhorou = True
    while melhorou and time.time() < deadline:
        melhorou = False
        melhor_delta, melhor_par = -1e-9, None
        for i in range(n - 1):
            for j in range(i + 1, n):
                if j == i + 1:
                    continue  # segmento de tamanho 0, sem efeito
                d = _delta_2opt(ordem, G, i, j)
                if d < melhor_delta:
                    melhor_delta, melhor_par = d, (i, j)
            if time.time() >= deadline:
                break
        if melhor_par is not None:
            i, j = melhor_par
            ordem = ordem[:i + 1] + list(reversed(ordem[i + 1:j + 1])) + ordem[j + 1:]
            melhorou = True
    return ordem, custo_ciclo(ordem, G)


def shake_2opt(ordem: List, rng: random.Random) -> List:
    """Perturbacao aleatoria N1: reverte um segmento aleatorio (nao trivial)."""
    n = len(ordem)
    if n < 4:
        return list(ordem)
    i = rng.randrange(0, n - 1)
    j = rng.randrange(i + 2, n) if i + 2 < n else i + 2
    j = min(j, n - 1)
    if j <= i + 1:
        return list(ordem)
    return ordem[:i + 1] + list(reversed(ordem[i + 1:j + 1])) + ordem[j + 1:]


# =============================================================================
# Vizinhanca N2: Shift (Or-opt classico -- move bloco de 1-3 grupos)
# =============================================================================

def _remover_bloco(ordem: List, i: int, tam: int) -> Tuple[List, List]:
    n = len(ordem)
    bloco = [ordem[(i + k) % n] for k in range(tam)]
    resto = [ordem[k] for k in range(n) if k not in {(i + t) % n for t in range(tam)}]
    return bloco, resto


def busca_local_or_opt(ordem: List, G: nx.Graph, deadline: float) -> Tuple[List, float]:
    """Descida por melhor-melhora em Or-opt (blocos de tamanho 1-3,
    reinsercao nas duas orientacoes) ate' otimo local ou deadline."""
    melhorou = True
    while melhorou and time.time() < deadline:
        melhorou = False
        n = len(ordem)
        if n < 5:
            break
        melhor_delta, melhor_mov = -1e-9, None
        for tam in _TAM_BLOCO_OR_OPT:
            if tam >= n - 2:
                continue
            for i in range(n):
                bloco, resto = _remover_bloco(ordem, i, tam)
                # custo antes: arestas que cercam o bloco no ciclo original
                prev_idx = (i - 1) % n
                next_idx = (i + tam) % n
                a, d = ordem[prev_idx], ordem[next_idx]
                antes_remocao = (
                    _peso(G, a, bloco[0]) + _peso(G, bloco[-1], d) - _peso(G, a, d)
                )
                for pos in range(len(resto)):
                    p, q = resto[pos - 1 if pos > 0 else -1], resto[pos % len(resto)]
                    if p in bloco or q in bloco:
                        continue
                    base = _peso(G, p, q)
                    for orient in (bloco, list(reversed(bloco))):
                        custo_insercao = (
                            _peso(G, p, orient[0]) + _peso(G, orient[-1], q) - base
                        )
                        delta = custo_insercao - antes_remocao
                        if delta < melhor_delta:
                            melhor_delta = delta
                            melhor_mov = (i, tam, pos, orient)
            if time.time() >= deadline:
                break
        if melhor_mov is not None:
            i, tam, pos, orient = melhor_mov
            bloco, resto = _remover_bloco(ordem, i, tam)
            ordem = resto[:pos] + orient + resto[pos:]
            melhorou = True
    return ordem, custo_ciclo(ordem, G)


def shake_or_opt(ordem: List, rng: random.Random) -> List:
    """Perturbacao aleatoria N2: remove um bloco aleatorio de 1-3 grupos e
    reinsere em posicao aleatoria (orientacao aleatoria)."""
    n = len(ordem)
    if n < 5:
        return list(ordem)
    tam = rng.choice([t for t in _TAM_BLOCO_OR_OPT if t < n - 2])
    i = rng.randrange(0, n)
    bloco, resto = _remover_bloco(ordem, i, tam)
    if rng.random() < 0.5:
        bloco = list(reversed(bloco))
    pos = rng.randrange(0, len(resto) + 1)
    return resto[:pos] + bloco + resto[pos:]


# =============================================================================
# VNS basico (Mladenovic & Hansen) -- k=1 Reverse, k=2 Shift
# =============================================================================

_VIZINHANCAS = [
    (shake_2opt, busca_local_2opt),
    (shake_or_opt, busca_local_or_opt),
]


def vns(G: nx.Graph, raiz, seed: int,
        tempo_limite_s: float = _TEMPO_LIMITE_PADRAO_S,
        max_sem_melhora: int = _MAX_SEM_MELHORA_PADRAO) -> Tuple[List, float, int]:
    """VNS basico sobre a ordem de grupos de um componente conexo. Retorna
    (melhor_ordem, melhor_custo_proxy, n_iteracoes)."""
    rng = random.Random(seed)
    t0 = time.time()
    deadline_total = t0 + tempo_limite_s

    ordem = _tour_mastri_sobre_grafo(G, raiz)  # construcao TSH (= MASTRI, ver docstring)
    melhor_ordem = ordem
    melhor_custo = custo_ciclo(ordem, G)

    sem_melhora = 0
    it = 0
    k_max = len(_VIZINHANCAS)
    while time.time() < deadline_total and sem_melhora < max_sem_melhora:
        k = 0
        while k < k_max and time.time() < deadline_total:
            shake_fn, busca_fn = _VIZINHANCAS[k]
            candidato = shake_fn(melhor_ordem, rng)
            fatia_deadline = min(deadline_total, time.time() + max(0.05, tempo_limite_s / 20))
            candidato, custo_candidato = busca_fn(candidato, G, fatia_deadline)
            if custo_candidato < melhor_custo - 1e-9:
                melhor_ordem, melhor_custo = candidato, custo_candidato
                k = 0
                sem_melhora = 0
            else:
                k += 1
        sem_melhora += 1
        it += 1

    return melhor_ordem, melhor_custo, it


# =============================================================================
# Entrada principal (mesma interface de mastri.py::resolver_mastri)
# =============================================================================

def resolver_tsh_vns(path, seed: int = 0,
                      tempo_limite_s: float = _TEMPO_LIMITE_PADRAO_S,
                      max_sem_melhora: int = _MAX_SEM_MELHORA_PADRAO) -> Dict:
    t0 = time.time()
    parsed = parse_pcglns(path)
    G = construir_grafo_grupos(parsed)

    fo_total = 0.0
    tour_total: List[int] = []
    viol_total = 0
    it_total = 0
    for comp in nx.connected_components(G):
        sub = G.subgraph(comp)
        raiz = parsed["start_group"] if parsed["start_group"] in comp else next(iter(comp))
        # orcamento de tempo proporcional ao tamanho do componente, mesmo
        # total agregado nao ultrapassa tempo_limite_s * n_componentes
        ordem_grupos, _custo_proxy, it = vns(
            sub, raiz, seed=seed,
            tempo_limite_s=tempo_limite_s,
            max_sem_melhora=max_sem_melhora,
        )
        it_total += it
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
        "vns_iteracoes": it_total,
        "seed": seed,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("instancias", nargs="*", help="arquivos .pcglns (default: todas as 48 de instances/ensigndaniels_cpp)")
    ap.add_argument("--tempo-limite", type=float, default=_TEMPO_LIMITE_PADRAO_S, help="segundos de VNS por componente conexo por semente")
    ap.add_argument("--seeds", type=int, default=1, help="numero de sementes (repeticoes independentes) por instancia")
    args = ap.parse_args()

    if args.instancias:
        alvos = [Path(p) for p in args.instancias]
    else:
        base = Path(__file__).resolve().parent / "instances" / "ensigndaniels_cpp"
        alvos = sorted(base.rglob("*.pcglns"))

    resultados = []
    for fp in alvos:
        for s in range(args.seeds):
            r = resolver_tsh_vns(fp, seed=s, tempo_limite_s=args.tempo_limite)
            resultados.append(r)
            print(f"{r['name']:<20} seed={s:<2} FO={r['fo']:>14.2f}  grupos={r['n_grupos']:>4}  "
                  f"pares={r['n_pares']:>4}  viol={r['violacoes']:>3}  it={r['vns_iteracoes']:>4}  t={r['tempo_s']:.3f}s")

    if len(resultados) > 1:
        print(f"\nTotal: {len(alvos)} instancias x {args.seeds} sementes = {len(resultados)} execucoes, "
              f"{sum(r['violacoes'] for r in resultados)} violacoes de Pi no total "
              f"(esperado > 0 -- TSH+VNS, como o MASTRI, nao modela precedencia, ver docstring do modulo), "
              f"tempo total {sum(r['tempo_s'] for r in resultados):.1f}s")
