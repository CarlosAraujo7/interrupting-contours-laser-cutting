"""
escala_fibra_aninhados.py  --  LAYOUTS REAIS ANINHADOS E LAYOUTS DENSOS EM ESCALA DE MAQUINA DE FIBRA (docs/59, Estudo G; 20/11/2026; autorizado por Carlos)
=======================================================================================================================================================
Lacuna dos relatorios simulados (R2-2, R2-3 de docs/53): (i) os 47 layouts aninhados do CPPLib (V2) foram resolvidos so em t = 0 e t = 1 s (escala do benchmark, ar a 24 m/min); o que valem a ~140 m/min de voo,
com custos de reinicio de dezenas de ms, nao foi calculado; (ii) trabalhos de chapa fina com centenas de furos pequenos nao estao representados.
Como a solucao otima para (v_c', v_a', t') e a do benchmark com t'' = t' v_a'/v_a (o plano nao depende de v_c' e o ar so muda de escala), basta resolver o benchmark em t'' = 0,06 e 0,25 s (mais os t = 0 e 1 s de V2):
a rota de t'' avaliada a (v_c', v_a', t' = t'' v_a/v_a') e a rota ciente do reinicio daquela maquina. G1: os layouts de V2 (mesmo metodo e orcamentos de `rodar_v2`: GTSP de arcos + PCGLNS, Pi de FECHAMENTO,
2 rodadas, tempo = min(120, 20 + arcos/4) s por rodada, portais reduzidos). G2: uma familia DENSA sintetica (n = 30, 60, 100 contornos pequenos disjuntos, 3 sementes por n) resolvida por completo (referencia de
contorno: PCGLNS por peca, 10 sementes, 30 s; segmento: t'' em 0, 0,06, 0,25 e 1 s).
Cenarios de maquina (premissas, nao medidas; 1 unidade de desenho = 1 mm): ar v_a' = 140 m/min (o da fibra mais lenta listada no N1) e corte v_c' = 15 e 30 m/min. T_seg = L_seg/v_c' + ar/v_a' + t' R;
T_contorno = L_P/v_c' + A_P/v_a' + t' n (convencao do artigo) ou t' min(n, R) (CONSERVADORA: o contorno e cobrado so as corridas da rota, como no restante do N1). Previsoes G-1..G-5 e regras: docs/59.
Uso: python escala_fibra_aninhados.py autoteste | selecionar | rodar [--workers 3] [--parte g1|g2|ambas] | verificar | resultados     (`rodar` idempotente: pula o que tem JSON; `verificar` ANTES de `resultados`)
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

OUT = os.path.join(AQUI, "fibra_aninhados_resultados")
MANIFESTO = os.path.join(AQUI, "confirmacao_estudos_manifesto.json")
VC, VA = 100.0 / 6.0, 400.0                       # o benchmark (unidades de desenho por segundo)
VA_F = 140.0 * 1000.0 / 60.0                      # 140 m/min em mm/s (1 unidade = 1 mm)
VC_F = {15: 15.0 * 1000.0 / 60.0, 30: 30.0 * 1000.0 / 60.0}
T_NOVOS = (0.06, 0.25)
T_DENSO = (0.0, 0.06, 0.25, 1.0)
DENSOS = [(n, s) for n in (30, 60, 100) for s in (1, 2, 3)]
SEMENTE_DENSO = 2026112100


def v2_dados():
    return {os.path.basename(f)[3:-5]: json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "v2_resultados", "v2_*.json")))}


def selecionados():
    """Os layouts de V2 do artigo: >= 2 contornos, referencia de contorno e solucoes de segmento verificadas em t = 0 e t = 1 s."""
    return [nome for nome, r in v2_dados().items() if r.get("n_contornos", 0) >= 2 and r.get("peca_10s") and r["peca_10s"].get("fo_media") and r.get("seg_t0", {}).get("melhor") and r.get("seg_t1", {}).get("melhor")]


def _segmento(polys, pares, ts, log=print):
    """Replica o ramo de segmento de `rodar_v2._job` para cada t: 2 rodadas, Pi de fechamento refinada, portais reduzidos. -> {t: {melhor, historico, arcos}}, orcamento."""
    import ea0_lib as lib
    import instancias_lcpp1 as il
    import segmento_gtsp as sg
    import caminho_honesto as ch
    aneis = [list(p.exterior.coords)[:-1] for p in polys]
    coords, req, dono = il.requeridas_com_noding(aneis)
    pos = {c: i for i, c in enumerate(coords)}
    aneis_ids = [[pos[(round(float(x), il.ND), round(float(y), il.ND))] for x, y in a_ if (round(float(x), il.ND), round(float(y), il.ND)) in pos] for a_ in aneis]
    grafo = {"coords": coords, "req": req, "dono": dono, "aneis_ids": aneis_ids}
    L_seg = float(sum(ch._cheb(coords[u], coords[v]) for u, v in req))
    saida, orc = {}, 0.0
    for t in ts:
        fech, melhor, hist = None, None, []
        for rd in range(2):
            inst = sg.montar(polys, pares, t_perf=t, fechamento=fech, portais="reduzido", grafo=grafo)
            tempo = int(min(120, 20 + inst["E"] / 4))
            t1 = time.time()
            tour = sg.resolver(inst, tempo=tempo, semente=rd)
            orc += time.time() - t1
            if tour is None:
                hist.append({"rodada": rd, "erro": "sem tour"})
                continue
            cam = sg.caminho_do_tour(inst, tour)
            h = ch.fo_honesta(cam, t_perf=t, ja_contiguo=True)
            v = ch.verificar(h["caminho"], polys, pares_pi=pares)
            ar = sum(ch._cheb(s.coords[0], s.coords[-1]) for s, tg in h["caminho"] if tg == "d")
            reg = {"rodada": rd, "fo": h["fo"], "ar": ar, "n_perf": h["n_perfuracoes"], "contiguo": v["contiguo"], "geo_ok": v["geo_ok"], "viol_fechamento": v["violacoes_pi_relaxada"], "viol_estrita": v["violacoes_pi_estrita"]}
            hist.append(reg)
            if v["contiguo"] and v["geo_ok"] and v["violacoes_pi_relaxada"] == 0 and (melhor is None or reg["fo"] < melhor["fo"]):
                melhor = reg
            fech = sg.ultima_aresta_por_contorno(inst, tour)
        saida[f"{t:g}"] = {"melhor": melhor, "historico": hist, "arcos": inst["E"]}
        log(f"   t''={t:g}: {'ok' if melhor else 'SEM solucao verificada'} (arcos {inst['E']})")
    return saida, orc, L_seg


def _job_g1(a):
    nome, arq = a
    f = os.path.join(OUT, f"g1_{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    import dxf_parser
    import ea0_lib as lib
    hc = lib.hc
    v2 = v2_dados()[nome]
    nm, polys, info = dxf_parser.load_instance_dxf(arq)
    pares = hc._detectar_precedencia(list(polys))
    t0 = time.time()
    seg, orc, L_seg = _segmento(polys, pares, T_NOVOS, log=lambda s: print(f"[{time.strftime('%H:%M:%S')}] {nome}: {s}", flush=True))
    rec = {"instancia": nome, "fonte": "v2", "n_contornos": v2["n_contornos"], "n_pares_pi": v2["n_pares_pi"], "L_pecas": v2["L_pecas"], "L_segmento": v2["L_segmento"], "L_segmento_novo": L_seg,
           "fo_contorno_media": v2["peca_10s"]["fo_media"],
           "seg": {"0": v2["seg_t0"]["melhor"], "1": v2["seg_t1"]["melhor"], **{k: x["melhor"] for k, x in seg.items()}}, "orcamento_s": orc, "tempo_total_s": time.time() - t0}
    os.makedirs(OUT, exist_ok=True)
    json.dump(rec, open(f, "w"), indent=1)
    return nome, f"novos t'': " + ", ".join(f"{k}:{'ok' if x['melhor'] else 'SEM'}" for k, x in seg.items()) + f" em {rec['tempo_total_s']:.0f}s"


def gerar_denso(n, semente):
    """Familia densa: n contornos pequenos DISJUNTOS (quadrados de 6-10 mm ou 12-gonos de raio 3-5 mm) em grade com passo 14-20 mm e jitter de +-1,5 mm; a origem (0,0) fica fora (canto)."""
    import math
    import random
    from shapely.geometry import Polygon, box
    rng = random.Random(semente)
    cols = max(2, round(math.sqrt(n * 1.6)))
    passo = rng.uniform(14, 20)
    polys = []
    for k in range(n):
        i, j = divmod(k, cols)
        cx, cy = 15 + j * passo + rng.uniform(-1.5, 1.5), 15 + i * passo + rng.uniform(-1.5, 1.5)
        if rng.random() < 0.5:
            s = rng.uniform(6, 10)
            polys.append(box(cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2))
        else:
            r = rng.uniform(3, 5)
            polys.append(Polygon([(cx + r * math.cos(2 * math.pi * q / 12), cy + r * math.sin(2 * math.pi * q / 12)) for q in range(12)]))
    return polys


def _contorno_media(polys, sementes=10, tempo=30):
    import ea0_lib as lib
    from rodar_v2 import _pcglns_peca
    inst = lib.montar_instancia(polys)
    fos = []
    for s in range(sementes):
        x = _pcglns_peca(polys, inst, tempo, s)
        if x:
            fos.append(x["fo"])
    return statistics.mean(fos) if fos else None, len(fos)


def _job_g2(a):
    n, s = a
    nome = f"denso_n{n}_s{s}"
    f = os.path.join(OUT, f"g2_{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    import ea0_lib as lib
    import caminho_honesto as ch
    hc = lib.hc
    polys = gerar_denso(n, SEMENTE_DENSO + 100 * n + s)
    pares = hc._detectar_precedencia(list(polys))
    t0 = time.time()
    L_pecas = float(sum(ch._cheb(a_, b_) for p in polys for a_, b_ in zip(list(p.exterior.coords)[:-1], list(p.exterior.coords)[1:])))
    fo_c, nn = _contorno_media(polys)
    seg, orc, L_seg = _segmento(polys, pares, T_DENSO, log=lambda x: print(f"[{time.strftime('%H:%M:%S')}] {nome}: {x}", flush=True))
    rec = {"instancia": nome, "fonte": "denso", "n_contornos": len(polys), "n_pares_pi": len(pares), "L_pecas": L_pecas, "L_segmento": L_seg, "fo_contorno_media": fo_c, "n_sementes_contorno": nn,
           "seg": {k: x["melhor"] for k, x in seg.items()}, "orcamento_s": orc, "tempo_total_s": time.time() - t0}
    os.makedirs(OUT, exist_ok=True)
    json.dump(rec, open(f, "w"), indent=1)
    return nome, f"contorno {fo_c:.1f} s; " + ", ".join(f"{k}:{'ok' if x['melhor'] else 'SEM'}" for k, x in seg.items()) + f" em {rec['tempo_total_s']:.0f}s"


# ---------------------------------------------------------------------------------------------------------------- cenarios e analise
def custo_segmento(rec, t_pp, vc, va, t_linha):
    """Tempo da rota resolvida para t'' = t_pp avaliada na maquina (vc, va) com reinicio t' = t_linha."""
    m = rec["seg"][t_pp]
    return rec["L_segmento"] / vc + m["ar"] / va + t_linha * m["n_perf"], m


