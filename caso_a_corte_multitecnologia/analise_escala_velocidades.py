"""
analise_escala_velocidades.py  --  SENSIBILIDADE DA ECONOMIA EXATA MAXIMA AS VELOCIDADES DE CORTE E DE VOO (18/11/2026; EXPLORATORIO, POS-HOC; nenhum solver e rodado)
===========================================================================================================================================================
Motivo (revisao duplo-cega de 18/11, `docs/45` §5): o benchmark corta a v_c = 100/6 u/s e voa a v_a = 400 u/s; com 1 u = 1 mm (NAO confirmado) sao 1 m/min e 24 m/min, isto e, chapa GROSSA com voo
lento, enquanto as faixas de reinicio de "chapa fina" do N1 (Tabela 12) sao de chapa fina e as maquinas citadas voam a 140-170 m/min. O ponto de equilibrio (em segundos) e a fatia do tempo total
dependem dessa escala.

Reprocessamento (so valores exatos GUARDADOS: `teto_resultados/*.json`, `milp_certificado_resultados/*.json`). Com velocidades (v_c', v_a'):
    T'(t) = L/v_c' + A/v_a' + t R = L/v_c' + (v_a/v_a') [ A/v_a + t'' R ],   t'' = t v_a'/v_a,
logo o plano otimo para (v_c', v_a', t) e o plano otimo do problema ORIGINAL com restart t''; a economia em segundos e (v_a/v_a') vezes a original em t''; so o denominador (T_P') muda com v_c'.
AUTOTESTE: com (v_c, v_a) do benchmark a curva reproduz `analise_ancoras_por_espessura.curva_exata()` (afirmado por assert).
As velocidades de corte de chapa fina (5, 15, 30 m/min) sao PREMISSAS (docs/35: sem fonte lida; classe "thin" de `analise_ancoras_por_espessura.CLASSES`); entram como CENARIOS, nao como fatos.
Uso: python analise_escala_velocidades.py   (imprime o relatorio em markdown; as funcoes `dados()` e `CENARIOS` sao usadas por `manuscrito/gerar_tabelas_n1.py`)
"""
import glob
import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import analise_ancoras_por_espessura as ae  # noqa: E402
import teto_certificado as tc  # noqa: E402

VC, VA = ae.VC, ae.VA                                  # unidades de desenho por segundo (benchmark)
TS = ae.TS_CURVA
MMIN = 1000.0 / 60.0                                   # u/s por m/min (1 u = 1 mm)
NIL = 0.005                                            # % abaixo do qual a mediana da economia e tratada como nula
# (chave, rotulo, v_c m/min, v_a m/min) -- v_a = 140 m/min e o menor dos valores de fabricante do N1 (BLM LS7); 170 m/min: TRUMPF, Bystronic, Salvagnini
# (as chaves so tem letras: viram nomes de macro LaTeX)
CENARIOS = [
    ("Bench", "Benchmark", 1.0, 24.0),
    ("ThinA", "Thin sheet, slow", 5.0, 140.0),
    ("ThinB", "Thin sheet, medium", 15.0, 140.0),
    ("ThinC", "Thin sheet, fast", 30.0, 140.0),
    ("Med", "Medium plate", 2.0, 140.0),
]


def _dados_guardados():
    T = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(AQUI, "teto_resultados", "*.json"))}
    MJ = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "milp_certificado_resultados", "*.json")))]
    return T, MJ


