"""
tsh_pi.py  --  TSH com precedencia de FECHAMENTO (Pi "relaxada", a restricao fisica) -- prototipo
==================================================================================================
Semantica (docs/15): um contorno interno i deve FECHAR (seu ultimo segmento ser cortado) antes de o contorno externo o FECHAR; o externo pode ser cortado em varias passadas e comecado antes.
A solucao do TSH e um multigrafo euleriano (arestas requeridas + arestas de ar); TODO passeio euleriano do mesmo multigrafo tem o MESMO custo de ar. Logo, se algum passeio satisfizer a precedencia de
fechamento, a solucao tem o custo do TSH (que e quase otimo SEM Pi). Aqui: passeio de Fleury com PORTAO (um segmento requerido de um contorno so pode ser o ULTIMO desse contorno quando todos os
descendentes ja fecharam) e escolhas aleatorias com reinicios. Se travar em todas as tentativas, o prototipo devolve None (a versao completa precisara alterar o multigrafo).
Uso: ver `rodar_tsh_pi.py`.
"""
import os
import sys
import random
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import tsh_segmento as tsh                                      # noqa: E402


def _multigrafo(polys):
    """-> (coords, req [(u, v)], ar [(u, v)], dono_req {indice de req: [contornos]})"""
    coords, req = tsh.construir_requeridas(polys)
    comp, nc = tsh._componentes(len(coords), req)
    mst = tsh._mst_conecta(coords, comp, nc)
    grau = defaultdict(int)
    for u, v in req + mst:
        grau[u] += 1
        grau[v] += 1
    impares = sorted(v for v, g in grau.items() if g % 2 == 1)
    mt = tsh._matching_paridade(coords, impares)
    # dono de cada aresta requerida (contornos cujo anel contem a aresta)
    pos = {c: i for i, c in enumerate(coords)}
    dono = defaultdict(list)
    chave = {}
    for k, (u, v) in enumerate(req):
        chave[(min(u, v), max(u, v))] = k
    for ci, p in enumerate(polys):
        ring = list(p.exterior.coords)[:-1]
        ids = [pos[(round(float(x), tsh.ND), round(float(y), tsh.ND))] for x, y in ring]
        for i in range(len(ids)):
            u, v = ids[i], ids[(i + 1) % len(ids)]
            if u != v and (min(u, v), max(u, v)) in chave:
                dono[chave[(min(u, v), max(u, v))]].append(ci)
    return coords, req, mst + mt, dono


def _descendentes(n, pares):
    filhos = defaultdict(list)
    for i, j in pares:                      # i (interno) antes de j (externo): i e descendente de j
        filhos[j].append(i)
    desc = {}

    def f(j):
        if j in desc:
            return desc[j]
        s = set()
        for i in filhos.get(j, []):
            s.add(i)
            s |= f(i)
        desc[j] = s
        return s
    for j in range(n):
        f(j)
    return desc


