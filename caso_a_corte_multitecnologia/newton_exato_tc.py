"""
newton_exato_tc.py  --  PONTO DE EQUILIBRIO EXATO t_c de cada layout (Proposicao 3 do N1) pela iteracao de Newton sobre o MILP com custo de reinicio  (19/11/2026; autorizado por Carlos)
=======================================================================================================================================================================================
Proposicao 3: para contornos disjuntos, a economia exata S(t) = P0 + t n - min_k (c_k + t R_k) e convexa, nao crescente, e nula a partir de t_c <= t_cert. Dado um plano pi_j OTIMO em t_j com R_j > n corridas e
custo sem reinicio c_j = L/v_c + A_j/v_a, a raiz da sua reta, t_{j+1} = (P0 - c_j)/(R_j - n), e uma cota inferior de t_c; se S(t_{j+1}) = 0 entao t_c = t_{j+1}; senao o plano otimo em t_{j+1} tem MENOS corridas
(R_{j+1} < R_j) e a iteracao continua. Aqui o plano de partida vem das solucoes guardadas em `milp_certificado_resultados/` (otimas nos t da grade; ver `verificar_certificado_milp.py`): escolhe-se o de maior raiz.
Cada passo novo e UM MILP exato (HiGHS, o mesmo `verificar_certificado_milp.resolver_t`, com `corte_sup` = custo do plano de contorno, que e viavel e so poda). Layouts: os de contornos disjuntos sem furos, origem
fora dos contornos, com pelo menos um MILP provado com R > n e economia > 0 e um ponto da grade provado com economia nula (os que tem o primeiro zero conhecido). Protocolo e previsoes: docs/52 (escrito antes dos dados).
Tolerancia de "economia nula": S <= 1e-5 * T_P (a mesma do restante do artigo). Saida: `newton_resultados/<layout>.json` (trilha completa: t, R, c, S, tempo, rodadas).
Uso: python newton_exato_tc.py autoteste | congelar | rodar [--workers 3] [--limite 1800] [--instancias a,b] | verificar | resultados
(`rodar` e idempotente: pula o que ja terminou com status "exato"; `verificar` ANTES de `resultados`.)
"""
import glob
import hashlib
import json
import os
import statistics
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
import verificar_certificado_milp as vm  # noqa: E402

OUT = os.path.join(AQUI, "newton_resultados")
MANIFESTO = os.path.join(AQUI, "newton_causa_manifesto.json")
ARQUIVOS_CONGELADOS = ("newton_exato_tc.py", "causa_aninhados_v2.py", "verificar_certificado_milp.py", "teto_certificado.py", os.path.join("..", "docs", "52_protocolo_newton_exato_e_causa_aninhados.md"))
VC, VA = vm.VC, vm.VA
TOL_GRADE = 1e-5          # economia "nula" nos valores guardados da grade: a convencao do artigo (1e-5 do tempo total)
TOL = 1e-7                # economia "nula" no criterio de parada da iteracao (o MILP tem mip_rel_gap = 1e-9): resolucao de t_c de ~1e-5 s


def dados_layout(nome):
    """Valores guardados: otimo exato de contorno (DP), n, L, P0 = L/v_c + A_P*/v_a, t_cert, planos guardados com S > 0 e R > n [(t, R, c)] e o primeiro ponto da grade com economia nula."""
    teto = json.load(open(os.path.join(AQUI, "teto_resultados", f"{nome}.json")))
    reg = json.load(open(os.path.join(vm.OUT, f"{nome}.json")))
    L, n = reg["L_corte"], teto["n_contornos"]
    AP, As = teto["dp"]["ar_otimo_contorno"], teto["ar_otimo"]
    P0 = L / VC + AP / VA
    planos, nulos = [], []
    for ts, x in reg["t"].items():
        if not x.get("otimo"):
            continue
        t = float(ts)
        if (P0 + t * n) - x["M"] <= TOL_GRADE * (P0 + t * n):
            nulos.append(t)
        elif x["R"] > n:
            planos.append((t, x["R"], L / VC + x["ar_len"] / VA))
    return {"nome": nome, "L": L, "n": n, "AP": AP, "As": As, "P0": P0, "t_cert": (AP - As) / VA, "planos": planos, "hi": min(nulos) if nulos else None}


