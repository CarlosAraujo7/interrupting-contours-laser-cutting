"""
vns_zhang_pi.py  --  EXTENSAO (nossa, NAO do artigo) do VNS de Zhang et al. (2024) que RESPEITA a precedencia Pi
================================================================================================================
O VNS de Zhang, Yao, Liu, Wei & Zhang (2024) (`vns_zhang.py`, fiel ao artigo) resolve o GTSP SEM precedencia; ao
rodar nas instancias PCGTSP o resultado viola Pi (~20 pares em media nas 48 instancias, ver
`comparacao_vns_zhang.csv`) e por isso NAO e comparavel ao PCGLNS (que garante 0 violacoes). Este modulo e a variante
VIAVEL: mesma estrutura (NearestFirst -> Shake -> LocalSearch com os 7 operadores, Algoritmos 3-6 do artigo), mas
TODA solucao visitada satisfaz Pi. Escrita em 02/10/2026; reimplementacao independente (a mesma ideia existe no
`vns_zhang_fiel.py` do LCPP-main, "extensao declarada" dele; nao foi copiado nem importado).

ESCOLHAS (todas rotuladas -- nada disto esta no artigo)
  1. Convencao PCGTSP: o tour comeca no `start_group` (posicao 0 fixa; o ponto desse grupo ainda pode ser trocado por
     Change/Nearest/Double) e Pi e avaliado nessa ordem (pred antes de suc a partir do inicio), a mesma de
     `mastri._viol_precedencia`. O ciclo e lido num unico sentido.
  2. Construcao `NearestFirst-Pi`: comeca num ponto aleatorio do `start_group` (em vez de grupo aleatorio) e, a cada
     passo, so considera grupos cujos predecessores ja foram visitados; escolhe o ponto mais proximo do ultimo.
  3. Operadores que NAO mudam a ordem dos grupos (Change, Nearest replace, Farthest replace, Double replace) sao os do
     artigo, sem alteracao (reaproveitados de `vns_zhang._melhores_movimentos`): preservam a viabilidade.
  4. Swap / Reverse / Shift no LocalSearch: sao enumerados TODOS os movimentos que nao mexem na posicao 0 e so' contam os
     VIAVEIS (teste O(1) por movimento a partir de posicoes pre-calculadas; validado contra checagem completa em
     `_validar_pi`). Shift ganha o alvo "fim da sequencia" (equivalente ao alvo 'a frente do primeiro ponto', que no ciclo
     fixo-no-inicio cai na posicao 0). Perde-se a fracao ~2/n dos movimentos que trocariam o ponto da posicao 0.
  5. Shake: cada uma das `max_shake` aplicacoes sorteia o operador/posicoes como no artigo, mas so aceita se a solucao
     continuar viavel; tenta ate 5 sorteios por aplicacao (sem sorteio viavel, nao aplica nada).
  6. Custo/FO: DIRECIONAL, ciclo fechado, com a matriz do `.pcglns` (arco proibido = custo infinito) -- o objetivo que o
     PCGLNS otimiza. DIFERE do `vns_zhang.py` (simetrizado min(d(a,b),d(b,a))): em 37 das 48 instancias a matriz so e
     assimetrica nos arcos proibidos (que codificam Pi) e os dois custos coincidem em solucoes viaveis; nas outras 11
     (familias P5XJ, p1xj/P1xl, p7xj...) ha assimetria FINITA em ate ~90% dos pares e o custo simetrizado SUBESTIMA o
     direcional. Por isso os deltas aqui sao direcionais (Reverse soma os arcos internos nos dois sentidos; Swap adjacente
     inclui o arco do meio).

Interface: `resolver_vns_zhang_pi(path, seed=0, tempo_limite_s=10.0, max_sem_melhora=10000) -> dict` (mesmas chaves
de `vns_zhang.resolver_vns_zhang`; `violacoes` e recalculado de forma independente e DEVE ser 0; `fo_direcional` = custo do
ciclo com a matriz direcional do `.pcglns` (a mesma convencao do "Tour Cost" do PCGLNS, conferida em e1x_7_m: ciclo fechado,
1732) e DEVE coincidir com `fo`: numa solucao viavel nenhum arco proibido e usado).
"""
from __future__ import annotations

import random
import time
from pathlib import Path
from typing import Dict, List, Optional

import vns_zhang as vz
from mastri import parse_pcglns, _viol_precedencia, _dist