def curva(vc_u, va_u, T=None, MJ=None):
    """-> {t_grade_original: [saving % por layout]} para as velocidades (vc_u, va_u) em u/s; so layouts disjuntos sem furos com MILP provado (em t = 0, RPP exato)."""
    if T is None:
        T, MJ = _dados_guardados()
    esc = VA / va_u
    out = {t: [] for t in TS}
    for reg in MJ:
        r = T[reg["instancia"]]
        L, n = r["L_corte"], r["n_contornos"]
        AP, As = r["dp"]["ar_otimo_contorno"], r["ar_otimo"]
        for t in TS:
            if t == 0.0:
                Q = min(AP, As) / VA                    # RPP exato (layout disjunto sem furos)
            else:
                x = reg["t"].get(str(t))
                if not x or not x.get("otimo"):
                    continue
                Q = x["M"] - L / VC                     # tempo sem corte do plano otimo, velocidades originais
            QP = AP / VA + t * n
            tp = L / vc_u + esc * QP
            tb = L / vc_u + esc * Q
            sv = 100.0 * (tp - tb) / tp
            out[t].append(max(0.0, sv) if sv > -1e-6 else sv)
    return out


def dados():
    """-> lista de dicts por cenario: curva, t escalado, fatia do voo, certificado, limites R1/R3 escalados."""
    T, MJ = _dados_guardados()
    # autoteste: o cenario do benchmark reproduz a curva exata do N1
    ref, _ = ae.curva_exata()
    cb = curva(VC, VA, T, MJ)
    for t in TS:
        assert len(ref[t]) == len(cb[t]) and np.allclose(ref[t], cb[t], atol=1e-9), ("autoteste falhou", t)
    R = [r for r in T.values() if r.get("P0") is not None]
    Dj = [r for r in R if tc.disjunta(r)]
    out = []
    for chave, rotulo, vc_m, va_m in CENARIOS:
        vc_u, va_u = vc_m * MMIN, va_m * MMIN
        c = curva(vc_u, va_u, T, MJ)
        esc = VA / va_u
        med = {t: float(np.median(v)) for t, v in c.items() if v}
        mx = {t: float(max(v)) for t, v in c.items() if v}
        nil_t = next((t * esc for t in TS if t in med and med[t] <= NIL), None)       # primeiro t (em segundos do cenario) com mediana nula
        voo = [100.0 * (r["dp"]["ar_otimo_contorno"] / va_u) / (r["L_corte"] / vc_u + r["dp"]["ar_otimo_contorno"] / va_u) for r in Dj]
        tcs = [tc.t_cert(r, va_u) for r in Dj]
        out.append({"chave": chave, "rotulo": rotulo, "vc": vc_m, "va": va_m, "curva": c, "med": med, "max": mx, "n": {t: len(v) for t, v in c.items()},
                    "t_escalado": {t: t * esc for t in TS}, "nil_t": nil_t, "voo_med": float(np.median(voo)), "tcert_max": float(max(tcs)), "tcert_med": float(np.median(tcs)),
                    "r1": ae.LIM_R1 * esc, "r3": ae.LIM_R3 * esc})
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    D = dados()
    print("# Sensibilidade da economia exata maxima as velocidades (exploratorio, pos-hoc; reprocessamento de valores exatos guardados)\n")
    print("Autoteste do cenario do benchmark: reproduz `curva_exata()` (assert).\n")
    print("| Cenario | v_c (m/min) | v_a (m/min) | voo/total (mediana) | teto em t=0: mediana (max) | primeiro t com mediana nula (s) | t_cert max (s) | limite R1 (s) | limite R3 (s) |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for d in D:
        print(f"| {d['rotulo']} | {d['vc']:g} | {d['va']:g} | {d['voo_med']:.2f}% | {d['med'][0.0]:.2f}% ({d['max'][0.0]:.2f}%) | {d['nil_t']:.3g} | {d['tcert_max']:.3f} | {d['r1']:.4f} | {d['r3']:.3f} |")
    print("\nCurva por cenario (t em segundos do cenario; n = layouts resolvidos no ponto):")
    for d in D:
        print(f"\n{d['rotulo']} (v_c {d['vc']:g}, v_a {d['va']:g} m/min):")
        for t in TS:
            if t in d["med"]:
                print(f"  t = {d['t_escalado'][t]:.4f} s: n = {d['n'][t]:2d}, mediana {d['med'][t]:.2f}%, max {d['max'][t]:.2f}%")
