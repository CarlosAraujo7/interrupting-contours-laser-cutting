"""
heuristica_ls.py  --  HEURISTICA PROPOSTA = construtiva (LCA + Pi) + BUSCA LOCAL sobre o tour de pecas   (aprovado por Carlos em 05/10/2026)
===========================================================================================================================================
Estagio 1 (construcao): `heuristic_core.run_heuristic(..., enforce_precedence=True)` -- a heuristica do LCPP (arvore com LCA/MST, ordem dos filhos,
vertice de entrada `nearest`), que ja garante Pi.
Estagio 2 (pos-otimizacao, NOVO; ver continuacao 85 do log): o caminho do estagio 1 e convertido no TOUR de pecas (peca, vertice de entrada) e
refinado pela busca local do VNS-Pi (`vns_zhang_pi`: operadores Change / Swap / Reverse / Shift / Nearest, Double e Farthest replace, SO movimentos
que mantem Pi e que nao usam arco proibido). Duas variantes:
  modo "ls"  -- uma DESCIDA (busca local ate nenhum operador melhorar; a ordem dos operadores e sorteada pela semente);
  modo "vns" -- VNS (Shake + descida, como no `vns_zhang_pi`) por `tempo` segundos a partir do tour do estagio 1.
Por que: a investigacao `investigar_gap_ea0.py` mostrou que o gap de ~0,7% da construcao para o PCGLNS vem da ORDEM das pecas nao ser localmente
otima (otimizar so os vertices de entrada recupera 19% do gap; a busca local sobre o tour, 73%; +5 s de VNS, 82%), e que a busca local da
heuristica original atua na arvore e nao no tour.
Limitacoes declaradas: o estagio 2 trabalha no nivel de PECA INTEIRA (cada contorno cortado de uma vez) e portanto NAO explora o espaco de segmentos /
tecnicas especiais em que a heuristica original pode ter vantagem (categoria p7 do CPPLib); os operadores sao a extensao VNS-Pi (nossa) do VNS de
Zhang et al. (2024). O resultado e SEMPRE viavel quanto a Pi (assercao).
"""
import os
import random
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import ea0_lib as lib
import heuristic_core as hc
import vns_zhang_pi as vp


def vns_a_partir_de(inst_pi, S0, seed, tempo):
    """Laco do VNS-Pi (Shake + LocalSearch) partindo de S0 (em vez do NearestFirst-Pi), por `tempo` segundos."""
    rng = random.Random(seed)
    deadline = time.time() + tempo
    S = list(S0)
    custo = vp.vz._custo(S, inst_pi)
    while time.time() < deadline:
        Sp = vp._local_search_pi(vp._shake_pi(S, inst_pi, rng), inst_pi, rng, deadline)
        cp = vp.vz._custo(Sp, inst_pi)
        if cp < custo - 1e-9:
            S, custo = Sp, cp
    return S


def rodar(polys, inst, seed, modo, tempo=5.0, limite_construcao_s=60):
    """-> dict(tour_construcao, tour, t_construcao_s, t_pos_s, fo_nativa_construcao). `tour` = tour final (ids de cidade 1-based, inicia na origem)."""
    assert modo in ("ls", "vns")
    t0 = time.time()
    res = hc.run_heuristic(list(polys), {**lib.CFG_BASE, "time_limit": limite_construcao_s, "enforce_precedence": True})
    t_constr = time.time() - t0
    if not res["caminho"]:
        return {"tour": None, "tour_construcao": None, "t_construcao_s": t_constr, "t_pos_s": 0.0, "timeout": True}
    tourA = lib.tour_de_caminho(polys, inst, res["caminho"])
    inst_pi = vp._InstanciaPi(lib.parsed_de_instancia(inst))
    t1 = time.time()
    if modo == "ls":
        S = vp._local_search_pi(list(tourA), inst_pi, random.Random(seed), time.time() + limite_construcao_s)
    else:
        S = vns_a_partir_de(inst_pi, tourA, seed, tempo)
    t_pos = time.time() - t1
    assert lib.violacoes(inst, S) == 0, "pos-otimizacao violou Pi"
    return {"tour": S, "tour_construcao": tourA, "t_construcao_s": t_constr, "t_pos_s": t_pos, "fo_nativa_construcao": float(res["fo_total"]), "timeout": False}
