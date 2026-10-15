"""
vns_zhang.py  --  VNS do modelo de NOS (GTSP) de Zhang, Yao, Liu, Wei & Zhang (2024), versao FIEL ao artigo
================================================================================================================
Reimplementacao INDEPENDENTE (escrita em 02/10/2026 a partir do texto do artigo, PDF em `Artigos/`:
*Heuristic approaches for the cutting path problem*, Expert Systems With Applications 237:121567, Secao 4.2,
Algoritmos 3-6 e Figura 6). NAO copia nem importa `LCPP-main/pcgtsp_comparison/vns_zhang_fiel.py` (regra
do projeto: ler/entender o LCPP-main, mas reimplementar aqui); so reaproveita o parser `.pcglns` e as
funcoes de FO/precedencia de `mastri.py` deste mesmo projeto.

Substitui, como "baseline Zhang et al.", o hibrido proprio de `tsh_vns.py` (construcao do MASTRI + VNS
Reverse/Shift), que NAO e o metodo do artigo (auditoria de 01/10/2026; ver o aviso naquele arquivo).

O QUE O ARTIGO ESPECIFICA (e aqui esta implementado)
  Representacao: sequencia de PONTOS S = (S_1..S_|P|), exatamente um ponto por peca (grupo); a ordem da
  sequencia e a ordem de visita; custo = ciclo fechado (soma das distancias entre consecutivos, mais a volta).
  Sete operadores (Fig. 6):
    Change(p, q)       -- troca o ponto p da peca por outro ponto q da MESMA peca;
    Swap(p, q)         -- troca as posicoes de dois pontos;
    Reverse(p, q)      -- inverte o intervalo entre dois pontos;
    Shift(p, q)        -- move p para a frente de q;
    Nearest replace(p) -- acha o ponto q, de OUTRA peca, mais proximo de p e substitui o ponto atual da peca de q por q;
    Farthest replace(p)-- idem, com o mais distante;
    Double replace(p)  -- sejam p1, p2 os vizinhos de p na sequencia; substitui p1 e p2 por outros pontos de suas
                          proprias pecas, com distancia total minima.
  Construcao NearestFirst (Alg. 4): ponto aleatorio de peca aleatoria; a cada passo, adiciona o ponto de uma peca
  nao visitada mais proximo do ultimo adicionado.
  Shake (Alg. 5): `max_shake` aplicacoes (10): operador entre os 4 primeiros (Change, Swap, Reverse, Shift) com
  igual probabilidade, ponto p aleatorio; Change usa q da mesma peca; os demais, q aleatorio da solucao.
  LocalSearch (Alg. 6): embaralha UMA vez a ordem dos 7 operadores; percorre; para cada operador testa TODOS os
  movimentos possiveis, aplica o MELHOR se melhorar e REINICIA do primeiro operador da mesma ordem; senao passa ao
  proximo; termina quando nenhum operador melhora.
  VNS (Alg. 3): S <- NearestFirst; repete (Shake -> LocalSearch -> aceita se melhor, zera contador; senao conta)
  ate `max_sem_melhora` iteracoes sem melhora (10.000 no artigo) ou limite de tempo (1200 s no artigo).

O QUE O ARTIGO NAO ESPECIFICA (escolhas daqui, rotuladas)
  - O artigo NAO trata precedencia: o resultado e a ordem "como esta", e as violacoes de Pi sao apenas CONTADAS
    (como no MASTRI deste projeto) -- diferente do `vns_zhang_fiel.py` do LCPP-main, que estende o metodo para
    respeitar Pi (extensao declarada dele, nao do artigo).
  - Custo/FO: distancia simetrizada `min(d(a,b), d(b,a))` (a mesma de `mastri.escolher_cidades_e_fo`), para
    comparar com MASTRI/hibrido nas mesmas condicoes.
  - Orcamento: o artigo usa 1200 s / 10.000 iteracoes sem melhora; aqui `tempo_limite_s` e `max_sem_melhora`
    sao parametros (padrao: 10 s e 10.000) -- comparacao de tempo igual entre algoritmos fica a cargo do chamador.
  - "Nearest/Farthest replace": a "peca de q" ganha q como ponto; se q ja e o ponto atual, o movimento e nulo.
  - Em LocalSearch, "melhor movimento do operador" = o de menor custo resultante entre todos os movimentos validos.

Interface: `resolver_vns_zhang(path, seed=0, tempo_limite_s=10.0, max_sem_melhora=10000) -> dict` com as mesmas chaves de
`tsh_vns.resolver_tsh_vns` (name, fo, tour, n_grupos, n_pares, violacoes, tempo_s, vns_iteracoes, seed).
"""
from __future__ import annotations

