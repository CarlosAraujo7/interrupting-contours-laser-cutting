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
  (3) 19/11/2026 (Carlos: "tudo que foi feito no outro artigo esta em LCPP-main"; lido SOMENTE LEITURA, nada importado nem copiado): o CSV FINAL por instancia do artigo irmao,
      `LCPP-main/pcgtsp_comparison/rerun_frente1_282_FINAL.csv` (fo_baseline = construcao; fo_forte = busca local forte; os padroes de `busca_local_forte` sao `time_limit=3.0`, `seed=0`),
      comparado com os FO listados guardados aqui: construcao IGUAL em 282 de 282; busca local forte igual em 232 de 282 e, nas outras 50, a guardada e MAIOR (pior), no maximo 0,26% (media 0,01%),
      nenhuma menor (a busca e limitada por relogio); nas 15 instancias em que o CSV publico (maio/2026) difere, o CSV FINAL e igual ao guardado (15 de 15): o CSV publico e de uma versao anterior da construcao.
      As constantes `FINAL_*` abaixo sao reconferidas contra o disco por `conferir_contra_final()` quando `LCPP-main/` e os caminhos guardados existem (a copia publica do repositorio do N1 nao os tem: so imprime o aviso).
Uso: python verificar_repositorio_publico_artigo_irmao.py   (confere `DIFERENCAS` e `FINAL_*` contra o disco e imprime o resumo; `resumo()` e usada por `manuscrito/gerar_tabelas_n1.py`)
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
# (3) comparacao com o CSV FINAL do artigo irmao em LCPP-main (somente leitura; 19/11/2026); recalculada por `conferir_contra_final()` quando LCPP-main existe
FINAL_CSV_REL = os.path.join("pcgtsp_comparison", "rerun_frente1_282_FINAL.csv")                       # relativo a LCPP-main (arquivo de 13/08/2026)
FINAL_CSV_SHA256 = "f986f6fd07d51d89f3ce61fd6178c41ebd7c04635e170f241b00f525a0b8964c"
FINAL_FONTES_SHA256 = {"src/busca_local_arvore.py": "4ff61f6c9d4b3458caf32bf818e57311640df8ee41d475fc33d5fd985b3e9116",    # onde `busca_local_forte` tem time_limit=3.0 e seed=0 como padroes
                       "src/heuristic_core.py": "02c9c87785844cf764ae5feed0eb9498092e034d542afaf69f609fb8fb6e0ce3"}
FINAL_CONS_IGUAIS = 282            # FO listado da construcao guardado == fo_baseline do CSV final (tolerancia relativa 1e-7)
FINAL_FORTE_IGUAIS = 232           # FO listado da busca local forte guardado == fo_forte do CSV final
FINAL_FORTE_MAIORES = 50           # nas demais o guardado e MAIOR (pior); nenhum e menor
FINAL_FORTE_REL_MAX_PCT = 0.2596   # maior diferenca relativa (guardado / final - 1), em %
FINAL_FORTE_REL_MEDIA_PCT = 0.0099  # media sobre as 282
FINAL_DIF15_IGUAIS_AO_NOSSO = 15   # das 15 de `DIFERENCAS`, em quantas o CSV final e igual ao guardado aqui


def resumo():
    rel = {n: 100.0 * (pub / loc - 1.0) for n, (loc, pub) in DIFERENCAS.items()}
    return {"n_instancias": INSTANCIAS_IDENTICAS, "fo_iguais": N_TOTAL - len(DIFERENCAS), "fo_diferentes": len(DIFERENCAS), "diferentes_pack": sum(1 for n in DIFERENCAS if n.endswith("_pack")),
            "dif_rel_max_pct": max(abs(v) for v in rel.values()), "todas_publicas_menores": all(v < 0 for v in rel.values()), "rel": rel,
            "final_cons_iguais": FINAL_CONS_IGUAIS, "final_forte_iguais": FINAL_FORTE_IGUAIS, "final_forte_maiores": FINAL_FORTE_MAIORES,
            "final_forte_max_pct": FINAL_FORTE_REL_MAX_PCT, "final_forte_media_pct": FINAL_FORTE_REL_MEDIA_PCT, "final_dif_iguais_nosso": FINAL_DIF15_IGUAIS_AO_NOSSO}


