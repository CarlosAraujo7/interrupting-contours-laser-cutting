"""
reparo_reinicio.py  --  REPARO CIENTE DO CUSTO DE REINICIO da heuristica do LCPP (busca local propria sobre a ORDEM DE SERVICO; docs/23)
==========================================================================================================================================
Entrada: o caminho que a heuristica do LCPP (busca local forte, 3 s) ja devolveu (`auditoria_lcpp1/caminhos_282/<inst>.json`, campo `forte`); so os trechos de corte ('c') em ordem sao usados. Nao se executa nem se importa
codigo do LCPP-main. Objetivo (FO formal, `docs/18` §4): corte + sum(cordas Chebyshev)/v_ar + t * (nº de corridas); uma corrida recomeca sempre que o proximo servico nao comeca onde o anterior terminou; as pernas de/para a
origem custam so o ar. Vizinhancas (delta O(1) por movimento, avaliadas em bloco com numpy): inversao de orientacao de um servico (flip), 2-opt com inversao de subsequencia (as orientacoes internas sao invertidas; o custo
interno e simetrico), Or-opt de blocos de 1 a 3 servicos (inseridos direto ou invertidos); apos convergir, DP exata das orientacoes (o `dir-opt` de Dewil et al., 2011). Melhor melhora a cada iteracao; PARADA DETERMINISTICA
(convergencia ou `max_iter`; o limite de tempo e so uma salvaguarda e e REPORTADO quando atingido). Precedencia de FECHAMENTO (so nas instancias com furo): um movimento so e aceito se, para cada par (interno i, externo o),
o ultimo servico de i vem antes do ultimo servico de o; a posse de cada servico por contorno e calculada GEOMETRICAMENTE (ponto medio sobre o anel, tolerancia 1e-5). Cada solucao final e verificada com `caminho_honesto.verificar`.
Uso: python reparo_reinicio.py teste [--instancias a,b] [--t 1.0] | rodar [--workers 8] [--ts 0.25,1.0] [--amostra v3|a,b,c] [--max-iter 5000] [--limite 120]
"""
import os
import sys
import json
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
from heuristic_core import _DEFAULT_CONFIG as D                     # noqa: E402

VC, VA = D["v_cut"], D["v_air"]
TOL = 1e-7
CAM = os.path.join(AQUI, "auditoria_lcpp1", "caminhos_282")
DADOS = os.path.join(AQUI, "instancias_lcpp1_dados")
OUT = os.path.join(AQUI, "reparo_resultados")


def cst(px, py, ip, qx, qy, iq, t):
    """custo do deslocamento entre (px, py) [fim de um servico] e (qx, qy) [inicio do seguinte]; o item 0 e a origem (sem custo de reinicio nas pernas de/para ela)."""
    d = np.maximum(np.abs(px - qx), np.abs(py - qy))
    base = np.where(d > TOL, d / VA, 0.0)
    pen = np.where((d > TOL) & (ip != 0) & (iq != 0), t, 0.0)
    return base + pen


def servicos(nome):
    r = json.load(open(os.path.join(CAM, f"{nome}.json")))
    return [(s[0], s[1], s[2], s[3]) for s in r["forte"] if s[4] == "c"]


def preparar(srv):
    n = len(srv)
    A = np.zeros((n + 1, 2))
    B = np.zeros((n + 1, 2))
    for k, (x0, y0, x1, y1) in enumerate(srv, start=1):
        A[k] = (x0, y0)
        B[k] = (x1, y1)
    return A, B


def dp_flags(A, B, ordp, t):
    """orientacoes otimas (DP exata) para a ordem dada; flags[pos] = True se o servico e percorrido de B para A."""
    n = len(ordp) - 1
    items = ordp[1:]
    INF = float("inf")

    def ext(it, o):
        return (A[it], B[it]) if o == 0 else (B[it], A[it])
    custo = np.full((n, 2), INF)
    pai = np.zeros((n, 2), int)
    for o in (0, 1):
        s, _ = ext(items[0], o)
        custo[0, o] = max(abs(s[0]), abs(s[1])) / VA
    for k in range(1, n):
        for o in (0, 1):
            s, _ = ext(items[k], o)
            for q in (0, 1):
                _, e = ext(items[k - 1], q)
                d = max(abs(e[0] - s[0]), abs(e[1] - s[1]))
                c = custo[k - 1, q] + ((d / VA + t) if d > TOL else 0.0)
                if c < custo[k, o] - 1e-12:
                    custo[k, o], pai[k, o] = c, q
    fim = []
    for o in (0, 1):
        _, e = ext(items[n - 1], o)
        fim.append(custo[n - 1, o] + max(abs(e[0]), abs(e[1])) / VA)
    o = 0 if fim[0] <= fim[1] else 1
    flags = np.zeros(n + 1, bool)
    for k in range(n - 1, -1, -1):
        flags[k + 1] = bool(o)
        if k > 0:
            o = pai[k, o]
    return flags


