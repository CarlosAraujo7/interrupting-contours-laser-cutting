"""
dxf_parser.py
=============
Parser das instâncias .dxf do CPPLib (Petunin et al., 2020 -- ver
instances/cpplib/README.md) para o formato de entrada da heurística LCPP
(`List[shapely.Polygon]`), no MESMO contrato de
`src/data/load_instances.py::load_instance()` do LCPP-main.

Usa `ezdxf` (biblioteca padrão para leitura de DXF em Python) em vez de um
parser de texto próprio -- mais robusto a variações do formato (ordem de
group codes, presença/ausência de HEADER/TABLES, etc.). Os arquivos do
CPPLib são minimalistas: só `SECTION`/`ENTITIES`, uma entidade `POLYLINE`
por contorno, cada uma com uma sequência de sub-entidades `VERTEX`
(vértices em (x, y), sem arcos/bulge nas amostras inspecionadas).

Achado importante (29/08/2026, ver docs/00_log_cronologico.md e
instances/cpplib/README.md para o detalhe completo): ao escanear as 85
instâncias "com precedência", ~50% de TODAS as entidades POLYLINE (4702 de
9383) são DEGENERADAS -- exatamente 2 vértices, um segmento de reta ABERTO
(não uma peça fechada, área zero), sem conexão de endpoint com nenhuma
outra entidade do arquivo (confirmado: não são fragmentos de uma peça
maior que precisariam ser encadeados, ao contrário do formato .txt do
LCPP-main). Presente em 83/85 arquivos, em TODAS as bandas de tamanho
(j/k/e) e aninhamento (1x/3x/5x/7x) -- não é um artefato raro de um
arquivo isolado.

Hipótese mais provável (não confirmada com a literatura -- checado o
abstract do paper original via Springer, que só descreve o formato em alto
nível, e uma tentativa de acessar um paper relacionado do mesmo grupo via
Tandfonline, bloqueada com 403): são "slots"/fendas de corte retas, com
largura física não especificada no arquivo .dxf (só a linha de centro).
Comprimentos uniformes por arquivo (tipicamente 2-3 valores distintos, ex.
30/40/55 unidades) são consistentes com um padrão real de fenda/ranhura,
não com ruído aleatório.

Decisão de escopo para esta primeira versão do parser (registrada aqui,
NÃO resolvida unilateralmente -- sinalizada ao Carlos): estas entidades de
2 vértices são EXCLUÍDAS da lista de peças retornada (não podem virar
`Polygon` -- teriam área zero, e a pipeline geométrica original
(`heuristic_core.py`/`quadtree.py`, ambos reaproveitados sem modificação
de `src_base/`) é inteiramente baseada em `Polygon` com área positiva).
Alternativa considerada e descartada por ora: dar um `buffer()` de largura
arbitrária pra transformar cada fenda num polígono fino e alimentar a
pipeline sem modificação nenhuma -- teria a vantagem de não descartar ~50%
do conteúdo geométrico de cada instância, mas introduziria um parâmetro
numérico (a largura) sem base na literatura nem no arquivo de origem, o
que contaminaria a comparação de FO entre métodos/modos de forma dificil
de justificar num artigo. Cada instância carregada expõe as contagens
(`n_dxf_entities`, `n_pieces_used`, `n_entities_excluded`) para que o
descarte seja sempre visível e auditável nos resultados, nunca silencioso.

Isso NÃO compromete o teste da hipótese H2 (o alvo desta rodada): a
precedência Π testada aqui vem inteiramente do aninhamento geométrico
entre peças FECHADAS (contorno externo contendo um furo/peça interna),
que são exatamente as entidades com >=3 vértices -- as fendas de 2 vértices
não têm papel de "furo" nem de "pai" nesse sentido (uma reta aberta não
pode geometricamente cobrir nem estar contida em outro polígono no sentido
de `Polygon.covers`).

Achado (30/08/2026, ver docs/00_log_cronologico.md): identificado um typo
no PRÓPRIO dataset original do CPPLib -- o arquivo em
".../100-250 clusters/1x - contour nesting/p1xk_15/p1xj_15.DXF" está
nomeado com a banda de tamanho ERRADA (deveria ser "p1xk_15.DXF", igual à
sua pasta-mãe; a banda "k" = 100-250 clusters, "j" = 30-100 clusters,
convenção já decodificada em instances/cpplib/README.md). Isso faz
"p1xj_15" colidir com a instância genuinamente diferente (bbox
1500 vs 2000 unidades de span, 40 vs 65 polígonos válidos) que já existe
em ".../30-100 clusters/1x - contour nesting/p1xj_15/p1xj_15.dxf". Usar
`fp.stem` (nome do ARQUIVO) como identidade da instância -- como este
módulo fazia até esta data -- herda esse typo e produz 2 instâncias
diferentes com o mesmo nome (84 execuções, 83 nomes únicos). Confirmado
que os nomes de PASTA são únicos nas 85 pastas de instância desta
categoria (cada instância do CPPLib vive em sua própria pasta, essa é a
unidade organizacional real do dataset) -- por isso `load_instance_dxf`
agora retorna `fp.parent.name` (nome da PASTA) em vez de `fp.stem`, o que
resolve a colisão sem exigir nenhuma correção manual do dataset de
terceiros. Achado incidentalmente ao investigar um resultado suspeito em
`rodar_caso_a_plasma.py` (Bloco 2 pareava a FO de plasma de uma geometria
com a FO de laser CACHEADA da outra, sob o mesmo nome "p1xj_15" --
mecanismo documentado em `docs/00_log_cronologico.md`). Não afeta nenhum
resultado JÁ REPORTADO fora daquele CSV específico: toda comparação
anterior (regressão, "original" vs "com_pi", MASTRI/PCGLNS/TSH+VNS) pareia
laser/plasma ou modo-A/modo-B dentro da MESMA iteração sobre o MESMO
objeto de polígonos, então um nome duplicado não troca a geometria
comparada -- só a ETIQUETA de 2 das 84 linhas ficava ambígua (não errada
numericamente). `resultado_heuristica_cpplib.csv` (29/08/2026) mantém essa
ambiguidade de rótulo cosmética por ora (barato de regenerar se algum dia
for preciso distinguir as 2 linhas "p1xj_15" ali).
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import ezdxf
from shapely.geometry import MultiPolygon, Polygon

_TOL = 1e-6

# Nome da subpasta (dentro da raiz do CPPLib) com as 85 instâncias "com
# precedência" -- a categoria relevante para H2 (ver instances/cpplib/README.md).
CATEGORIA_COM_PRECEDENCIA = "Category - All example with precedence constraints"


# ---------------------------------------------------------------------------
# Parsing de uma entidade POLYLINE
# ---------------------------------------------------------------------------

def _polyline_to_points(entity) -> List[Tuple[float, float]]:
    """Extrai (x, y) de cada VERTEX de uma entidade POLYLINE (ignora z)."""
    return [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]


def _points_to_polygon(pts: List[Tuple[float, float]]) -> Optional[Polygon]:
    """
    Tenta construir um Polygon válido a partir de uma lista de pontos.

    Mesma tolerância/fallback de
    `load_instances.py::_segments_to_polygons()` do LCPP-main: se o anel
    resultante for inválido (auto-interseção etc.), tenta `buffer(0)`;
    descarta se a área final for <= _TOL. Retorna None para os casos
    degenerados (< 3 pontos distintos, área ~0) -- ver nota de escopo no
    docstring do módulo.
    """
    if len(pts) < 3:
        return None
    try:
        poly = Polygon(pts)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty:
            return None
        if isinstance(poly, MultiPolygon):
            # buffer(0) em anel auto-intersectante pode devolver
            # MultiPolygon -- ao contrário de load_instances.py (que
            # explode em vários polígonos, pois ali cada fragmento vem de
            # uma cadeia de segmentos independente), aqui a entidade de
            # origem é uma peça só, então ficamos com o maior pedaço.
            poly = max(poly.geoms, key=lambda g: g.area)
        if poly.area <= _TOL:
            return None
        return poly
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Carregamento de uma instância
# ---------------------------------------------------------------------------

def load_instance_dxf(filepath: str | Path) -> Tuple[str, List[Polygon], Dict]:
    """
    Carrega uma instância .dxf do CPPLib.

    Retorna (nome, lista_de_polygons, stats) -- mesmo contrato de
    `load_instances.py::load_instance()` (LCPP-main), com um dict de
    estatísticas extra:

      stats = {
          "n_dxf_entities":      total de entidades POLYLINE no arquivo,
          "n_pieces_used":       quantas viraram Polygon válido (usadas),
          "n_entities_excluded": quantas foram descartadas (degeneradas),
      }
    """
    fp = Path(filepath)
    doc = ezdxf.readfile(str(fp))
    msp = doc.modelspace()

    polygons: List[Polygon] = []
    n_total = 0
    n_excluded = 0
    for e in msp:
        if e.dxftype() != "POLYLINE":
            continue
        n_total += 1
        pts = _polyline_to_points(e)
        poly = _points_to_polygon(pts)
        if poly is None:
            n_excluded += 1
            continue
        polygons.append(poly)

    stats = {
        "n_dxf_entities": n_total,
        "n_pieces_used": len(polygons),
        "n_entities_excluded": n_excluded,
    }
    # (30/08/2026) Nome da instância = nome da PASTA, não do arquivo --
    # ver nota "Achado (30/08/2026)" no docstring do módulo. O CPPLib
    # organiza uma instância por pasta; usar o arquivo (`fp.stem`) herda
    # um typo real do dataset original (um arquivo "p1xj_15.DXF" dentro da
    # pasta "p1xk_15/") que colide com uma instância genuinamente diferente.
    return fp.parent.name, polygons, stats


# ---------------------------------------------------------------------------
# Carregamento em lote
# ---------------------------------------------------------------------------

def load_all_cpplib(
    root: str | Path,
    category_dirname: Optional[str] = CATEGORIA_COM_PRECEDENCIA,
) -> List[Tuple[str, List[Polygon], Dict]]:
    """
    Carrega todas as instâncias .dxf do CPPLib sob `root` (a pasta
    `instances/cpplib/`).

    Parâmetros
    ----------
    root : pasta raiz do CPPLib (contém as 4 subpastas "Category - ...").
    category_dirname : nome exato de UMA subpasta de categoria para
        restringir o carregamento (default: a categoria "com precedência",
        as 85 instâncias relevantes para H2). Passe None para carregar as
        148 instâncias das 4 categorias.

    Busca a extensão de forma case-insensitive (.dxf/.DXF) -- achado de
    29/08/2026: 24 dos 148 arquivos usam maiúscula (glob "*.dxf" comum
    perderia esses arquivos silenciosamente).
    """
    root = Path(root)
    base = (root / category_dirname) if category_dirname else root
    files = sorted(base.rglob("*.[Dd][Xx][Ff]"))

    out: List[Tuple[str, List[Polygon], Dict]] = []
    for fp in files:
        name, polys, stats = load_instance_dxf(fp)
        out.append((name, polys, stats))
    return out


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "instances" / "cpplib"
    insts = load_all_cpplib(root)
    print(f"Total de instâncias carregadas: {len(insts)}")
    tot_entities = sum(s["n_dxf_entities"] for _, _, s in insts)
    tot_used = sum(s["n_pieces_used"] for _, _, s in insts)
    tot_excl = sum(s["n_entities_excluded"] for _, _, s in insts)
    print(f"Entidades POLYLINE totais: {tot_entities}  usadas: {tot_used}  "
          f"excluídas (degeneradas): {tot_excl}  ({100*tot_excl/tot_entities:.1f}%)")
    n_zero_poly = sum(1 for _, polys, _ in insts if not polys)
    print(f"Instâncias com 0 peças válidas: {n_zero_poly}")
