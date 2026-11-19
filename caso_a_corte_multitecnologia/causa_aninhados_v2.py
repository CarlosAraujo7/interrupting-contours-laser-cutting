"""
causa_aninhados_v2.py  --  CAUSA da economia que persiste a t = 1 s nos layouts ANINHADOS do CPPLib (V2) com rho_1 > 0,3  (19/11/2026; autorizado por Carlos; protocolo docs/52, escrito antes dos dados)
===================================================================================================================================================================================================
Achado de `docs/50`: a economia da rota de segmento (Pi de FECHAMENTO) sobre a referencia de contorno (Pi estrita) a t = 1 s cai com rho_1 = t v_a / (L/n), mas 4 layouts com rho_1 entre 0,31 e 0,45 ainda economizam
0,12% a 0,33% do tempo total, onde os layouts exatos (sem aninhamento) nao economizam nada. Duas explicacoes candidatas, testadas aqui com computacao nova:
  (a) ALIVIO DA PRECEDENCIA: o segmento corta o contorno externo em varias corridas (fechamento), o contorno nao pode. Teste: o nivel de segmento com Pi ESTRITA (todo arco do contorno interno antes de qualquer arco do
      externo), t = 1 s, MESMO metodo e orcamento de V2 (2 rodadas, tempo = min(120, 20 + arcos/4) s por rodada, noding como em `rodar_v2`), solucao verificada (contigua, cobertura, 0 violacoes de Pi estrita);
  (b) FOLGA DA REFERENCIA: o PCGLNS de contorno nao e otimo. Teste: DP exata do nivel de contorno com Pi (`ea0_otimo_dp.resolver_dp`) onde couber (teto de estados e de tempo por layout).
Layouts: os de V2 com rho_1 > 0,3 e economia conservadora a t = 1 s > 0,1% (a mesma regra de `gerar_tabelas_n1.macros_layouts_reais`; sao 4: cj1x_2, ck1x_3, snce_5, cj3x_1).
Uso: python causa_aninhados_v2.py selecionar | rodar [--workers 2] | dp [--limite 900] [--maxestados 300000] | verificar | resultados      (`rodar` e `dp` sao idempotentes)
"""
import glob
import json
import os
import statistics
import subprocess
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
OUT = os.path.join(AQUI, "causa_aninhados_resultados")
VC, VA = 100.0 / 6.0, 400.0
T_REINICIO = 1.0
RHO_LIM, ECONOMIA_MIN = 0.3, 0.1                  # a regra de selecao (fixada no protocolo)


def v2_dados():
    return {os.path.basename(f)[3:-5]: json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "v2_resultados", "v2_*.json")))}


def economia(v2, m):
    """Economia (% do tempo total) da rota `m` sobre a referencia de contorno a t = 1 s: o contorno cobrado um reinicio por contorno; versao CONSERVADORA: onde a rota tem menos corridas que contornos o contorno
    e cobrado so as corridas dela (a mesma convencao de `gerar_tabelas_n1.macros_layouts_reais`)."""
    n = v2["n_contornos"]
    tot = v2["peca_10s"]["fo_media"] + T_REINICIO * n
    return 100.0 * (tot - m["fo"]) / tot - 100.0 * max(0, n - m["n_perf"]) / tot


def selecionados():
    S = []
    for nome, r in v2_dados().items():
        if r.get("n_contornos", 0) < 2 or not r.get("peca_10s") or not r["seg_t0"]["melhor"] or not r["seg_t1"]["melhor"]:
            continue
        rho = T_REINICIO * VA / (r["L_pecas"] / r["n_contornos"])
        if rho > RHO_LIM and economia(r, r["seg_t1"]["melhor"]) > ECONOMIA_MIN:
            S.append(nome)
    return S


def _carregar(nome):
    import dxf_parser
    import rodar_v2 as rv
    nm, polys, info = dxf_parser.load_instance_dxf(rv.listar_v2()[nome])
    return polys


