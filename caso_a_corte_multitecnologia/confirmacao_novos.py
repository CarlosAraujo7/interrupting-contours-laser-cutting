"""
confirmacao_novos.py  --  VALIDACAO CONFIRMATORIA do saving exato, do ponto de equilibrio e do certificado em LAYOUTS NOVOS (docs/59, Estudo F; 20/11/2026; autorizado por Carlos)
===============================================================================================================================================================================
Os resultados exatos centrais do N1 (teto de ~0,7% a t = 0, ponto de equilibrio exato ~0,05-0,16 s, rho_c 0,29-0,52, certificado) vieram de 9 a 17 layouts de UM conjunto (as familias `art_*`, `dighe*`, `fu_*` do
artigo irmao) e foram EXPLORATORIOS. Aqui eles sao postos a prova em layouts que NAO foram vistos: um gerador com semente fixa (4 familias de formas) produz layouts de contornos DISJUNTOS, sem furos, com a origem
fora dos contornos (a mesma classe em que o certificado vale); para cada um o pipeline e o dos layouts antigos: otimo exato de nivel de contorno (Held-Karp sobre subconjuntos de contornos), ar minimo exato
(MILP em t = 0 = RPP sem Pi), economia exata em t = 0,03, 0,1 e 0,25 s (MILP com custo de reinicio, HiGHS) e ponto de equilibrio exato por Newton (Proposicao 3; `newton_exato_tc.iterar`).
Previsoes F-1..F-5 e regras de decisao: docs/59 (escritas ANTES dos dados; as sementes de teste do desenvolvimento sao distintas das sementes finais).
Uso: python confirmacao_novos.py autoteste | calibrar | congelar | rodar [--workers 3] [--limite 1800] | verificar | resultados      (`rodar` idempotente: pula layouts com JSON; `verificar` ANTES de `resultados`)
"""
import glob
import hashlib
import json
import math
import os
import random
import statistics
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
import verificar_certificado_milp as vm  # noqa: E402
import newton_exato_tc as nx  # noqa: E402
import teto_certificado as tc  # noqa: E402
import tsh_segmento as tsh  # noqa: E402

OUT = os.path.join(AQUI, "confirmacao_novos_resultados")
MANIFESTO = os.path.join(AQUI, "confirmacao_estudos_manifesto.json")
VC, VA = vm.VC, vm.VA
TS_GRADE = (0.03, 0.1, 0.25)
TOL = nx.TOL
CAMPO = (160.0, 240.0)                       # x, y do campo (a escala dos layouts antigos: bbox ate 166 x 248); a origem fica no canto (0, 0)
SEMENTE_BASE = 2026112000
# (familia, n de contornos) por layout final; 4 familias x 10 layouts = 40; as sementes sao SEMENTE_BASE + indice (as de teste do desenvolvimento, 1 a 6, sao outras)
PLANO = ([("ret", n) for n in (6, 8, 10, 12, 6, 8, 10, 12, 7, 9)] + [("pol", n) for n in (5, 6, 7, 8, 9, 10, 6, 8, 7, 9)] + [("mix", n) for n in (5, 6, 7, 8, 9, 10, 6, 8, 7, 9)]
         + [("agr", n) for n in (6, 8, 10, 12, 6, 8, 10, 12, 7, 9)])
MIN_EXATOS = 30                              # as previsoes F-1..F-5 so sao avaliadas com >= 30 layouts de ponto de equilibrio exato (regra do protocolo)
FAMILIAS = ("ret", "pol", "mix", "agr")


def _forma(rng, tipo):
    from shapely.geometry import Polygon, box
    from shapely.affinity import rotate
    if tipo == "ret":
        w, h = rng.uniform(14, 60), rng.uniform(14, 60)
        return box(-w / 2, -h / 2, w / 2, h / 2)
    if tipo == "pol":                                          # poligono convexo de 5 ou 6 vertices inscrito numa elipse (angulos ordenados => convexo)
        k = rng.choice((5, 6))
        a, b = rng.uniform(9, 32), rng.uniform(9, 32)
        passo = 2 * math.pi / k
        th = [i * passo + rng.uniform(-0.25, 0.25) * passo for i in range(k)]
        return rotate(Polygon([(a * math.cos(t), b * math.sin(t)) for t in th]), rng.uniform(0, 360), origin=(0, 0))
    if tipo == "ele":                                          # forma em L (6 vertices)
        w, h = rng.uniform(24, 60), rng.uniform(24, 60)
        cw, ch = rng.uniform(0.35, 0.6) * w, rng.uniform(0.35, 0.6) * h
        return Polygon([(0, 0), (w, 0), (w, ch), (cw, ch), (cw, h), (0, h)])
    if tipo == "oct":                                          # octogono quase regular
        r = rng.uniform(9, 30)
        return rotate(Polygon([(r * math.cos(i * math.pi / 4 + math.pi / 8), r * math.sin(i * math.pi / 4 + math.pi / 8)) for i in range(8)]), rng.uniform(0, 45), origin=(0, 0))
    raise ValueError(tipo)


