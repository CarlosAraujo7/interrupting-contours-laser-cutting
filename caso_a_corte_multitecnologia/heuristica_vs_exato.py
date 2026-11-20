"""
heuristica_vs_exato.py  --  DISTANCIA DO PCGLNS DE ARCOS (nivel de segmento, com custo de reinicio) AO OTIMO EXATO nos layouts dos estudos E e F (docs/60; 20/11/2026; autorizado por Carlos)
===============================================================================================================================================================================
Para cada layout dos estudos E (`grupo_comum_resultados/`, t = 0,06; 0,25; 1,0) e F (`confirmacao_novos_resultados/`, t = 0,03; 0,1; 0,25) com M(t) exato provado, resolve o GTSP de arcos com PCGLNS (mesmo metodo e
orcamentos de `rodar_v2`; funcao `escala_fibra_aninhados._segmento`) e compara o tempo da solucao verificada com o otimo exato. Previsoes H-S1..H-S3 e H-1..H-4 e regras: docs/60 (escritas ANTES dos dados).
Uso: python heuristica_vs_exato.py autoteste | congelar | rodar [--workers 3] | verificar | resultados      (`rodar` idempotente; `verificar` ANTES de `resultados`)
"""
import glob
import hashlib
import json
import os
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
OUT = os.path.join(AQUI, "heuristica_vs_exato_resultados")
MANIFESTO = os.path.join(AQUI, "estudo_h_manifesto.json")
PROTOCOLO = os.path.join("..", "docs", "60_protocolo_estudo_H_pcglns_de_arcos_contra_o_otimo_exato.md")
ARQUIVOS_CONGELADOS = ("heuristica_vs_exato.py", "escala_fibra_aninhados.py", "segmento_gtsp.py", "caminho_honesto.py", "confirmacao_novos.py", "grupo_comum.py", PROTOCOLO)
VC, VA = 100.0 / 6.0, 400.0
TS_E, TS_F = ("0.06", "0.25", "1"), ("0.03", "0.1", "0.25")
MIN_CASOS = 100


def _polys_E(nome):
    import instancias_lcpp1 as il
    from shapely.geometry import Polygon
    segs = il.ler_segmentos(os.path.join(AQUI, "instancias_lcpp1_dados", f"{nome}.txt"))
    return [Polygon(a) for a in il.agrupar_contornos(segs) if len(a) >= 3]


def _polys_F(r):
    import confirmacao_novos as cn
    return cn.gerar(r["familia"], r["n"], r["semente"])


def tarefas():
    T = []
    for f in sorted(glob.glob(os.path.join(AQUI, "grupo_comum_resultados", "*.json"))):
        r = json.load(open(f))
        ts = [t for t in TS_E if "M" in r["pontos"].get(t, {})]
        if ts:
            T.append(("E", r["instancia"], ts))
    for f in sorted(glob.glob(os.path.join(AQUI, "confirmacao_novos_resultados", "*.json"))):
        r = json.load(open(f))
        ts = [t for t in TS_F if "M" in r["pontos"].get(t, {})]
        if ts:
            T.append(("F", r["instancia"], ts))
    return T


def _job(a):
    estudo, nome, ts = a
    f = os.path.join(OUT, f"{estudo}_{nome}.json")
    if os.path.exists(f):
        return estudo, nome, "pulado"
    import escala_fibra_aninhados as fb
    import ea0_lib as lib
    hc = lib.hc
    if estudo == "E":
        ex = json.load(open(os.path.join(AQUI, "grupo_comum_resultados", f"{nome}.json")))
        polys = _polys_E(nome)
        T_P = lambda t: ex["TP0"] + float(t) * ex["n"]
    else:
        ex = json.load(open(os.path.join(AQUI, "confirmacao_novos_resultados", f"{nome}.json")))
        polys = _polys_F(ex)
        T_P = lambda t: ex["P0"] + float(t) * ex["n"]
    pares = hc._detectar_precedencia(list(polys))
    t0 = time.time()
    seg, orc, L_seg = fb._segmento(polys, pares, [float(t) for t in ts], log=lambda s: print(f"[{time.strftime('%H:%M:%S')}] {estudo} {nome}: {s}", flush=True))
    out = {"estudo": estudo, "instancia": nome, "n": ex["n"], "L": ex["L"], "L_segmento": L_seg, "casos": {}, "orcamento_s": orc, "tempo_s": time.time() - t0}
    for t in ts:
        m = seg[t]["melhor"]
        out["casos"][t] = {"t": float(t), "M": ex["pontos"][t]["M"], "T_P": T_P(t), "h": m}
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(f, "w"), indent=1)
    return estudo, nome, f"{len(ts)} casos em {out['tempo_s']:.0f}s"


