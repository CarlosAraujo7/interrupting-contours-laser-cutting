"""
rodar_ea0.py  --  experimento E-A0 (plano 07, WP4.3): heuristica proposta (LCA + Pi) x PCGLNS x VNS-Pi x MASTRI nas MESMAS instancias geometricas do CPPLib
==============================================================================================================================================
Instancias: as DXF da categoria "All example with precedence constraints" do CPPLib (85 arquivos; 84 com >= 2 pecas). Conversao, objetivo comum e
limitacoes: ver `ea0_lib.py` (FO = `heuristic_core.fo_from_path`, a MESMA funcao para todos; validada: o caminho da heuristica reconvertido em tour
reproduz o proprio `fo_total`).

Metodos (um JSON por (instancia, metodo, semente) em `ea0_resultados/`; idempotente):
  heur_pi   -- heuristica proposta com Pi (`enforce_precedence=True`), deterministica -> semente 0 apenas.
  heur_orig -- heuristica no modo original (sem Pi garantida), deterministica, referencia de custo.
  pcglns    -- PCGLNS upstream (ferramentas/PCGLNS_upstream, Julia `--threads=1,0`), modo default, `-max_time=T`, `-seed=s`.
  vns_pi    -- VNS de Zhang et al. estendido para respeitar Pi (EXTENSAO NOSSA; `vns_zhang_pi.py`), T segundos, semente s.
  mastri    -- MASTRI (reimplementado; NAO respeita Pi), deterministico -> semente 0; reportado com suas violacoes, sem concorrer pelo "melhor viavel".
ORCAMENTO: T segundos por execucao de PCGLNS e VNS-Pi (padrao 30) e `time_limit = T` da heuristica; DECLARAR o T ao citar. Maquina compartilhada:
tempos de parede so tem valor de ordem de grandeza.

Uso:
    python rodar_ea0.py rodar [--tempo 30] [--sementes 3] [--workers 3] [--limite N | inst ...]     (--limite: N instancias espacadas na lista ordenada)
    python rodar_ea0.py resumo [--tempo 30]  > RESULTADOS_EA0.md
"""
import os, sys, json, glob, re, time, tempfile, subprocess, warnings, statistics
from concurrent.futures import ProcessPoolExecutor

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
RAIZ = os.path.dirname(AQUI)
import ea0_lib as lib
import dxf_parser
import heuristic_core as hc

OUT = os.path.join(AQUI, "ea0_resultados")
CAT = os.path.join(AQUI, "instances", "cpplib", "Category - All example with precedence constraints")
PCGLNS_DIR = os.path.join(RAIZ, "ferramentas", "PCGLNS_upstream")
METODOS = ["heur_pi", "heur_orig", "heur_ls", "heur_vns", "pcglns", "vns_pi", "mastri"]
ESTOCASTICOS = {"pcglns", "vns_pi", "heur_ls", "heur_vns"}


def listar():
    """Nome -> arquivo DXF. CORRECAO (09/10/2026): dois arquivos da categoria tem o MESMO nome de arquivo (`p1xj_15`: um em `.../p1xk_15/p1xj_15.DXF`, outro em `.../p1xj_15/p1xj_15.dxf`; ver
    `dxf_parser.py`); a versao anterior (dicionario por nome de arquivo) descartava um deles em silencio e o E-A0 cobriu 83 instancias com >= 2 pecas em vez de 84. Para o nome repetido usa-se o nome
    da PASTA (a identidade que o `dxf_parser` ja usa): `p1xk_15` e `p1xj_15`."""
    fs = sorted(glob.glob(os.path.join(CAT, "**", "*.dxf"), recursive=True))
    nomes = [os.path.splitext(os.path.basename(f))[0] for f in fs]
    out = {}
    for f, base in zip(fs, nomes):
        pasta = os.path.basename(os.path.dirname(f))
        out[pasta if nomes.count(base) > 1 and pasta != base else base] = f
    return out