def custo_contorno(rec, vc, va, t_linha, R, conservador):
    n, L_P = rec["n_contornos"], rec["L_pecas"]
    A_P = (rec["fo_contorno_media"] - L_P / VC) * VA          # ar de contorno em unidades de desenho
    return L_P / vc + A_P / va + t_linha * (min(n, R) if conservador else n), A_P


def economia(rec, t_pp, vc_m, conservador=True, base_t0=False):
    """% do tempo total do contorno e % do tempo NAO cortante (ar + reinicios) economizados pela rota de t'' (casada) na maquina de corte vc_m m/min e ar de 140 m/min, t' = t'' v_a/v_a'."""
    vc, va = VC_F[vc_m], VA_F
    t_linha = float(t_pp) * VA / VA_F
    chave = "0" if base_t0 else t_pp
    Ts, m = custo_segmento(rec, chave, vc, va, t_linha)
    Tc, A_P = custo_contorno(rec, vc, va, t_linha, m["n_perf"], conservador)
    nc_c = Tc - rec["L_pecas"] / vc
    nc_s = Ts - rec["L_segmento"] / vc
    return 100.0 * (Tc - Ts) / Tc, (100.0 * (nc_c - nc_s) / nc_c if nc_c > 0 else None), 100.0 * (A_P / va) / Tc, m


