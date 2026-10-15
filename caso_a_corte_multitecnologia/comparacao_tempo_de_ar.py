"""
comparacao_tempo_de_ar.py  --  Os gaps do E-A0/TSH reportados sobre o tempo TOTAL (FO) ficam DILUIDOS pelo tempo de corte (constante): aqui, os mesmos resultados sobre o tempo de AR (nao cortante)
=========================================================================================================================================================================================
Em FO = L/v_cut + A/v_air a parcela L/v_cut nao depende da rota (no nivel de peca); logo "+0,87% de FO" pode ser uma diferenca de dezenas de por cento no tempo de ar. Este script recomputa, para as 84 layouts:
  - tempo de ar de cada metodo = FO - L_corte/v_cut, com L_corte = soma (Chebyshev) dos lados dos contornos (nivel de peca; MESMA constante para todos);
  - para a heuristica (modo original e com Pi) e para o TSH, o tempo de ar NATIVO de nivel de segmento (soma dos segmentos 'd' do caminho, mesma regra de `reclassificar_tags`);
e reporta os gaps em relacao ao tempo de ar do TSH (referencia de segmento sem Pi) e do PCGLNS (referencia de peca com Pi).
Uso: python comparacao_tempo_de_ar.py rodar [--workers 4] (grava `ar_resultados/`)  |  python comparacao_tempo_de_ar.py resumo > RESULTADOS_TEMPO_DE_AR.md
"""
import os
import sys
import json
import glob
import time
import statistics
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
OUT = os.path.join(AQUI, "ar_resultados")
EA0 = os.path.join(AQUI, "ea0_resultados")
METODOS_PECA = ["pcglns", "vns_pi", "heur_ls", "heur_vns", "mastri"]


def _cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _job(nome):
    f = os.path.join(OUT, f"ar_{nome}.json")
    if os.path.exists(f):
        return nome, "pulado"
    import rodar_ea0 as ea0
    import ea0_lib as lib
    hc = lib.hc
    v_cut, v_air = hc._DEFAULT_CONFIG["v_cut"], hc._DEFAULT_CONFIG["v_air"]
    polys = ea0._carregar(nome)
    r = {"instancia": nome, "n_pecas": len(polys), "v_cut": v_cut, "v_air": v_air}
    r["L_pecas"] = float(sum(_cheb(a, b) for p in polys for a, b in zip(list(p.exterior.coords)[:-1], list(p.exterior.coords)[1:])))
    for chave, enforce in (("heur_orig", False), ("heur_pi", True)):
        cfg = {**lib.CFG_BASE, "time_limit": 120, "enforce_precedence": enforce}
        res = hc.run_heuristic(list(polys), cfg)
        cam = hc.reclassificar_tags(res["caminho"])
        L = sum(_cheb(s.coords[0], s.coords[1]) for s, t in cam if t == "c")
        A = sum(_cheb(s.coords[0], s.coords[1]) for s, t in cam if t == "d")
        perf = sum(1 for i, (s, t) in enumerate(cam) if t == "c" and (i == 0 or cam[i - 1][1] != "c"))
        from tsh_segmento import saltos_caminho
        ns, ls = saltos_caminho(cam)
        r[chave] = {"L_corte": float(L), "A_ar": float(A), "n_perfuracoes": perf, "fo": float(res["fo_total"]), "n_saltos": ns, "comprimento_saltos": float(ls)}
    import tsh_segmento as tsh
    t = tsh.resolver_tsh(polys)
    r["tsh"] = {"L_corte": t["corte_cheb"], "A_ar": t["ar_cheb"], "n_perfuracoes": t["n_perfuracoes"], "fo": t["fo"]}
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f, "w"))
    return nome, f"L_pecas={r['L_pecas']:.0f} L_orig={r['heur_orig']['L_corte']:.0f} L_tsh={r['tsh']['L_corte']:.0f}"


