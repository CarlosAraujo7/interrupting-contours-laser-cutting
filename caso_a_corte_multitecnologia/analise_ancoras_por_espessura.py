"""
analise_ancoras_por_espessura.py  --  ANCORAS DE REINICIO POR ESPESSURA (literatura + derivacao) CONTRA A CURVA EXATA DA ECONOMIA MAXIMA (14/10/2026; exploratorio; plano B sem maquina; `docs/35`)
==================================================================================================================================================================================================
(1) Faixas do custo de reinicio por classe de espessura: PERFURACAO em ponto virgem (`t_perf`, da literatura: Hashemzadeh 2014, Garcia 2019, vendor claims) e RETOMADA em ponto ja cortado (`t_ret`,
    NAO medida por ninguem; derivada: pre-corte de l_pc / v_c + parada e arranque no vertice v_c^2 / a + levantar/descer do Z de 0 a 0,15 s, limitada acima por `t_perf`).
(2) Curva EXATA da economia maxima de qualquer plano sobre o otimo exato de nivel de contorno, em funcao de t: S(t) = (T_P*(t) - M(t)) / T_P*(t), com M(t) o otimo do MILP com custo de reinicio
    (`verificar_certificado_milp.py`) nos layouts disjuntos sem furos em que foi provado; em t = 0, M e o RPP exato.
(3) Classificacao: regime R1 (t <= 0,06 s), R2 (0,06 < t < 0,87 s), R3 (t >= 0,87 s; certificado: o nivel de contorno e otimo para todo layout disjunto estudado).
Uso: python analise_ancoras_por_espessura.py > RESULTADOS_ANCORAS_POR_ESPESSURA.md ; as funcoes `dados()` e `FAIXAS` sao usadas por `manuscrito/gerar_figuras_n1.py` e `gerar_tabelas_n1.py`.
"""
import glob
import json
import os
import sys
import statistics as st

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
OUT_MILP = os.path.join(AQUI, "milp_certificado_resultados")
OUT_TETO = os.path.join(AQUI, "teto_resultados")
VC, VA = 100.0 / 6.0, 400.0
LIM_R1, LIM_R3 = 0.06, 0.87
TS_CURVA = (0.0, 0.01, 0.03, 0.06, 0.1, 0.25, 0.5, 1.0)

# premissas EXPLICITAS (docs/35). Velocidades de corte em m/min; l_pc em mm; aceleracao de corte em mm/s2; levantar/descer do Z: 0 a 0,15 s.
L_PC = 2.0
A_CORTE = 10000.0
Z_LEVANTA = (0.0, 0.15)
CLASSES = {
    "thin": {"rotulo": "Thin sheet (up to 3 mm)", "vc": (5.0, 30.0), "perf": (0.002, 0.06), "perf_fontes": "Hashemzadeh 2014 (breakthrough 2-8 ms; tens of ms at lower power); on-the-fly piercing up to 5-6 mm (vendors)"},
    "med": {"rotulo": "Medium plate (9 to 12 mm)", "vc": (0.6, 2.0), "perf": (0.5, 2.0), "perf_fontes": "West 2018 (9 mm: 0.5-2 s); Prima Power 2015 (12 mm: < 1 s); Garcia 2019 (10 mm stainless/aluminium: <= 1.5 s)"},
    "thick": {"rotulo": "Thick plate (20 to 25 mm)", "vc": (0.5, 1.0), "perf": (2.0, 11.5), "perf_fontes": "Piranha-Whitney (25 mm, 12 kW: ~2 s); Garcia 2019 (20 mm, 5 kW: 8-11.5 s)"},
}


def faixas():
    """-> {classe: dict(perf=(lo, hi), ret=(lo, hi))}. perf inclui, no limite superior, o levantar/descer do Z; ret = pre-corte + parada/arranque + Z, limitada por perf."""
    out = {}
    for k, c in CLASSES.items():
        v_lo, v_hi = c["vc"][0] * 1000 / 60.0, c["vc"][1] * 1000 / 60.0              # mm/s
        pre_lo = L_PC / v_hi                                                         # corte mais rapido: pre-corte mais curto
        pre_hi = L_PC / v_lo
        parada_lo, parada_hi = 0.0, v_hi * v_hi / A_CORTE
        ret_lo = pre_lo + parada_lo + Z_LEVANTA[0]
        ret_hi = pre_hi + parada_hi + Z_LEVANTA[1]
        perf_lo, perf_hi = c["perf"][0], c["perf"][1] + Z_LEVANTA[1]
        out[k] = {"perf": (perf_lo, perf_hi), "ret": (ret_lo, min(ret_hi, perf_hi)), "rotulo": c["rotulo"]}
    return out


def regimes(lo, hi):
    """Regimes tocados por [lo, hi]."""
    R = []
    if lo <= LIM_R1:
        R.append("R1")
    if hi > LIM_R1 and lo < LIM_R3:
        R.append("R2")
    if hi >= LIM_R3:
        R.append("R3")
    return R