def carregar():
    return [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "g1_*.json")))], [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "g2_*.json")))]


def autoteste():
    """(1) a conta do cenario reproduz o `fo` guardado de V2 (fo = L/v_c + ar/v_a + t n_perf) em t'' = 0 e 1 s para todos os layouts selecionados e a referencia de contorno; (2) o gerador denso e determinista,
    disjunto e longe da origem; (3) o ramo de segmento e a referencia de contorno rodam num brinquedo denso de 8 contornos (nao e dado do estudo)."""
    from shapely.geometry import Point
    sel = selecionados()
    assert len(sel) >= 40, len(sel)
    V2 = v2_dados()
    maxerr = 0.0
    for nome in sel:
        r = V2[nome]
        for t, k in ((0.0, "seg_t0"), (1.0, "seg_t1")):
            m = r[k]["melhor"]
            fo = r["L_segmento"] / VC + m["ar"] / VA + t * m["n_perf"]
            maxerr = max(maxerr, abs(fo - m["fo"]) / m["fo"])
    assert maxerr < 1e-6, maxerr
    print(f"{len(sel)} layouts selecionados; FO guardada = L/v_c + ar/v_a + t R (erro relativo maximo {maxerr:.2e}) OK")
    a, b = gerar_denso(30, 7), gerar_denso(30, 7)
    assert [p.wkt for p in a] == [p.wkt for p in b]
    for i, p in enumerate(a):
        assert p.is_valid and p.distance(Point(0, 0)) > 5 and all(p.distance(q) > 2 for q in a[:i])
    print("gerador denso OK")
    import ea0_lib as lib
    hc = lib.hc
    polys = gerar_denso(8, 99)
    pares = hc._detectar_precedencia(list(polys))
    assert pares == []
    t0 = time.time()
    seg, orc, L_seg = _segmento(polys, pares, (0.0, 0.06), log=lambda x: print("  ", x))
    assert all(x["melhor"] for x in seg.values()), seg
    fo_c, nn = _contorno_media(polys, sementes=2, tempo=5)
    assert fo_c and nn == 2
    rec = {"instancia": "brinquedo", "n_contornos": 8, "L_pecas": L_seg, "L_segmento": L_seg, "fo_contorno_media": fo_c, "seg": {k: x["melhor"] for k, x in seg.items()}}
    e = economia(rec, "0.06", 15)
    print(f"brinquedo denso: contorno {fo_c:.3f} s; economia (t''=0,06; 15 m/min) = {e[0]:.4f}% do total, {e[1]:.3f}% do nao cortante, ar = {e[2]:.2f}% do total  [{time.time() - t0:.0f} s]")
    print("AUTOTESTE OK")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def verificar():
    """(1) codigo e protocolo iguais aos congelados; (2) estrutura G-S1..G-S3 em cada resultado: solucoes verificadas (contiguas, geometria ok, 0 violacoes de fechamento), FO = L/v_c + ar/v_a + t'' R."""
    ok = True
    man = json.load(open(MANIFESTO))
    for a, h in man["arquivos"].items():
        igual = sha(os.path.join(AQUI, a)) == h
        ok &= igual
        print(("OK       " if igual else "ALTERADO ") + a)
    g1, g2 = carregar()
    print(f"{len(g1)} layouts reais (G1), {len(g2)} densos (G2)")
    for r in g1 + g2:
        probs = []
        for t, m in r["seg"].items():
            if not m:
                probs.append(f"G-S1: t''={t} sem solucao verificada")
                continue
            if not (m.get("contiguo") and m.get("geo_ok") and m.get("viol_fechamento") == 0):
                probs.append(f"G-S1: t''={t} solucao nao verificada")
            fo = r.get("L_segmento_novo", r["L_segmento"]) / VC + m["ar"] / VA + float(t) * m["n_perf"]
            if abs(fo - m["fo"]) > 1e-6 * m["fo"]:
                probs.append(f"G-S2: FO de t''={t} != L/v_c + ar/v_a + t R")
        if r["fonte"] == "v2" and abs(r["L_segmento_novo"] - r["L_segmento"]) > 1e-6 * r["L_segmento"]:
            probs.append("G-S3: L_segmento novo difere do de V2")
        ok &= not probs
        print(f"  {r['instancia'][:70]}: " + ("; ".join(probs) if probs else "estrutura OK"))
    print("VERIFICACAO " + ("OK" if ok else "COM PROBLEMAS"))
    sys.exit(0 if ok else 1)