def conferir_contra_final(raiz_lcpp_main=None):
    """Recalcula as constantes FINAL_* a partir de `LCPP-main/` (SOMENTE LEITURA) e dos caminhos guardados; devolve None se algum dos dois nao existe (por exemplo, na copia publica do repositorio)."""
    import csv
    import hashlib
    raiz = raiz_lcpp_main or os.environ.get("LCPP_MAIN") or os.path.join(AQUI, "..", "..", "LCPP-main")
    caminho_csv = os.path.join(raiz, FINAL_CSV_REL)
    P = os.path.join(AQUI, "auditoria_lcpp1", "caminhos_282")
    if not (os.path.isfile(caminho_csv) and os.path.isdir(P)):
        return None
    fin = {r["instance"]: r for r in csv.DictReader(open(caminho_csv, encoding="utf-8"))}
    nos = {}
    for f in glob.glob(os.path.join(P, "*.json")):
        j = json.load(open(f, encoding="utf-8"))
        nos[j["instancia"]] = j
    com = sorted(set(nos) & set(fin))

    def igual(a, b):
        return abs(a - b) <= 1e-7 * max(1.0, abs(b))
    rel = [100.0 * (nos[n]["fo_listada_forte"] / float(fin[n]["fo_forte"]) - 1.0) for n in com]
    fontes = {}
    for rel_src in FINAL_FONTES_SHA256:
        p = os.path.join(raiz, *rel_src.split("/"))
        fontes[rel_src] = hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.isfile(p) else None
    return {"n": len(com), "sha256": hashlib.sha256(open(caminho_csv, "rb").read()).hexdigest(), "fontes": fontes,
            "cons_iguais": sum(1 for n in com if igual(nos[n]["fo_listada_original"], float(fin[n]["fo_baseline"]))),
            "forte_iguais": sum(1 for n in com if igual(nos[n]["fo_listada_forte"], float(fin[n]["fo_forte"]))),
            "forte_maiores": sum(1 for r in rel if r > 1e-7), "forte_menores": sum(1 for r in rel if r < -1e-7),
            "forte_max_pct": max(rel), "forte_media_pct": sum(rel) / len(rel),
            "dif15_iguais_ao_nosso": sum(1 for n in DIFERENCAS if n in fin and igual(nos[n]["fo_listada_original"], float(fin[n]["fo_baseline"])))}


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
    C = conferir_contra_final()
    if C is None:
        print("CSV final do artigo irmao (LCPP-main) ou caminhos guardados ausentes: as constantes FINAL_* nao foram reconferidas aqui")
    else:
        assert C["sha256"] == FINAL_CSV_SHA256, ("o CSV final mudou", C["sha256"])
        for rel_src, h in FINAL_FONTES_SHA256.items():
            assert C["fontes"][rel_src] == h, ("o codigo mudou", rel_src, C["fontes"][rel_src])
        assert C["n"] == N_TOTAL and C["forte_menores"] == 0, C
        assert (C["cons_iguais"], C["forte_iguais"], C["forte_maiores"], C["dif15_iguais_ao_nosso"]) == (FINAL_CONS_IGUAIS, FINAL_FORTE_IGUAIS, FINAL_FORTE_MAIORES, FINAL_DIF15_IGUAIS_AO_NOSSO), C
        assert abs(C["forte_max_pct"] - FINAL_FORTE_REL_MAX_PCT) < 5e-5 and abs(C["forte_media_pct"] - FINAL_FORTE_REL_MEDIA_PCT) < 5e-5, C
        print(f"CSV final do artigo irmao (LCPP-main, somente leitura): construcao igual em {C['cons_iguais']}/{C['n']}; busca local forte igual em {C['forte_iguais']}, maior em {C['forte_maiores']} "
              f"(max {C['forte_max_pct']:.3f}%, media {C['forte_media_pct']:.4f}%), menor em {C['forte_menores']}; nas {len(DIFERENCAS)} de `DIFERENCAS` o CSV final e igual ao guardado em {C['dif15_iguais_ao_nosso']}")
