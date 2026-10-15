"""
montar_suplementar_n1.py  --  builds the SUPPLEMENTARY MATERIAL of manuscript N1 in `manuscrito/suplementar_N1/` (candidate; the authors decide what to publish)
==========================================================================================================================================================
Copies, without changing, the files that support the numbers of the manuscript: pre-specified protocols, our scripts, per-task result files (JSON), result reports (`RESULTADOS_*.md`), the table generator
and SHA-256 manifests. Writes `MANIFESTO_SHA256.txt`, `README.md`, `CITATION.cff` and `.gitignore` into `repositorio_N1/` (the folder to copy into the authors' public repository).

NOT included (explicit decision; see the generated README): `src_base/` (code of the heuristic of the companion manuscript: decision of its authors), third-party instances (the 282 synthetic instances
`instancias_lcpp1_dados/`, CPPLib, PCGTSPLIB), any file that contains the geometry of third-party instances (the stored paths `caminhos_282*/` and the coordinates of the solution paths inside
`v3_resultados/`, which are STRIPPED here), `ferramentas/` (PCGLNS, LKH-3: point to the source), PDFs, internal documents (`docs/16`, `18`, `20`, `22`, notes, log).
Usage: python montar_suplementar_n1.py   (idempotent: deletes and rebuilds `suplementar_N1/`, which is only a copy)
"""
import os
import json
import shutil
import hashlib
import fnmatch

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
DEST = os.path.join(AQUI, "repositorio_N1")                  # o pacote suplementar E o repositorio publico do N1 (copiar este conteudo para o repositorio dos autores)
REPO_NOME = "interrupting-contours-laser-cutting"
REPO_URL = "https://github.com/CarlosAraujo7/interrupting-contours-laser-cutting"   # criado por Carlos em 14/10/2026
A = "caso_a_corte_multitecnologia"

ARQUIVOS = [
    "docs/17_protocolo_V2_segmento.md", "docs/19_protocolo_V3_reinicio.md", "docs/21_sensibilidade_pi_estrita_x_fechamento.md", "docs/23_protocolo_reparo_ciente_do_reinicio.md",
    "docs/24_robustez_e_escala.md", "docs/25_leitura_dewil_completa_e_voo_nao_linear.md", "docs/26_protocolo_reotimizacao_tau.md", "docs/27_protocolo_tau_mais_reinicio.md", "docs/28_ancoras_sem_maquina_rpp_cpplib_e_fendas.md", "docs/34_plano_de_pesquisa_dados_de_maquina_N1.md", "docs/35_base_de_evidencias_de_parametros_de_maquina.md", "docs/LEDGER_USO_IA.md", "ENVIRONMENT.md", "requirements.txt", "LICENSE", "LICENSES.md", "lancar_v3_estrita.sh",
]
PASTAS = [
    (A, ["*.py", "RESULTADOS_*.md", "v3_manifesto.json", "rpp_exato.json", "lista_varredura_t.txt"], ["lcpp1_segmento_resultados", "estrita_resultados", "reparo_resultados", "escala_resultados", "rpp_lcpp1_resultados",
                                                                                                       "segmento_resultados", "v2_resultados", "tau_resultados", "tau_reinicio_resultados", "rpp_cpplib_resultados", "fendas_resultados", "teto_resultados", "milp_certificado_resultados"]),
    (A + "/auditoria_lcpp1", ["*.py", "LEIA-ME.md", "nomes_amostra_v3.txt", "auditoria_resumo.json", "RESULTADOS_CONTINUIDADE_282.txt"], ["honesta_282", "continuidade_282_dp", "pecas_robustez"]),
    ("manuscrito", ["gerar_tabelas_n1.py", "gerar_figuras_n1.py", "montar_suplementar_n1.py", "verificar_referencias_n1.py"], []),
    ("manuscrito/N1/submissao", ["verificacao_referencias_crossref.md"], []),
]
EXCLUIR_PY = ("lancar_", "tmp_")