INF = float("inf")
OPERADORES = vz.OPERADORES
_POSICIONAIS = ("swap", "reverse", "shift")        # os que mudam a ordem dos grupos


class _InstanciaPi(vz._Instancia):
    def __init__(self, parsed: Dict):
        super().__init__(parsed)
        self.start: int = parsed["start_group"]
        gs = set(self.grupos)
        self.pares = [(a, b) for a, b in parsed["pares"] if a in gs and b in gs]
        self.preds: Dict[int, List[int]] = {g: [] for g in self.grupos}
        self.succs: Dict[int, List[int]] = {g: [] for g in self.grupos}
        for a, b in self.pares:
            self.succs[a].append(b)
            self.preds[b].append(a)
        if self.preds[self.start]:
            raise ValueError("start_group com predecessores em Pi: instancia inviavel para esta convencao")

    def d(self, a: int, b: int) -> float:
        """Distancia DIRECIONAL a->b da matriz do .pcglns (INF se o arco e proibido)."""
        return _dist(self._m, a, b)


# ------------------------------------------------------------------ viabilidade
def _canonizar(S: List[int], inst: _InstanciaPi) -> List[int]:
    """Gira o ciclo para que o ponto do start_group fique na posicao 0 (mesmo sentido)."""
    k = next(i for i, c in enumerate(S) if inst.grupo_da_cidade[c] == inst.start)
    return S if k == 0 else S[k:] + S[:k]


def _viavel(S: List[int], inst: _InstanciaPi) -> bool:
    """Checagem completa (O(n + |Pi|)) de Pi na ordem de S (S ja canonizada)."""
    pos = {inst.grupo_da_cidade[c]: k for k, c in enumerate(S)}
    return all(pos[a] < pos[b] for a, b in inst.pares)


def _viavel_completo(S: List[int], inst: _InstanciaPi) -> bool:
    """Pi satisfeita E nenhum arco proibido no ciclo (custo direcional finito)."""
    return _viavel(S, inst) and vz._custo(S, inst) < INF


def _nearest_first_pi(inst: _InstanciaPi, rng: random.Random) -> List[int]:
    S = [rng.choice(inst.cidades_do_grupo[inst.start])]
    visitados = {inst.start}
    restantes = set(inst.grupos) - visitados
    while restantes:
        disp = [g for g in restantes if all(p in visitados for p in inst.preds[g])]
        if not disp:                                      # nao ocorre se Pi e um DAG (todas as 48 instancias sao)
            raise ValueError("Pi cíclica ou inconsistente: nenhum grupo disponivel")
        ultimo = S[-1]
        melhor, mc = None, INF
        for g in disp:
            for c in inst.cidades_do_grupo[g]:
                dc = inst.d(ultimo, c)
                if dc < mc:
                    melhor, mc = c, dc
        if melhor is None:                                # grupos disponiveis sem arco finito
            melhor = inst.cidades_do_grupo[disp[0]][0]
        S.append(melhor)
        g = inst.grupo_da_cidade[melhor]
        visitados.add(g)
        restantes.discard(g)
    return S


def _arrays_pos(S: List[int], inst: _InstanciaPi):
    """Para cada posicao k: minsucc[k] = menor posicao entre os sucessores do grupo em k (n+1 se nenhum);
    maxpred[k] = maior posicao entre os predecessores (-1 se nenhum); M[i] = min_{k>=i} minsucc[k]."""
    n = len(S)
    gpos = {inst.grupo_da_cidade[c]: k for k, c in enumerate(S)}
    minsucc, maxpred = [n + 1] * n, [-1] * n
    for k, c in enumerate(S):
        g = inst.grupo_da_cidade[c]
        ss = inst.succs[g]
        if ss:
            minsucc[k] = min(gpos[s] for s in ss)
        pp = inst.preds[g]
        if pp:
            maxpred[k] = max(gpos[p] for p in pp)
    M = [n + 1] * (n + 1)
    for i in range(n - 1, -1, -1):
        M[i] = min(minsucc[i], M[i + 1])
    return minsucc, maxpred, M