def _media_fo(nome, metodo, tempo=30):
    v = []
    for f in glob.glob(os.path.join(EA0, f"ea0_{nome}_{metodo}_T{tempo}_s*.json")):
        d = json.load(open(f))
        if d.get("fo") is not None:
            v.append(d["fo_reavaliada"] if metodo.startswith("heur") and d.get("fo_reavaliada") is not None else d["fo"])
    return statistics.mean(v) if v else None


def gaps_peca():
    """Medianas dos gaps de FO e de TEMPO DE AR (nivel de peca, sobre o PCGLNS) por metodo + participacao do ar na FO do PCGLNS -- para os macros do manuscrito."""
    nomes = sorted(os.path.basename(f)[3:-5] for f in glob.glob(os.path.join(OUT, "ar_*.json")))
    res = {m: {"fo": [], "ar": []} for m in ["heur_pi", "heur_ls", "heur_vns", "vns_pi", "mastri"]}
    part = []
    for n in nomes:
        r = json.load(open(os.path.join(OUT, f"ar_{n}.json")))
        vc = r["L_pecas"] / r["v_cut"]
        pg = _media_fo(n, "pcglns")
        if pg is None:
            continue
        part.append(100 * (pg - vc) / pg)
        for m in res:
            fo = _media_fo(n, m)
            if fo is None:
                continue
            res[m]["fo"].append(100 * (fo / pg - 1))
            res[m]["ar"].append(100 * ((fo - vc) / (pg - vc) - 1))
    return {"n": len(part), "part_ar_pcglns": statistics.median(part),
            **{m: {"fo_med": statistics.median(v["fo"]), "ar_med": statistics.median(v["ar"]), "ar_media": statistics.mean(v["ar"])} for m, v in res.items() if v["fo"]}}