def caminho(nome, metodo, s, tempo):
    return os.path.join(OUT, f"ea0_{nome}_{metodo}_T{tempo}_s{s}.json")


def _carregar(nome):
    """`nome` = instancia do CPPLib; `nome@k` = o MESMO layout repetido k vezes lado a lado (teste de ESCALA sintetico; cada copia preserva o seu Pi)."""
    base, _, k = nome.partition("@")
    f = listar()[base]
    nm, polys, info = dxf_parser.load_instance_dxf(f)
    if not k:
        return polys
    from shapely import affinity
    k = int(k)
    minx = min(p.bounds[0] for p in polys)
    maxx = max(p.bounds[2] for p in polys)
    larg = (maxx - minx) + 10.0
    return [affinity.translate(p, xoff=i * larg) for i in range(k) for p in polys]


def _job(a):
    nome, metodo, s, tempo = a
    f = caminho(nome, metodo, s, tempo)
    if os.path.exists(f):
        return nome, metodo, s, "pulado"
    polys = _carregar(nome)
    if len(polys) < 2:
        return nome, metodo, s, "poucas pecas"
    v_cut, v_air = hc._DEFAULT_CONFIG["v_cut"], hc._DEFAULT_CONFIG["v_air"]
    t0 = time.time()
    inst = lib.montar_instancia(polys)
    r = {"instancia": nome, "metodo": metodo, "semente": s, "tempo_limite_s": tempo, "n_pecas": len(polys), "n_cidades": len(inst["cidades"]),
         "n_pares_pi": len(inst["pares"])}
    if metodo in ("heur_pi", "heur_orig"):
        cfg = {**lib.CFG_BASE, "time_limit": max(tempo, 60), "enforce_precedence": metodo == "heur_pi"}   # a construcao nao tem "orcamento": limite folgado (resultados ja gravados com T curto ficam como estao)
        res = hc.run_heuristic(list(polys), cfg)
        r["timeout"] = bool(res.get("timeout"))
        if res["caminho"]:
            tour = lib.tour_de_caminho(polys, inst, res["caminho"])
            r.update(fo=float(res["fo_total"]), violacoes=lib.violacoes(inst, tour))
            r["fo_reavaliada"] = lib.fo_do_tour(polys, inst, tour, v_cut, v_air)
        else:
            r.update(fo=None, violacoes=None)
    elif metodo in ("heur_ls", "heur_vns"):            # heuristica proposta = construcao (LCA + Pi) + busca local sobre o tour de pecas (heuristica_ls.py)
        import heuristica_ls as hls
        out = hls.rodar(polys, inst, s, "ls" if metodo == "heur_ls" else "vns", tempo=tempo)
        r.update(t_construcao_s=out["t_construcao_s"], t_pos_s=out["t_pos_s"], timeout=bool(out["timeout"]))
        if out["tour"] is not None:
            r.update(fo=lib.fo_do_tour(polys, inst, out["tour"], v_cut, v_air), violacoes=lib.violacoes(inst, out["tour"]),
                     fo_construcao=lib.fo_do_tour(polys, inst, out["tour_construcao"], v_cut, v_air))
        else:
            r.update(fo=None, violacoes=None)
    else:
        tmp = tempfile.mkdtemp(prefix="ea0_")
        arq = os.path.join(tmp, f"{nome}.pcglns")
        lib.escrever_pcglns(inst, arq, nome)
        if metodo == "pcglns":
            saida = os.path.join(tmp, "saida.tour")
            p = subprocess.run(["julia", "--threads=1,0", "runPCGLNS.jl", arq, "-mode=default", f"-max_time={tempo}", "-verbose=0",
                                f"-output={saida}", f"-seed={s}"], cwd=PCGLNS_DIR, capture_output=True, text=True, errors="replace")
            txt = open(saida, encoding="latin-1").read() if os.path.exists(saida) else ""
            m = re.search(r"Tour\s*:\s*\[([^\]]+)\]", txt)
            tour = [int(x) for x in m.group(1).split(",")] if m else None
            if tour is None:
                r.update(fo=None, violacoes=None, erro=(p.stdout + p.stderr)[-300:])
        elif metodo == "vns_pi":
            import vns_zhang_pi
            rv = vns_zhang_pi.resolver_vns_zhang_pi(arq, seed=s, tempo_limite_s=tempo)
            tour = list(rv["tour"])
            r["iteracoes"] = rv["vns_iteracoes"]
        else:  # mastri
            import mastri
            rm = mastri.resolver_mastri(arq)
            tour = list(rm["tour"])
        if tour is not None:
            if tour[0] != 1:                           # garante o inicio na origem (rotaciona o ciclo)
                k = tour.index(1)
                tour = tour[k:] + tour[:k]
            assert sorted(tour) != [] and len(set(inst["cidades"][c - 1][2] for c in tour)) == len(polys) + 1, "tour nao visita todos os grupos"
            r.update(violacoes=lib.violacoes(inst, tour), fo=lib.fo_do_tour(polys, inst, tour, v_cut, v_air))
        try:
            for x in os.listdir(tmp):
                os.remove(os.path.join(tmp, x))
            os.rmdir(tmp)
        except OSError:
            pass
    r["tempo_parede_s"] = time.time() - t0
    os.makedirs(OUT, exist_ok=True)
    json.dump(r, open(f + ".tmp", "w"))
    os.replace(f + ".tmp", f)
    return nome, metodo, s, f"fo={r.get('fo')} viol={r.get('violacoes')} em {r['tempo_parede_s']:.0f}s"