def copiar(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def copiar_v3():
    """v3_resultados/: copia os JSON SEM as coordenadas dos caminhos (geometria das instancias de terceiros)."""
    s, d = os.path.join(RAIZ, A, "v3_resultados"), os.path.join(DEST, A, "v3_resultados")
    os.makedirs(d, exist_ok=True)
    for f in sorted(os.listdir(s)):
        r = json.load(open(os.path.join(s, f)))
        if isinstance(r.get("melhor"), dict):
            r["melhor"].pop("caminho", None)
        json.dump(r, open(os.path.join(d, f), "w"))


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.makedirs(DEST)
    for rel in ARQUIVOS:
        s = os.path.join(RAIZ, rel)
        if os.path.exists(s):
            copiar(s, os.path.join(DEST, rel))
        else:
            print("absent:", rel)
    for pasta, padroes, subs in PASTAS:
        base = os.path.join(RAIZ, pasta)
        for f in sorted(os.listdir(base)):
            p = os.path.join(base, f)
            if os.path.isfile(p) and any(fnmatch.fnmatch(f, pad) for pad in padroes):
                copiar(p, os.path.join(DEST, pasta, f))
        for sub in subs:
            s = os.path.join(base, sub)
            if os.path.isdir(s):
                shutil.copytree(s, os.path.join(DEST, pasta, sub))
    copiar_v3()
    linhas, tot = [], 0
    for r, _, fs in os.walk(DEST):
        for f in sorted(fs):
            if f in ("MANIFESTO_SHA256.txt", "README.md", "CITATION.cff", ".gitignore"):
                continue
            p = os.path.join(r, f)
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            linhas.append(f"{h}  {os.path.relpath(p, DEST).replace(os.sep, '/')}")
            tot += os.path.getsize(p)
    linhas.sort(key=lambda x: x.split("  ", 1)[1])
    open(os.path.join(DEST, "MANIFESTO_SHA256.txt"), "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    leia = f"""# {REPO_NOME}

{REPO_URL}

Code, protocols and results for the manuscript **"What does interrupting contours buy? Optimality gaps, cost conventions, restart costs and air-move times in segment-level laser cutting path planning"**
(Amaro Junior, Costa Santos, Nepomuceno de Carvalho, Pinheiro, Dantas Araújo), prepared for *Computers & Operations Research* [status: in preparation; update on submission]. The repository holds everything needed to
recompute every number, table and figure of the paper from the stored results, the pre-specified protocols with their dates and code hashes, and the scripts that regenerate the results; it does **not** hold third-party
instances or the heuristic of the companion manuscript (see "What is NOT here").

**Licence:** code and documents under Apache-2.0 (`LICENSE`); third-party components keep their own licences (`LICENSES.md`). **Citation:** `CITATION.cff`. **Contact:** the corresponding author, Bonfim Amaro Junior (bonfim.amaro@uece.br).
**Use of generative AI:** an AI assistant (Claude, Anthropic) wrote and debugged the code and drafted the protocols and text under the direction of the authors, who reviewed everything; the declaration is in the paper and the usage ledger is in `docs/LEDGER_USO_IA.md`.

---

# Supplementary material — manuscript N1 (candidate; the authors decide what to publish)

Generated by `manuscrito/montar_suplementar_n1.py`: {len(linhas)} files, {tot / 1e6:.1f} MB; `MANIFESTO_SHA256.txt` lists the SHA-256 of each file. Everything is a copy, unchanged, except that the
coordinates of solution paths were removed from `v3_resultados/*.json` (they reproduce the geometry of third-party instances).

## What is here
- **Pre-specified protocols** (written and dated before the corresponding data; code frozen by SHA-256, verified before and after the run; deviations dated at the end of each; no external registry): `docs/17`
  (confirmatory CPPLib set), `docs/19` (restart-aware routes on the synthetic instances), `docs/21` (strict versus closing precedence), `docs/23` (restart-aware repair of the heuristic), `docs/24` (robustness and
  scale checks), `docs/26` (re-optimisation for non-linear air-move times), `docs/27` (air-move time with restart cost), `docs/28` (anchors without a machine, exact optima on CPPLib, open slits); `docs/25` is the
  reading of the literature behind the air-move time curve.
- **Our code** (`{A}/*.py`): arc-based generalised TSP + PCGLNS (`segmento_gtsp.py`), path verifier (`caminho_honesto.py`), the evaluation of the heuristic under three conventions (`avaliar_heuristica_formal.py`),
  exact rural-postman optimum (`rpp_exato.py`, `rpp_lcpp1.py`), runners and analysis scripts of each protocol, the restart-aware repair (`reparo_reinicio.py`), the independent reader of the synthetic instances
  (`instancias_lcpp1.py`), the re-optimisation for non-linear air-move times (`reotimizar_tau.py`, `reotimizar_tau_reinicio.py`), the map of regimes (`analise_mapa_regimes.py`), the exact optima on CPPLib (`rpp_cpplib.py`), the open
  slits (`fendas_segmento.py`), the certified bounds and the exact contour-level optimum (`teto_certificado.py`, independently checked by an exact restart-aware MILP in `verificar_certificado_milp.py`; exploratory, computed after the main results and not pre-specified; report
  `RESULTADOS_TETO_CERTIFICADO.md`), the bibliographic check against Crossref (`manuscrito/verificar_referencias_n1.py`, report in `manuscrito/N1/submissao/`), `manuscrito/gerar_tabelas_n1.py`, which produces every table and result number of the manuscript from the result files, and `manuscrito/gerar_figuras_n1.py`, which produces its four
  figures (Figure 1 is a toy layout of our own, solved exactly by the script).
- **Results per task** (JSON) and **reports** (`RESULTADOS_*.md`): `lcpp1_segmento_resultados/`, `v3_resultados/`, `estrita_resultados/`, `reparo_resultados/`, `escala_resultados/`, `rpp_lcpp1_resultados/`,
  `segmento_resultados/`, `v2_resultados/`, `tau_resultados/`, `tau_reinicio_resultados/`, `rpp_cpplib_resultados/`, `fendas_resultados/`, `teto_resultados/`, `milp_certificado_resultados/`, `auditoria_lcpp1/{{honesta_282,continuidade_282_dp,pecas_robustez}}/`.

## Licence
Our code and documents: Apache License 2.0 (file `LICENSE`); third-party components keep their own licences (`LICENSES.md`). The authors confirm this before publication.

## What is NOT here, and why
- **The synthetic instances and the heuristic of the companion manuscript** (`instancias_lcpp1_dados/`, `src_base/`, and the stored paths `auditoria_lcpp1/caminhos_282*/`, which contain instance geometry): third-party
  material that we do not redistribute. The companion repository gives the instances and the code. The scripts that regenerate the stored paths are `auditoria_lcpp1/caminhos_heuristica_282.py` (it runs on a temporary
  copy of the companion pipeline; it does not modify it); because the strong local search of the heuristic is limited by the clock, a regeneration may differ slightly (Section~"Budgets" of the manuscript and
  `docs/24`: 246 of 282 formal costs identical, largest difference 0.23%). The hash of the 282 stored paths used in the manuscript is in `docs/19` (section 7).
- **CPPLib layouts, PCGLNS, LKH-3**: obtain them from their sources; `LICENSES.md` and `ENVIRONMENT.md` give versions and licences.
- **Internal working documents and the chronological log.**

## How to reproduce (outline)
1. Install the environment of `ENVIRONMENT.md`; obtain the instances and the companion code; run `caminhos_heuristica_282.py` on the companion pipeline (stored paths) and the PCGLNS-by-piece audit
   (`auditoria_lcpp1/auditoria_honesta_282.py`).
2. Run, in this order and with the frozen scripts: `rodar_lcpp1_segmento.py`, `rodar_v3.py`, `rodar_estrita.py`, `reparo_reinicio.py rodar`, `rodar_escala.py`, `rpp_lcpp1.py`, `reotimizar_tau.py`, `reotimizar_tau_reinicio.py`, `rpp_cpplib.py`, `fendas_segmento.py`, `teto_certificado.py rodar` (needs `rpp_lcpp1.py` and the stored paths),
   then the analysis scripts (`analise_v3.py`, `analise_estrita.py`, `analise_reparo.py`, `comparar_robustez.py`, `rodar_escala.py resumo`, `rpp_lcpp1.py resumo`, `analise_voo_nao_linear.py`, `analise_tau.py`,
   `analise_tau_reinicio.py`, `analise_mapa_regimes.py`, `analise_fendas.py`, `teto_certificado.py resumo`), then `manuscrito/gerar_tabelas_n1.py` and `manuscrito/gerar_figuras_n1.py`.
3. Check the code hashes against the protocols (`sha256sum`) before and after each run. Runtimes in the manuscript were obtained on a laptop with a 12-thread CPU; PCGLNS budgets are wall-clock.
"""
    open(os.path.join(DEST, "README.md"), "w", encoding="utf-8").write(leia)
    cff = f"""cff-version: 1.2.0
message: "If you use this software or data, please cite the article (when published) and this repository."
title: "{REPO_NOME}: code, protocols and results for 'What does interrupting contours buy?'"
type: software
license: Apache-2.0
authors:
  - family-names: "Amaro Junior"
    given-names: "Bonfim"
    affiliation: "Universidade Estadual do Ceará (UECE)"
  - family-names: "Costa Santos"
    given-names: "Marcio"
    affiliation: "Universidade Federal de Minas Gerais (UFMG)"
  - family-names: "Nepomuceno de Carvalho"
    given-names: "Guilherme"
    affiliation: "Universidade Estadual do Ceará (UECE)"
  - family-names: "Pinheiro"
    given-names: "Plácido Rogério"
    affiliation: "Universidade de Fortaleza (UNIFOR)"
  - family-names: "Dantas Araújo"
    given-names: "Carlos Vinicio"
    affiliation: "Universidade Estadual do Ceará (UECE)"
repository-code: "{REPO_URL}"
"""
    open(os.path.join(DEST, "CITATION.cff"), "w", encoding="utf-8").write(cff)
    open(os.path.join(DEST, ".gitignore"), "w", encoding="utf-8").write("__pycache__/\n*.pyc\n*.log\n.ipynb_checkpoints/\n.venv/\n")
    print(f"repositorio_N1: {len(linhas)} files (+README, CITATION, .gitignore), {tot / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