import random
import time
from pathlib import Path
from typing import Dict, List, Optional

from mastri import parse_pcglns, _viol_precedencia, _dist

INF = float("inf")
OPERADORES = ("change", "swap", "reverse", "shift", "nearest", "double", "farthest")


class _Instancia:
    """Distancias simetrizadas e estruturas de apoio."""

    def __init__(self, parsed: Dict):
        self.parsed = parsed
        self.grupos: List[int] = sorted(parsed["group_cities"])
        self.cidades_do_grupo: Dict[int, List[int]] = parsed["group_cities"]
        self.grupo_da_cidade: Dict[int, int] = parsed["city_group"]
        m = parsed["matrix"]
        self._m = m

    def d(self, a: int, b: int) -> float:
        x, y = _dist(self._m, a, b), _dist(self._m, b, a)
        return x if x < y else y


def _custo(S: List[int], inst: _Instancia) -> float:
    n = len(S)
    return sum(inst.d(S[i], S[(i + 1) % n]) for i in range(n))


def _nearest_first(inst: _Instancia, rng: random.Random) -> List[int]:
    g0 = rng.choice(inst.grupos)
    S = [rng.choice(inst.cidades_do_grupo[g0])]
    nao_visitados = set(inst.grupos) - {g0}
    while nao_visitados:
        ultimo = S[-1]
        melhor, mc = None, INF
        for g in nao_visitados:
            for c in inst.cidades_do_grupo[g]:
                dc = inst.d(ultimo, c)
                if dc < mc:
                    melhor, mc = c, dc
        if melhor is None:                       # grupo sem arco finito: pega qualquer um
            g = next(iter(nao_visitados))
            melhor = inst.cidades_do_grupo[g][0]
        S.append(melhor)
        nao_visitados.discard(inst.grupo_da_cidade[melhor])
    return S


# ---------------------------------------------------------------- operadores (cada um devolve nova sequencia ou None)
def _op_change(S, i, novo):                      # troca o ponto da posicao i por `novo` (mesma peca)
    T = S[:]
    T[i] = novo
    return T


def _op_swap(S, i, j):
    if i == j:
        return None
    T = S[:]
    T[i], T[j] = T[j], T[i]
    return T


def _op_reverse(S, i, j):
    if i == j:
        return None
    if i > j:
        i, j = j, i
    T = S[:]
    T[i:j + 1] = reversed(T[i:j + 1])
    return T


def _op_shift(S, i, j):                          # move o ponto da posicao i para a frente do ponto da posicao j
    if i == j or j == (i + 1) % len(S):
        return None
    T = S[:]
    p = T.pop(i)
    j2 = j if i > j else j - 1                   # indice de q depois da remocao de p
    T.insert(j2, p)
    return T


def _delta_change(S, i, c, d):
    n = len(S)
    a, b, p = S[(i - 1) % n], S[(i + 1) % n], S[i]
    return d(a, c) + d(c, b) - d(a, p) - d(p, b)


def _delta_swap(S, i, j, d):
    """Delta de trocar as posicoes i<j (custo simetrico, ciclo fechado)."""
    n = len(S)
    if (j - i) % n in (1, n - 1):                  # adjacentes (inclui o par ciclico 0 / n-1)
        if (j - i) % n == 1:
            x, y, a, b = S[i], S[j], S[(i - 1) % n], S[(j + 1) % n]
        else:                                      # j == i-1 ciclico: S[j] vem antes de S[i]
            x, y, a, b = S[j], S[i], S[(j - 1) % n], S[(i + 1) % n]
        return d(a, y) + d(x, b) - d(a, x) - d(y, b)
    p, q = S[i], S[j]
    ai, bi, aj, bj = S[(i - 1) % n], S[(i + 1) % n], S[(j - 1) % n], S[(j + 1) % n]
    return (d(ai, q) + d(q, bi) - d(ai, p) - d(p, bi)) + (d(aj, p) + d(p, bj) - d(aj, q) - d(q, bj))


def _delta_reverse(S, i, j, d):
    n = len(S)
    if i == 0 and j == n - 1:
        return 0.0
    a, b = S[(i - 1) % n], S[(j + 1) % n]
    return d(a, S[j]) + d(S[i], b) - d(a, S[i]) - d(S[j], b)


