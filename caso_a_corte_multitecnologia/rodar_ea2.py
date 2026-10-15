"""
rodar_ea2.py  --  E-A2 (plano 07, WP4.5): TETO DE GANHO do roteamento por perfil de tecnologia
==============================================================================================
Pergunta: quanto do tempo total de uma peca/layout e GASTO FORA DO CORTE (deslocamento em vazio + perfuracao)? Essa fracao e o TETO do que qualquer
otimizacao de roteamento pode economizar. Se for ~0,5%, nenhum otimizador de rota importa; se for 10-30% (plasma fino, escalas pequenas), importa.

Metodo: para cada uma das instancias do CPPLib com precedencia (84 com >= 2 pecas), roda a heuristica proposta (construcao com Pi, MST rapida, sem busca local)
e extrai do caminho RECLASSIFICADO: comprimento de corte (Chebyshev), comprimento em vazio (Chebyshev) e numero de perfuracoes (corridas contiguas de corte).
Para cada PERFIL (laser original do LCPP + plasma Hypertherm 45A em 8 espessuras, `perfil_tecnologia.py`) e cada ESCALA k (mm por unidade do DXF; o CPPLib
NAO tem escala confirmada -- k e uma sensibilidade, nao um fato):
    t_corte = k*L_corte / v_cut ;  t_vazio = k*L_vazio / v_air ;  t_perf = n_perf * tempo_perfuracao ;  fracao nao cortante = (t_vazio + t_perf)/total.
O comprimento de corte e CONSTANTE por layout (todas as arestas uma vez), entao so L_vazio e n_perf dependem da rota.
Saidas: `ea2_resultados/ea2_<instancia>.json`; `RESULTADOS_EA2.md` (modo resumo). Criterio G1 do plano 07: fracao nao cortante >= 5% em pelo menos um perfil.
Uso:  python rodar_ea2.py rodar [--limite N]   |   python rodar_ea2.py resumo > RESULTADOS_EA2.md
"""
import os, sys, json, time, statistics, warnings

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import ea0_lib as lib           # liga hc.MST_RAPIDA = True
import rodar_ea0 as ea0
import heuristic_core as hc
import perfil_tecnologia as pt
from scipy.spatial.distance import chebyshev

OUT = os.path.join(AQUI, "ea2_resultados")
KS = [0.1, 0.5, 1.0, 2.0]


def n_perfuracoes(cam):
    n, ant = 0, None
    for seg, tag in cam:
        if tag == "c" and ant != "c":
            n += 1
        ant = tag
    return n


def rodar_uma(nome):
    f = os.path.join(OUT, f"ea2_{nome}.json")
    if os.path.exists(f):
        return
    polys = ea0._carregar(nome)
    if len(polys) < 2:
        return
    t0 = time.time()
    res = hc.run_heuristic(list(polys), {**lib.CFG_BASE, "time_limit": 120, "enforce_precedence": True})
    if not res["caminho"]:
        return
    cam = hc.reclassificar_tags(res["caminho"])
    Lc = sum(chebyshev(s.coords[0], s.coords[-1]) for s, t in cam if t == "c")
    La = sum(chebyshev(s.coords[0], s.coords[-1]) for s, t in cam if t == "d")
    os.makedirs(OUT, exist_ok=True)
    json.dump({"instancia": nome, "n_pecas": len(polys), "L_corte": Lc, "L_vazio": La, "n_perf": n_perfuracoes(cam),
               "fo_laser_original": float(res["fo_total"]), "tempo_s": time.time() - t0}, open(f + ".tmp", "w"))
    os.replace(f + ".tmp", f)


def perfis():
    L = [("laser (LCPP original)", pt.LASER_ORIGINAL)]
    for esp in pt.PLASMA_ACO_45A_REFERENCIA_MM_S:
        L.append((f"plasma 45A {esp}", pt.perfil_plasma_por_espessura(esp)))
    return L