def gerar(familia, n, semente):
    """Layout de `n` contornos disjuntos (folga minima 3), sem furos, no campo CAMPO, origem (0,0) fora de todos. Determinista dada a semente. -> lista de Polygon."""
    from shapely.geometry import Point
    from shapely.affinity import translate
    rng = random.Random(semente)
    tipos = {"ret": ("ret",), "pol": ("pol",), "mix": ("ret", "ele", "oct"), "agr": ("ret", "pol", "ele", "oct")}[familia]
    for _tentativa in range(200):
        centros_g = [(rng.uniform(40, CAMPO[0] - 40), rng.uniform(40, CAMPO[1] - 40)) for _ in range(rng.choice((2, 3)))] if familia == "agr" else None
        colocados, ok = [], True
        for _ in range(n):
            for _t in range(800):
                f = _forma(rng, rng.choice(tipos))
                if centros_g:
                    cx, cy = rng.choice(centros_g)
                    px, py = rng.gauss(cx, 26), rng.gauss(cy, 26)
                else:
                    px, py = rng.uniform(5, CAMPO[0] - 5), rng.uniform(5, CAMPO[1] - 5)
                c = f.centroid
                g = translate(f, px - c.x, py - c.y)
                x0, y0, x1, y1 = g.bounds
                if x0 < 4 or y0 < 4 or x1 > CAMPO[0] or y1 > CAMPO[1]:
                    continue
                if g.distance(Point(0, 0)) < 6:
                    continue
                if any(g.distance(o) < 3 for o in colocados):
                    continue
                colocados.append(g)
                break
            else:
                ok = False
                break
        if ok:
            return colocados
    raise RuntimeError("nao consegui gerar o layout")


def pipeline(polys, limite_s, log=print, nome="?"):
    """Pipeline exato de um layout de contornos disjuntos. -> dict (JSON)."""
    t_ini = time.time()
    coords, req = tsh.construir_requeridas(polys)
    L = float(sum(max(abs(coords[u][0] - coords[v][0]), abs(coords[u][1] - coords[v][1])) for u, v in req))
    n = len(polys)
    AP, _tour = tc.dp_contornos(polys, [])
    P0 = L / VC + AP / VA
    inst = vm.preparar(coords, req)
    res = {"instancia": nome, "n": n, "V": len(coords), "L": L, "AP": AP, "P0": P0, "limite_s": limite_s, "pontos": {}, "status": "?"}
    r0 = vm.resolver_t(inst, req, 0.0, limite_s, corte_sup=AP / VA)
    if not r0.get("otimo"):
        res.update({"status": "sem_prova_t0", "tempo_total_s": time.time() - t_ini})
        return res
    As = r0["ar_len"]
    res["As"] = As
    res["t_cert"] = (AP - As) / VA
    R0, c0 = r0["n_ar"] - 1, L / VC + r0["ar_len"] / VA
    res["pontos"]["0"] = {"t": 0.0, "M": L / VC + r0["ar_custo"], "R": R0, "c": c0, "S": P0 - (L / VC + r0["ar_custo"]), "tempo_s": r0["tempo_s"]}
    log(f"   {nome}: V={len(coords)} n={n} AP={AP:.1f} A*={As:.1f} t_cert={res['t_cert']:.3f} R0={R0} S0={res['pontos']['0']['S']:.4f} ({r0['tempo_s']:.0f}s)")
    for t in TS_GRADE:
        r = vm.resolver_t(inst, req, t, limite_s, corte_sup=AP / VA + t * (n + 1))
        if not r.get("otimo"):
            res["pontos"][f"{t:g}"] = {"t": t, "status": "sem_prova", "motivo": r.get("motivo")}
            log(f"   {nome}: t={t}: sem prova ({r.get('motivo')})")
            continue
        M, R, c = L / VC + r["ar_custo"] - t, r["n_ar"] - 1, L / VC + r["ar_len"] / VA
        res["pontos"][f"{t:g}"] = {"t": t, "M": M, "R": R, "c": c, "S": (P0 + t * n) - M, "tempo_s": r["tempo_s"]}
        log(f"   {nome}: t={t}: R={R} S={(P0 + t * n) - M:.6g} ({r['tempo_s']:.0f}s)")
    # Newton a partir do plano de t = 0 (R0 > n e S > 0) ou, se S(0) = 0, t_c = 0
    if res["pontos"]["0"]["S"] <= TOL * P0 or not R0 > n:
        res.update({"status": "exato", "t_c": 0.0, "trilha": [], "tempo_total_s": time.time() - t_ini})
        return res
    d = {"nome": nome, "L": L, "n": n, "AP": AP, "P0": P0}
    trilha, status = nx.iterar(d, inst, req, limite_s, (0.0, R0, c0), log=log)
    res.update({"status": status, "t_c": trilha[-1]["t"] if status == "exato" else None, "trilha": trilha, "tempo_total_s": time.time() - t_ini})
    return res


