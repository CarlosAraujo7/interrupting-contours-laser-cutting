"""progresso_ea0.py -- andamento do E-A0 completo (T = 30, 10 sementes): tarefas gravadas / esperadas e estimativa de termino. Uso: python progresso_ea0.py"""
import os, glob, time, json
import rodar_ea0 as ea0

AQUI = os.path.dirname(os.path.abspath(__file__))
nomes = [n for n in sorted(ea0.listar()) if len(ea0._carregar(n)) >= 2]
esp = {m: len(nomes) * (10 if m in ea0.ESTOCASTICOS else 1) for m in ea0.METODOS}
tot_esp = sum(esp.values())
feitos = {m: len(glob.glob(os.path.join(ea0.OUT, f"ea0_*_{m}_T30_s*.json"))) for m in ea0.METODOS}
# o glob de heur_ls casa tambem heur_ls (nome distinto) sem colisao; pcglns/vns_pi/heur_vns idem
man = os.path.join(AQUI, "ea0_manifesto.json")
t0 = time.mktime(time.strptime(json.load(open(man))["inicio"], "%Y-%m-%d %H:%M:%S")) if os.path.exists(man) else None
print(f"instancias: {len(nomes)}; tarefas esperadas: {tot_esp}")
for m in ea0.METODOS:
    print(f"  {m:10s} {feitos[m]:5d} / {esp[m]:5d}")
f_tot = sum(min(feitos[m], esp[m]) for m in ea0.METODOS)
print(f"TOTAL {f_tot} / {tot_esp} ({100 * f_tot / tot_esp:.1f}%)")
# estimativa: as tarefas estocasticas custam ~19 s em media (pilot: heur_vns 30, vns_pi 30, pcglns 14, heur_ls 1); 5 processos
resta_estoc = sum(max(0, esp[m] - feitos[m]) for m in ea0.ESTOCASTICOS)
custo_medio = {"heur_vns": 30.5, "vns_pi": 30.2, "pcglns": 14.4, "heur_ls": 1.2}
resta_s = sum(max(0, esp[m] - feitos[m]) * custo_medio[m] for m in ea0.ESTOCASTICOS)
print(f"estimativa de termino: ~{resta_s / 5 / 3600:.1f} h com 5 processos (pior caso: tarefas das instancias grandes demoram mais)")
