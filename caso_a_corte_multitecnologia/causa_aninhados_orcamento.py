"""
causa_aninhados_orcamento.py  --  ORCAMENTO do PCGLNS no nivel de segmento nos 4 layouts ANINHADOS: fechamento e estrita com 600 s por rodada  (19/11/2026; docs/55, escrito antes dos dados)
=============================================================================================================================================================================================
Por que: a explicacao da economia que persiste nos layouts aninhados (docs/52 B) compara solucoes do PCGLNS; o lado do contorno esta convergido (controle `peca_ctrl` de V2) e o do segmento reproduz com sementes
novas (docs/52 D3), mas sementes que convergem para o mesmo otimo local de um orcamento curto nao revelariam isso. Aqui o UNICO fator que muda e o orcamento: o MESMO metodo da replica
(`causa_aninhados_replica.py`; fechamento = metodo e regra de aceitacao de `rodar_v2`, segunda rodada refinada pela ultima aresta de cada contorno; estrita = `causa_aninhados_v2.py`; t = 1 s; mesmo grafo com noding;
so entra solucao verificada), com as sementes ORIGINAIS (0 e 1) e **600 s por rodada** (era min(120, 20 + E/4) s).
Previsoes (decisao fixada em docs/55 ANTES dos dados): **P-O1a/b** a economia (fechamento / estrita) com 600 s difere da original em <= 0,05 ponto percentual em >= 3 dos 4 layouts; **P-O2** (estrutural) com 600 s a economia do
fechamento e >= a da estrita nos 4; **P-O3** com 600 s a economia da estrita e <= 0,10% em >= 3 dos 4; **P-O4** (diagnostico) o melhor FO muda <= 0,01% (relativo) entre os dois orcamentos em >= 3 dos 4, por semantica.
Uso: python causa_aninhados_orcamento.py congelar | rodar [--workers 2] [--tempo S --saida DIR --so TRECHO]  (as tres opcoes so para TESTE: o codigo recusa gravar na pasta oficial se o tempo nao for 600) | verificar | resultados
"""
import hashlib
import json
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "src_base"))
os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
import causa_aninhados_v2 as cn  # noqa: E402

SEMENTES = (0, 1)                     # as originais de V2 e de `causa_aninhados_v2.py`: so o orcamento muda
TEMPO_RODADA = 600                    # segundos de PCGLNS por rodada (o original era min(120, 20 + E/4))
MANIFESTO = os.path.join(AQUI, "causa_orcamento_manifesto.json")
CONGELADOS = ("causa_aninhados_orcamento.py", "causa_aninhados_v2.py", os.path.join("..", "docs", "55_protocolo_orcamento_aninhados_e_newton_longo.md"), os.path.join("..", "docs", "52_desvios.md"))