def iterar(d, inst, req, limite_s, arranque, log=print):
    """Newton a partir de um plano `arranque` = (t_k, R_k, c_k) otimo em t_k com R_k > n e economia > 0. -> (trilha, status), status in {exato, sem_prova, alerta, iteracoes}."""
    n, P0, AP, L = d["n"], d["P0"], d["AP"], d["L"]
    t_k, R_k, c_k = arranque
    trilha = [{"t": t_k, "R": R_k, "c": c_k, "origem": "partida"}]
    t = (P0 - c_k) / (R_k - n)
    for _ in range(60):
        r = vm.resolver_t(inst, req, t, limite_s, corte_sup=AP / VA + t * (n + 1))
        reg = {"t": t}
        if not r.get("otimo"):
            reg.update({"origem": "novo", "status": "sem_prova", "motivo": r.get("motivo"), "tempo_s": r.get("tempo_s")})
            trilha.append(reg)
            log(f"   {d['nome']}: t={t:.6f}: sem prova ({r.get('motivo')}, {r.get('tempo_s', 0):.0f}s)")
            return trilha, "sem_prova"
        M, R, c = d["L"] / VC + r["ar_custo"] - t, r["n_ar"] - 1, d["L"] / VC + r["ar_len"] / VA
        S = (P0 + t * n) - M
        reg.update({"origem": "novo", "M": M, "R": R, "c": c, "S": S, "rodadas": r["rodadas"], "tempo_s": r["tempo_s"]})
        trilha.append(reg)
        log(f"   {d['nome']}: t={t:.6f}: R={R} S={S:.6g} ({r['rodadas']} rod., {r['tempo_s']:.0f}s)")
        if S <= TOL * (P0 + t * n):
            return trilha, "exato"
        if not R > n:
            reg["alerta"] = "R <= n com S > 0 (impossivel pela Proposicao 2)"
            return trilha, "alerta"
        t_novo = (P0 - c) / (R - n)
        if not t_novo > t + 1e-12:
            reg["alerta"] = "a raiz nao cresce"
            return trilha, "alerta"
        t = t_novo
    return trilha, "iteracoes"


def candidatas():
    """Layouts com MILP guardado, plano de partida utilizavel e primeiro zero da grade conhecido, do menor para o maior numero de vertices."""
    L = []
    for f in sorted(glob.glob(os.path.join(vm.OUT, "*.json"))):
        nome = os.path.basename(f)[:-5]
        d = dados_layout(nome)
        if d["planos"] and d["hi"] is not None:
            reg = json.load(open(f))
            L.append((reg.get("vertices", 0), nome))
    return [n for _, n in sorted(L)]


def _job(a):
    nome, limite = a
    f = os.path.join(OUT, f"{nome}.json")
    if os.path.exists(f) and json.load(open(f)).get("status") == "exato":
        return nome, "pulado (exato)"
    d = dados_layout(nome)
    arranque = max(d["planos"], key=lambda p: (d["P0"] - p[2]) / (p[1] - d["n"]))
    coords, req, _ = vm.instancia(nome)
    inst = vm.preparar(coords, req)
    t0 = time.time()
    trilha, status = iterar(d, inst, req, limite, arranque, log=lambda s: print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True))
    res = {"instancia": nome, "n": d["n"], "L": d["L"], "P0": d["P0"], "t_cert": d["t_cert"], "hi_grade": d["hi"], "partida": list(arranque), "limite_s": limite,
           "status": status, "t_c": trilha[-1]["t"] if status == "exato" else None, "trilha": trilha, "tempo_total_s": time.time() - t0}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(f, "w"), indent=1)
    return nome, f"{status}" + (f" t_c={res['t_c']:.6f}" if status == "exato" else "") + f" em {res['tempo_total_s']:.0f}s ({len(trilha) - 1} MILPs novos)"


