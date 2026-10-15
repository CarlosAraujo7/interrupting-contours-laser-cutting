"""
perfil_anytime_ea0.py  --  perfil QUALIDADE x TEMPO do E-A0 (pilot de 12 instancias): quanto cada metodo entrega com T = 2, 5, 10, 30 s.
=====================================================================================================================================
Referencia = PCGLNS com T = 30 s (media das sementes) por instancia; gap = 100*(FO/ref - 1), FO no nivel de peca (`fo_from_path`), media sobre as
instancias COMPARAVEIS (a FO nativa da construcao coincide com a reavaliada; calculado com a heuristica de T = 30 s). Para cada metodo e T mostra o gap
medio e o tempo medio de parede por execucao. Metodos sem orcamento (heuristica so construcao; heuristica + descida) aparecem uma vez. O tempo de parede
do PCGLNS inclui ~10-12 s de partida/compilacao do Julia (nao e tempo do solver). `heur+VNS`: T e o orcamento do VNS depois da construcao (tempo total = construcao + T).
Uso:  python perfil_anytime_ea0.py [--limite 12] > RESULTADOS_EA0_ANYTIME.md
"""
import os, sys, json, statistics, warnings

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import rodar_ea0 as ea0

TS = [2, 5, 10, 30]
REF_T = 30


def main():
    lim = int(sys.argv[sys.argv.index("--limite") + 1]) if "--limite" in sys.argv else 12
    todas = sorted(ea0.listar())
    nomes = [todas[int(i * len(todas) / lim)] for i in range(lim)]
    ref = {}
    comp = {}
    for n in nomes:
        d = ea0._coletar(n, REF_T)
        if "pcglns" not in d or "heur_pi" not in d:
            continue
        ref[n] = d["pcglns"]["fo_med"]
        h = d["heur_pi"]
        comp[n] = abs(h["nativa_min"] - h["fo_min"]) <= 5e-4 * h["nativa_min"]
    ok = [n for n in ref if comp[n]]
    print(f"# E-A0 -- perfil qualidade x tempo (piloto: {len(ok)} instancias comparaveis de {len(nomes)}; referencia = PCGLNS a {REF_T} s)\n")
    print("Gap medio (%) sobre a FO media do PCGLNS(30 s), no nivel de peca; (entre parenteses) tempo medio de parede por execucao em s, maquina compartilhada. "
          "PCGLNS inclui ~10-12 s de partida do Julia. Ver o docstring de `perfil_anytime_ea0.py`.\n")
    print("| metodo | " + " | ".join(f"T = {t} s" for t in TS) + " |")
    print("|---|" + "---:|" * len(TS))
    for m, nm in (("pcglns", "PCGLNS"), ("vns_pi", "VNS-Pi (a partir do NearestFirst-Pi)"), ("heur_vns", "heuristica + VNS")):
        cel = []
        for t in TS:
            g, tt = [], []
            for n in ok:
                d = ea0._coletar(n, t)
                if m in d and d[m]["viol_max"] == 0:
                    g.append(100 * (d[m]["fo_med"] / ref[n] - 1)); tt.append(d[m]["t"])
            cel.append(f"{statistics.mean(g):+.2f}% ({statistics.mean(tt):.1f} s; n={len(g)})" if g else "--")
        print(f"| {nm} | " + " | ".join(cel) + " |")
    print()
    print("Metodos sem orcamento de tempo:\n")
    print("| metodo | gap medio | tempo medio (s) | #instancias |")
    print("|---|---:|---:|---:|")
    for m, nm in (("heur_pi", "heuristica (so construcao)"), ("heur_ls", "heuristica + busca local (descida)")):
        g, tt = [], []
        for n in ok:
            d = ea0._coletar(n, REF_T)
            if m in d and d[m]["viol_max"] == 0:
                g.append(100 * (d[m]["fo_med"] / ref[n] - 1)); tt.append(d[m]["t"])
        if g:
            print(f"| {nm} | {statistics.mean(g):+.2f}% | {statistics.mean(tt):.1f} | {len(g)} |")


if __name__ == "__main__":
    main()
