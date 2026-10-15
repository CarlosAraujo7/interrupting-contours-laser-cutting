"""
avaliar_heuristica_formal.py  --  a heuristica do LCPP sob a FO FORMAL do LCPP-1 (Eq. 3) e sob custo de reinicio (t > 0), a partir dos caminhos guardados (`auditoria_lcpp1/caminhos_282/`)
=============================================================================================================================================================================
Tres convencoes para a MESMA sequencia de servicos (os trechos 'c' na ordem em que a heuristica os corta):
  listada     a FO do codigo do LCPP (`calcular_fo`): soma dos segmentos emitidos, sem contar os saltos entre segmentos nao contiguos (so informativa);
  poligonal   caminho executavel: os saltos sao contados (`caminho_honesto.fo_honesta`) e os trajetos 'd' emitidos (que percorrem trechos ja cortados) custam o seu comprimento;
  formal      a FO do LCPP-1 (Eq. 3): entre servicos consecutivos, o menor deslocamento disponivel; como a metrica de Chebyshev ponderada (Eq. 2) e uma metrica, e a CORDA DIRETA
              (custo 0 se o servico seguinte comeca onde o anterior terminou). A orientacao de cada servico e escolhida por DP exata (a orientacao listada nao e confiavel).
              Para t > 0 o DP minimiza ar + t * (nº de corridas); R = 1 + nº de interrupcoes.
A formal e a que corresponde ao problema definido no LCPP-1 e ao nosso GTSP de arcos (mesmo custo de transicao); a poligonal e o que o codigo emite.
Tambem conta, entre as corridas, as que comecam em vertice JA CORTADO (retomadas: no modelo de Dewil et al. custam um pre-cut, nao uma perfuracao) e as que comecam em vertice virgem.
Uso:  python avaliar_heuristica_formal.py [--t 0,0.25,0.5,1]  > RESULTADOS_HEURISTICA_FORMAL.md
"""
import os
import sys
import json
import glob
import warnings

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
from heuristic_core import _DEFAULT_CONFIG as D                     # noqa: E402

VC, VA = D["v_cut"], D["v_air"]
TOL = 1e-7
CAM = os.path.join(AQUI, "auditoria_lcpp1", "caminhos_282")


def _cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def servicos(caminho):
    """Trechos 'c' na ordem listada: [((x0, y0), (x1, y1))]."""
    return [((s[0], s[1]), (s[2], s[3])) for s in caminho if s[4] == "c"]


def fo_formal(caminho, t_perf=0.0, origem=(0.0, 0.0)):
    """FO formal (corda direta entre servicos consecutivos; DP exato sobre as orientacoes). -> dict(fo, corte, ar, corridas, virgens, retomadas)."""
    sv = servicos(caminho)
    n = len(sv)
    corte = sum(_cheb(a, b) for a, b in sv) / VC
    INF = float("inf")

    def pontas(i, o):
        a, b = sv[i]
        return (a, b) if o == 0 else (b, a)

    def trans(p, q):
        d = _cheb(p, q)
        return 0.0 if d <= TOL else d / VA + t_perf
    custo = [[INF, INF] for _ in range(n)]
    pai = [[None, None] for _ in range(n)]
    for o in (0, 1):
        custo[0][o] = _cheb(origem, pontas(0, o)[0]) / VA
    for i in range(1, n):
        for o in (0, 1):
            for q in (0, 1):
                c = custo[i - 1][q] + trans(pontas(i - 1, q)[1], pontas(i, o)[0])
                if c < custo[i][o] - 1e-12:
                    custo[i][o], pai[i][o] = c, q
    fim = [custo[n - 1][o] + _cheb(pontas(n - 1, o)[1], origem) / VA for o in (0, 1)]
    o = 0 if fim[0] <= fim[1] else 1
    ori = [0] * n
    for i in range(n - 1, -1, -1):
        ori[i] = o
        if i > 0:
            o = pai[i][o]
    ar = _cheb(origem, pontas(0, ori[0])[0]) / VA + _cheb(pontas(n - 1, ori[n - 1])[1], origem) / VA
    corridas = 1
    # inicios de corrida em vertice VIRGEM (nenhum trecho incidente cortado antes: exige perfuracao) x RETOMADAS (vertice ja cortado: so reiniciar/pre-cut), cf. docs/18 §4
    k = lambda p: (round(p[0], 6), round(p[1], 6))
    tocados = {k(pontas(0, ori[0])[0]), k(pontas(0, ori[0])[1])}
    virgens, retomadas = 1, 0
    for i in range(1, n):
        a, b = pontas(i, ori[i])
        d = _cheb(pontas(i - 1, ori[i - 1])[1], a)
        if d > TOL:
            ar += d / VA
            corridas += 1
            if k(a) in tocados:
                retomadas += 1
            else:
                virgens += 1
        tocados.add(k(a))
        tocados.add(k(b))
    return {"fo": corte + ar + t_perf * corridas, "corte": corte, "ar": ar, "corridas": corridas, "virgens": virgens, "retomadas": retomadas}