def _lista():
    return [(f"nv_{i:02d}_{fam}{n}", fam, n, SEMENTE_BASE + i) for i, (fam, n) in enumerate(PLANO)]


def _job(a):
    nome, fam, n, semente, limite = a
    f = os.path.join(OUT, f"{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    polys = gerar(fam, n, semente)
    res = pipeline(polys, limite, log=lambda s: print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True), nome=nome)
    res.update({"familia": fam, "semente": semente})
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(f, "w"), indent=1)
    return nome, f"{res['status']}" + (f" t_c={res['t_c']:.5f}" if res.get("t_c") is not None else "") + f" em {res['tempo_total_s']:.0f}s"


def autoteste():
    """(1) o gerador e determinista e produz contornos disjuntos, sem furos, longe da origem; (2) o pipeline num layout de brinquedo (3 retangulos, o da Fig. 1 do N1) reproduz o autoteste de
    `newton_exato_tc` (t_c >= 0,0325 s e conferencia independente em t_c(1 -+ 1e-3))."""
    from shapely.geometry import box, Point
    for fam in FAMILIAS:
        a, b = gerar(fam, 6, 1), gerar(fam, 6, 1)
        assert [p.wkt for p in a] == [p.wkt for p in b], "o gerador deve ser determinista"
        for i, p in enumerate(a):
            assert p.is_valid and len(p.interiors) == 0 and p.distance(Point(0, 0)) >= 6
            assert all(p.distance(q) >= 3 for q in a[:i])
    print("gerador OK (4 familias)")
    polys = [box(5, 8, 15, 18), box(20, 4, 30, 12), box(18, 17, 28, 25)]
    res = pipeline(polys, 120, nome="brinquedo")
    assert res["status"] == "exato" and res["t_c"] >= 0.0325 - 1e-9, res
    coords, req = tsh.construir_requeridas(polys)
    inst = vm.preparar(coords, req)
    for t, esperado in ((res["t_c"] * (1 - 1e-3), True), (res["t_c"] * (1 + 1e-3), False)):
        r = vm.resolver_t(inst, req, t, 120)
        S = (res["P0"] + t * res["n"]) - (res["L"] / VC + r["ar_custo"] - t)
        assert (S > TOL * (res["P0"] + t * res["n"])) == esperado, (t, S)
    print("pipeline OK: brinquedo t_c =", res["t_c"], "t_cert =", res["t_cert"])
    print("AUTOTESTE OK")


def calibrar():
    """Desenvolvimento (NAO e dado do estudo): tempo dos MILPs em layouts gerados com sementes de TESTE (1-6), distintas das finais."""
    for fam, n, s in (("ret", 6, 1), ("pol", 6, 2), ("mix", 6, 3), ("agr", 6, 4), ("ret", 8, 5), ("pol", 8, 6)):
        polys = gerar(fam, n, s)
        t0 = time.time()
        res = pipeline(polys, 900, nome=f"teste_{fam}{n}_s{s}")
        print(f"CALIBRACAO {fam}{n} s{s}: V={res['V']} status={res['status']} t_c={res.get('t_c')} total {time.time() - t0:.0f}s", flush=True)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def congelar():
    """O manifesto dos TRES estudos (E, F, G) e o protocolo: gravado por `grupo_comum.py congelar` (um so manifesto); aqui so confere que existe."""
    print("use: python grupo_comum.py congelar   (manifesto comum dos estudos E, F e G em", MANIFESTO, ")")