def resumo():
    nomes = sorted(os.path.basename(f)[3:-5] for f in glob.glob(os.path.join(OUT, "ar_*.json")))
    linhas = []
    for n in nomes:
        r = json.load(open(os.path.join(OUT, f"ar_{n}.json")))
        vc, va = r["v_cut"], r["v_air"]
        ar = {}
        for m in METODOS_PECA:
            fo = _media_fo(n, m)
            if fo is not None:
                ar[m] = (fo - r["L_pecas"] / vc) * 1.0                      # tempo de ar do nivel de peca (em s)
        ar["heur_pi_piece"] = None
        fo_hp = _media_fo(n, "heur_pi")
        if fo_hp is not None:
            ar["heur_pi_piece"] = fo_hp - r["L_pecas"] / vc
        for m in ("heur_orig", "heur_pi", "tsh"):
            ar[m + "_listado"] = r[m]["A_ar"] / va                          # tempo de ar LISTADO no caminho (como a FO do LCPP-main o conta)
            ar[m + "_nativo"] = (r[m]["A_ar"] + r[m].get("comprimento_saltos", 0.0)) / va   # + saltos entre segmentos nao contiguos (limite inferior do custo real)
        linhas.append((n, r, ar))
    print(f"# Tempo de ar (parcela não cortante) — {len(linhas)} layouts do CPPLib\n")
    print("Os gaps de FO do E-A0 diluem as diferenças pelo tempo de corte (constante). Aqui, o tempo de AR = FO − L/v_cut (peça) ou a soma dos segmentos 'd' (nativo de segmento), em s. "
          "Referência de **peça** (com Π): PCGLNS; referência de **segmento** (sem Π): TSH.\n")
    # participacao do ar
    part = [100 * (ar["pcglns"]) / (m["L_pecas"] / m["v_cut"] + ar["pcglns"]) for _, m, ar in linhas if "pcglns" in ar]
    print(f"Participação do ar na FO do PCGLNS (mediana): {statistics.median(part):.2f}% (min {min(part):.2f}%, máx {max(part):.2f}%).\n")
    print("## Nível de peça (com Π): gap do tempo de ar sobre o PCGLNS\n")
    print("| método | gap de FO (mediana) | **gap do tempo de ar (mediana)** | **média** | melhor / pior que o PCGLNS (nº de layouts) |")
    print("|---|---:|---:|---:|---:|")
    for m, nome in [("heur_pi_piece", "heurística (construção com Π)"), ("heur_ls", "construção + busca local"), ("heur_vns", "construção + VNS"), ("vns_pi", "VNS-Π"), ("mastri", "MASTRI (viola Π)")]:
        g_fo, g_ar = [], []
        for n, r, ar in linhas:
            if ar.get(m) is None or "pcglns" not in ar:
                continue
            vc = r["L_pecas"] / r["v_cut"]
            g_fo.append(100 * ((ar[m] + vc) / (ar["pcglns"] + vc) - 1))
            g_ar.append(100 * (ar[m] / ar["pcglns"] - 1))
        if g_ar:
            g_ar = np.array(g_ar)
            print(f"| {nome} | {statistics.median(g_fo):+.2f}% | {np.median(g_ar):+.1f}% | {g_ar.mean():+.1f}% | {int((g_ar < -1e-9).sum())} / {int((g_ar > 1e-9).sum())} |")
    print("\n## Nível de segmento: gap do tempo de ar sobre o TSH (sem Π)\n")
    print("| método | **gap do tempo de ar (mediana)** | **média** | melhor / pior que o TSH |")
    print("|---|---:|---:|---:|")
    for m, nome in [("heur_orig_listado", "heurística, modo original, ar **listado** (como a FO do LCPP-main; caminho NÃO contíguo)"), ("heur_orig_nativo", "heurística, modo original, ar listado **+ saltos** (limite inferior do custo real)"),
                    ("heur_pi_nativo", "heurística com Π (construção; caminho contíguo)")]:
        g = np.array([100 * (ar[m] / ar["tsh_nativo"] - 1) for _, _, ar in linhas])
        print(f"| {nome} | {np.median(g):+.1f}% | {g.mean():+.1f}% | {int((g < -1e-9).sum())} / {int((g > 1e-9).sum())} |")
    g = np.array([100 * (ar["pcglns"] / ar["tsh_nativo"] - 1) for _, _, ar in linhas if "pcglns" in ar])
    print(f"| PCGLNS (peça inteira, com Π) | {np.median(g):+.1f}% | {g.mean():+.1f}% | {int((g < -1e-9).sum())} / {int((g > 1e-9).sum())} |")
    print("\n## Controle: o comprimento de corte é o mesmo?\n")
    dif = [abs(r["heur_orig"]["L_corte"] - r["tsh"]["L_corte"]) / r["tsh"]["L_corte"] * 100 for _, r, _ in linhas]
    dif2 = [abs(r["L_pecas"] - r["tsh"]["L_corte"]) / r["tsh"]["L_corte"] * 100 for _, r, _ in linhas]
    print(f"Diferença relativa do comprimento de corte, heurística (nativo) × TSH: mediana {statistics.median(dif):.3f}%, máx {max(dif):.3f}%; soma dos lados dos contornos × TSH (arestas deduplicadas): mediana {statistics.median(dif2):.3f}%, máx {max(dif2):.3f}%.")
    perf = np.array([[r["tsh"]["n_perfuracoes"], r["heur_orig"]["n_perfuracoes"], r["heur_pi"]["n_perfuracoes"], r["n_pecas"]] for _, r, _ in linhas])
    print(f"Perfurações (corridas de corte), mediana: TSH {np.median(perf[:, 0]):.0f}; heurística original {np.median(perf[:, 1]):.0f}; heurística com Π {np.median(perf[:, 2]):.0f}; nº de peças {np.median(perf[:, 3]):.0f}.")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    if modo == "resumo":
        resumo()
        sys.exit(0)
    import rodar_ea0 as ea0
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    nomes = [n for n in sorted(ea0.listar()) if len(ea0._carregar(n)) >= 2]
    print(f"[{time.strftime('%H:%M:%S')}] tempo de ar: {len(nomes)} layouts, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, msg in ex.map(_job, nomes, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
    print("AR CONCLUIDO", flush=True)
