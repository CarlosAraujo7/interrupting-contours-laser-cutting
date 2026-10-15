"""
analise_mapa_regimes.py  --  MAPA DE REGIMES ancorado em fontes (docs/28; exploratorio; sem maquina real): rotas guardadas avaliadas em perfis de movimento e custos de reinicio tirados da literatura e de fichas de fabricantes
==============================================================================================================================================================================================================
Sem acesso a uma maquina, o parametro desconhecido (aceleracao, velocidade de voo, custo de reinicio) e varrido numa grade cujos pontos sao ANCORADOS em fontes (valores citados como indicativos, nao como medidas nossas):
  perfis de movimento (trapezoidal; Chebyshev; 1 unidade = 1 mm, nao confirmado)
    FIBRA_1G    v = 1667 mm/s (100 m/min), a = 10 000 mm/s^2 (~1,0 g)         = o perfil LASER do E-A1 / docs/25 (referencia compativel com o benchmark; sem fonte de fabricante)
    V170_1_4G   v = 2833 mm/s (170 m/min), a = 13 730 mm/s^2 (1,4 g)          [170 m/min simultaneos: TRUMPF TruLaser 3030 fiber, Bystronic ByStar Fiber 6225/8025, Salvagnini L3.G4 (paginas dos fabricantes);
                                                                               1,4 g: AMADA ENSIS AJe, 'sobre toda a area de trabalho'; combinacao de duas maquinas]
    BLM_2G      v = 2333 mm/s (140 m/min), a = 20 000 mm/s^2 (2,0 g)          [BLM Group LS7, pagina tecnica: 'Max XY speed 140 m/min', 'Maximum XY acceleration 20 m/s^2 (2g)'; uma so maquina]
    SALV_5G     v = 2600 mm/s (156 m/min), a = 49 033 mm/s^2 (5 g)            [Salvagnini L5: 156 m/min; 'ate 5 g em movimentos curtos' (chapa fina e media-fina); uma so maquina]
    DEWIL16     curva lida de Dewil et al. (2016, Fig. 3; CO2 4 kW)
  custos de reinicio t (s por corrida): 0; 0,01 (rompimento de fibra, chapa fina: 2-8 ms, Hashemzadeh et al. 2014, + folga); 0,06 (idem, ate ~60 ms com pouca pressao); 0,25 e 1,0 (chapa mais grossa: perfuracoes de
  ~0,5-2 s em 9-12 mm segundo materiais de fabricantes e, em aco-doce de 20 mm, 8-11,5 s medidos com laser de fibra de 5 kW por Garcia et al. 2019; so indicativo)
Rotas (sem reotimizar; as do V3 e do reparo): H (heuristica cega ao reinicio), Rep (heuristica reparada para t = 1), G (GTSP de arcos ciente de t = 0,25) contra P (peca, PCGLNS). Celula = mediana de T/T_P - 1 em % (60 instancias).
A reotimizacao completa por ponto da grade esta em docs/26-27 so para as curvas DEWIL16 e LASER (e deu ~0 de vantagem de roteamento).
Uso: python analise_mapa_regimes.py > RESULTADOS_MAPA_REGIMES.md
"""
import os
import sys
import warnings

import numpy as np

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
import analise_voo_nao_linear as vn                                        # noqa: E402

# v2 (14/10/2026): perfis ancorados em paginas de FABRICANTES conferidas (a v1, com anuncios de revenda nao conferidos, esta em RESULTADOS_MAPA_REGIMES_v1_anuncios_de_revenda.md)
PERFIS = {"FIBRA_1G": (1667.0, 10000.0), "V170_1_4G": (2833.0, 13730.0), "BLM_2G": (2333.0, 20000.0), "SALV_5G": (2600.0, 49033.0)}
PERFIS_ORDEM = ("FIBRA_1G", "V170_1_4G", "BLM_2G", "SALV_5G", "DEWIL16")
TS = (0.0, 0.01, 0.06, 0.25, 1.0)


def tau(d, perfil):
    if perfil == "DEWIL16":
        return vn.tau(d, "DEWIL16")
    v, a = PERFIS[perfil]
    d = np.asarray(d, float)
    return np.where(d >= v * v / a, d / v + v / a, 2.0 * np.sqrt(np.maximum(d, 0.0) / a))


def total(rota, perfil, t):
    corte, d, runs = rota
    return corte + float(tau(d, perfil).sum()) + t * runs


def main():
    L = vn.carregar()
    print("# Mapa de regimes ancorado em fontes (`docs/28`; exploratório; rotas guardadas, sem reotimizar)\n")
    print(f"{len(L)} instâncias. Célula: mediana de T(rota)/T(peça) − 1, em %. Perfis ancorados em páginas de fabricantes conferidas em 14/10/2026 e custos de reinício na literatura e em materiais de fabricantes (ver o cabeçalho de `analise_mapa_regimes.py`; a versão 1, com anúncios de revenda, está em `RESULTADOS_MAPA_REGIMES_v1_anuncios_de_revenda.md`).\n")
    for rota, nome in (("H", "Heurística (cega ao reinício)"), ("Rep1.0", "Heurística reparada (t = 1)"), ("G0.25", "Arcos ciente do reinício (t = 0,25)")):
        print(f"## {nome}\n")
        print("| perfil de movimento | " + " | ".join(f"t = {t:g} s" for t in TS) + " |\n|---|" + "---:|" * len(TS))
        for perfil in PERFIS_ORDEM:
            cel = []
            for t in TS:
                x = np.array([100 * (total(R[rota], perfil, t) / total(R["P"], perfil, t) - 1) for _, R, _ in L])
                cel.append(f"{np.median(x):+.2f}")
            print(f"| {perfil} | " + " | ".join(cel) + " |")
        print()
    # ar como fracao do tempo total do nivel de peca em cada perfil (peso do voo)
    print("## Peso do tempo de voo (nível de peça; mediana)\n\n| perfil | ar / tempo total |\n|---|---:|")
    for perfil in PERFIS_ORDEM:
        f = [float(tau(R["P"][1], perfil).sum()) / total(R["P"], perfil, 0.0) for _, R, _ in L]
        print(f"| {perfil} | {100 * np.median(f):.2f}% |")


if __name__ == "__main__":
    main()