# ------------------------------------------------------------------ shift com alvo "fim"
def _delta_shift_pi(S, i, j, d):
    """Delta de mover o ponto da posicao i para a FRENTE do ponto da posicao j; j == n significa 'ao fim'
    (entre S[n-1] e S[0] no ciclo)."""
    n = len(S)
    p, a, b = S[i], S[(i - 1) % n], S[(i + 1) % n]
    q, qp = S[j % n], S[(j - 1) % n]
    return d(a, b) - d(a, p) - d(p, b) + d(qp, p) + d(p, q) - d(qp, q)


def _op_shift_pi(S, i, j):
    n = len(S)
    if j == n:
        return S[:i] + S[i + 1:] + [S[i]]
    return vz._op_shift(S, i, j)


def _delta_swap_a(S, i, j, d):
    """Delta DIRECIONAL de trocar as posicoes i<j (1 <= i; j <= n-1, entao nunca ha adjacencia ciclica)."""
    n = len(S)
    p, q = S[i], S[j]
    ai, bj = S[i - 1], S[(j + 1) % n]
    if j == i + 1:
        return d(ai, q) + d(q, p) + d(p, bj) - d(ai, p) - d(p, q) - d(q, bj)
    bi, aj = S[i + 1], S[j - 1]
    return (d(ai, q) + d(q, bi) - d(ai, p) - d(p, bi)) + (d(aj, p) + d(p, bj) - d(aj, q) - d(q, bj))


def _prefixos_arcos(S, d):
    """F[k] = soma dos arcos S[t]->S[t+1], t<k; B[k] = idem no sentido inverso (S[t+1]->S[t]); Bi[k] = quantos arcos
    inversos sao proibidos (somados como 0 em B). Arcos diretos proibidos nao ocorrem (S viavel e finita)."""
    n = len(S)
    F, B, Bi = [0.0] * n, [0.0] * n, [0] * n
    for t in range(n - 1):
        f, b = d(S[t], S[t + 1]), d(S[t + 1], S[t])
        F[t + 1] = F[t] + f
        if b == INF:
            B[t + 1], Bi[t + 1] = B[t], Bi[t] + 1
        else:
            B[t + 1], Bi[t + 1] = B[t] + b, Bi[t]
    return F, B, Bi


def _delta_reverse_a(S, i, j, d, F, B, Bi):
    """Delta DIRECIONAL de inverter o intervalo i..j (1 <= i < j <= n-1); INF se algum arco interno invertido e proibido."""
    if Bi[j] - Bi[i]:
        return INF
    n = len(S)
    a, b = S[i - 1], S[(j + 1) % n]
    return d(a, S[j]) + d(S[i], b) - d(a, S[i]) - d(S[j], b) + (B[j] - B[i]) - (F[j] - F[i])


def _melhores_movimentos_pi(S: List[int], op: str, inst: _InstanciaPi, custo_atual: float):
    """Como `vz._melhores_movimentos`, mas Swap/Reverse/Shift so consideram movimentos VIAVEIS e que nao mexem na posicao 0."""
    if op not in _POSICIONAIS:
        return vz._melhores_movimentos(S, op, inst, custo_atual)
    n = len(S)
    d = inst.d
    minsucc, maxpred, M = _arrays_pos(S, inst)
    melhor, md = None, INF
    F = B = Bi = None
    if op == "reverse":
        F, B, Bi = _prefixos_arcos(S, d)
    if op == "swap":
        for i in range(1, n):
            ms = minsucc[i]
            for j in range(i + 1, n):
                if ms > j and maxpred[j] < i:
                    dl = _delta_swap_a(S, i, j, d)
                    if dl < md:
                        md, melhor = dl, ("swap", i, j)
    elif op == "reverse":
        for i in range(1, n):
            lim = M[i]                                    # reverse(i, j) viavel sse j < lim
            for j in range(i + 1, min(n, lim)):
                dl = _delta_reverse_a(S, i, j, d, F, B, Bi)
                if dl < md:
                    md, melhor = dl, ("reverse", i, j)
    else:  # shift
        for i in range(1, n):
            ms, mp = minsucc[i], maxpred[i]
            for j in range(1, n + 1):
                if j == i or j == i + 1:                  # nao muda a sequencia
                    continue
                if (j > i and ms < j) or (j < i and mp >= j):
                    continue
                dl = _delta_shift_pi(S, i, j, d)
                if dl < md:
                    md, melhor = dl, ("shift", i, j)
    if melhor is None:
        return None, INF
    tipo = melhor[0]
    T = (vz._op_swap(S, melhor[1], melhor[2]) if tipo == "swap" else
         vz._op_reverse(S, melhor[1], melhor[2]) if tipo == "reverse" else
         _op_shift_pi(S, melhor[1], melhor[2]))
    return T, custo_atual + md


