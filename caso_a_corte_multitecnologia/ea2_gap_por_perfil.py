"""
ea2_gap_por_perfil.py  --  a MESMA diferenca de qualidade de rota, expressa no tempo total de cada PERFIL de tecnologia
==========================================================================================================================
Os resultados do E-A0 (piloto, 11 instancias comparaveis, nivel de peca) estao na FO do laser original (corte a v_cut, vazio a v_air, SEM perfuracao). Como o
comprimento de corte e constante por layout (E-A2: `L_corte`) e todos os metodos cortam cada contorno de uma vez, o comprimento em vazio de cada metodo e
        L_vazio = (FO_laser - L_corte/v_cut_laser) * v_air_laser.
Para cada perfil P e escala k (mm por unidade do DXF; NAO confirmada) o tempo do metodo m e
        T_P(m) = k*L_corte/v_cut_P + k*L_vazio(m)/v_air_P + n_pecas * tempo_perfuracao_P            (n_perf = n_pecas: contornos inteiros; aproximacao)
e o GAP de m sobre o PCGLNS no perfil P e T_P(m)/T_P(PCGLNS) - 1. Mostra quanto a MESMA diferenca de rota pesa em cada tecnologia -- o efeito do perfil
no VALOR de otimizar a rota (o regret cruzado de rotas e ZERO por construcao quando o corte e a perfuracao sao constantes por contorno: a rota otima nao
depende do perfil; so o PESO da rota depende).
Entrada: `ea0_resultados/` (T = 30 s) e `ea2_resultados/`. Uso: python ea2_gap_por_perfil.py [--k 1.0] > RESULTADOS_EA2_GAP_POR_PERFIL.md
"""
import os, sys, json, statistics, warnings
warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import rodar_ea0 as ea0
import perfil_tecnologia as pt

METODOS = [("vns_pi", "VNS-Pi"), ("heur_ls", "heuristica + busca local"), ("heur_pi", "heuristica (construcao)")]


def main():
    k = float(sys.argv[sys.argv.index("--k") + 1]) if "--k" in sys.argv else 1.0
    todas = sorted(ea0.listar())
    nomes = [todas[int(i * len(todas) / 12)] for i in range(12)]
    dados = []
    for n in nomes:
        d = ea0._coletar(n, 30)
        f2 = os.path.join(AQUI, "ea2_resultados", f"ea2_{n}.json")
        if "pcglns" not in d or "heur_pi" not in d or not os.path.exists(f2):
            continue
        h = d["heur_pi"]
        if abs(h["nativa_min"] - h["fo_min"]) > 5e-4 * h["nativa_min"]:
            continue                                        # fora do mesmo problema (p7xj_4)
        e = json.load(open(f2))
        dados.append((n, d, e))
    L = pt.LASER_ORIGINAL
    print(f"# E-A2 (complemento) -- o gap de rota em cada perfil de tecnologia (k = {k}; {len(dados)} instancias comparaveis do piloto, FO a T = 30 s)\n")
    print("Gap de cada metodo sobre o PCGLNS, no TEMPO TOTAL de cada perfil, com as mesmas rotas. O corte e a perfuracao por contorno sao constantes; so o tempo em vazio muda "
          "entre os metodos, e seu peso relativo depende do perfil. Aproximacao: n_perf = n_pecas. **Escala `k` NAO confirmada** (sensibilidade: `--k`). "
          "O laser original do LCPP e em unidades do DXF (k nao se aplica).\n")
    cab = "| perfil | fracao nao cortante (mediana) | " + " | ".join(nm for _, nm in METODOS) + " |"
    print(cab)
    print("|---|---:|" + "---:|" * len(METODOS))
    perfis = [("laser (LCPP original)", L)] + [(f"plasma 45A {esp}", pt.perfil_plasma_por_espessura(esp)) for esp in pt.PLASMA_ACO_45A_REFERENCIA_MM_S]
    for nome, p in perfis:
        kk = 1.0 if p is L else k
        gaps = {m: [] for m, _ in METODOS}
        fr = []
        for n, d, e in dados:
            Lc = e["L_corte"]
            npec = e["n_pecas"]
            def T(m):
                fo = d[m]["fo_med"]
                Lv = (fo - Lc / L.v_cut) * L.v_air          # comprimento em vazio implicito (unidades do DXF)
                return kk * Lc / p.v_cut + kk * Lv / p.v_air + npec * p.tempo_perfuracao, kk * Lv / p.v_air + npec * p.tempo_perfuracao
            Tp, naop = T("pcglns")
            fr.append(100 * naop / Tp)
            for m, _ in METODOS:
                if m in d:
                    gaps[m].append(100 * (T(m)[0] / Tp - 1))
        print(f"| {nome} | {statistics.median(fr):.2f}% | " + " | ".join(f"{statistics.mean(gaps[m]):+.2f}%" for m, _ in METODOS) + " |")
    print()
    print("Leitura: a coluna 'heuristica (construcao)' no laser e o gap do E-A0 (~+0,7%); no plasma fino a MESMA rota custa varias vezes mais em tempo total, "
          "porque o corte e rapido e o deslocamento pesa mais. A rota otima, porem, e a mesma em todos os perfis.")


if __name__ == "__main__":
    main()
