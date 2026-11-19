"""
analise_familias.py  --  INTERVALOS POR FAMILIA (bootstrap por cluster) PARA AS COMPARACOES NAS 282 INSTANCIAS  (19/11/2026; EXPLORATORIO, POS-HOC; nenhum solver e rodado)
================================================================================================================================================================
Motivo (revisao duplo-cega, `docs/45` R1-M3): as 282 instancias NAO sao independentes. 150 sao `art_<k>_<categoria>_<pack|sep>` (3 categorias x 25 padroes-base x {empacotado, separado}; o numero de
contornos de `art_k_regular`, `art_k_irregular` e `art_k_hole` difere, entao cada (categoria, k) e um padrao proprio) e 132 sao `<projeto>[_mod]_<pack|sep>` (33 projetos ESICUP x 4 variantes).
A unidade de reamostragem aqui e a FAMILIA: (categoria, k) para as `art_*` (75) e o projeto para as ESICUP (33), 108 familias. Bootstrap por cluster: reamostra familias com reposicao (B sorteios,
semente fixa) e recalcula cada estatistica sobre as instancias das familias sorteadas (estimador conjunto). Intervalos de 95% por percentis.
Uso: python analise_familias.py   (imprime um resumo; `familia`, `bootstrap` e `contar_familias` sao usadas por `manuscrito/gerar_tabelas_n1.py`)
"""
import glob
import json
import os
import re
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RE_ART = re.compile(r"^art_(\d+)_(regular|irregular|hole)_(pack|sep)$")
RE_ESI = re.compile(r"^(.+?)(?:_mod)?_(pack|sep)$")
SEMENTE, B = 2027, 10000


def familia(nome):
    m = RE_ART.match(nome)
    if m:
        return f"art_{m.group(2)}_{m.group(1)}"
    m = RE_ESI.match(nome)
    assert m, f"nome de instancia fora dos dois padroes: {nome}"
    return m.group(1)


def contar_familias(nomes):
    return len({familia(n) for n in nomes})


def verificar_estrutura(nomes):
    """Confere que as 282 formam 75 familias `art` de 2 instancias e 33 projetos de 4."""
    fam = {}
    for n in nomes:
        fam.setdefault(familia(n), []).append(n)
    art = {f: v for f, v in fam.items() if f.startswith("art_")}
    esi = {f: v for f, v in fam.items() if not f.startswith("art_")}
    assert len(nomes) == 282 and len(art) == 75 and all(len(v) == 2 for v in art.values()), (len(art), sorted({len(v) for v in art.values()}))
    assert len(esi) == 33 and all(len(v) == 4 for v in esi.values()), (len(esi), sorted({len(v) for v in esi.values()}))
    return len(fam)


def bootstrap(nomes, valores, estatisticas, B=B, semente=SEMENTE):
    """-> {chave: (inf, sup)} intervalos de 95% por percentis do bootstrap por cluster; `estatisticas` = {chave: funcao(vetor)}."""
    valores = np.asarray(valores, dtype=float)
    fam = np.array([familia(n) for n in nomes])
    ufam = np.unique(fam)
    idx = [np.where(fam == f)[0] for f in ufam]
    rng = np.random.default_rng(semente)
    amostras = {k: np.empty(B) for k in estatisticas}
    for b in range(B):
        esc = rng.integers(0, len(ufam), size=len(ufam))
        ii = np.concatenate([idx[c] for c in esc])
        v = valores[ii]
        for k, f in estatisticas.items():
            amostras[k][b] = f(v)
    return {k: (float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))) for k, a in amostras.items()}


def nomes_de_subconjuntos():
    """Nomes das instancias dos subconjuntos exatos usados no manuscrito (so leitura de JSONs guardados)."""
    sys.path.insert(0, AQUI)
    import teto_certificado as tc
    rpp = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "rpp_lcpp1_resultados", "*.json")))]
    resolvidas = [r["instancia"] for r in rpp if r["resolvida"]]
    sem_pi = [n for n in resolvidas if "_hole_" not in n]
    teto = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(AQUI, "teto_resultados", "*.json")))]
    teto = [r for r in teto if r.get("P0") is not None]
    disjuntas = [r["instancia"] for r in teto if tc.disjunta(r)]
    milp = [json.load(open(f))["instancia"] for f in sorted(glob.glob(os.path.join(AQUI, "milp_certificado_resultados", "*.json")))]
    return {"resolvidas": resolvidas, "sem_pi": sem_pi, "teto": [r["instancia"] for r in teto], "disjuntas": disjuntas, "milp": milp}


if __name__ == "__main__":
    S = nomes_de_subconjuntos()
    for k, v in S.items():
        print(f"{k:11s}: {len(v):3d} instancias em {contar_familias(v):3d} familias")