def metricas(c, L):
    """excesso (% do tempo nao cortante do otimo), lacuna (% de T_P) e captura (None se a economia exata <= 1e-3 T_P)."""
    h = c["h"]
    if not h:
        return None
    nc_h, nc_x = h["fo"] - L / VC, c["M"] - L / VC
    S = c["T_P"] - c["M"]
    return {"excesso": 100.0 * (nc_h - nc_x) / nc_x, "lacuna": 100.0 * (h["fo"] - c["M"]) / c["T_P"], "captura": (c["T_P"] - h["fo"]) / S if S > 1e-3 * c["T_P"] else None}


def autoteste():
    """Toy de 3 retangulos com uma aresta compartilhada (o do autoteste de `grupo_comum`): o PCGLNS de arcos em t = 0,06 deve dar T_h >= M(t) exato (H-S1) e muito perto dele."""
    from shapely.geometry import box
    import escala_fibra_aninhados as fb
    import grupo_comum as gc
    import verificar_certificado_milp as vm
    import tsh_segmento as tsh
    import ea0_lib as lib
    polys = [box(5, 8, 15, 18), box(15, 8, 25, 18), box(20, 28, 30, 38)]
    coords, req = tsh.construir_requeridas(polys)
    inst = vm.preparar(coords, req)
    L = float(sum(max(abs(coords[u][0] - coords[v][0]), abs(coords[u][1] - coords[v][1])) for u, v in req))
    for t in (0.06, 1.0):
        r = vm.resolver_t(inst, req, t, 120)
        M = L / VC + r["ar_custo"] - t
        seg, orc, L_seg = fb._segmento(polys, lib.hc._detectar_precedencia(list(polys)), [t], log=lambda s: None)
        h = seg[f"{t:g}"]["melhor"]
        assert h, "sem solucao verificada"
        assert abs(L_seg - L) < 1e-9
        assert abs(h["fo"] - (L_seg / VC + h["ar"] / VA + t * h["n_perf"])) <= 1e-6 * h["fo"]
        assert h["fo"] >= M - 1e-9 * M, (h["fo"], M)
        print(f"  t={t}: exato {M:.5f} | PCGLNS {h['fo']:.5f} (R={h['n_perf']}) | excesso nao cortante {100 * ((h['fo'] - L / VC) - (M - L / VC)) / (M - L / VC):.3f}%")
    print("AUTOTESTE OK")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def congelar():
    man = {"data": time.strftime("%Y-%m-%d %H:%M:%S"), "arquivos": {os.path.normpath(a): sha(os.path.join(AQUI, a)) for a in ARQUIVOS_CONGELADOS}}
    json.dump(man, open(MANIFESTO, "w"), indent=1)
    print("congelado:", json.dumps(man, indent=1))


def carregar():
    return [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "*.json")))]


def verificar():
    ok = True
    man = json.load(open(MANIFESTO))
    for a, h in man["arquivos"].items():
        igual = sha(os.path.join(AQUI, a)) == h
        ok &= igual
        print(("OK       " if igual else "ALTERADO ") + a)
    R = carregar()
    print(f"{len(R)} layouts com resultado")
    for r in R:
        probs = []
        for t, c in r["casos"].items():
            h = c["h"]
            if not h:
                probs.append(f"H-S3: t={t} sem solucao verificada")
                continue
            if not (h.get("contiguo") and h.get("geo_ok") and h.get("viol_fechamento") == 0):
                probs.append(f"H-S3: t={t} solucao nao verificada")
            if abs(h["fo"] - (r["L_segmento"] / VC + h["ar"] / VA + c["t"] * h["n_perf"])) > 1e-6 * h["fo"]:
                probs.append(f"H-S2: t={t} FO != L/v_c + ar/v_a + t R")
            if h["fo"] < c["M"] * (1 - 1e-9):
                probs.append(f"H-S1: t={t} PCGLNS ({h['fo']:.6f}) abaixo do otimo exato ({c['M']:.6f})")
        ok &= not probs
        print(f"  {r['estudo']} {r['instancia']}: " + ("; ".join(probs) if probs else "estrutura OK"))
    print("VERIFICACAO " + ("OK" if ok else "COM PROBLEMAS"))
    sys.exit(0 if ok else 1)