def resultados():
    g1, g2 = carregar()
    f = lambda x, d=3: "--" if x is None else f"{x:.{d}f}"
    L = ["# Escala de maquina de fibra: layouts aninhados reais (G1) e layouts densos (G2) (docs/59, Estudo G)", "",
         "Economia da rota ciente do reinicio (resolvida em t'' no benchmark e avaliada na maquina de ar 140 m/min, t' = t'' v_a/v_a') sobre a referencia de contorno; convencao CONSERVADORA (contorno cobrado so as corridas da rota).", ""]
    resumo = {}
    for nome, G in (("G1 (layouts reais, CPPLib)", g1), ("G2 (densos sinteticos)", g2)):
        if not G:
            continue
        L += [f"## {nome}: {len(G)} layouts", "", "| corte (m/min) | t'' (s) | t' (ms) | economia do total: mediana | max | % com > 0,1% | economia do nao cortante: mediana | parcela de ar no total: mediana | corridas: mediana (contornos) |", "|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
        for vc_m in (15, 30):
            for t_pp in ("0", "0.06", "0.25", "1"):
                if not all(t_pp in r["seg"] and r["seg"][t_pp] for r in G):
                    continue
                es = [economia(r, t_pp, vc_m) for r in G]
                tot = [e[0] for e in es]
                nc = [e[1] for e in es if e[1] is not None]
                arp = [e[2] for e in es]
                runs = [r["seg"][t_pp]["n_perf"] for r in G]
                resumo[(nome[:2], vc_m, t_pp)] = tot
                L.append(f"| {vc_m} | {t_pp} | {float(t_pp) * VA / VA_F * 1000:.1f} | {statistics.median(tot):.4f}% | {max(tot):.4f}% | {100 * sum(1 for x in tot if x > 0.1) / len(tot):.0f}% | "
                         f"{statistics.median(nc):.2f}% | {statistics.median(arp):.2f}% | {statistics.median(runs):.0f} ({statistics.median([r['n_contornos'] for r in G]):.0f}) |")
        L.append("")
    fmt = lambda b: "SUSTENTADA" if b else "NAO SUSTENTADA"
    if g1 and all("0.06" in r["seg"] and r["seg"]["0.06"] and "0.25" in r["seg"] and r["seg"]["0.25"] for r in g1):
        med = lambda t: statistics.median([economia(r, t, 15)[0] for r in g1])
        m0, m06, m25, m1 = med("0"), med("0.06"), med("0.25"), med("1")
        tot06 = [economia(r, "0.06", 15)[0] for r in g1]
        corr = sum(1 for r in g1 if r["seg"]["0.06"]["n_perf"] >= r["seg"]["0.25"]["n_perf"] >= r["seg"]["1"]["n_perf"])
        G1 = m0 + 1e-4 >= m06 and m06 + 1e-4 >= m25 and m25 + 1e-4 >= m1
        G2 = statistics.median(tot06) <= 1.0 and max(tot06) <= 3.0
        G3 = m25 <= 0.1 and m1 <= 0.1
        G4 = sum(1 for x in tot06 if x > 0.01) >= 0.5 * len(tot06)
        G5 = corr >= 0.8 * len(g1)
        L += [f"G-1 (medianas nao crescentes em t''; 15 m/min): {m0:.4f}, {m06:.4f}, {m25:.4f}, {m1:.4f} %: **{fmt(G1)}**.",
              f"G-2 (t''=0,06 s, t'=10,3 ms: mediana <= 1,0% e max <= 3,0% do total): mediana {statistics.median(tot06):.4f}%, max {max(tot06):.4f}%: **{fmt(G2)}**.",
              f"G-3 (t'' = 0,25 e 1 s: mediana <= 0,1%): {m25:.4f}%, {m1:.4f}%: **{fmt(G3)}**.",
              f"G-4 (a t''=0,06 s a rota ainda economiza > 0,01% em >= 50% dos layouts): {sum(1 for x in tot06 if x > 0.01)} de {len(tot06)}: **{fmt(G4)}**.",
              f"G-5 (corridas nao crescentes em t'' em >= 80% dos layouts): {corr} de {len(g1)}: **{fmt(G5)}**."]
    if g2:
        e06 = [economia(r, "0.06", 15)[0] for r in g2 if "0.06" in r["seg"] and r["seg"]["0.06"]]
        ar06 = [economia(r, "0.06", 15)[2] for r in g2 if "0.06" in r["seg"] and r["seg"]["0.06"]]
        ar_g1 = statistics.median([economia(r, "0.06", 15)[2] for r in g1]) if g1 else None
        G6 = bool(e06) and max(e06) <= 0.2 and ar_g1 is not None and statistics.median(ar06) >= 3 * ar_g1
        L += [f"G-6 (densos: a t''=0,06 s a economia e <= 0,2% do total em todos e a parcela de ar de contorno e >= 3 vezes a mediana dos layouts reais — a tensao entre ter ar para poupar e poder poupa-lo): "
              f"economia max {max(e06):.4f}%, parcela de ar mediana {statistics.median(ar06):.2f}% contra {f(ar_g1, 2)}% nos reais: **{fmt(G6)}**." if e06 else "G-6: sem dados."]
    open(os.path.join(AQUI, "RESULTADOS_ESCALA_FIBRA.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "autoteste"
    arg = lambda fl, tp, d: tp(sys.argv[sys.argv.index(fl) + 1]) if fl in sys.argv else d
    if modo == "autoteste":
        autoteste()
    elif modo == "selecionar":
        sel = selecionados()
        print(len(sel), "layouts de V2")
    elif modo == "verificar":
        verificar()
    elif modo == "resultados":
        resultados()
    elif modo == "rodar":
        workers, parte = arg("--workers", int, 3), arg("--parte", str, "ambas")
        import rodar_v2 as rv
        arqs = rv.listar_v2()
        itens = []
        if parte in ("g1", "ambas"):
            itens += [(_job_g1, (n, arqs[n])) for n in selecionados()]
        if parte in ("g2", "ambas"):
            itens += [(_job_g2, a) for a in DENSOS]
        print(f"[{time.strftime('%H:%M:%S')}] Escala de fibra: {len(itens)} tarefas ({parte}), {workers} processos", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(fn, a) for fn, a in itens]
            for fu in futs:
                n_, msg = fu.result()
                print(f"[{time.strftime('%H:%M:%S')}] {n_}: {msg}", flush=True)
        print("ESCALA DE FIBRA CONCLUIDA", flush=True)
