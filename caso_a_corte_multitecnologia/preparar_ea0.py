"""
preparar_ea0.py  --  pre-voo do E-A0 completo (docs/11_protocolo_E-A0.md): recusa-se a iniciar com a maquina ocupada e grava o manifesto da execucao (WP0.3)
Uso: python preparar_ea0.py [--forcar]   (codigo de saida 0 = pode rodar; 1 = maquina ocupada ou fora da tomada)
Criterio de "ocupada": qualquer processo python/julia/LKH com linha de comando de rodada (run_, rodar_, multiprocessing.spawn, runPCGLNS, LKH) que NAO seja um servidor MCP;
a memoria DISPONIVEL (AvailableMBytes: livre + cache liberavel) deve ser >= 4 GB (pico medido por tarefa: PCGLNS ~575 MB, demais <= 330 MB; 5 processos ~3 GB no pior caso); a bateria deve estar na tomada. Nunca mata processos de ninguem.
"""
import os, sys, json, time, hashlib, platform, subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ARQ = ["rodar_ea0.py", "ea0_lib.py", "heuristica_ls.py", "vns_zhang_pi.py", "vns_zhang.py", "mastri.py", "dxf_parser.py", "perfil_tecnologia.py",
       os.path.join("..", "src_base", "heuristic_core.py"), os.path.join("..", "src_base", "quadtree_rapido.py"), os.path.join("..", "src_base", "quadtree.py")]


def ps(cmd):
    return subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, errors="replace").stdout.strip()


def processos_pesados():
    out = ps("Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python|julia|LKH' } | ForEach-Object { \"$($_.ProcessId)|$($_.Name)|$($_.CommandLine)\" }")
    achados = []
    for linha in out.splitlines():
        pid, nome, cmd = (linha.split("|", 2) + ["", ""])[:3]
        if "mcp" in cmd.lower() or "mcp-servers" in cmd.lower() or str(os.getpid()) == pid:
            continue
        if any(k in cmd for k in ("run_", "rodar_", "multiprocessing.spawn", "runPCGLNS", "LKH", "retomar")) or "julia" in nome.lower():
            achados.append((pid, nome, cmd[:140]))
    return achados


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    forcar = "--forcar" in sys.argv
    ocupados = processos_pesados()
    livre_gb = float(ps("[math]::Round((Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory).AvailableMBytes/1024,1)").replace(",", ".") or 0)
    bat = ps("(Get-CimInstance Win32_Battery | Select-Object -First 1 | ForEach-Object { \"$($_.EstimatedChargeRemaining)|$($_.BatteryStatus)\" })")
    na_tomada = (bat.split("|")[-1] in ("2", "6", "7", "8", "9", "")) if bat else True
    print(f"processos pesados de outras rodadas: {len(ocupados)}; memoria disponivel: {livre_gb} GB; bateria: {bat or 'n/d'} (status 2 = na tomada)")
    for p in ocupados:
        print("   ", p)
    problemas = []
    if ocupados:
        problemas.append("ha outras rodadas pesadas em andamento")
    if livre_gb < 4:
        problemas.append("memoria disponivel < 4 GB")
    if not na_tomada:
        problemas.append("notebook fora da tomada")
    if problemas and not forcar:
        print("NAO INICIAR:", "; ".join(problemas), "(use --forcar so se aceitar tempos/FO distorcidos e declare no relatorio)")
        sys.exit(1)
    man = {"inicio": time.strftime("%Y-%m-%d %H:%M:%S"), "protocolo": "docs/11_protocolo_E-A0.md", "forcado": bool(problemas), "problemas_ignorados": problemas, "maquina": platform.platform(),
           "python": sys.version.split()[0], "julia": ps("julia --version"), "cpu": ps("(Get-CimInstance Win32_Processor).Name"), "threads": os.cpu_count(), "memoria_disponivel_gb": livre_gb,
           "bateria": bat, "processos_pesados_na_partida": ocupados, "sha256": {a: sha(os.path.join(AQUI, a)) for a in ARQ if os.path.exists(os.path.join(AQUI, a))},
           "pcglns": "ferramentas/PCGLNS_upstream (commit bc09d9d)", "parametros": "rodar --tempo 30 --sementes 10 --workers 5"}
    json.dump(man, open(os.path.join(AQUI, "ea0_manifesto.json"), "w"), indent=1)
    print("manifesto gravado: caso_a_corte_multitecnologia/ea0_manifesto.json")


if __name__ == "__main__":
    main()
