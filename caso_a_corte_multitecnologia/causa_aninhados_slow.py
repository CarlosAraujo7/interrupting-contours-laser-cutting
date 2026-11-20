"""
causa_aninhados_slow.py  --  ESFORCO de busca do PCGLNS no nivel de segmento nos 4 layouts ANINHADOS: fechamento e estrita com `-mode=slow`  (19/11/2026; docs/55_desvios.md D1, extensao C2)
=====================================================================================================================================================================================
Por que: na parte C (`causa_aninhados_orcamento.py`) o teto de 600 s nao era limitante no modo `default` do PCGLNS (as quatro primeiras tarefas terminaram em 21-50 s, com os FO originais: o solver para por conta
propria, apos 5 tentativas a frio x 3 reinicios com 60*n iteracoes). Aqui muda o ESFORCO de busca, nao o teto: `-mode=slow` (150*n iteracoes, 10 tentativas a frio x 5 reinicios, remocoes ate 40% dos grupos), com o
MESMO metodo, as MESMAS sementes (0 e 1), o mesmo teto de 600 s por rodada e a mesma regra de aceitacao (`causa_aninhados_orcamento._job`, que e reutilizado SEM alteracao). A unica diferenca em relacao a parte C e que,
em tempo de execucao, `segmento_gtsp.resolver` e trocado por uma copia com `-mode=slow` (o arquivo `segmento_gtsp.py` nao e alterado: outros protocolos o congelam).
Previsoes (decisao fixada em docs/55_desvios.md D1 ANTES de qualquer resultado do modo slow): **P-S1/P-S2** a economia (fechamento / estrita) no modo slow difere da original em <= 0,05 pp em >= 3 dos 4 layouts; **P-S3** a economia
da estrita no modo slow e <= 0,10% em >= 3 dos 4; **P-S4** (estrutural) fechamento >= estrita nos 4; **P-S5** (diagnostico) o melhor FO do modo slow fica no maximo 0,01% acima do original em >= 3 dos 4, por semantica.
Uso: python causa_aninhados_slow.py congelar | rodar [--workers 2] | verificar | resultados      (`rodar` e idempotente)
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
import causa_aninhados_v2 as cn  # noqa: E402
import causa_aninhados_orcamento as co  # noqa: E402
import segmento_gtsp as sg  # noqa: E402

SAIDA = os.path.join(AQUI, "causa_aninhados_resultados_slow")
MANIFESTO = os.path.join(AQUI, "causa_slow_manifesto.json")
CONGELADOS = ("causa_aninhados_slow.py", "causa_aninhados_orcamento.py", "causa_aninhados_v2.py", os.path.join("..", "docs", "55_protocolo_orcamento_aninhados_e_newton_longo.md"),
              os.path.join("..", "docs", "55_desvios.md"), os.path.join("..", "docs", "52_desvios.md"))


def _resolver_slow(inst, tempo=60, semente=0):
    """Copia de `segmento_gtsp.resolver` com `-mode=slow` (a unica diferenca)."""
    tmp = tempfile.mkdtemp(prefix="segslow_")
    arq, saida = os.path.join(tmp, "seg.pcglns"), os.path.join(tmp, "o.tour")
    sg.escrever(inst, arq)
    subprocess.run(["julia", "--threads=1,0", "runPCGLNS.jl", arq, "-mode=slow", f"-max_time={tempo}", "-verbose=0", f"-output={saida}", f"-seed={semente}"],
                   cwd=sg.PCGLNS_DIR, capture_output=True, text=True, errors="replace")
    txt = open(saida, encoding="latin-1").read() if os.path.exists(saida) else ""
    m = re.search(r"Tour\s*:\s*\[([^\]]+)\]", txt)
    for x in os.listdir(tmp):
        try:
            os.remove(os.path.join(tmp, x))
        except OSError:
            pass
    try:
        os.rmdir(tmp)
    except OSError:
        pass
    if not m:
        return None
    tour = [int(x) for x in m.group(1).split(",")]
    if tour[0] != 1:
        k = tour.index(1)
        tour = tour[k:] + tour[:k]
    return tour


sg.resolver = _resolver_slow           # no NIVEL DO MODULO: os processos filhos (spawn) reimportam este arquivo e repetem a troca


def _job(a):
    nome, sem = a
    nome_, sem_, msg = co._job((nome, sem, co.TEMPO_RODADA, SAIDA))
    f = os.path.join(SAIDA, f"orc_{sem}_{nome}.json")
    if os.path.exists(f):
        r = json.load(open(f))
        if r.get("modo") != "slow":
            r["modo"] = "slow"
            json.dump(r, open(f, "w"), indent=1)
    return nome, sem, msg


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def verificar():
    man = json.load(open(MANIFESTO))
    ok = True
    for a, h in man["arquivos"].items():
        igual = sha(os.path.join(AQUI, a)) == h
        ok &= igual
        print(("OK       " if igual else "ALTERADO ") + a)
    for nome in cn.selecionados():
        for sem in ("fechamento", "estrita"):
            f = os.path.join(SAIDA, f"orc_{sem}_{nome}.json")
            if not os.path.exists(f):
                print(f"  {nome[-14:]} {sem}: sem resultado")
                ok = False
                continue
            r = json.load(open(f))
            m = r["melhor"]
            bom = bool(m) and (m["viol_fechamento"] == 0) and (sem == "fechamento" or m["viol_estrita"] == 0) and m["contiguo"] and m["geo_ok"]
            bom = bom and r.get("tempo_rodada_s") == co.TEMPO_RODADA and r.get("sementes") == list(co.SEMENTES) and r.get("modo") == "slow"
            ok &= bom
            print(f"  {nome[-14:]} {sem}: " + ("solucao verificada, modo slow, teto de 600 s, sementes 0 e 1" if bom else "SEM solucao verificada OU modo/teto/sementes fora do protocolo"))
    print("VERIFICACAO " + ("OK" if ok else "COM PROBLEMAS"))
    sys.exit(0 if ok else 1)


def resultados():
    V2 = cn.v2_dados()
    L = ["# Esforco de busca do PCGLNS no nivel de segmento (`-mode=slow`, teto de 600 s por rodada, sementes 0 e 1) nos 4 layouts aninhados, t = 1 s", "",
         "Economia conservadora (% do tempo total) sobre a referencia de contorno de V2 (`causa_aninhados_v2.economia`). Original = V2 guardado (fechamento) e `causa_aninhados_v2.py` (estrita), modo `default` com `min(120, 20 + E/4)` s por rodada; "
         "600 s default = parte C (`causa_aninhados_orcamento.py`); slow = esta extensao (docs/55_desvios.md D1). Tempos: total das duas rodadas, em s.", "",
         "| layout | n | semantica | original | 600 s default | slow | dFO slow | tempo default (s) | tempo slow (s) |", "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    sf_o, sf_s, se_o, se_s, df, de = [], [], [], [], [], []
    for nome in cn.selecionados():
        r = V2[nome]
        orig = {"fechamento": r["seg_t1"]["melhor"], "estrita": json.load(open(os.path.join(cn.OUT, f"est_{nome}.json")))["melhor"]}
        for sem in ("fechamento", "estrita"):
            rs = json.load(open(os.path.join(SAIDA, f"orc_{sem}_{nome}.json")))
            fc = os.path.join(cn.OUT, f"orc_{sem}_{nome}.json")
            rd = json.load(open(fc)) if os.path.exists(fc) else None
            ms, mo = rs["melhor"], orig[sem]
            md = rd["melhor"] if rd else None
            a, b, c = (cn.economia(r, mo) if mo else None), (cn.economia(r, md) if md else None), (cn.economia(r, ms) if ms else None)
            x = 100.0 * (ms["fo"] / mo["fo"] - 1.0) if (ms and mo) else None
            (sf_o if sem == "fechamento" else se_o).append(a)
            (sf_s if sem == "fechamento" else se_s).append(c)
            (df if sem == "fechamento" else de).append(x)
            fm = lambda v: f"{v:+.3f}%" if v is not None else "--"
            L.append(f"| {nome[-14:]} | {r['n_contornos']} | {sem} | {fm(a)} | {fm(b)} | {fm(c)} | {fm(x)} | {rd['tempo_total_s']:.0f} | {rs['tempo_total_s']:.0f} |" if rd else f"| {nome[-14:]} | {r['n_contornos']} | {sem} | {fm(a)} | -- | {fm(c)} | {fm(x)} | -- | {rs['tempo_total_s']:.0f} |")
    n = len(sf_o)
    ok1 = lambda o, s: sum(1 for a, b in zip(o, s) if a is not None and b is not None and abs(a - b) <= 0.05)
    p1, p2 = ok1(sf_o, sf_s), ok1(se_o, se_s)
    p3 = sum(1 for d in se_s if d is not None and d <= 0.10)
    pares = [(b, d) for b, d in zip(sf_s, se_s) if b is not None and d is not None]
    p4 = sum(1 for b, d in pares if b >= d - 1e-9)
    p5f, p5e = sum(1 for x in df if x is not None and x <= 0.01), sum(1 for y in de if y is not None and y <= 0.01)
    sus = lambda ok: "SUSTENTADA" if ok else "NAO SUSTENTADA"
    L += ["",
          f"P-S1 (o fechamento nao depende do esforco de busca): |economia slow - original| <= 0,05 pp em {p1} de {n} layouts (previsao: >= 3 de 4): {sus(p1 >= 3)}.",
          f"P-S2 (a estrita nao depende do esforco de busca): idem, em {p2} de {n} (previsao: >= 3 de 4): {sus(p2 >= 3)}.",
          f"P-S3 (o residuo da estrita): economia da estrita no modo slow <= 0,10% em {p3} de {n} (previsao: >= 3 de 4): {sus(p3 >= 3)}; maior valor {max(d for d in se_s if d is not None):+.3f}%.",
          f"P-S4 (estrutural: fechamento >= estrita no modo slow): em {p4} de {len(pares)} layouts (previsao: todos): {sus(p4 == len(pares))}.",
          f"P-S5 (diagnostico: o melhor FO do modo slow no maximo 0,01% acima do original): fechamento em {p5f} de {n}, estrita em {p5e} de {n} (previsao: >= 3 de 4 em cada): {sus(p5f >= 3 and p5e >= 3)}."]
    open(os.path.join(AQUI, "RESULTADOS_CAUSA_ANINHADOS_SLOW.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "resultados"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "congelar":
        man = {"data": time.strftime("%Y-%m-%d %H:%M:%S"), "arquivos": {a: sha(os.path.join(AQUI, a)) for a in CONGELADOS}}
        json.dump(man, open(MANIFESTO, "w"), indent=1)
        print("congelado:", json.dumps(man, indent=1))
    elif modo == "rodar":
        workers = arg("--workers", int, 2)
        tarefas = [(n, s) for n in cn.selecionados() for s in ("fechamento", "estrita")]
        os.makedirs(SAIDA, exist_ok=True)
        print(f"[{time.strftime('%H:%M:%S')}] modo slow, teto {co.TEMPO_RODADA} s por rodada (sementes {co.SEMENTES}) em {len(tarefas)} tarefas, {workers} processos, saida {SAIDA}", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for n, s, msg in ex.map(_job, tarefas, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {n[-14:]} {s}: {msg}", flush=True)
        print("SLOW CONCLUIDO", flush=True)
    elif modo == "verificar":
        verificar()
    elif modo == "resultados":
        resultados()