def total(A, B, ordp, flp, t):
    Ax, Ay, Bx, By = A[:, 0], A[:, 1], B[:, 0], B[:, 1]
    sx = np.where(flp, Bx[ordp], Ax[ordp])
    sy = np.where(flp, By[ordp], Ay[ordp])
    ex = np.where(flp, Ax[ordp], Bx[ordp])
    ey = np.where(flp, Ay[ordp], By[ordp])
    return float(cst(ex, ey, ordp, np.roll(sx, -1), np.roll(sy, -1), np.roll(ordp, -1), t).sum())


def aplicar(mv, ordp, flp):
    ordp, flp = ordp.copy(), flp.copy()
    if mv[0] == "f":
        flp[mv[1]] = ~flp[mv[1]]
    elif mv[0] == "r":
        i, j = mv[1], mv[2]
        ordp[i:j + 1] = ordp[i:j + 1][::-1].copy()
        flp[i:j + 1] = ~flp[i:j + 1][::-1]
    else:
        i, L, p, rev = mv[1], mv[2], mv[3], mv[4]
        j = i + L - 1
        bo, bf = ordp[i:j + 1].copy(), flp[i:j + 1].copy()
        if rev:
            bo, bf = bo[::-1].copy(), ~bf[::-1]
        ro = np.concatenate([ordp[:i], ordp[j + 1:]])
        rf = np.concatenate([flp[:i], flp[j + 1:]])
        pp = p if p < i else p - L
        ordp = np.concatenate([ro[:pp + 1], bo, ro[pp + 1:]])
        flp = np.concatenate([rf[:pp + 1], bf, rf[pp + 1:]])
    return ordp, flp