def verificar():
    """(1) codigo e protocolo iguais aos congelados; (2) previsoes ESTRUTURAIS F-S1..F-S4 em cada resultado (violar uma e erro de codigo ou da teoria: investigar, nao relatar como achado)."""
    ok = True
    man = json.load(open(MANIFESTO))
    for a, h in man["arquivos"].items():
        igual = sha(os.path.join(AQUI, a)) == h
        ok &= igual
        print(("OK       " if igual else "ALTERADO ") + a)
    fs = sorted(glob.glob(os.path.join(OUT, "*.json")))
    print(f"{len(fs)} layouts com resultado")
    for f in fs:
        r = json.load(open(f))
        probs = []
        if r["status"] in ("exato", "sem_prova", "iteracoes") and "As" in r:
            n, P0, L, AP, As = r["n"], r["P0"], r["L"], r["AP"], r["As"]
            for k, p in r["pontos"].items():
                if "M" not in p:
                    continue
                t = p["t"]
                lb = L / VC + min(AP / VA + t * n, As / VA + t * (n + 1))
                if p["M"] < lb * (1 - 1e-9) - 1e-9:
                    probs.append(f"F-S1: M(t={t}) abaixo do limite inferior")
                if p["M"] > P0 + t * n + 1e-9:
                    probs.append(f"F-S1: M(t={t}) acima do plano de contorno")
                if p["S"] > r["t_cert"] - t + 1e-6:
                    probs.append(f"F-S2: economia em t={t} maior que t_cert - t")
            pts = sorted((p["t"], p["S"]) for p in r["pontos"].values() if "S" in p)
            for (t1, s1), (t2, s2), (t3, s3) in zip(pts, pts[1:], pts[2:]):
                if not (s2 <= s1 + 1e-9 and s3 <= s2 + 1e-9):
                    probs.append("F-S3: economia nao decrescente na grade")
                lamb = (t2 - t1) / (t3 - t1)
                if s2 > (1 - lamb) * s1 + lamb * s3 + 1e-7:
                    probs.append("F-S3: economia nao convexa na grade")
        if r["status"] == "exato" and r.get("trilha"):
            tr = r["trilha"]
            ts = [x["t"] for x in tr]
            Rs = [x["R"] for x in tr if "R" in x]
            if not all(b > a for a, b in zip(ts, ts[1:])) or not all(b < a for a, b in zip(Rs, Rs[1:])):
                probs.append("F-S4: t nao cresce ou R nao decresce estritamente")
            if r["t_c"] > r["t_cert"] * (1 + 1e-6):
                probs.append("F-S2: t_c > t_cert")
        ok &= not probs
        print(f"  {r['instancia']}: {r['status']}" + (f" t_c={r['t_c']:.5f}" if r.get("t_c") is not None else "") + (" | " + "; ".join(probs) if probs else " | estrutura OK"))
    print("VERIFICACAO " + ("OK" if ok else "COM PROBLEMAS"))
    sys.exit(0 if ok else 1)