def _local_search_pi(S, inst, rng, deadline):
    ordem = list(OPERADORES)
    rng.shuffle(ordem)
    custo = vz._custo(S, inst)
    k = 0
    while k < len(ordem) and time.time() < deadline:
        T, c = _melhores_movimentos_pi(S, ordem[k], inst, custo)
        if T is not None and c < custo - 1e-9:
            S, custo, k = T, c, 0
        else:
            k += 1
    return S


def _shake_pi(S, inst, rng, max_shake: int = 10, tentativas: int = 5):
    n = len(S)
    for _ in range(max_shake):
        for _t in range(tentativas):
            op = rng.choice(("change", "swap", "reverse", "shift"))
            i = rng.randrange(n)
            if op == "change":
                alt = [c for c in inst.cidades_do_grupo[inst.grupo_da_cidade[S[i]]] if c != S[i]]
                if not alt:
                    continue
                T = vz._op_change(S, i, rng.choice(alt))
            else:
                j = rng.randrange(n)
                T = {"swap": vz._op_swap, "reverse": vz._op_reverse, "shift": vz._op_shift}[op](S, i, j)
                if T is not None:
                    T = _canonizar(T, inst)
            if T is not None and _viavel_completo(T, inst):
                S = T
                break
    return S


def vns_pi(inst: _InstanciaPi, seed: int, tempo_limite_s: float, max_sem_melhora: int):
    rng = random.Random(seed)
    t0 = time.time()
    deadline = t0 + tempo_limite_s
    S = _nearest_first_pi(inst, rng)
    custo = vz._custo(S, inst)
    sem_melhora, it = 0, 0
    while sem_melhora < max_sem_melhora and time.time() < deadline:
        it += 1
        Sp = _local_search_pi(_shake_pi(S, inst, rng), inst, rng, deadline)
        cp = vz._custo(Sp, inst)
        if cp < custo - 1e-9:
            S, custo, sem_melhora = Sp, cp, 0
        else:
            sem_melhora += 1
    return S, custo, it


def resolver_vns_zhang_pi(path, seed: int = 0, tempo_limite_s: float = 10.0, max_sem_melhora: int = 10000) -> Dict:
    t0 = time.time()
    parsed = parse_pcglns(path)
    inst = _InstanciaPi(parsed)
    S, custo, it = vns_pi(inst, seed, tempo_limite_s, max_sem_melhora)
    ordem_grupos = [inst.grupo_da_cidade[c] for c in S]
    m, n = parsed["matrix"], len(S)
    fo_dir = sum(_dist(m, S[k], S[(k + 1) % n]) for k in range(n))   # ciclo com a matriz DIRECIONAL (INF se usar arco proibido)
    return {"name": parsed["name"], "fo": custo, "tour": S, "n_grupos": len(inst.grupos), "n_pares": len(parsed["pares"]),
            "violacoes": _viol_precedencia(ordem_grupos, parsed["pares"]), "tempo_s": time.time() - t0,
            "vns_iteracoes": it, "seed": seed, "fo_direcional": fo_dir}