def fo_poligonal(caminho, t_perf=0.0):
    """FO executavel (saltos contados, trajetos 'd' emitidos pelo seu comprimento)."""
    from shapely.geometry import LineString
    import caminho_honesto as ch
    cam = [(LineString([(s[0], s[1]), (s[2], s[3])]), s[4]) for s in caminho]
    h = ch.fo_honesta(cam, t_perf=t_perf)
    return {"fo": h["fo"], "corridas": h["n_perfuracoes"], "saltos": h["n_saltos"]}


def carregar():
    R = {}
    for f in sorted(glob.glob(os.path.join(CAM, "*.json"))):
        r = json.load(open(f))
        R[r["instancia"]] = r
    return R


def categoria(n):
    for c in ("regular", "irregular", "hole"):
        if f"_{c}_" in n:
            return c
    return "esicup"


def main():
    ts = [float(x) for x in sys.argv[sys.argv.index("--t") + 1].split(",")] if "--t" in sys.argv else [0.0, 0.25, 0.5, 1.0]
    R = carregar()
    seg_dir = os.path.join(AQUI, "lcpp1_segmento_resultados")
    hon_dir = os.path.join(AQUI, "auditoria_lcpp1", "honesta_282")
    pct = lambda a, b: 100 * (a / b - 1)
    L = []
    for n, r in sorted(R.items()):
        c = r["forte"]
        f = {"nome": n, "cat": categoria(n), "listada": r["fo_listada_forte"], "poli0": fo_poligonal(c, 0.0)["fo"]}
        for t in ts:
            ff = fo_formal(c, t)
            f[f"formal_{t}"], f[f"corr_{t}"], f[f"retom_{t}"], f[f"virg_{t}"] = ff["fo"], ff["corridas"], ff["retomadas"], ff["virgens"]
        try:
            g = json.load(open(os.path.join(seg_dir, f"{n}.json")))
            h = json.load(open(os.path.join(hon_dir, f"{n}.json")))
            if g.get("melhor") and "fo_pcglns_honesta" in h:
                f["gtsp0"], f["gtsp_perf0"], f["peca0"], f["n_cont"] = g["melhor"]["fo"], g["melhor"]["n_perf"], h["fo_pcglns_honesta"], g["n_contornos"]
        except FileNotFoundError:
            pass
        L.append(f)
    C = [x for x in L if "gtsp0" in x]
    print(f"# A heurística do LCPP sob a FO formal do LCPP-1 (Eq. 3) e sob custo de reinício — {len(L)} instâncias com caminho guardado ({len(C)} com GTSP e PCGLNS por peça honestos)\n")
    print("Busca local forte (3 s, semente 0). **poligonal** = caminho executável como emitido (saltos contados); **formal** = corda direta entre serviços consecutivos, orientação por DP (`docs/18` §7).\n")
    a = np.array([pct(x["poli0"], x["listada"]) for x in L])
    b = np.array([pct(x["formal_0.0"], x["poli0"]) for x in L])
    print(f"- FO poligonal sobre a FO listada pelo código: mediana {np.median(a):+.3f}% (média {a.mean():+.3f}%).")
    print(f"- FO formal sobre a poligonal: mediana {np.median(b):+.3f}% (média {b.mean():+.3f}%); formal ≤ poligonal em {int((b <= 1e-9).sum())}/{len(b)}.\n")
    print("## t = 0 (convenção do LCPP-1): heurística × PCGLNS por peça × GTSP de arcos\n")
    print("| comparação | mediana | média | vitórias do primeiro |\n|---|---:|---:|---:|")
    for nome, fa, fb in (("heurística poligonal × PCGLNS por peça", "poli0", "peca0"), ("heurística formal × PCGLNS por peça", "formal_0.0", "peca0"),
                         ("heurística formal × GTSP de arcos (PCGLNS, 2 rodadas)", "formal_0.0", "gtsp0"), ("heurística poligonal × GTSP de arcos", "poli0", "gtsp0")):
        d = np.array([pct(x[fa], x[fb]) for x in C])
        print(f"| {nome} | {np.median(d):+.3f}% | {d.mean():+.3f}% | {int((d < 0).sum())}/{len(d)} |")
    print("\n### Por categoria (heurística formal)\n| categoria | n | × peça (mediana) | vitórias | × GTSP (mediana) | vitórias |\n|---|---:|---:|---:|---:|---:|")
    for cat in ("regular", "irregular", "hole", "esicup"):
        S = [x for x in C if x["cat"] == cat]
        if S:
            d1 = np.array([pct(x["formal_0.0"], x["peca0"]) for x in S])
            d2 = np.array([pct(x["formal_0.0"], x["gtsp0"]) for x in S])
            print(f"| {cat} | {len(S)} | {np.median(d1):+.3f}% | {int((d1 < 0).sum())}/{len(S)} | {np.median(d2):+.3f}% | {int((d2 < 0).sum())}/{len(S)} |")
    if len(ts) > 1:
        print("\n## t > 0 — tempo total (corte + ar + t·corridas)\n")
        print("Heurística: ordem de serviço fixa, orientação re-otimizada por DP para cada t (formal). Peça: PCGLNS por peça + t·(nº de contornos) (a rota de peça não muda com t: Proposição 1). "
              "**GTSP(t = 0) avaliado em t = limite superior do ótimo ciente de t** (a rota de t = 0 com o seu nº de corridas).\n")
        print("| t (s) | corridas da heurística (mediana) | corridas do GTSP(0) (mediana) | contornos (mediana) | heurística × peça | heurística × GTSP(0)@t | GTSP(0)@t × peça |\n|---:|---:|---:|---:|---:|---:|---:|")
        for t in ts:
            hp = np.array([pct(x[f"formal_{t}"], x["peca0"] + t * x["n_cont"]) for x in C])
            hg = np.array([pct(x[f"formal_{t}"], x["gtsp0"] + t * x["gtsp_perf0"]) for x in C])
            gp = np.array([pct(x["gtsp0"] + t * x["gtsp_perf0"], x["peca0"] + t * x["n_cont"]) for x in C])
            print(f"| {t} | {np.median([x[f'corr_{t}'] for x in C]):.0f} | {np.median([x['gtsp_perf0'] for x in C]):.0f} | {np.median([x['n_cont'] for x in C]):.0f} | "
                  f"{np.median(hp):+.3f}% ({int((hp < 0).sum())}/{len(C)}) | {np.median(hg):+.3f}% ({int((hg < 0).sum())}/{len(C)}) | {np.median(gp):+.3f}% ({int((gp < 0).sum())}/{len(C)}) |")
        t0 = ts[0]
        ret = np.array([x[f"retom_{t0}"] / max(1, x[f"retom_{t0}"] + x[f"virg_{t0}"]) for x in L])
        print(f"\n## Retomadas × inícios virgens (heurística, t = {t0}; `docs/18` §4.2)\nFração das corridas que **recomeçam num vértice já cortado** (retomada: custo de *pre-cut*/reinício, não de perfuração no modelo de Dewil): "
              f"mediana {100 * np.median(ret):.1f}% (quartis {100 * np.percentile(ret, 25):.1f}-{100 * np.percentile(ret, 75):.1f}%).")
        vv = np.array([x[f"virg_{t0}"] for x in L])
        print(f"Inícios virgens (perfurações físicas no modelo de Dewil): mediana {np.median(vv):.0f}; contornos: mediana {np.median([x['n_cont'] for x in C]):.0f}.")


if __name__ == "__main__":
    main()