def _delta_shift(S, i, j, d):
    """Delta de mover o ponto da posicao i para a FRENTE do ponto da posicao j."""
    n = len(S)
    p, a, b = S[i], S[(i - 1) % n], S[(i + 1) % n]
    q, qp = S[j], S[(j - 1) % n]
    return d(a, b) - d(a, p) - d(p, b) + d(qp, p) + d(p, q) - d(qp, q)


def _melhores_movimentos(S: List[int], op: str, inst: _Instancia, custo_atual: float):
    """Devolve (melhor_sequencia, melhor_custo) entre TODOS os movimentos do operador `op`, ou (None, INF).
    Change/Swap/Reverse/Shift usam delta O(1) (validado contra recalculo completo em `_validar_deltas`)."""
    n = len(S)
    d = inst.d
    melhor, md = None, INF                       # melhor = descritor do movimento

    if op == "change":
        for i in range(n):
            for c in inst.cidades_do_grupo[inst.grupo_da_cidade[S[i]]]:
                if c != S[i]:
                    dl = _delta_change(S, i, c, d)
                    if dl < md:
                        md, melhor = dl, ("change", i, c)
    elif op == "swap":
        for i in range(n):
            for j in range(i + 1, n):
                dl = _delta_swap(S, i, j, d)
                if dl < md:
                    md, melhor = dl, ("swap", i, j)
    elif op == "reverse":
        for i in range(n):
            for j in range(i + 1, n):
                dl = _delta_reverse(S, i, j, d)
                if dl < md:
                    md, melhor = dl, ("reverse", i, j)
    elif op == "shift":
        for i in range(n):
            for j in range(n):
                if j == i or j == (i + 1) % n:   # nao muda a sequencia
                    continue
                dl = _delta_shift(S, i, j, d)
                if dl < md:
                    md, melhor = dl, ("shift", i, j)
    elif op in ("nearest", "farthest"):
        sinal = 1 if op == "nearest" else -1
        for i in range(n):
            p = S[i]
            gp = inst.grupo_da_cidade[p]
            melhor_q, mq = None, INF
            for g in inst.grupos:
                if g == gp:
                    continue
                for q in inst.cidades_do_grupo[g]:
                    dq = d(p, q)
                    if dq == INF:
                        continue
                    if sinal * dq < mq:
                        melhor_q, mq = q, sinal * dq
            if melhor_q is not None:
                gq = inst.grupo_da_cidade[melhor_q]
                j = next(k for k in range(n) if inst.grupo_da_cidade[S[k]] == gq)
                if S[j] != melhor_q:
                    dl = _delta_change(S, j, melhor_q, d)
                    if dl < md:
                        md, melhor = dl, ("change", j, melhor_q)
    elif op == "double":
        for i in range(n):
            ia, ib = (i - 1) % n, (i + 1) % n
            if ia == ib or n < 4:
                continue
            ant, suc = S[(ia - 1) % n], S[(ib + 1) % n]
            p = S[i]
            melhor_par, mp = None, INF
            for a in inst.cidades_do_grupo[inst.grupo_da_cidade[S[ia]]]:
                for b in inst.cidades_do_grupo[inst.grupo_da_cidade[S[ib]]]:
                    c = d(ant, a) + d(a, p) + d(p, b) + d(b, suc)
                    if c < mp:
                        melhor_par, mp = (a, b), c
            if melhor_par and (melhor_par[0] != S[ia] or melhor_par[1] != S[ib]):
                a0, b0 = S[ia], S[ib]
                dl = mp - (d(ant, a0) + d(a0, p) + d(p, b0) + d(b0, suc))
                if dl < md:
                    md, melhor = dl, ("double", ia, ib, melhor_par)
    if melhor is None:
        return None, INF
    tipo = melhor[0]
    if tipo == "change":
        T = _op_change(S, melhor[1], melhor[2])
    elif tipo == "swap":
        T = _op_swap(S, melhor[1], melhor[2])
    elif tipo == "reverse":
        T = _op_reverse(S, melhor[1], melhor[2])
    elif tipo == "shift":
        T = _op_shift(S, melhor[1], melhor[2])
    else:
        T = S[:]
        T[melhor[1]], T[melhor[2]] = melhor[3]
    return T, custo_atual + md