def busca_local(A, B, t, ordp, flp, max_iter=5000, limite_s=120.0, viavel=None):
    N = len(ordp)
    n = N - 1
    Ax, Ay, Bx, By = A[:, 0], A[:, 1], B[:, 0], B[:, 1]
    P = np.arange(N)
    t0 = time.time()
    it, conv, por_tempo = 0, False, False
    while it < max_iter:
        if time.time() - t0 > limite_s:
            por_tempo = True
            break
        sx = np.where(flp, Bx[ordp], Ax[ordp])
        sy = np.where(flp, By[ordp], Ay[ordp])
        ex = np.where(flp, Ax[ordp], Bx[ordp])
        ey = np.where(flp, Ay[ordp], By[ordp])
        sx1, sy1, ids1 = np.roll(sx, -1), np.roll(sy, -1), np.roll(ordp, -1)
        w = cst(ex, ey, ordp, sx1, sy1, ids1, t)
        cands = []
        k = np.arange(1, N)
        # (1) flip de um servico
        df = cst(ex[k - 1], ey[k - 1], ordp[k - 1], ex[k], ey[k], ordp[k], t) + cst(sx[k], sy[k], ordp[k], sx1[k], sy1[k], ids1[k], t) - w[k - 1] - w[k]
        for q in np.argsort(df)[:3]:
            if df[q] < -1e-9:
                cands.append((float(df[q]), ("f", int(k[q]))))
        # (2) 2-opt com inversao de subsequencia i..j
        ii, jj = k[:, None], k[None, :]
        c1 = cst(ex[ii - 1], ey[ii - 1], ordp[ii - 1], ex[jj], ey[jj], ordp[jj], t)
        c2 = cst(sx[ii], sy[ii], ordp[ii], sx1[jj], sy1[jj], ids1[jj], t)
        d2 = np.where(jj > ii, c1 + c2 - w[ii - 1] - w[jj], np.inf)
        flat = np.argpartition(d2.ravel(), min(5, d2.size - 1))[:5]
        for q in flat:
            a, b = divmod(int(q), n)
            if d2[a, b] < -1e-9:
                cands.append((float(d2[a, b]), ("r", a + 1, b + 1)))
        # (3) Or-opt de blocos de 1..3 servicos (direto ou invertido)
        for L in (1, 2, 3):
            for i in range(1, n - L + 2):
                j = i + L - 1
                ok = (P < i - 1) | (P > j)
                rem = float(cst(ex[i - 1], ey[i - 1], ordp[i - 1], sx1[j], sy1[j], ids1[j], t)) - w[i - 1] - w[j]
                fwd = cst(ex, ey, ordp, sx[i], sy[i], ordp[i], t) + cst(ex[j], ey[j], ordp[j], sx1, sy1, ids1, t) - w
                rev = cst(ex, ey, ordp, ex[j], ey[j], ordp[j], t) + cst(sx[i], sy[i], ordp[i], sx1, sy1, ids1, t) - w
                fwd = np.where(ok, fwd, np.inf)
                rev = np.where(ok, rev, np.inf)
                pf, pr = int(np.argmin(fwd)), int(np.argmin(rev))
                if rem + fwd[pf] < -1e-9:
                    cands.append((float(rem + fwd[pf]), ("o", i, L, pf, False)))
                if rem + rev[pr] < -1e-9:
                    cands.append((float(rem + rev[pr]), ("o", i, L, pr, True)))
        if not cands:
            conv = True
            break
        cands.sort(key=lambda c: c[0])
        aplicado = False
        for delta, mv in cands:
            no, nf = aplicar(mv, ordp, flp)
            if viavel is None or viavel(no):
                ordp, flp = no, nf
                aplicado = True
                break
        if not aplicado:
            conv = True
            break
        it += 1
    return ordp, flp, {"iteracoes": it, "convergiu": conv, "por_tempo": por_tempo, "tempo_busca_s": time.time() - t0}


def contexto_precedencia(nome, srv):
    """(viavel, info) para instancias com Pi; (None, {}) se nao ha. Posse dos servicos por contorno calculada geometricamente."""
    import instancias_lcpp1 as il
    import segmento_gtsp as sg
    from shapely.geometry import Polygon, LineString, Point
    from shapely.strtree import STRtree
    hc = sg.hc
    segs = il.ler_segmentos(os.path.join(DADOS, f"{nome}.txt"))
    aneis = [a for a in il.agrupar_contornos(segs) if len(a) >= 3]
    polys = [Polygon(a) for a in aneis]
    pares = hc._detectar_precedencia(list(polys))
    if not pares:
        return None, {"polys": polys, "pares": pares}
    rings = [LineString(list(a) + [a[0]]) for a in aneis]
    tree = STRtree(rings)
    N = len(srv) + 1
    M = np.zeros((N, len(rings)), bool)
    for k, (x0, y0, x1, y1) in enumerate(srv, start=1):
        for c in tree.query(Point((x0 + x1) / 2, (y0 + y1) / 2), predicate="dwithin", distance=1e-5):
            M[k, int(c)] = True
    inn = np.array([p[0] for p in pares])
    out = np.array([p[1] for p in pares])

    def viavel(ordp):
        pos = np.empty(len(ordp), int)
        pos[ordp] = np.arange(len(ordp))
        last = np.max(np.where(M, pos[:, None], -1), axis=0)
        li, lo = last[inn], last[out]
        return bool(np.all((li < 0) | (lo < 0) | (li < lo)))
    return viavel, {"polys": polys, "pares": pares, "M": M}