def fracoes(r, perfil, k):
    """-> (frac_nao_cortante, frac_vazio, frac_perfuracao, tempo_total_s). Laser original: v_cut/v_air do LCPP (unidades do DXF por s, k=1 por construcao)."""
    ehLaser = perfil is pt.LASER_ORIGINAL
    kk = 1.0 if ehLaser else k          # o perfil laser original ja esta em unidades do DXF (sem escala fisica)
    t_c = kk * r["L_corte"] / perfil.v_cut
    t_a = kk * r["L_vazio"] / perfil.v_air
    t_p = r["n_perf"] * perfil.tempo_perfuracao
    tot = t_c + t_a + t_p
    return (t_a + t_p) / tot, t_a / tot, t_p / tot, tot


def resumo():
    import glob
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "ea2_*.json")))]
    print(f"# E-A2 -- teto de ganho do roteamento (fracao do tempo fora do corte) -- {len(R)} instancias do CPPLib com precedencia\n")
    print("Fracao nao cortante = (tempo em vazio + tempo de perfuracao) / tempo total, com a rota da heuristica proposta (construcao com Pi). E o TETO do que "
          "qualquer otimizacao de rota pode economizar (o corte e constante). `k` = mm por unidade do DXF (**escala NAO confirmada**; o laser original do LCPP "
          "e em unidades do DXF e nao depende de k). Mediana [min; max] sobre as instancias. Criterio G1 do plano 07: >= 5% em pelo menos um perfil.\n")
    print("| perfil | " + " | ".join(f"k = {k}" for k in KS) + " |")
    print("|---|" + "---:|" * len(KS))
    G1 = False
    linhas = []
    for nome, p in perfis():
        cel = []
        for k in KS:
            v = [fracoes(r, p, k)[0] * 100 for r in R]
            if p is pt.LASER_ORIGINAL and k != KS[0]:
                cel.append("(= k independente)")
                continue
            cel.append(f"{statistics.median(v):.2f}% [{min(v):.2f}; {max(v):.2f}]")
            if max(v) >= 5.0 and statistics.median(v) >= 5.0:
                G1 = True
        print(f"| {nome} | " + " | ".join(cel) + " |")
    print()
    # decomposicao no caso k=1: vazio vs perfuracao (mediana)
    print("Decomposicao (mediana, k = 1): fracao em vazio / fracao em perfuracao\n")
    print("| perfil | em vazio | em perfuracao |")
    print("|---|---:|---:|")
    for nome, p in perfis():
        fa = statistics.median(fracoes(r, p, 1.0)[1] * 100 for r in R)
        fp = statistics.median(fracoes(r, p, 1.0)[2] * 100 for r in R)
        print(f"| {nome} | {fa:.2f}% | {fp:.2f}% |")
    print()
    nm = [(nome, statistics.median(fracoes(r, p, 1.0)[0] * 100 for r in R)) for nome, p in perfis()]
    melhor = max(nm, key=lambda x: x[1])
    print(f"**Criterio G1 (mediana >= 5% em algum perfil, k = 1):** {'ATENDIDO' if melhor[1] >= 5.0 else 'NAO atendido'}; maior fracao mediana: {melhor[0]} = {melhor[1]:.2f}%.")
    print(f"Menor fracao mediana (k = 1): {min(nm, key=lambda x: x[1])[0]} = {min(nm, key=lambda x: x[1])[1]:.2f}%.")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    if modo == "resumo":
        resumo()
    else:
        lim = int(sys.argv[sys.argv.index("--limite") + 1]) if "--limite" in sys.argv else 0
        nomes = sorted(ea0.listar())
        if lim:
            nomes = nomes[:lim]
        for i, n in enumerate(nomes):
            rodar_uma(n)
            if (i + 1) % 10 == 0:
                print(f"[{time.strftime('%H:%M:%S')}] {i + 1}/{len(nomes)}", flush=True)
        print("EA2 CONCLUIDO", flush=True)