def autoteste():
    """O layout de brinquedo da Fig. 1 (3 retangulos; origem (0,0)): a iteracao a partir de t = 0 termina em S = 0; t_c >= o ponto de equilibrio dos dois planos da figura (0,0325 s); e um MILP
    independente em t_c(1 - 1e-3) tem economia > 0 e em t_c(1 + 1e-3) economia nula."""
    from shapely.geometry import box
    import tsh_segmento as tsh
    import teto_certificado as tc
    polys = [box(5, 8, 15, 18), box(20, 4, 30, 12), box(18, 17, 28, 25)]
    coords, req = tsh.construir_requeridas(polys)
    inst = vm.preparar(coords, req)
    L = sum(max(abs(coords[u][0] - coords[v][0]), abs(coords[u][1] - coords[v][1])) for u, v in req)
    custo_dp, _ = tc.dp_contornos(polys, [])
    n = len(polys)
    P0 = L / VC + custo_dp / VA
    d = {"nome": "brinquedo", "L": L, "n": n, "AP": custo_dp, "P0": P0}
    r0 = vm.resolver_t(inst, req, 0.0, 120)
    R0, c0 = r0["n_ar"] - 1, L / VC + r0["ar_len"] / VA
    S0 = P0 - (L / VC + r0["ar_custo"])
    print(f"brinquedo: n={n}, ar de contorno {custo_dp:.0f}, ar minimo {r0['ar_len']:.0f}, R_0={R0}, S(0)={S0:.4f} s")
    assert R0 > n and S0 > 0, "o brinquedo deve ter economia em t = 0"
    trilha, status = iterar(d, inst, req, 120, (0.0, R0, c0))
    assert status == "exato", status
    t_c = trilha[-1]["t"]
    print("trilha:", [(round(x["t"], 6), x.get("R")) for x in trilha], "| t_c =", t_c)
    assert t_c >= 0.0325 - 1e-9, "t_c deve ser >= ao ponto de equilibrio dos dois planos da figura"
    for t, esperado in ((t_c * (1 - 1e-3), True), (t_c * (1 + 1e-3), False)):
        r = vm.resolver_t(inst, req, t, 120)
        S = (P0 + t * n) - (L / VC + r["ar_custo"] - t)
        print(f"  conferencia independente em t={t:.6f}: S={S:.6g}")
        assert (S > TOL * (P0 + t * n)) == esperado
    Rs = [x["R"] for x in trilha if "R" in x]
    ts = [x["t"] for x in trilha]
    assert all(b > a for a, b in zip(ts, ts[1:])) and all(b < a for a, b in zip(Rs, Rs[1:])), "t cresce e R decresce estritamente"
    assert len(trilha) - 1 <= R0 - n + 1
    print("AUTOTESTE OK")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def congelar():
    man = {"data": time.strftime("%Y-%m-%d %H:%M:%S"), "arquivos": {os.path.normpath(a): sha(os.path.join(AQUI, a)) for a in ARQUIVOS_CONGELADOS}}
    json.dump(man, open(MANIFESTO, "w"), indent=1)
    print("congelado:", json.dumps(man, indent=1))


def verificar():
    """(1) codigo e protocolo iguais aos congelados; (2) previsoes ESTRUTURAIS H-N1..H-N4 em cada resultado (violar uma significa erro de codigo ou da teoria: investigar, nao relatar como achado)."""
    ok = True
    man = json.load(open(MANIFESTO))
    for a, h in man["arquivos"].items():
        igual = sha(os.path.join(AQUI, a)) == h
        ok &= igual
        print(("OK       " if igual else "ALTERADO ") + a)
    fs = sorted(glob.glob(os.path.join(OUT, "*.json")))
    print(f"{len(fs)} layouts com resultado")
    for f in fs:
        r = json.load(open(f))
        tr = r["trilha"]
        ts = [x["t"] for x in tr]
        Rs = [x["R"] for x in tr if "R" in x]
        probs = []
        if not all(b > a for a, b in zip(ts, ts[1:])):
            probs.append("H-N1: t nao cresce estritamente")
        if not all(b < a for a, b in zip(Rs, Rs[1:])):
            probs.append("H-N1: R nao decresce estritamente")
        novos = [x for x in tr if x.get("origem") == "novo"]
        if len([x for x in novos if "M" in x]) > r["partida"][1] - r["n"] + 1:
            probs.append("H-N1: mais MILPs que R_k - n + 1")
        if r["status"] == "exato":
            tc = r["t_c"]
            if tc > r["t_cert"] * (1 + 1e-6):
                probs.append("H-N3: t_c > t_cert")
            lo = (r["P0"] - r["partida"][2]) / (r["partida"][1] - r["n"])
            if not (lo * (1 - 1e-9) <= tc <= r["hi_grade"] * (1 + 1e-9)):
                probs.append("H-N2: t_c fora do intervalo guardado")
            if not all(x.get("S", 1) > TOL * (r["P0"] + x["t"] * r["n"]) for x in tr[1:-1]):
                probs.append("H-N4: passo intermediario com S nula")
            if not abs(tr[-1]["S"]) <= TOL * (r["P0"] + tc * r["n"]):
                probs.append("H-N4: S final nao e nula")
        ok &= not probs
        print(f"  {r['instancia']}: {r['status']}" + (f" t_c={r['t_c']:.6f}" if r["status"] == "exato" else "") + (" | " + "; ".join(probs) if probs else " | estrutura OK"))
    print("VERIFICACAO " + ("OK" if ok else "COM PROBLEMAS"))
    sys.exit(0 if ok else 1)


