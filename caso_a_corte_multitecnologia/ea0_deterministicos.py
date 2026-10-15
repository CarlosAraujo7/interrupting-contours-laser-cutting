"""
ea0_deterministicos.py -- adianta, SEM depender de maquina ociosa, os metodos DETERMINISTICOS do E-A0 completo (heur_pi, heur_orig, mastri; T = 30, semente 0) nas 84 instancias.
Esses metodos nao tem orcamento de relogio (a construcao usa limite folgado de 60 s), entao a FO nao depende da carga da maquina. Idempotente (usa o mesmo `_job` e os mesmos arquivos do rodar_ea0.py).
Uso: python ea0_deterministicos.py [--tempo 30]
"""
import sys, time
import rodar_ea0 as ea0

if __name__ == "__main__":
    tempo = int(sys.argv[sys.argv.index("--tempo") + 1]) if "--tempo" in sys.argv else 30
    nomes = sorted(ea0.listar())
    n_ok = 0
    for i, n in enumerate(nomes):
        for m in ("heur_pi", "heur_orig", "mastri"):
            r = ea0._job((n, m, 0, tempo))
            n_ok += 1
        if (i + 1) % 10 == 0:
            print(f"[{time.strftime('%H:%M:%S')}] {i + 1}/{len(nomes)} instancias", flush=True)
    print("DETERMINISTICOS CONCLUIDO", flush=True)