def _job_estrita(nome):
    f = os.path.join(OUT, f"est_{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    import ea0_lib as lib
    import instancias_lcpp1 as il
    import segmento_gtsp as sg
    import caminho_honesto as ch
    import rodar_estrita as rest
    hc = lib.hc
    polys = _carregar(nome)
    pares = hc._detectar_precedencia(list(polys))
    aneis = [list(p.exterior.coords)[:-1] for p in polys]                               # o mesmo grafo (noding) de `rodar_v2`
    coords, req, dono = il.requeridas_com_noding(aneis)
    pos = {c: i for i, c in enumerate(coords)}
    aneis_ids = [[pos[(round(float(x), il.ND), round(float(y), il.ND))] for x, y in a_ if (round(float(x), il.ND), round(float(y), il.ND)) in pos] for a_ in aneis]
    grafo = {"coords": coords, "req": req, "dono": dono, "aneis_ids": aneis_ids}
    t0 = time.time()
    melhor, hist = None, []
    for rd in range(2):
        inst = sg.montar(polys, pares, t_perf=T_REINICIO, fechamento=None, portais="reduzido", grafo=grafo)
        inst["ordem"] = rest.ordem_estrita(inst, pares)
        tempo = int(min(120, 20 + inst["E"] / 4))
        tour = sg.resolver(inst, tempo=tempo, semente=rd)
        if tour is None:
            hist.append({"rodada": rd, "erro": "sem tour"})
            continue
        cam = sg.caminho_do_tour(inst, tour)
        h = ch.fo_honesta(cam, t_perf=T_REINICIO, ja_contiguo=True)
        v = ch.verificar(h["caminho"], polys, pares_pi=pares)
        ar = sum(ch._cheb(s.coords[0], s.coords[-1]) for s, tg in h["caminho"] if tg == "d")
        reg = {"rodada": rd, "fo": h["fo"], "ar": ar, "n_perf": h["n_perfuracoes"], "ok": v["ok"], "viol_fechamento": v["violacoes_pi_relaxada"], "viol_estrita": v["violacoes_pi_estrita"], "tempo_pcglns_s": tempo}
        hist.append(reg)
        if v["ok"] and v["violacoes_pi_estrita"] == 0 and (melhor is None or reg["fo"] < melhor["fo"]):
            melhor = reg
    res = {"instancia": nome, "t_perf": T_REINICIO, "n_contornos": len(polys), "n_pares_pi": len(pares), "E": inst["E"], "melhor": melhor, "historico": hist, "tempo_total_s": time.time() - t0}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(f, "w"), indent=1)
    return nome, (f"fo={melhor['fo']:.3f} perf={melhor['n_perf']}" if melhor else "SEM SOLUCAO VIAVEL (estrita)") + f" em {res['tempo_total_s']:.0f}s"


def dp1(nome, maxe):
    import ea0_lib as lib
    import ea0_otimo_dp as dpm
    hc = lib.hc
    polys = _carregar(nome)
    inst = lib.montar_instancia(polys)
    t0 = time.time()
    r, est = dpm.resolver_dp(inst, maxe)
    res = {"instancia": nome, "n_contornos": len(polys), "estados": est, "maxestados": maxe}
    if r is None:
        res["resolvida"] = False
    else:
        custo, tour = r
        v_cut, v_air = hc._DEFAULT_CONFIG["v_cut"], hc._DEFAULT_CONFIG["v_air"]
        res.update({"resolvida": True, "custo_abstrato": custo, "fo_otimo": lib.fo_do_tour(polys, inst, tour, v_cut, v_air), "violacoes": lib.violacoes(inst, tour)})
    res["tempo_s"] = time.time() - t0
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, f"dp_{nome}.json"), "w"), indent=1)


def rodar_dp(limite, maxe):
    for nome in selecionados():
        f = os.path.join(OUT, f"dp_{nome}.json")
        if os.path.exists(f):
            print(f"{nome}: DP ja existe", flush=True)
            continue
        t0 = time.time()
        try:
            subprocess.run([sys.executable, "-X", "utf8", os.path.abspath(__file__), "dp1", nome, str(maxe)], timeout=limite, check=False)
        except subprocess.TimeoutExpired:
            os.makedirs(OUT, exist_ok=True)
            json.dump({"instancia": nome, "resolvida": False, "motivo": f"tempo limite de {limite:g} s"}, open(f, "w"), indent=1)
        r = json.load(open(f)) if os.path.exists(f) else {}
        print(f"[{time.strftime('%H:%M:%S')}] {nome}: DP " + (f"resolvida, FO {r['fo_otimo']:.4f} ({r['estados']} estados)" if r.get("resolvida") else f"NAO resolvida ({r.get('motivo', 'teto de estados ' + str(r.get('estados')))})") + f" em {time.time() - t0:.0f}s", flush=True)


