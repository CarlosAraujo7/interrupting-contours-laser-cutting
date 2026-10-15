"""
verificar_referencias_n1.py  --  confere, no Crossref, os metadados (titulo, ano, volume, paginas, TODOS os autores) das referencias citadas no N1 (14/10/2026)
=======================================================================================================================================================
Le `N1/main.aux` (chaves citadas) e `N1/referencias.bib`. Com DOI: consulta `https://api.crossref.org/works/<doi>`. Sem DOI (artigos): busca por titulo e autor (`query.bibliographic`) e aceita
so se o titulo bater (similaridade >= 0,9). Compara titulo, ano (o do Crossref e o da publicacao online; a diferenca de 1 ano com o ano do volume e esperada e marcada como "ano online"),
volume, paginas e a lista de sobrenomes dos autores. NAO substitui a leitura dos artigos: so confere dados bibliograficos.
Uso: python verificar_referencias_n1.py > N1/submissao/verificacao_referencias_crossref.md
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request
from difflib import SequenceMatcher

AQUI = os.path.dirname(os.path.abspath(__file__))
N1 = os.path.join(AQUI, "N1")
UA = {"User-Agent": "verificar_referencias_n1 (bibliographic check script; add a mailto: contact to use the Crossref polite pool)"}


def citadas():
    aux = open(os.path.join(N1, "main.aux"), encoding="utf-8", errors="replace").read()
    chaves = set()
    for m in re.finditer(r"\\citation\{([^}]*)\}", aux):
        chaves.update(x.strip() for x in m.group(1).split(","))
    return chaves


def ler_bib(caminho):
    txt = open(caminho, encoding="utf-8").read()
    entradas = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}\n", txt, re.S):
        tipo, chave, corpo = m.group(1), m.group(2).strip(), m.group(3)
        campos = {}
        for f in re.finditer(r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|\d+)", corpo):
            v = f.group(2)
            campos[f.group(1).lower()] = v[1:-1] if v[0] in "{\"" else v
        entradas[chave] = (tipo, campos)
    return entradas


def limpa(s):
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)
    s = re.sub(r"[{}\\'\"`^~$]", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def sobrenomes_bib(autores):
    out = []
    for a in autores.split(" and "):
        a = limpa(a)
        nome = a.split(",")[0] if a else ""
        nome = re.sub(r"\b(jr|sr)\.?$", "", nome.strip()).strip()        # "Stewart Jr., William R."
        out.append(nome.split()[-1] if nome else "")
    return out


def sobrenomes_cr(m):
    return [limpa(x.get("family", x.get("name", ""))).split()[-1] if (x.get("family") or x.get("name")) else "" for x in m.get("author", [])]


def comparar(c, m):
    obs = []
    t_cr, t_bib = limpa((m.get("title") or [""])[0]), limpa(c.get("title", ""))
    sim = SequenceMatcher(None, t_cr, t_bib).ratio()
    if sim < 0.9:
        obs.append(f"titulo no Crossref: {(m.get('title') or [''])[0][:70]}")
    ano_cr = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
    if c.get("year") and str(ano_cr) != c["year"]:
        obs.append(f"ano {c['year']} x {ano_cr}" + (" (ano online/impresso)" if ano_cr and abs(int(c['year']) - int(ano_cr)) == 1 else ""))
    vol = str(m.get("volume", ""))
    if c.get("volume") and vol and c["volume"] != vol:
        obs.append(f"volume {c['volume']} x {vol}")
    pag_cr = str(m.get("page", m.get("article-number", ""))).replace("–", "-")
    pag_bib = c.get("pages", "").replace("--", "-").replace("–", "-")
    if pag_bib and pag_cr and pag_bib.split("-")[0] != pag_cr.split("-")[0]:
        obs.append(f"paginas {pag_bib} x {pag_cr}")
    a_bib, a_cr = sobrenomes_bib(c.get("author", "")), sobrenomes_cr(m)
    if a_bib and a_cr and a_bib != a_cr:
        obs.append(f"autores {a_bib} x {a_cr}")
    return sim, obs


def main():
    cit = citadas()
    bib = ler_bib(os.path.join(N1, "referencias.bib"))
    print("# Verificacao dos metadados no Crossref (14/10/2026)\n")
    print("Conferido: titulo (similaridade), ano, volume, paginas/numero do artigo e a lista completa de sobrenomes dos autores. O ano do Crossref e o da publicacao online; 1 ano a mais ou a menos que o do volume e normal. Isto confere dados bibliograficos, nao o conteudo dos artigos.\n")
    print("| chave | como achado | titulo (sim.) | resultado |\n|---|---|---:|---|")
    sem = []
    for ch in sorted(cit):
        if ch not in bib:
            continue
        tipo, c = bib[ch]
        doi = c.get("doi")
        try:
            if doi:
                m = get("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/"))["message"]
                como = f"DOI {doi}"
            elif tipo in ("article", "inproceedings", "incollection"):
                q = urllib.parse.quote(c.get("title", "") + " " + c.get("author", "").split(" and ")[0])
                itens = get(f"https://api.crossref.org/works?query.bibliographic={q}&rows=1")["message"]["items"]
                if not itens:
                    sem.append((ch, tipo, c.get("title", ""), "sem resultado"))
                    continue
                m = itens[0]
                como = f"busca (DOI {m.get('DOI', '?')})"
            else:
                sem.append((ch, tipo, c.get("title", ""), (c.get("howpublished", c.get("note", "")))[:80]))
                continue
        except Exception as e:                                           # noqa: BLE001
            print(f"| {ch} | erro | | {type(e).__name__} |")
            continue
        time.sleep(0.4)
        sim, obs = comparar(c, m)
        if not doi and sim < 0.9:
            sem.append((ch, tipo, c.get("title", ""), f"busca nao confirmou (melhor: {(m.get('title') or [''])[0][:60]})"))
            continue
        print(f"| {ch} | {como} | {sim:.2f} | {'ok' if not obs else '; '.join(obs)} |")
    print("\n## Nao conferidas no Crossref (conferir a mao ou na fonte)\n")
    for ch, tipo, tit, ref in sem:
        print(f"- `{ch}` ({tipo}): {tit[:90]} -- {ref}")
    print(MANUAL)


MANUAL = """
## Conferencia manual na web (14/10/2026; fora do Crossref)

