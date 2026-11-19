"""
verificar_repositorio_publico_artigo_irmao.py  --  O QUE O REPOSITORIO PUBLICO DO ARTIGO IRMAO (versao de congresso) TEM EM COMUM COM O QUE O N1 USOU  (19/11/2026)
==================================================================================================================================================================
Repositorio publico: https://github.com/cuttinglaser103-ai/lasercutting-codes-and-images (commit abaixo; sem licenca; README vazio; site de resultados: https://cuttinglaser103-ai.github.io/).
Dois testes, feitos em 19/11/2026 lendo o repositorio no navegador do app (nenhum arquivo foi baixado para o disco):
  (1) as 282 instancias `instances_ga_brkga/*.txt` comparadas com as usadas aqui (`LCPP-main/instances/generated/*.txt`): SHA-256 de cada arquivo e SHA-256 conjunto das 282 linhas "nome sha256";
  (2) `resultados_heuristica.csv` (coluna funcao_objetivo, 282 linhas) comparado com o FO LISTADO da etapa de construcao ('original') guardado em `auditoria_lcpp1/caminhos_282/*.json`
      (digests de blocos de 10 instancias e de 4 hex por instancia sobre "nome fo(5 casas)"; instancias em desacordo listadas abaixo com os dois valores).
Resultado: instancias byte a byte identicas nas 282; FO da construcao igual em 267 de 282; nas 15 restantes o valor publico e MENOR (ver `DIFERENCAS`). A busca local forte (3 s, semente 0) que o N1 avalia
NAO esta no repositorio publico (so a heuristica construtiva, tempo mediano de 0,82 s e maximo de 27,5 s no CSV).
Uso: python verificar_repositorio_publico_artigo_irmao.py   (confere `DIFERENCAS` contra o disco e imprime o resumo; `resumo()` e usada por `manuscrito/gerar_tabelas_n1.py`)
"""
import glob
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = "https://github.com/cuttinglaser103-ai/lasercutting-codes-and-images"
SITE = "https://cuttinglaser103-ai.github.io/"
COMMIT = "f306df6768655a2b072f7a4095c14594491fa0a5"                                                    # HEAD de `main` em 19/11/2026 (commit de 01/05/2026 21:23 UTC)
DATA_CONFERENCIA = "2026-11-19"
INSTANCIAS_IDENTICAS = 282
SHA256_CONJUNTO_INSTANCIAS = "247fd451dcd0496fe3a4749431510a088d6975399d091eabe9c639a375fa70cd"       # SHA-256 de "nome sha256" (ordenado, uma por linha) das 282, igual no GitHub e no disco
# instancia: (FO listado da construcao guardado no projeto, FO do CSV publico), 5 casas
DIFERENCAS = {
    "art_15_regular_pack": (165.73515, 165.55910), "art_16_hole_pack": (335.35981, 335.32019), "art_1_hole_pack": (227.42443, 227.39462),
    "han100_pack": (22248.00000, 22240.62000), "han120_pack": (25405.13000, 25371.93500), "han150_pack": (32661.98250, 32597.46750),
    "han80_pack": (15666.27250, 15651.32250), "han_pack": (53.84000, 53.78250), "jakobs2_pack": (45.29500, 45.18000),
    "jotika60_pack": (14512.14750, 14485.92750), "jotika70_pack": (16553.30250, 16543.18250), "marques_pack": (93.25000, 93.24000),
    "poly1a_sep": (19.56450, 19.56200), "shirts_pack": (105.47000, 105.41500), "shirts_sep": (106.38250, 106.38000),
}
N_TOTAL = 282


def resumo():
    rel = {n: 100.0 * (pub / loc - 1.0) for n, (loc, pub) in DIFERENCAS.items()}
    return {"n_instancias": INSTANCIAS_IDENTICAS, "fo_iguais": N_TOTAL - len(DIFERENCAS), "fo_diferentes": len(DIFERENCAS), "diferentes_pack": sum(1 for n in DIFERENCAS if n.endswith("_pack")),
            "dif_rel_max_pct": max(abs(v) for v in rel.values()), "todas_publicas_menores": all(v < 0 for v in rel.values()), "rel": rel}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    R = resumo()
    # confere os valores locais de DIFERENCAS contra o disco (so se os caminhos guardados existirem)
    P = os.path.join(AQUI, "auditoria_lcpp1", "caminhos_282")
    if os.path.isdir(P):
        ok = 0
        for n, (loc, _) in DIFERENCAS.items():
            j = json.load(open(os.path.join(P, n + ".json")))
            assert abs(j["fo_listada_original"] - loc) < 5e-6, (n, j["fo_listada_original"], loc)
            ok += 1
        print(f"valores locais conferidos contra os caminhos guardados: {ok}/{len(DIFERENCAS)}")
    print(f"{R['n_instancias']} instancias identicas | FO da construcao igual em {R['fo_iguais']} | diferente em {R['fo_diferentes']} ({R['diferentes_pack']} pack) | "
          f"maior diferenca relativa {R['dif_rel_max_pct']:.3f}% | publico sempre menor: {R['todas_publicas_menores']}")
    for n, v in sorted(R["rel"].items(), key=lambda kv: kv[1]):
        print(f"  {n}: {v:+.3f}%")
