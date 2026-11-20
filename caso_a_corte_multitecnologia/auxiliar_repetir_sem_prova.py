"""auxiliar_repetir_sem_prova.py -- repete, com limite maior por MILP, os layouts dos estudos E e F que ficaram sem prova (docs/59_desvios.md, D7).
Move o JSON antigo para `_limite<antigo>/` (dentro da pasta de resultados) e roda a MESMA `_job` do codigo congelado com o novo limite; o JSON novo substitui o antigo. So repete layouts com status != 'exato'.
Uso: python auxiliar_repetir_sem_prova.py <E|F> --limite 5400 [--workers 2]"""
import glob
import json
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import confirmacao_novos as cn  # noqa: E402
import grupo_comum as gc  # noqa: E402


def _job_E(a):
    nome, limite = a
    return gc._job((nome, limite))


def _job_F(a):
    nome, fam, n, s, limite = a
    return cn._job((nome, fam, n, s, limite))


if __name__ == "__main__":
    est = sys.argv[1]
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    limite, workers = arg("--limite", float, 5400.0), arg("--workers", int, 2)
    pasta = gc.OUT if est == "E" else cn.OUT
    alvo = []
    for f in sorted(glob.glob(os.path.join(pasta, "*.json"))):
        r = json.load(open(f))
        if r["status"] != "exato" and r.get("limite_s", 0) < limite:
            arq_ant = os.path.join(pasta, f"_limite{r.get('limite_s', 0):.0f}")
            os.makedirs(arq_ant, exist_ok=True)
            shutil.move(f, os.path.join(arq_ant, os.path.basename(f)))
            alvo.append(r["instancia"])
    print(f"[{time.strftime('%H:%M:%S')}] repetindo {len(alvo)} layouts de {est} com limite {limite:g} s: {', '.join(alvo)}", flush=True)
    if est == "E":
        itens = [(n, limite) for n in alvo]
        fn = _job_E
    else:
        mapa = {nome: (nome, fam, n, s, limite) for nome, fam, n, s in cn._lista()}
        itens = [mapa[n] for n in alvo]
        fn = _job_F
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n_, msg in ex.map(fn, itens, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n_}: {msg}", flush=True)
    print("REPETICAO CONCLUIDA", flush=True)