def _job(a):
    nome, sem, tempo_rodada, saida = a
    f = os.path.join(saida, f"orc_{sem}_{nome}.json")
    if os.path.exists(f):
        return nome, sem, "pulado"
    import ea0_lib as lib
    import instancias_lcpp1 as il
    import segmento_gtsp as sg
    import caminho_honesto as ch
    import rodar_estrita as rest
    hc = lib.hc
    polys = cn._carregar(nome)
    pares = hc._detectar_precedencia(list(polys))
    aneis = [list(p.exterior.coords)[:-1] for p in polys]                               # o mesmo grafo (noding) de `rodar_v2`
    coords, req, dono = il.requeridas_com_noding(aneis)
    pos = {c: i for i, c in enumerate(coords)}
    aneis_ids = [[pos[(round(float(x), il.ND), round(float(y), il.ND))] for x, y in a_ if (round(float(x), il.ND), round(float(y), il.ND)) in pos] for a_ in aneis]
    grafo = {"coords": coords, "req": req, "dono": dono, "aneis_ids": aneis_ids}
    t = cn.T_REINICIO
    t0 = time.time()
    melhor, hist, fech, E, tempo_orig = None, [], None, None, None
    for semente in SEMENTES:
        inst = sg.montar(polys, pares, t_perf=t, fechamento=(fech if sem == "fechamento" else None), portais="reduzido", grafo=grafo)
        if sem == "estrita":
            inst["ordem"] = rest.ordem_estrita(inst, pares)
        E = inst["E"]
        tempo_orig = int(min(120, 20 + E / 4))                                           # o orcamento que o metodo original teria
        tour = sg.resolver(inst, tempo=int(tempo_rodada), semente=semente)
        if tour is None:
            hist.append({"semente": semente, "erro": "sem tour"})
            continue
        cam = sg.caminho_do_tour(inst, tour)
        h = ch.fo_honesta(cam, t_perf=t, ja_contiguo=True)
        v = ch.verificar(h["caminho"], polys, pares_pi=pares)
        ar = sum(ch._cheb(s.coords[0], s.coords[-1]) for s, tg in h["caminho"] if tg == "d")
        reg = {"semente": semente, "fo": h["fo"], "ar": ar, "n_perf": h["n_perfuracoes"], "contiguo": v["contiguo"], "geo_ok": v["geo_ok"], "viol_fechamento": v["violacoes_pi_relaxada"], "viol_estrita": v["violacoes_pi_estrita"]}
        hist.append(reg)
        if sem == "fechamento":                                                         # a mesma regra de aceitacao de `rodar_v2` e da replica
            aceita = v["contiguo"] and v["geo_ok"] and v["violacoes_pi_relaxada"] == 0
            fech = sg.ultima_aresta_por_contorno(inst, tour)
        else:                                                                           # a mesma de `causa_aninhados_v2` e da replica
            aceita = v["ok"] and v["violacoes_pi_estrita"] == 0
        if aceita and (melhor is None or reg["fo"] < melhor["fo"]):
            melhor = reg
    res = {"instancia": nome, "semantica": sem, "sementes": list(SEMENTES), "tempo_rodada_s": tempo_rodada, "tempo_original_s": tempo_orig, "E": E, "melhor": melhor, "historico": hist, "tempo_total_s": time.time() - t0}
    os.makedirs(saida, exist_ok=True)
    json.dump(res, open(f, "w"), indent=1)
    return nome, sem, (f"fo={melhor['fo']:.3f} perf={melhor['n_perf']}" if melhor else "SEM SOLUCAO VERIFICADA") + f" em {res['tempo_total_s']:.0f}s"


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
            f = os.path.join(cn.OUT, f"orc_{sem}_{nome}.json")
            if not os.path.exists(f):
                print(f"  {nome[-14:]} {sem}: sem resultado")
                ok = False
                continue
            r = json.load(open(f))
            m = r["melhor"]
            bom = bool(m) and (m["viol_fechamento"] == 0) and (sem == "fechamento" or m["viol_estrita"] == 0) and m["contiguo"] and m["geo_ok"]
            bom = bom and r.get("tempo_rodada_s") == TEMPO_RODADA and r.get("sementes") == list(SEMENTES)
            ok &= bom
            print(f"  {nome[-14:]} {sem}: " + ("solucao verificada, 600 s por rodada, sementes 0 e 1" if bom else "SEM solucao verificada OU orcamento/sementes fora do protocolo"))
    print("VERIFICACAO " + ("OK" if ok else "COM PROBLEMAS"))
    sys.exit(0 if ok else 1)