def _coletar(nome, tempo):
    """-> {metodo: dict(fo_min, fo_med, n, viol_max, t, nativa_min)} ; para heuristicas, `fo_*` = FO REAVALIADA no nivel de peca (a mesma funcao dos baselines)."""
    d = {}
    for m in METODOS:
        v, nat, viol, tt = [], [], [], []
        for s in range(100):
            f = caminho(nome, m, s, tempo)
            if os.path.exists(f):
                x = json.load(open(f))
                if x.get("fo") is not None:
                    v.append(x.get("fo_reavaliada", x["fo"])); nat.append(x["fo"]); viol.append(x["violacoes"]); tt.append(x["tempo_parede_s"])
        if v:
            d[m] = {"fo_min": min(v), "fo_med": statistics.mean(v), "n": len(v), "viol_max": max(viol), "t": statistics.mean(tt), "nativa_min": min(nat)}
    return d


def resumo(nomes, tempo, tol_comparavel=5e-4):
    """Tabela do E-A0 com TODOS os metodos no nivel de peca (FO media das sementes) e estatistica pareada contra o PCGLNS sobre as instancias comparaveis
    (as em que a FO nativa da construcao coincide, tol. relativa, com a reavaliada no nivel de peca: mesmo problema)."""
    from scipy import stats
    dados = {n: _coletar(n, tempo) for n in nomes}
    dados = {n: d for n, d in dados.items() if "heur_pi" in d and d["heur_pi"]["viol_max"] == 0 and "pcglns" in d}
    comp = {n: abs(d["heur_pi"]["nativa_min"] - d["heur_pi"]["fo_min"]) <= tol_comparavel * d["heur_pi"]["nativa_min"] for n, d in dados.items()}
    cols = [("pcglns", "PCGLNS"), ("vns_pi", "VNS-Pi"), ("heur_pi", "heur. (construcao)"), ("heur_ls", "heur. + busca local"), ("heur_vns", "heur. + VNS")]
    print(f"# E-A0 -- heuristica proposta (construcao e construcao + busca local) x PCGLNS x VNS-Pi nas instancias geometricas do CPPLib (T = {tempo} s)\n")
    print("FO = `fo_from_path` (tempo em s), MESMA funcao para todos, no NIVEL DE PECA; menor e melhor; media das sementes (n entre parenteses). "
          f"'Comparavel' = a FO nativa da construcao coincide (tol. {tol_comparavel:g}) com a reavaliada no nivel de peca (mesmo problema que os baselines). "
          "Todas as solucoes dos metodos listados respeitam Pi (violacoes = 0), exceto onde marcado. Ver `ea0_lib.py`, `heuristica_ls.py`.\n")
    print("| instancia | pecas | comparavel | " + " | ".join(nm for _, nm in cols) + " |")
    print("|---|---:|:--:|" + "---:|" * len(cols))
    for n, d in dados.items():
        npec = json.load(open(caminho(n, "heur_pi", 0, tempo)))["n_pecas"]
        cel = lambda m: (f"{d[m]['fo_med']:.1f} (n={d[m]['n']})" + ("" if d[m]["viol_max"] == 0 else f" **viol {d[m]['viol_max']}**")) if m in d else "--"
        print(f"| {n} | {npec} | {'sim' if comp[n] else '**nao**'} | " + " | ".join(cel(m) for m, _ in cols) + " |")
    print()
    print("Gap sobre o PCGLNS (FO media das sementes), so instancias comparaveis; positivo = pior que o PCGLNS; Wilcoxon pareado bilateral (zeros descartados):\n")
    print("| metodo | #inst | gap medio | mediana | melhor que o PCGLNS em | p (Wilcoxon) | tempo medio de parede (s) |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for m, nm in cols[1:]:
        g = [100 * (d[m]["fo_med"] / d["pcglns"]["fo_med"] - 1) for n, d in dados.items() if comp[n] and m in d and d[m]["viol_max"] == 0]
        if not g:
            continue
        tt = statistics.mean(d[m]["t"] for n, d in dados.items() if comp[n] and m in d)
        try:
            p = f"{float(stats.wilcoxon(g, method='auto').pvalue):.4f}" if len(g) >= 6 and any(abs(x) > 1e-9 for x in g) else "--"
        except ValueError:
            p = "--"
        print(f"| {nm} | {len(g)} | {statistics.mean(g):+.2f}% | {statistics.median(g):+.2f}% | {sum(1 for x in g if x < 0)} de {len(g)} | {p} | {tt:.1f} |")
    excl = [n for n in dados if not comp[n]]
    if excl:
        print(f"\nFora da comparacao (corte em segmentos / tecnicas especiais; a construcao explora um espaco maior que o GTSP de peca inteira): {', '.join(excl)}.")


def resumo_pecas_antigo(nomes, tempo, tol_comparavel=5e-4):
    """(versao anterior do resumo, so heur_pi) Compara so onde a FO NATIVA da heuristica coincide (tol. relativa) com a FO reavaliada no nivel de peca: nessas instancias a heuristica
    esta resolvendo o MESMO problema (cada contorno cortado de uma vez) que os baselines. Onde diferem (corte em segmentos, tecnicas especiais
    como corte comum -- categoria p7 do CPPLib), a heuristica explora um espaco de solucoes maior e a comparacao nao e de mesma natureza."""
    linhas = {n: _coletar(n, tempo) for n in nomes}
    linhas = {n: d for n, d in linhas.items() if "heur_pi" in d and d["heur_pi"]["viol_max"] == 0}
    print(f"# E-A0 -- heuristica proposta x PCGLNS x VNS-Pi x MASTRI nas instancias geometricas do CPPLib (T = {tempo} s por execucao de PCGLNS/VNS-Pi)\n")
    print("FO =`fo_from_path` (tempo em s: corte a v_cut, deslocamento a v_air), MESMA funcao para todos; menor e melhor. Heuristica: 'peca' = FO reavaliada no nivel de peca "
          "(o tour de entradas da heuristica, cortando cada contorno de uma vez), 'nativa' = o `fo_total` dela. Estocasticos: media (melhor) sobre as sementes; 'viol' = pares de Pi violados. "
          f"'Comparavel' = |nativa - peca| <= {tol_comparavel:g} x nativa. Ver `ea0_lib.py` para a conversao e as limitacoes.\n")
    print("| instancia | pecas | Pi | heur_pi peca | heur_pi nativa | comparavel | PCGLNS (media; melhor) | VNS-Pi (media; melhor) | MASTRI (viol) | melhor viavel (peca) | gap heur_pi vs. PCGLNS | t heur (s) |")
    print("|---|---:|---:|---:|---:|:--:|---:|---:|---:|---:|---:|---:|")
    gaps = {"pcglns": [], "vns_pi": []}
    excl = []
    for nome, d in linhas.items():
        h = d["heur_pi"]
        comp = abs(h["nativa_min"] - h["fo_min"]) <= tol_comparavel * h["nativa_min"]
        j = json.load(open(caminho(nome, "heur_pi", 0, tempo)))
        feas = [d[m]["fo_min"] for m in ("heur_pi", "pcglns", "vns_pi") if m in d and d[m]["viol_max"] == 0]
        ref = min(feas)
        cel = lambda m: (f"{d[m]['fo_med']:.1f} ({d[m]['fo_min']:.1f}) n={d[m]['n']}" + ("" if d[m]["viol_max"] == 0 else f" **viol {d[m]['viol_max']}**")) if m in d else "--"
        mas = f"{d['mastri']['fo_min']:.1f} ({d['mastri']['viol_max']})" if "mastri" in d else "--"
        gp = f"{100 * (h['fo_min'] / d['pcglns']['fo_med'] - 1):+.2f}%" if "pcglns" in d else "--"
        print(f"| {nome} | {j['n_pecas']} | {j['n_pares_pi']} | {h['fo_min']:.1f} | {h['nativa_min']:.1f} | {'sim' if comp else '**nao**'} | {cel('pcglns')} | {cel('vns_pi')} | {mas} | {ref:.1f} | {gp} | {h['t']:.0f} |")
        if comp:
            for m in gaps:
                if m in d and d[m]["viol_max"] == 0:
                    gaps[m].append(100 * (h["fo_min"] / d[m]["fo_med"] - 1))
        else:
            excl.append(nome)
    print()
    for m, nm in (("pcglns", "PCGLNS"), ("vns_pi", "VNS-Pi")):
        if gaps[m]:
            print(f"- heur_pi (nivel de peca) vs. {nm} (FO media das sementes), {len(gaps[m])} instancias comparaveis: gap medio **{statistics.mean(gaps[m]):+.2f}%** "
                  f"(mediana {statistics.median(gaps[m]):+.2f}%; positivo = heuristica PIOR); heuristica melhor em {sum(1 for x in gaps[m] if x < 0)} de {len(gaps[m])}.")
    if excl:
        print(f"- Fora da comparacao por nao serem do mesmo problema (corte em segmentos / tecnicas especiais): {', '.join(excl)}.")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "rodar"
    def _opt(flag, tipo, default):
        return tipo(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default
    com_valor = {"--tempo", "--sementes", "--workers", "--limite"}
    tempo = _opt("--tempo", int, 30)
    explicit = [a for i, a in enumerate(sys.argv[2:], 2) if not a.startswith("--") and sys.argv[i - 1] not in com_valor]
    todas = sorted(listar())
    lim = _opt("--limite", int, 0)
    nomes = explicit or ([todas[int(i * len(todas) / lim)] for i in range(lim)] if lim else todas)
    if modo == "resumo":
        resumo(nomes, tempo)
    else:
        nseeds, workers = _opt("--sementes", int, 3), _opt("--workers", int, 3)
        jobs = []
        for n in nomes:
            for m in METODOS:
                for s in (range(nseeds) if m in ESTOCASTICOS else [0]):
                    jobs.append((n, m, s, tempo))
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for n, m, s, msg in ex.map(_job, jobs, chunksize=1):
                print(f"[{time.strftime('%H:%M:%S')}] {n} {m} s{s}: {msg}", flush=True)
        print("EA0 CONCLUIDO", flush=True)