def resultados():
    fs = sorted(glob.glob(os.path.join(OUT, "*.json")))
    R = [json.load(open(f)) for f in fs]
    ex = [r for r in R if r["status"] == "exato"]
    L = ["# Validacao confirmatoria em layouts novos (docs/59, Estudo F)", "",
         "| layout | familia | n | V | t_cert (s) | S(0) % | S(0,03) % | S(0,1) % | S(0,25) % | t_c (s) | rho_c | t_c/t_cert | status |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    pc = lambda r, k: (100 * r["pontos"][k]["S"] / (r["P0"] + r["pontos"][k]["t"] * r["n"])) if k in r["pontos"] and "S" in r["pontos"][k] else None
    f2 = lambda x, d=3: "--" if x is None else f"{x:.{d}f}"
    linhas = []
    for r in R:
        rho = r["t_c"] * VA * r["n"] / r["L"] if r.get("t_c") is not None else None
        rr = r["t_c"] / r["t_cert"] if r.get("t_c") is not None and r.get("t_cert") else None
        linhas.append((r, rho, rr))
        L.append(f"| {r['instancia']} | {r['familia']} | {r['n']} | {r['V']} | {f2(r.get('t_cert'))} | {f2(pc(r, '0'))} | {f2(pc(r, '0.03'))} | {f2(pc(r, '0.1'))} | {f2(pc(r, '0.25'))} | "
                 f"{f2(r.get('t_c'), 5)} | {f2(rho)} | {f2(rr, 2)} | {r['status']} |")
    L += ["", f"Layouts: {len(R)}; com ponto de equilibrio exato: {len(ex)}."]
    if len(ex) >= MIN_EXATOS:
        s0 = [pc(r, "0") for r in ex]
        s25 = [pc(r, "0.25") for r in ex if pc(r, "0.25") is not None]
        s03 = [pc(r, "0.03") for r in ex if pc(r, "0.03") is not None]
        rhos = [rho for r, rho, _ in linhas if rho is not None and r["status"] == "exato"]
        rrs = [rr for r, _, rr in linhas if rr is not None and r["status"] == "exato"]
        med0, med03 = statistics.median(s0), (statistics.median(s03) if s03 else None)
        F1 = med0 <= 1.0 and max(s0) <= 2.0
        F2 = bool(s25) and sum(1 for x in s25 if x <= 1e-5) >= 0.9 * len(s25)
        F3 = 0.25 <= statistics.median(rhos) <= 0.75 and sum(1 for x in rhos if 0.15 <= x <= 1.0) >= 0.8 * len(rhos)
        F4 = statistics.median(rrs) <= 0.6 and sum(1 for x in rrs if x <= 0.9) >= 0.8 * len(rrs)
        F5 = med03 is not None and med0 > 0 and 0.5 <= med03 / med0 <= 0.9
        fmt = lambda b: "SUSTENTADA" if b else "NAO SUSTENTADA"
        L += ["", f"F-1 (teto): mediana de S(0) = {med0:.3f}% (max {max(s0):.3f}%); previsao: mediana <= 1,0% e max <= 2,0%: **{fmt(F1)}**.",
              f"F-2 (nulo em 0,25 s): {sum(1 for x in s25 if x <= 1e-5)} de {len(s25)} layouts com S(0,25) = 0; previsao: >= 90%: **{fmt(F2)}**.",
              f"F-3 (rho_c): mediana {statistics.median(rhos):.3f} (min {min(rhos):.3f}, max {max(rhos):.3f}); previsao: mediana em [0,25; 0,75] e >= 80% em [0,15; 1,0]: **{fmt(F3)}**.",
              f"F-4 (t_c / t_cert): mediana {statistics.median(rrs):.2f} (max {max(rrs):.2f}); previsao: mediana <= 0,6 e >= 80% <= 0,9: **{fmt(F4)}**.",
              f"F-5 (curva): S(0,03)/S(0) na mediana = {med03 / med0:.2f}; previsao em [0,5; 0,9]: **{fmt(F5)}**." if med03 is not None and med0 > 0 else "F-5: sem dados."]
    else:
        L += ["", f"Menos de {MIN_EXATOS} layouts com ponto de equilibrio exato ({len(ex)}): as previsoes F-1..F-5 NAO sao avaliadas (regra de decisao do protocolo); relatar so a tabela."]
    open(os.path.join(AQUI, "RESULTADOS_CONFIRMACAO_NOVOS.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "autoteste"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "autoteste":
        autoteste()
    elif modo == "calibrar":
        calibrar()
    elif modo == "congelar":
        congelar()
    elif modo == "verificar":
        verificar()
    elif modo == "resultados":
        resultados()
    elif modo == "rodar":
        workers, limite = arg("--workers", int, 3), arg("--limite", float, 1800.0)
        itens = [(nome, fam, n, s, limite) for nome, fam, n, s in _lista()]
        print(f"[{time.strftime('%H:%M:%S')}] Confirmacao em layouts novos: {len(itens)} layouts, {workers} processos, limite {limite:g} s por MILP", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for n_, msg in ex.map(_job, itens, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {n_}: {msg}", flush=True)
        print("CONFIRMACAO CONCLUIDA", flush=True)