def verificar():
    import newton_exato_tc as nw
    man = json.load(open(nw.MANIFESTO))
    ok = True
    for a, h in man["arquivos"].items():
        igual = nw.sha(os.path.join(AQUI, a)) == h
        ok &= igual
        print(("OK       " if igual else "ALTERADO ") + a)
    for nome in selecionados():
        f = os.path.join(OUT, f"est_{nome}.json")
        if not os.path.exists(f):
            print(f"  {nome}: sem resultado da estrita")
            ok = False
            continue
        r = json.load(open(f))
        m = r["melhor"]
        bom = bool(m) and m["ok"] and m["viol_estrita"] == 0 and m["viol_fechamento"] == 0
        ok &= bom
        print(f"  {nome}: estrita " + ("verificada (contigua, cobertura, 0 violacoes de Pi estrita)" if bom else "SEM solucao verificada"))
        fd = os.path.join(OUT, f"dp_{nome}.json")
        if os.path.exists(fd):
            d = json.load(open(fd))
            if d.get("resolvida"):
                bomd = d["violacoes"] == 0
                ok &= bomd
                print(f"     DP exata: FO {d['fo_otimo']:.4f}, violacoes de Pi {d['violacoes']}" + ("" if bomd else "  <-- PROBLEMA"))
    print("VERIFICACAO " + ("OK" if ok else "COM PROBLEMAS"))
    sys.exit(0 if ok else 1)


def resultados():
    V2 = v2_dados()
    L = ["# Causa da economia persistente nos layouts aninhados (t = 1 s)", "",
         "Economia = % do tempo total sobre a referencia de contorno (PCGLNS, media de 10 sementes; Pi estrita), versao conservadora (ver docstring). Fechamento = V2 guardado; estrita = rodada nova com o mesmo metodo e orcamento.", "",
         "| layout | n | rho_1 | corridas (fech./estr.) | economia fechamento | economia estrita | DP exata: FO / referencia - 1 |", "|---|---:|---:|---|---:|---:|---|"]
    sc, ss, gaps = [], [], []
    for nome in selecionados():
        r = V2[nome]
        n = r["n_contornos"]
        rho = T_REINICIO * VA / (r["L_pecas"] / n)
        m1 = r["seg_t1"]["melhor"]
        fe = os.path.join(OUT, f"est_{nome}.json")
        e = json.load(open(fe))["melhor"] if os.path.exists(fe) else None
        c = economia(r, m1)
        s = economia(r, e) if e else None
        fd = os.path.join(OUT, f"dp_{nome}.json")
        d = json.load(open(fd)) if os.path.exists(fd) else None
        gap = 100.0 * (r["peca_10s"]["fo_media"] / d["fo_otimo"] - 1.0) if d and d.get("resolvida") else None
        sc.append(c)
        ss.append(s)
        if gap is not None:
            gaps.append(gap)
        L.append(f"| {nome[-14:]} | {n} | {rho:.2f} | {m1['n_perf']} / " + (str(e['n_perf']) if e else "--") + f" | {c:+.3f}% | " + (f"{s:+.3f}%" if s is not None else "--")
                 + " | " + (f"{gap:+.4f}%" if gap is not None else "nao resolvida") + " |")
    ok_est = [(c, s) for c, s in zip(sc, ss) if s is not None]
    metade = sum(1 for c, s in ok_est if s < 0.5 * c)
    L += ["", f"P-C1 (alivio da precedencia): economia estrita < metade da de fechamento em {metade} de {len(ok_est)} layouts (a previsao: >= 3 de 4): " + ("SUSTENTADA" if metade >= 3 else "NAO SUSTENTADA") + ".",
          "P-C2 (folga da referencia): " + (f"DP exata resolvida em {len(gaps)} layouts; referencia acima do otimo em no maximo {max(gaps):+.4f}%: " + ("a referencia NAO e a causa (|gap| <= 0,02%)" if max(abs(g) for g in gaps) <= 0.02 else "a referencia TEM folga de mais de 0,02% em ao menos um layout")
                                              if gaps else "DP nao resolveu nenhum layout")  + "."]
    open(os.path.join(AQUI, "RESULTADOS_CAUSA_ANINHADOS.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "selecionar"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "selecionar":
        S = selecionados()
        print(len(S), "layouts:", *S, sep="\n  ")
    elif modo == "rodar":
        workers = arg("--workers", int, 2)
        nomes = selecionados()
        print(f"[{time.strftime('%H:%M:%S')}] estrita (t = {T_REINICIO:g} s) em {len(nomes)} layouts aninhados, {workers} processos", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for n, msg in ex.map(_job_estrita, nomes, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {n[-20:]}: {msg}", flush=True)
        print("ESTRITA CONCLUIDA", flush=True)
    elif modo == "dp":
        rodar_dp(arg("--limite", float, 900.0), arg("--maxestados", int, 300000))
    elif modo == "dp1":
        dp1(sys.argv[2], int(sys.argv[3]))
    elif modo == "verificar":
        verificar()
    elif modo == "resultados":
        resultados()