# ------------------------------------------------------------------ autoteste
def _validar_pi(n_testes: int = 400, seed: int = 0) -> None:
    """Instancias aleatorias com matriz ASSIMETRICA (custos finitos diferentes nos dois sentidos) e arcos proibidos
    codificando Pi (de cada cidade do grupo sucessor para as do predecessor, como nos `.pcglns`). Confere:
    (1) o teste O(1) de viabilidade de swap/reverse/shift == checagem completa de Pi;
    (2) os deltas DIRECIONAIS de swap/reverse/shift (e shift 'ao fim') == recalculo do ciclo; delta INF <=> ciclo INF;
    (3) a construcao NearestFirst-Pi e viavel; (4) Change/Nearest/Double preservam Pi e seus deltas batem."""
    rng = random.Random(seed)
    feitos = 0
    while feitos < n_testes:
        n = rng.randint(4, 10)
        ordem_topo = list(range(2, n + 1))
        rng.shuffle(ordem_topo)
        ordem_topo = [1] + ordem_topo                       # grupo 1 e o inicial e vem primeiro
        pares = [(ordem_topo[a], ordem_topo[b]) for a in range(1, n) for b in range(a + 1, n) if rng.random() < 0.25]
        group_cities = {g: [g, g + n] for g in range(1, n + 1)}   # 2 pontos por grupo
        city_group = {c: g for g, cs in group_cities.items() for c in cs}
        pts = {c: (rng.random(), rng.random()) for c in range(1, 2 * n + 1)}
        eu = lambda a, b: ((pts[a][0] - pts[b][0]) ** 2 + (pts[a][1] - pts[b][1]) ** 2) ** 0.5
        matrix = [[eu(a, b) * (1 + 0.5 * rng.random()) for b in range(1, 2 * n + 1)] for a in range(1, 2 * n + 1)]   # assimetrica
        for pa, sb in pares:                                # arcos proibidos: do sucessor para o predecessor
            for cs in group_cities[sb]:
                for cp in group_cities[pa]:
                    matrix[cs - 1][cp - 1] = -1.0
        parsed = {"dim": 2 * n, "matrix": matrix, "city_group": city_group, "group_cities": group_cities,
                  "pares": pares, "start_group": 1, "name": "t"}
        inst = _InstanciaPi(parsed)
        S = _nearest_first_pi(inst, rng)
        assert _viavel(S, inst) and inst.grupo_da_cidade[S[0]] == 1, "construcao inviavel"
        d = inst.d
        cyc = lambda T: sum(d(T[k], T[(k + 1) % n]) for k in range(n))
        c0 = cyc(S)
        if c0 == INF:                                       # fechamento proibido: instancia de teste invalida, sorteia outra
            continue
        feitos += 1
        minsucc, maxpred, M = _arrays_pos(S, inst)
        F, B, Bi = _prefixos_arcos(S, d)

        def confere(nome, T, delta, viab_formula, ctx):
            assert sorted(T) == sorted(S) and T[0] == S[0], (nome, "permutacao", ctx)
            Tc = _canonizar(T, inst)
            assert viab_formula == _viavel(Tc, inst), (nome, "viabilidade Pi", ctx, pares)
            cT = cyc(T)
            if cT == INF:
                assert delta == INF, (nome, "delta deveria ser INF", ctx, delta)
            else:
                assert delta != INF and abs(cT - c0 - delta) < 1e-9, (nome, "delta", ctx, cT - c0, delta)

        for i in range(1, n):
            for j in range(i + 1, n):
                confere("swap", vz._op_swap(S, i, j), _delta_swap_a(S, i, j, d), minsucc[i] > j and maxpred[j] < i, (S, i, j))
                confere("reverse", vz._op_reverse(S, i, j), _delta_reverse_a(S, i, j, d, F, B, Bi), j < M[i], (S, i, j))
            for j in range(1, n + 1):
                if j == i or j == i + 1:
                    continue
                inviavel = (j > i and minsucc[i] < j) or (j < i and maxpred[i] >= j)
                confere("shift", _op_shift_pi(S, i, j), _delta_shift_pi(S, i, j, d), not inviavel, (S, i, j))
        for op in ("change", "nearest", "farthest", "double"):
            T, c = vz._melhores_movimentos(S, op, inst, c0)
            if T is not None:
                assert _viavel(_canonizar(T, inst), inst), (op, S, T)
                if cyc(T) != INF:
                    assert abs(cyc(T) - c) < 1e-9, (op, "delta", S, T, cyc(T), c)
    print(f"_validar_pi OK ({n_testes} instancias aleatorias assimetricas, com arcos proibidos)")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("instancias", nargs="*")
    ap.add_argument("--tempo-limite", type=float, default=10.0)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--validar", action="store_true")
    a = ap.parse_args()
    if a.validar:
        _validar_pi()
        raise SystemExit
    alvos = [Path(p) for p in a.instancias] or sorted((Path(__file__).resolve().parent / "instances" / "ensigndaniels_cpp").rglob("*.pcglns"))
    for fp in alvos:
        for s in range(a.seeds):
            r = resolver_vns_zhang_pi(fp, seed=s, tempo_limite_s=a.tempo_limite)
            print(f"{r['name']:<20} seed={s:<2} FO={r['fo']:>14.2f} grupos={r['n_grupos']:>4} pares={r['n_pares']:>4} "
                  f"viol={r['violacoes']:>3} it={r['vns_iteracoes']:>5} t={r['tempo_s']:.2f}s")