def reparar(nome, t, max_iter=5000, limite_s=120.0, verificar=True):
    import avaliar_heuristica_formal as af
    srv = servicos(nome)
    A, B = preparar(srv)
    N = len(srv) + 1
    ordp0 = np.arange(N)
    viavel, ctx = contexto_precedencia(nome, srv)
    cam0 = [[a, b, c, d, "c"] for a, b, c, d in srv]
    fo_antes = af.fo_formal(cam0, t)
    res = {"instancia": nome, "t_perf": t, "n_servicos": len(srv), "n_pares_pi": len(ctx.get("pares", [])), "H_fo": fo_antes["fo"], "H_corridas": fo_antes["corridas"],
           "inicio_viavel": True if viavel is None else bool(viavel(ordp0))}
    t0 = time.time()
    flp0 = dp_flags(A, B, ordp0, t)
    ordp, flp, info = busca_local(A, B, t, ordp0, flp0, max_iter, limite_s, viavel)
    flp = dp_flags(A, B, ordp, t)
    srv2 = [srv[k - 1] for k in ordp[1:]]
    cam1 = [[a, b, c, d, "c"] for a, b, c, d in srv2]
    fo_depois = af.fo_formal(cam1, t)
    res.update(info)
    res.update({"Rep_fo": fo_depois["fo"], "Rep_corridas": fo_depois["corridas"], "Rep_ar": fo_depois["ar"], "H_ar": fo_antes["ar"], "tempo_total_s": time.time() - t0,
                "fim_viavel": True if viavel is None else bool(viavel(ordp)), "ganho_pct": 100 * (fo_depois["fo"] / fo_antes["fo"] - 1), "ordem": [int(x) for x in ordp[1:]]})
    if verificar:
        import caminho_honesto as ch
        from shapely.geometry import LineString
        cam = []
        for k, f in zip(ordp[1:], flp[1:]):
            a, b = (srv[k - 1][2:], srv[k - 1][:2]) if f else (srv[k - 1][:2], srv[k - 1][2:])
            cam.append((LineString([a, b]), "c"))
        cc, nsal, tot = ch.contiguar(cam)
        v = ch.verificar(cc, ctx["polys"], pares_pi=ctx["pares"])
        res.update({"verif_contiguo": bool(v["contiguo"]), "verif_origem": bool(v["parte_e_volta_origem"]), "verif_geo_ok": bool(v["geo_ok"]), "verif_viol_fechamento": int(v["violacoes_pi_relaxada"]),
                    "verif_viol_estrita": int(v["violacoes_pi_estrita"])})
    return res


def _job(a):
    nome, t, max_iter, limite_s = a
    f = os.path.join(OUT, f"{nome}__t{t}.json")
    if os.path.exists(f):
        return nome, t, "pulado"
    r = reparar(nome, t, max_iter, limite_s)
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f, "w"))
    return nome, t, f"H {r['H_fo']:.3f} (R={r['H_corridas']}) -> Rep {r['Rep_fo']:.3f} (R={r['Rep_corridas']}) {r['ganho_pct']:+.2f}% em {r['tempo_total_s']:.1f}s, {r['iteracoes']} it" + ("" if r["convergiu"] else " [NAO CONVERGIU]") + ("" if r.get("verif_geo_ok", True) else " [VERIFICACAO FALHOU]")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "teste"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    max_iter, limite = arg("--max-iter", int, 5000), arg("--limite", float, 120.0)
    if modo == "teste":
        nomes = arg("--instancias", str, "albano_pack,art_2_regular_pack,art_3_hole_sep").split(",")
        for n in nomes:
            for t in [arg("--t", float, 1.0)]:
                r = reparar(n, t, max_iter, limite)
                print(f"{n:24s} t={t:g}: H {r['H_fo']:.3f} (R={r['H_corridas']}) -> Rep {r['Rep_fo']:.3f} (R={r['Rep_corridas']}) {r['ganho_pct']:+.2f}% | {r['iteracoes']} it, {r['tempo_total_s']:.1f}s, conv={r['convergiu']}, "
                      f"viavel={r['fim_viavel']}, verif={r.get('verif_contiguo')},{r.get('verif_geo_ok')},viol={r.get('verif_viol_fechamento')}", flush=True)
    elif modo == "rodar":
        import rodar_v3 as rv
        workers = arg("--workers", int, 8)
        ts = [float(x) for x in arg("--ts", str, "0.25,1.0").split(",")]
        am = arg("--amostra", str, "v3")
        nomes = rv.amostra() if am == "v3" else am.split(",")
        tarefas = [(n, t, max_iter, limite) for n in nomes for t in ts]
        print(f"[{time.strftime('%H:%M:%S')}] reparo: {len(tarefas)} tarefas ({len(nomes)} instancias x t em {ts}), {workers} processos", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for n, t, msg in ex.map(_job, tarefas, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {n} t={t:g}: {msg}", flush=True)
        print("REPARO CONCLUIDO", flush=True)