def curva_exata():
    """-> {t: [saving % por layout]} (so layouts disjuntos sem furos com MILP provado nesse t; em t = 0 o RPP exato)."""
    import teto_certificado as tc
    T = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(OUT_TETO, "*.json"))}
    out = {t: [] for t in TS_CURVA}
    lay = {t: [] for t in TS_CURVA}
    for f in sorted(glob.glob(os.path.join(OUT_MILP, "*.json"))):
        reg = json.load(open(f))
        r = T[reg["instancia"]]
        for t in TS_CURVA:
            if t == 0.0:
                lb2, tp = tc.teto_refinado(r, 0.0, VC, VA)
                sav = 100.0 * (tp - lb2) / tp
                out[t].append(sav)
                lay[t].append(reg["instancia"])
                continue
            x = reg["t"].get(str(t))
            if not x or not x.get("otimo"):
                continue
            lb2, tp = tc.teto_refinado(r, t, VC, VA)
            sav = 100.0 * (tp - x["M"]) / tp
            assert sav <= 100.0 * (tp - lb2) / tp + 1e-6, (reg["instancia"], t)                     # a economia exata nao pode passar do certificado
            out[t].append(max(0.0, sav) if sav > -1e-6 else sav)
            lay[t].append(reg["instancia"])
    return out, lay


def distancias_ao_otimo(ts=(0.0, 0.01, 0.06, 0.25, 1.0)):
    """Distancia ao OTIMO EXATO (MILP com custo de reinicio; t = 0: RPP exato) da heuristica do LCPP (formal, rota cega ao reinicio), da rota de arcos de t = 0 avaliada em t e do nivel de contorno (PCGLNS):
    -> {t: {'H': [%], 'G': [%], 'P': [%]}} por layout disjunto sem furos com MILP provado."""
    import teto_certificado as tc
    T = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(OUT_TETO, "*.json"))}
    out = {t: {"H": [], "G": [], "P": []} for t in ts}
    for f in sorted(glob.glob(os.path.join(OUT_MILP, "*.json"))):
        reg = json.load(open(f))
        r = T[reg["instancia"]]
        for t in ts:
            if t == 0.0:
                lb2, tp = tc.teto_refinado(r, 0.0, VC, VA)
                M = lb2                                                           # RPP exato (sem Pi; layout sem furos): otimo do problema
            else:
                x = reg["t"].get(str(t))
                if not x or not x.get("otimo"):
                    continue
                M = x["M"]
            h = r["H"].get(str(t))
            g = r["FO0_gtsp"] + t * r["R0_gtsp"]
            p = r["P0"] + t * r["n_contornos"]
            if h is not None:
                out[t]["H"].append(100.0 * (h / M - 1.0))
            out[t]["G"].append(100.0 * (g / M - 1.0))
            out[t]["P"].append(100.0 * (p / M - 1.0))
    return out


def dados():
    S, lay = curva_exata()
    return {"faixas": faixas(), "curva": S, "layouts": lay, "gaps": distancias_ao_otimo()}


def main():
    d = dados()
    print("# Âncoras de reinício por espessura contra a curva exata da economia máxima (14/10/2026; exploratório; plano B sem máquina)\n")
    print("Premissas explícitas: pré-corte ℓ = 2 mm (Dewil et al. 2015: \"um par de mm\"); aceleração de corte 10 m/s²; levantar/descer do Z de 0 a 0,15 s; velocidades de corte por classe: "
          + "; ".join(f"{c['rotulo']}: {c['vc'][0]}-{c['vc'][1]} m/min" for c in CLASSES.values()) + ". **A retomada (`t_ret`) não foi medida por nenhuma fonte encontrada: é derivada.**\n")
    print("| classe | perfuração t_perf (s) | regimes | retomada t_ret derivada (s) | regimes | fontes da perfuração |\n|---|---|---|---|---|---|")
    for k, f in d["faixas"].items():
        print(f"| {f['rotulo']} | {f['perf'][0]:.3g} a {f['perf'][1]:.3g} | {', '.join(regimes(*f['perf']))} | {f['ret'][0]:.3g} a {f['ret'][1]:.3g} | {', '.join(regimes(*f['ret']))} | {CLASSES[k]['perf_fontes']} |")
    print("\nRegimes: R1 t ≤ 0,06 s; R2 0,06 < t < 0,87 s; R3 t ≥ 0,87 s (certificado).\n")
    print("## Curva exata da economia máxima de qualquer plano sobre o ótimo de contorno (layouts disjuntos sem furos; MILP exato com custo de reinício; t = 0: RPP exato)\n")
    print("| t (s) | layouts | economia, mediana (%) | máxima (%) |\n|---:|---:|---:|---:|")
    for t in TS_CURVA:
        v = d["curva"][t]
        if v:
            print(f"| {t:g} | {len(v)} | {st.median(v):.3f} | {max(v):.3f} |")
    print("\n## Distância ao ótimo exato em função de t (mesmos layouts; % acima do ótimo do MILP; t = 0: RPP exato)\n")
    print("| t (s) | layouts | heurística do LCPP (cega ao reinício), mediana / máx. | rota de arcos de t = 0, mediana / máx. | nível de contorno (PCGLNS), mediana / máx. |\n|---:|---:|---|---|---|")
    for t, g in d["gaps"].items():
        if g["P"]:
            f = lambda v: f"{st.median(v):+.3f} / {max(v):+.3f}" if v else "—"
            print(f"| {t:g} | {len(g['P'])} | {f(g['H'])} | {f(g['G'])} | {f(g['P'])} |")
    print("\n**Leitura:** a economia máxima só é positiva para t abaixo de um ponto de equilíbrio exato (por layout); acima dele o nível de contorno é ótimo. As faixas por espessura devem ser lidas contra essa curva.")


if __name__ == "__main__":
    main()
