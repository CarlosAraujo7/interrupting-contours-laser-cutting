"""
preparar_v3.py  --  pre-voo do V3 (docs/19): recusa-se a iniciar com a maquina ocupada e grava o manifesto (codigo + hashes). Nunca mata processos de ninguem.
Uso: python preparar_v3.py [--forcar]   (codigo de saida 0 = pode rodar; 1 = maquina ocupada, pouca memoria ou fora da tomada)
Mesmo criterio de `preparar_ea0.py` (processos de rodadas pesadas de outros trabalhos; memoria DISPONIVEL >= 4 GB; na tomada).
"""
import os
import sys
import json
import time
import platform

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import preparar_ea0 as pe                                                # noqa: E402

ARQ = ["rodar_v3.py", "segmento_gtsp.py", "caminho_honesto.py", "instancias_lcpp1.py", "tsh_segmento.py", "avaliar_heuristica_formal.py", os.path.join("..", "src_base", "heuristic_core.py")]


def main():
    forcar = "--forcar" in sys.argv
    ocupados = pe.processos_pesados()
    livre_gb = float(pe.ps("[math]::Round((Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory).AvailableMBytes/1024,1)").replace(",", ".") or 0)
    bat = pe.ps("(Get-CimInstance Win32_Battery | Select-Object -First 1 | ForEach-Object { \"$($_.EstimatedChargeRemaining)|$($_.BatteryStatus)\" })")
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
    man = {"inicio": time.strftime("%Y-%m-%d %H:%M:%S"), "protocolo": "docs/19_protocolo_V3_reinicio.md", "forcado": bool(problemas), "problemas_ignorados": problemas, "maquina": platform.platform(),
           "python": sys.version.split()[0], "julia": pe.ps("julia --version"), "cpu": pe.ps("(Get-CimInstance Win32_Processor).Name"), "threads": os.cpu_count(), "memoria_disponivel_gb": livre_gb,
           "bateria": bat, "processos_pesados_na_partida": ocupados, "sha256": {a: pe.sha(os.path.join(AQUI, a)) for a in ARQ if os.path.exists(os.path.join(AQUI, a))},
           "pcglns": "ferramentas/PCGLNS_upstream (commit bc09d9d)", "parametros": "rodar --workers 3 --ts 0.25,1.0 --rodadas 2"}
    json.dump(man, open(os.path.join(AQUI, "v3_manifesto.json"), "w"), indent=1)
    print("manifesto gravado: caso_a_corte_multitecnologia/v3_manifesto.json")


if __name__ == "__main__":
    main()