def resultados():
    fs = sorted(glob.glob(os.path.join(OUT, "*.json")))
    R = [json.load(open(f)) for f in fs]
    L = ["# Ponto de equilibrio exato por iteracao de Newton (Proposicao 3)", "",
         "| layout | n | R de partida | MILPs novos | t_c (s) | t_cert (s) | t_c / t_cert | intervalo guardado (s) | rho_c | status |", "|---|---:|---:|---:|---:|---:|---:|---|---:|---|"]
    ex = []
    for r in R:
        novos = len([x for x in r["trilha"] if "M" in x])
        lo = (r["P0"] - r["partida"][2]) / (r["partida"][1] - r["n"])
        rho = r["t_c"] * VA * r["n"] / r["L"] if r["t_c"] else None
        if r["status"] == "exato":
            ex.append((r, rho))
        L.append(f"| {r['instancia']} | {r['n']} | {r['partida'][1]} | {novos} | " + (f"{r['t_c']:.5f}" if r["t_c"] else "--") + f" | {r['t_cert']:.3f} | " + (f"{r['t_c'] / r['t_cert']:.2f}" if r["t_c"] else "--")
                 + f" | [{lo:.4f}, {r['hi_grade']:g}] | " + (f"{rho:.3f}" if rho else "--") + f" | {r['status']} |")
    if ex:
        tcs = [r["t_c"] for r, _ in ex]
        rhos = [x for _, x in ex]
        L += ["", f"Layouts com t_c exato: {len(ex)} de {len(R)}. Mediana de t_c = {statistics.median(tcs):.4f} s (min {min(tcs):.4f}, max {max(tcs):.4f}); mediana de t_c/t_cert = {statistics.median([r['t_c'] / r['t_cert'] for r, _ in ex]):.2f};",
              f"rho_c: mediana {statistics.median(rhos):.3f}, max {max(rhos):.3f}.", "",
              "Previsao H-N5 (empirica, docs/52): mediana de t_c entre 0,04 e 0,15 s: " + ("SUSTENTADA" if 0.04 <= statistics.median(tcs) <= 0.15 else "NAO SUSTENTADA")
              + "; rho_c <= 1 em todos: " + ("SUSTENTADA" if max(rhos) <= 1 else "NAO SUSTENTADA") + "."]
    open(os.path.join(AQUI, "RESULTADOS_NEWTON.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "autoteste"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "autoteste":
        autoteste()
    elif modo == "congelar":
        congelar()
    elif modo == "verificar":
        verificar()
    elif modo == "resultados":
        resultados()
    elif modo == "rodar":
        workers, limite = arg("--workers", int, 3), arg("--limite", float, 1800.0)
        nomes = arg("--instancias", str, "").split(",") if "--instancias" in sys.argv else candidatas()
        print(f"[{time.strftime('%H:%M:%S')}] Newton exato: {len(nomes)} layouts, {workers} processos, limite {limite:g} s por MILP: {', '.join(nomes)}", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for n, msg in ex.map(_job, [(x, limite) for x in nomes], chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {n}: {msg}", flush=True)
        print("NEWTON CONCLUIDO", flush=True)