def resultados():
    R = carregar()
    casos = [(r, t, c, metricas(c, r["L_segmento"])) for r in R for t, c in r["casos"].items()]
    casos = [x for x in casos if x[3]]
    L = ["# PCGLNS de arcos contra o otimo exato (docs/60, estudo H)", "", f"Casos avaliaveis: {len(casos)} (layouts: {len(R)}).", "",
         "| estudo | t (s) | casos | excesso mediano (%) | excesso max (%) | no otimo | captura mediana |", "|---|---:|---:|---:|---:|---:|---:|"]
    for est in ("E", "F"):
        for t in sorted({t for r, t, _, _ in casos if r["estudo"] == est}, key=float):
            X = [m for r, tt, _, m in casos if r["estudo"] == est and tt == t]
            cap = [m["captura"] for m in X if m["captura"] is not None]
            L.append(f"| {est} | {t} | {len(X)} | {statistics.median(m['excesso'] for m in X):.3f} | {max(m['excesso'] for m in X):.3f} | {sum(1 for m in X if m['excesso'] <= 1e-6)} | " + (f"{statistics.median(cap):.3f}" if cap else "--") + " |")
    if len(casos) >= MIN_CASOS:
        ex = [m["excesso"] for *_, m in casos]
        cap = [m["captura"] for *_, m in casos if m["captura"] is not None]
        fmt = lambda b: "SUSTENTADA" if b else "NAO SUSTENTADA"
        H1 = statistics.median(ex) <= 2.0 and max(ex) <= 15.0
        H2 = sum(1 for x in ex if x <= 5.0) >= 0.8 * len(ex)
        H3 = sum(1 for x in ex if x <= 1e-6) >= 0.3 * len(ex)
        H4 = bool(cap) and statistics.median(cap) >= 0.9
        L += ["", f"H-1 (mediana do excesso <= 2% e max <= 15%): mediana {statistics.median(ex):.3f}%, max {max(ex):.3f}%: **{fmt(H1)}**.",
              f"H-2 (>= 80% dos casos com excesso <= 5%): {sum(1 for x in ex if x <= 5.0)} de {len(ex)}: **{fmt(H2)}**.",
              f"H-3 (o otimo exato e atingido em >= 30% dos casos): {sum(1 for x in ex if x <= 1e-6)} de {len(ex)}: **{fmt(H3)}**.",
              f"H-4 (captura mediana >= 0,9): mediana {statistics.median(cap):.3f} ({len(cap)} casos com economia exata > 0,1%): **{fmt(H4)}**." if cap else "H-4: sem casos com economia exata."]
    else:
        L += ["", f"Menos de {MIN_CASOS} casos avaliaveis: as previsoes H-1..H-4 NAO sao avaliadas (regra de decisao do protocolo)."]
    open(os.path.join(AQUI, "RESULTADOS_HEURISTICA_VS_EXATO.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "autoteste"
    arg = lambda fl, tp, d: tp(sys.argv[sys.argv.index(fl) + 1]) if fl in sys.argv else d
    if modo == "autoteste":
        autoteste()
    elif modo == "congelar":
        congelar()
    elif modo == "verificar":
        verificar()
    elif modo == "resultados":
        resultados()
    elif modo == "rodar":
        workers = arg("--workers", int, 3)
        T = tarefas()
        print(f"[{time.strftime('%H:%M:%S')}] PCGLNS contra o exato: {len(T)} layouts, {workers} processos", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for e, n_, msg in ex.map(_job, T, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {e} {n_}: {msg}", flush=True)
        print("ESTUDO H CONCLUIDO", flush=True)
