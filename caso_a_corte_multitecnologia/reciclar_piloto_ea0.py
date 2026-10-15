"""
reciclar_piloto_ea0.py -- DEPOIS que a rodada completa do E-A0 terminar: separa os resultados estocasticos a T = 30 que vieram do PILOTO (gravados antes do lancamento da rodada completa, com a maquina
COMPARTILHADA) para `ea0_resultados_piloto_T30_maquina_compartilhada/`, de modo que o runner (idempotente) os RECALCULE na maquina ociosa; o protocolo exige maquina ociosa para os metodos com orcamento
de relogio. Os deterministicos (heur_pi, heur_orig, mastri) nao dependem de relogio e ficam. Uso: python reciclar_piloto_ea0.py [--executar]   (sem --executar so lista)
Depois: `bash ../lancar_ea0_completo.sh` (so recalcula o que faltar; ~10 min).
"""
import os, sys, glob, json, time, shutil
import rodar_ea0 as ea0

AQUI = os.path.dirname(os.path.abspath(__file__))
man = json.load(open(os.path.join(AQUI, "ea0_manifesto.json")))
t0 = time.mktime(time.strptime(man["inicio"], "%Y-%m-%d %H:%M:%S"))
destino = os.path.join(AQUI, "ea0_resultados_piloto_T30_maquina_compartilhada")
alvo = []
for m in ("heur_ls", "heur_vns", "pcglns", "vns_pi"):
    for f in glob.glob(os.path.join(ea0.OUT, f"ea0_*_{m}_T30_s*.json")):
        if os.path.getmtime(f) < t0:
            alvo.append(f)
print(f"{len(alvo)} arquivos estocasticos T30 anteriores ao lancamento ({man['inicio']}):")
for f in sorted(alvo)[:5]:
    print("  ", os.path.basename(f))
if "--executar" in sys.argv:
    os.makedirs(destino, exist_ok=True)
    for f in alvo:
        shutil.move(f, os.path.join(destino, os.path.basename(f)))
    print("movidos para", destino)
else:
    print("(simulacao; use --executar)")
