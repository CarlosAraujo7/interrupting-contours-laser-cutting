"""
causa_aninhados_replica.py  --  CONTROLE da causa da economia persistente nos layouts aninhados: REPLICA com sementes novas (2 e 3) do fechamento e da estrita  (19/11/2026; docs/52 D3)
==================================================================================================================================================================================
Por que: os 4 layouts foram SELECIONADOS pela economia alta do fechamento guardado (V2, sementes 0 e 1); uma segunda rodada independente de um solver com orcamento limitado tende a dar economia menor mesmo sem
nenhum efeito da precedencia (regressao a media). Controle: o MESMO metodo e orcamento de V2 (fechamento com a segunda rodada refinada pela ultima aresta de cada contorno) e da estrita de `causa_aninhados_v2.py`,
com as sementes 2 e 3 (as originais foram 0 e 1). Decisao fixada ANTES de ver a replica (docs/52 D3): **P-C3** a economia do fechamento na replica e >= 75% da guardada em >= 3 dos 4 layouts (a economia do fechamento
se reproduz, nao e artefato da selecao); **P-C4** a economia da estrita na replica difere da original em <= 0,05 ponto percentual em >= 3 dos 4 layouts (a estrita e estavel).
Uso: python causa_aninhados_replica.py congelar | rodar [--workers 1] | verificar | resultados
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

SEMENTES = (2, 3)
MANIFESTO = os.path.join(AQUI, "causa_replica_manifesto.json")


def _job(a):
    nome, sem = a
    f = os.path.join(cn.OUT, f"rep_{sem}_{nome}.json")
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
    melhor, hist, fech = None, [], None
    for semente in SEMENTES:
        inst = sg.montar(polys, pares, t_perf=t, fechamento=(fech if sem == "fechamento" else None), portais="reduzido", grafo=grafo)
        if sem == "estrita":
            inst["ordem"] = rest.ordem_estrita(inst, pares)
        tempo = int(min(120, 20 + inst["E"] / 4))
        tour = sg.resolver(inst, tempo=tempo, semente=semente)
        if tour is None:
            hist.append({"semente": semente, "erro": "sem tour"})
            continue
        cam = sg.caminho_do_tour(inst, tour)
        h = ch.fo_honesta(cam, t_perf=t, ja_contiguo=True)
        v = ch.verificar(h["caminho"], polys, pares_pi=pares)
        ar = sum(ch._cheb(s.coords[0], s.coords[-1]) for s, tg in h["caminho"] if tg == "d")
        reg = {"semente": semente, "fo": h["fo"], "ar": ar, "n_perf": h["n_perfuracoes"], "contiguo": v["contiguo"], "geo_ok": v["geo_ok"], "viol_fechamento": v["violacoes_pi_relaxada"], "viol_estrita": v["violacoes_pi_estrita"]}
        hist.append(reg)
        if sem == "fechamento":                                                         # a mesma regra de aceitacao de `rodar_v2`
            aceita = v["contiguo"] and v["geo_ok"] and v["violacoes_pi_relaxada"] == 0
            fech = sg.ultima_aresta_por_contorno(inst, tour)
        else:                                                                           # a mesma de `causa_aninhados_v2`
            aceita = v["ok"] and v["violacoes_pi_estrita"] == 0
        if aceita and (melhor is None or reg["fo"] < melhor["fo"]):
            melhor = reg
    res = {"instancia": nome, "semantica": sem, "sementes": list(SEMENTES), "melhor": melhor, "historico": hist, "tempo_total_s": time.time() - t0}
    os.makedirs(cn.OUT, exist_ok=True)
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
            f = os.path.join(cn.OUT, f"rep_{sem}_{nome}.json")
            if not os.path.exists(f):
                print(f"  {nome[-14:]} {sem}: sem resultado")
                ok = False
                continue
            m = json.load(open(f))["melhor"]
            bom = bool(m) and (m["viol_fechamento"] == 0) and (sem == "fechamento" or m["viol_estrita"] == 0) and m["contiguo"] and m["geo_ok"]
            ok &= bom
            print(f"  {nome[-14:]} {sem}: " + ("solucao verificada" if bom else "SEM solucao verificada"))
    print("VERIFICACAO " + ("OK" if ok else "COM PROBLEMAS"))
    sys.exit(0 if ok else 1)


def resultados():
    V2 = cn.v2_dados()
    L = ["# Replica com sementes novas (2 e 3) do fechamento e da estrita, t = 1 s", "",
         "Economia conservadora (% do tempo total) sobre a referencia de contorno (ver `causa_aninhados_v2.py`). Original = V2 guardado (fechamento) e `causa_aninhados_v2.py` (estrita), sementes 0 e 1; replica = sementes 2 e 3.", "",
         "| layout | n | fechamento original | fechamento replica | estrita original | estrita replica |", "|---|---:|---:|---:|---:|---:|"]
    f_or, f_rep, e_or, e_rep = [], [], [], []
    for nome in cn.selecionados():
        r = V2[nome]
        fo_ = json.load(open(os.path.join(cn.OUT, f"est_{nome}.json")))["melhor"]
        fr = json.load(open(os.path.join(cn.OUT, f"rep_fechamento_{nome}.json")))["melhor"]
        er = json.load(open(os.path.join(cn.OUT, f"rep_estrita_{nome}.json")))["melhor"]
        a, b, c, d = cn.economia(r, r["seg_t1"]["melhor"]), (cn.economia(r, fr) if fr else None), (cn.economia(r, fo_) if fo_ else None), (cn.economia(r, er) if er else None)
        f_or.append(a)
        f_rep.append(b)
        e_or.append(c)
        e_rep.append(d)
        fm = lambda x: f"{x:+.3f}%" if x is not None else "--"
        L.append(f"| {nome[-14:]} | {r['n_contornos']} | {fm(a)} | {fm(b)} | {fm(c)} | {fm(d)} |")
    p3 = sum(1 for a, b in zip(f_or, f_rep) if b is not None and b >= 0.75 * a)
    p4 = sum(1 for c, d in zip(e_or, e_rep) if c is not None and d is not None and abs(c - d) <= 0.05)
    L += ["", f"P-C3 (o fechamento se reproduz): economia da replica >= 75% da guardada em {p3} de {len(f_or)} layouts (previsao: >= 3 de 4): " + ("SUSTENTADA" if p3 >= 3 else "NAO SUSTENTADA") + ".",
          f"P-C4 (a estrita e estavel): replica a <= 0,05 ponto percentual da original em {p4} de {len(e_or)} layouts (previsao: >= 3 de 4): " + ("SUSTENTADA" if p4 >= 3 else "NAO SUSTENTADA") + "."]
    open(os.path.join(AQUI, "RESULTADOS_CAUSA_ANINHADOS_REPLICA.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "resultados"
    arg = lambda f, tp, d: tp(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d
    if modo == "congelar":
        man = {"data": time.strftime("%Y-%m-%d %H:%M:%S"), "arquivos": {a: sha(os.path.join(AQUI, a)) for a in ("causa_aninhados_replica.py", "causa_aninhados_v2.py", os.path.join("..", "docs", "52_desvios.md"))}}
        json.dump(man, open(MANIFESTO, "w"), indent=1)
        print("congelado:", json.dumps(man, indent=1))
    elif modo == "rodar":
        workers = arg("--workers", int, 1)
        tarefas = [(n, s) for n in cn.selecionados() for s in ("fechamento", "estrita")]
        print(f"[{time.strftime('%H:%M:%S')}] replica (sementes {SEMENTES}) em {len(tarefas)} tarefas, {workers} processos", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for n, s, msg in ex.map(_job, tarefas, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {n[-14:]} {s}: {msg}", flush=True)
        print("REPLICA CONCLUIDA", flush=True)
    elif modo == "verificar":
        verificar()
    elif modo == "resultados":
        resultados()
