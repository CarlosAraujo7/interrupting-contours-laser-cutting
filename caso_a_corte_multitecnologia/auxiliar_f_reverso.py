"""auxiliar_f_reverso.py -- ajuda a terminar o estudo F mais cedo: roda os layouts de `confirmacao_novos.py` na ORDEM INVERSA com mais processos (o `rodar` normal segue na ordem direta; os dois se encontram no meio).
NAO altera o codigo congelado: so importa `confirmacao_novos` e chama a mesma `_job` (idempotente: pula o layout que ja tem JSON; no encontro, no maximo um layout e calculado duas vezes, com o mesmo resultado).
Uso: python auxiliar_f_reverso.py [--workers 2] [--limite 1800]"""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import confirmacao_novos as cn  # noqa: E402

if __name__ == "__main__":
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    workers, limite = arg("--workers", int, 2), arg("--limite", float, 1800.0)
    itens = [(nome, fam, n, s, limite) for nome, fam, n, s in reversed(cn._lista())]
    print(f"[{time.strftime('%H:%M:%S')}] F (ordem inversa): {len(itens)} layouts, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n_, msg in ex.map(cn._job, itens, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n_}: {msg}", flush=True)
    print("F INVERSO CONCLUIDO", flush=True)