def resultados():
    V2 = cn.v2_dados()
    L = ["# Orcamento do PCGLNS no nivel de segmento (600 s por rodada, sementes 0 e 1) nos 4 layouts aninhados, t = 1 s", "",
         "Economia conservadora (% do tempo total) sobre a referencia de contorno de V2 (`causa_aninhados_v2.economia`). Original = V2 guardado (fechamento) e `causa_aninhados_v2.py` (estrita), com `min(120, 20 + E/4)` s por rodada; 600 s = este experimento (docs/55).", "",
         "| layout | n | E | orcamento original (s) | fechamento original | fechamento 600 s | dFO fechamento | estrita original | estrita 600 s | dFO estrita |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    sf_o, sf_n, se_o, se_n, df, de = [], [], [], [], [], []
    for nome in cn.selecionados():
        r = V2[nome]
        fo_ = r["seg_t1"]["melhor"]
        eo_ = json.load(open(os.path.join(cn.OUT, f"est_{nome}.json")))["melhor"]
        rf = json.load(open(os.path.join(cn.OUT, f"orc_fechamento_{nome}.json")))
        re_ = json.load(open(os.path.join(cn.OUT, f"orc_estrita_{nome}.json")))
        nf, ne = rf["melhor"], re_["melhor"]
        a, b = cn.economia(r, fo_), (cn.economia(r, nf) if nf else None)
        c, d = (cn.economia(r, eo_) if eo_ else None), (cn.economia(r, ne) if ne else None)
        x, y = (100.0 * (nf["fo"] / fo_["fo"] - 1.0) if nf else None), (100.0 * (ne["fo"] / eo_["fo"] - 1.0) if (ne and eo_) else None)
        sf_o.append(a)
        sf_n.append(b)
        se_o.append(c)
        se_n.append(d)
        df.append(x)
        de.append(y)
        fm = lambda v: f"{v:+.3f}%" if v is not None else "--"
        L.append(f"| {nome[-14:]} | {r['n_contornos']} | {rf['E']} | {rf['tempo_original_s']} | {fm(a)} | {fm(b)} | {fm(x)} | {fm(c)} | {fm(d)} | {fm(y)} |")
    p1a = sum(1 for a, b in zip(sf_o, sf_n) if b is not None and abs(a - b) <= 0.05)
    p1b = sum(1 for c, d in zip(se_o, se_n) if c is not None and d is not None and abs(c - d) <= 0.05)
    pares = [(b, d) for b, d in zip(sf_n, se_n) if b is not None and d is not None]
    p2 = sum(1 for b, d in pares if b >= d - 1e-9)
    p3 = sum(1 for d in se_n if d is not None and d <= 0.10)
    p4f = sum(1 for x in df if x is not None and abs(x) <= 0.01)
    p4e = sum(1 for y in de if y is not None and abs(y) <= 0.01)
    n = len(sf_o)
    sus = lambda ok: "SUSTENTADA" if ok else "NAO SUSTENTADA"
    L += ["",
          f"P-O1a (o fechamento nao depende do orcamento): |economia 600 s - original| <= 0,05 pp em {p1a} de {n} layouts (previsao: >= 3 de 4): {sus(p1a >= 3)}.",
          f"P-O1b (a estrita nao depende do orcamento): idem, em {p1b} de {n} (previsao: >= 3 de 4): {sus(p1b >= 3)}.",
          f"P-O2 (estrutural: fechamento >= estrita com 600 s): em {p2} de {len(pares)} layouts (previsao: todos): {sus(p2 == len(pares))}.",
          f"P-O3 (o residuo da estrita): economia da estrita com 600 s <= 0,10% em {p3} de {n} (previsao: >= 3 de 4): {sus(p3 >= 3)}; maior valor {max(d for d in se_n if d is not None):+.3f}%.",
          f"P-O4 (convergencia: o melhor FO muda <= 0,01% entre os orcamentos): fechamento em {p4f} de {n}, estrita em {p4e} de {n} (previsao: >= 3 de 4 em cada): {sus(p4f >= 3 and p4e >= 3)}."]
    open(os.path.join(AQUI, "RESULTADOS_CAUSA_ANINHADOS_ORCAMENTO.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "resultados"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "congelar":
        man = {"data": time.strftime("%Y-%m-%d %H:%M:%S"), "arquivos": {a: sha(os.path.join(AQUI, a)) for a in CONGELADOS}}
        json.dump(man, open(MANIFESTO, "w"), indent=1)
        print("congelado:", json.dumps(man, indent=1))
    elif modo == "rodar":
        workers, tempo, saida, so = arg("--workers", int, 2), arg("--tempo", float, TEMPO_RODADA), arg("--saida", str, cn.OUT), arg("--so", str, "")
        if tempo != TEMPO_RODADA and os.path.abspath(saida) == os.path.abspath(cn.OUT):
            sys.exit(f"recusado: com tempo != {TEMPO_RODADA} (teste) use --saida para outra pasta; a pasta oficial so recebe o protocolo")
        tarefas = [(n, s, tempo, saida) for n in cn.selecionados() for s in ("fechamento", "estrita") if so in n]
        print(f"[{time.strftime('%H:%M:%S')}] orcamento {tempo:g} s por rodada (sementes {SEMENTES}) em {len(tarefas)} tarefas, {workers} processos, saida {saida}", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for n, s, msg in ex.map(_job, tarefas, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {n[-14:]} {s}: {msg}", flush=True)
        print("ORCAMENTO CONCLUIDO", flush=True)
    elif modo == "verificar":
        verificar()
    elif modo == "resultados":
        resultados()