def passeio_fleury(coords, req, ar, dono, desc, rng, max_passos=10 ** 7, info=None):
    """Passeio euleriano de Fleury com portao de fechamento; -> lista de (u, v, tipo, indice) ou None se travar."""
    n = len(coords)
    arestas = [(u, v, "c", k) for k, (u, v) in enumerate(req)] + [(u, v, "d", len(req) + k) for k, (u, v) in enumerate(ar)]
    adj = defaultdict(list)
    for k, (u, v, t, _) in enumerate(arestas):
        adj[u].append(k)
        adj[v].append(k)
    usada = [False] * len(arestas)
    rem = defaultdict(int)                  # arestas requeridas restantes por contorno
    for k in range(len(req)):
        for c in dono[k]:
            rem[c] += 1
    fechado = {c: False for c in range(len(desc))}
    nao_fechados_desc = {c: sum(1 for d in desc[c] if rem[d] > 0) for c in range(len(desc))}

    def gated(k):
        if arestas[k][2] != "c":
            return False
        for c in dono[arestas[k][3]]:
            if rem[c] == 1 and nao_fechados_desc[c] > 0:
                return True
        return False

    def eh_ponte(k, v_atual):
        """k e ponte no grafo das arestas ainda nao usadas, a partir de v_atual? (se a remocao desconecta v_atual das demais arestas)"""
        restantes = [i for i in range(len(arestas)) if not usada[i] and i != k]
        if not restantes:
            return False
        u, w, _, _ = arestas[k]
        outro = w if u == v_atual else u
        # alcancabilidade a partir de `outro` usando arestas nao usadas exceto k: tem de alcancar v_atual-ou-todas as arestas restantes
        alvo = set()
        for i in restantes:
            alvo.add(arestas[i][0])
            alvo.add(arestas[i][1])
        visto = {outro}
        pilha = [outro]
        while pilha:
            x = pilha.pop()
            for i in adj[x]:
                if usada[i] or i == k:
                    continue
                a, b = arestas[i][0], arestas[i][1]
                y = b if a == x else a
                if y not in visto:
                    visto.add(y)
                    pilha.append(y)
        return not alvo.issubset(visto)

    pos, seq = 0, []
    total = len(arestas)
    for _ in range(total):
        cand = [k for k in adj[pos] if not usada[k]]
        if not cand:
            if info is not None:
                info.update(passo=len(seq), total=total, pos=coords[pos], motivo='sem arestas')
            return None
        livres = [k for k in cand if not gated(k)]
        if not livres:
            if info is not None:
                info.update(passo=len(seq), total=total, pos=coords[pos], motivo='todas gated', cand=[(arestas[k][2], coords[arestas[k][0]], coords[arestas[k][1]], list(dono[arestas[k][3]]) if arestas[k][2] == 'c' else None) for k in cand])
            return None
        rng.shuffle(livres)
        # preferir segmentos de corte (continuar cortando) com probabilidade alta, depois nao-pontes
        livres.sort(key=lambda k: (0 if arestas[k][2] == "c" else 1) if rng.random() < 0.7 else 0)
        # lookahead por CADEIA FORCADA: ao entrar num vertice com uma unica aresta restante, a caminhada e forcada; simula a cadeia e recusa se ela esbarrar num segmento gated
        def seguro(k):
            if total - len(seq) == 1:
                return True
            sim = {k}
            rem_sim = dict(rem)
            def consumir(i):
                if arestas[i][2] == "c":
                    for c in dono[arestas[i][3]]:
                        rem_sim[c] = rem_sim.get(c, 0) - 1
            consumir(k)
            u0, v0 = arestas[k][0], arestas[k][1]
            cur = v0 if u0 == pos else u0
            while True:
                restantes = [i for i in adj[cur] if not usada[i] and i not in sim]
                if not restantes:
                    return (total - len(seq) - len(sim)) == 0
                if len(restantes) > 1:
                    # decisao livre: ha alguma aresta nao gated?
                    for i in restantes:
                        if arestas[i][2] != "c" or not any(rem_sim.get(c, 0) == 1 and sum(1 for d in desc[c] if rem_sim.get(d, 0) > 0) > 0 for c in dono[arestas[i][3]]):
                            return True
                    return False
                i = restantes[0]
                if arestas[i][2] == "c" and any(rem_sim.get(c, 0) == 1 and sum(1 for d in desc[c] if rem_sim.get(d, 0) > 0) > 0 for c in dono[arestas[i][3]]):
                    return False
                sim.add(i)
                consumir(i)
                x, y = arestas[i][0], arestas[i][1]
                cur = y if x == cur else x
        escolha = None
        for k in livres:
            if (len(cand) == 1 or not eh_ponte(k, pos)) and seguro(k):
                escolha = k
                break
        if escolha is None:
            seg = [k for k in livres if seguro(k)]
            escolha = seg[0] if seg else livres[0]
        u, v, t, idx = arestas[escolha]
        usada[escolha] = True
        prox = v if u == pos else u
        if t == "c":
            for c in dono[idx]:
                rem[c] -= 1
                if rem[c] == 0:
                    fechado[c] = True
                    for o in range(len(desc)):
                        if c in desc[o]:
                            nao_fechados_desc[o] -= 1
        seq.append((pos, prox, t, idx))
        pos = prox
    if pos != 0:
        return None
    return seq


def resolver_tsh_pi(polys, pares, tentativas=200, semente=0):
    coords, req, ar, dono = _multigrafo(polys)
    desc = _descendentes(len(polys), pares)
    rng = random.Random(semente)
    for t in range(tentativas):
        seq = passeio_fleury(coords, req, ar, dono, desc, rng)
        if seq is not None:
            return {"seq": seq, "coords": coords, "tentativas": t + 1, "ar_cheb": sum(tsh._cheb(coords[u], coords[v]) for u, v in ar), "n_req": len(req)}
    return None