| chave | o que foi conferido | resultado |
|---|---|---|
| `holm1979simple` | registro JSTOR 4615733 (busca na web) | autor, titulo, Scand. J. Stat. 6(2), 65-70, 1979: confere (o Crossref nao tem a entrada) |
| `rodrigues2012cutting` | cabecalho do artigo nos repositorios INESC TEC / U. Porto | vol. 3 n. 1, paginas 22-37, jan-abr 2012: confere com o `.bib`; a bibliografia do LCPP-1 traz 31-46 (nao confere; avisar os autores dele) |
| `westmfg2018piercing` | pagina aberta no navegador do app | a frase (9 mm de aco-carbono: 2 s com onda continua padrao, 0,5 s com SmartPierce) confere; o processo e da Prima Power Laserdyne (alegacao de fabricante); a pagina nao mostra autor |
| `prima2015platino` (antes `prima2016platino`) | pagina aberta no navegador do app | data 30/04/2015 (o `.bib` dizia 2016), autor Dave Tudor, Prima Power Platino Fiber; 12 mm de aco doce em menos de 1 s com nitrogenio: confere |
| `trumpf3030fiber` | pagina do fabricante (TRUMPF) lida | maximo simultaneo 170 m/min confere; aceleracao nao informada |
| `bystronic2025bystarfiber` | PDF do fabricante (Bystronic) baixado e lido com pdftotext | 'Max. simultaneous positioning speed 170 m/min' confere; documento sem data; aceleracao nao informada |
| `salvagnini2026l3g4` | pagina do fabricante (Salvagnini) lida | 170 m/min (L3-30.G4 e L3-40.G4) confere; aceleracao nao informada |
| `salvagnini2026l5` | pagina do fabricante (Salvagnini) lida | 156 m/min e 'reaching 5g accelerations on short movements' conferem (chapa fina e media-fina; nao diz que vale para todo o curso) |
| `blm2026ls7` | pagina do fabricante (BLM Group) lida | 140 m/min (5552 ipm) e 20 m/s2 (2 g) conferem |
| `amada2026ensis` | pagina do fabricante (AMADA) lida | '1.4g acceleration over the entire work area' confere; a pagina nao traz velocidade |
| `garcia2019piercing` | artigo de acesso aberto aberto no navegador do app | 20 mm aco-doce: 11-11,5 s, 8-8,6 s apos otimizacao; 10 mm inox/aluminio: perfuracao rapida (<= 1,5 s); laser IPG de 5 kW |
| `lcpp1companion` | - | manuscrito submetido ao EJOR; nao ha o que conferir fora dos autores |

Anos: `dewil2015improvement` e `huangfu2018highs` usam o ano do volume (2015, 2018); o Crossref informa a publicacao online (2014, 2017). Mantido o ano do volume (convencao das revistas); nao e erro.
"""


if __name__ == "__main__":
    main()