def _validar_deltas(n_testes: int = 3000, seed: int = 0) -> None:
    """Autoteste: delta O(1) == recalculo completo, em instancias aleatorias (cidades distintas, custo simetrico)."""
    rng = random.Random(seed)
    for _ in range(n_testes):
        n = rng.randint(3, 9)
        pts = {c: (rng.random(), rng.random()) for c in range(1, n + 1)}
        d = lambda a, b: ((pts[a][0] - pts[b][0]) ** 2 + (pts[a][1] - pts[b][1]) ** 2) ** 0.5
        S = list(range(1, n + 1)); rng.shuffle(S)
        cyc = lambda T: sum(d(T[k], T[(k + 1) % n]) for k in range(n))
        i, j = rng.sample(range(n), 2)
        if i > j:
            i, j = j, i
        for nome, fdelta, fop, (x, y) in (("swap", _delta_swap, _op_swap, (i, j)), ("reverse", _delta_reverse, _op_reverse, (i, j)),
                                          ("shift", _delta_shift, _op_shift, (i, j)), ("shift2", _delta_shift, _op_shift, (j, i))):
            if nome.startswith("shift") and (y == x or y == (x + 1) % n):
                continue
            T = fop(S, x, y)
            assert T is not None and sorted(T) == sorted(S), (nome, S, x, y, T)
            assert abs(cyc(T) - cyc(S) - fdelta(S, x, y, d)) < 1e-9, (nome, S, x, y)
    print(f"_validar_deltas OK ({n_testes} testes x 4 operadores)")


def _local_search(S: List[int], inst: _Instancia, rng: random.Random, deadline: float) -> List[int]:
    ordem = list(OPERADORES)
    rng.shuffle(ordem)                           # UMA vez por chamada (Alg. 6)
    custo = _custo(S, inst)
    k = 0
    while k < len(ordem) and time.time() < deadline:
        T, c = _melhores_movimentos(S, ordem[k], inst, custo)
        if T is not None and c < custo - 1e-9:
            S, custo, k = T, c, 0                # aplica o melhor e reinicia do primeiro operador
        else:
            k += 1
    return S


def _shake(S: List[int], inst: _Instancia, rng: random.Random, max_shake: int = 10) -> List[int]:
    n = len(S)
    for _ in range(max_shake):
        op = rng.choice(("change", "swap", "reverse", "shift"))
        i = rng.randrange(n)
        if op == "change":
            alt = [c for c in inst.cidades_do_grupo[inst.grupo_da_cidade[S[i]]] if c != S[i]]
            if not alt:
                continue
            T = _op_change(S, i, rng.choice(alt))
        else:
            j = rng.randrange(n)
            T = {"swap": _op_swap, "reverse": _op_reverse, "shift": _op_shift}[op](S, i, j)
        if T is not None:
            S = T
    return S


def vns(inst: _Instancia, seed: int, tempo_limite_s: float, max_sem_melhora: int):
    rng = random.Random(seed)
    t0 = time.time()
    deadline = t0 + tempo_limite_s
    S = _nearest_first(inst, rng)
    custo = _custo(S, inst)
    sem_melhora, it = 0, 0
    while sem_melhora < max_sem_melhora and time.time() < deadline:
        it += 1
        Sp = _local_search(_shake(S, inst, rng), inst, rng, deadline)
        cp = _custo(Sp, inst)
        if cp < custo - 1e-9:
            S, custo, sem_melhora = Sp, cp, 0
        else:
            sem_melhora += 1
    return S, custo, it


def resolver_vns_zhang(path, seed: int = 0, tempo_limite_s: float = 10.0, max_sem_melhora: int = 10000) -> Dict:
    t0 = time.time()
    parsed = parse_pcglns(path)
    inst = _Instancia(parsed)
    S, custo, it = vns(inst, seed, tempo_limite_s, max_sem_melhora)
    ordem_grupos = [inst.grupo_da_cidade[c] for c in S]
    return {"name": parsed["name"], "fo": custo, "tour": S, "n_grupos": len(inst.grupos), "n_pares": len(parsed["pares"]),
            "violacoes": _viol_precedencia(ordem_grupos, parsed["pares"]), "tempo_s": time.time() - t0,
            "vns_iteracoes": it, "seed": seed}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("instancias", nargs="*")
    ap.add_argument("--tempo-limite", type=float, default=10.0)
    ap.add_argument("--seeds", type=int, default=1)
    a = ap.parse_args()
    alvos = [Path(p) for p in a.instancias] or sorted((Path(__file__).resolve().parent / "instances" / "ensigndaniels_cpp").rglob("*.pcglns"))
    for fp in alvos:
        for s in range(a.seeds):
            r = resolver_vns_zhang(fp, seed=s, tempo_limite_s=a.tempo_limite)
            print(f"{r['name']:<20} seed={s:<2} FO={r['fo']:>14.2f} grupos={r['n_grupos']:>4} pares={r['n_pares']:>4} "
                  f"viol={r['violacoes']:>3} it={r['vns_iteracoes']:>5} t={r['tempo_s']:.2f}s")
