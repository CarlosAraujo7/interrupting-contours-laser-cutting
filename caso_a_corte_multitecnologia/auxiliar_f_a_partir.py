"""auxiliar_f_a_partir.py -- terceira fila para o estudo F: roda os layouts de `confirmacao_novos.py` a partir do indice `--inicio` (ordem direta), com o MESMO codigo congelado (`_job`, idempotente: pula o que ja tem JSON).
Mesmo estatuto de `auxiliar_f_reverso.py` (docs/59_desvios.md, D4): so acelera a execucao; no encontro das filas no maximo um layout e calculado duas vezes, com o mesmo resultado.
Uso: python auxiliar_f_a_partir.py --inicio 25 [--workers 2] [--limite 1800]"""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import confirmacao_novos as cn  # noqa: E402

if __name__ == "__main__":
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    workers, limite, ini = arg("--workers", int, 2), arg("--limite", float, 1800.0), arg("--inicio", int, 20)
    itens = [(nome, fam, n, s, limite) for nome, fam, n, s in cn._lista()][ini:]
    print(f"[{time.strftime('%H:%M:%S')}] F (a partir do indice {ini}): {len(itens)} layouts, {workers} processos", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n_, msg in ex.map(cn._job, itens, chunksize=1):
            print(f"[{time.strftime('%H:%M:%S')}] {n_}: {msg}", flush=True)
    print("F A PARTIR DE CONCLUIDO", flush=True)
