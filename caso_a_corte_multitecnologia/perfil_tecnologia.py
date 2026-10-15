"""
perfil_tecnologia.py
=====================
Ponto único de verdade para os parâmetros de velocidade/custo por tecnologia
de corte. Isso substitui as 3 definições duplicadas e independentes de
_V_CUT/_V_AIR encontradas no projeto original (LCPP-main):

  - src/heuristic_core.py       linhas 101-102 (constantes nomeadas)
  - src/local_search_tree.py    linhas 77-78   (constantes nomeadas, duplicadas)
  - src/main.py                 linha 122      (valores INLINE: "100/6 if ... else 400",
                                                 nem usa as constantes nomeadas)

Risco que isso resolve: mudar a velocidade em um lugar sem mudar nos outros
dois produziria busca local e FO reportada inconsistentes entre si. Ver
docs/00_log_cronologico.md, entrada de 13/08/2026, para o achado completo.

O código original em LCPP-main NÃO foi alterado -- esta consolidação vale só
para o trabalho novo dentro de LCPP-Generalizacao.

QUESTÃO DA ESCALA FÍSICA -- histórico completo da investigação
--------------------------------------------------------------
Não existe, em nenhum documento do projeto original, confirmação explícita
da escala física das coordenadas das instâncias CPPLib (mm? unidade
abstrata normalizada?). Isso importa DIRETAMENTE aqui porque o perfil
PLASMA_ACO_45A abaixo está em unidades físicas reais (mm/s, s) -- e só faz
sentido físico combiná-lo com as coordenadas da instância se a escala destas
for conhecida.

Tentativas de confirmar pela FONTE PRIMÁRIA (30/08/2026, todas sem sucesso --
mesmo padrão de bloqueio de acesso a artigo já visto com Zhang et al. 2024,
ver docs/00_log_cronologico.md): (1) artigo original do CPPLib (Petunin et
al. 2020, DOI 10.1007/978-3-030-68821-9_21) -- página do SpringerLink não
tem o PDF completo nem menciona unidades no resumo; busca por cópia livre
não encontrou nada; Carlos confirmou não ter acesso institucional. (2)
Artigos relacionados do mesmo grupo (Khachay/Petunin) que poderiam descrever
o mesmo gerador de instâncias com mais detalhe -- "Discrete cutting path
problems..." (IJPR 2024) bloqueado (403, Taylor & Francis), "General Model
of Tool Path Problem for CNC Sheet Cutting Machines" bloqueado (robots.txt,
ScienceDirect), "Heuristic approaches for the cutting path problem"
bloqueado (429, ResearchGate). (3) Dataset "Profiles" (Burke et al. 2006,
citado por Zhang et al. 2024 como possível origem do CPPLib) -- busca não
encontrou documentação de escala em agregadores de nesting (ESICUP, etc.).
NENHUM bypass de bloqueio foi tentado (regra permanente deste projeto).

Evidência INDIRETA, mas agora SISTEMÁTICA (30/08/2026 -- decisão registrada
em docs/00_log_cronologico.md desse dia): com a fonte primária esgotada
como via de confirmação, testamos a escala pela ÚNICA outra via disponível
-- consistência dimensional interna, medida nas 148 instâncias .dxf REAIS
(não uma amostra) do CPPLib. Duas medições independentes:

  (a) Cabeçalho DXF ($INSUNITS): as instâncias amostradas retornam
      INSUNITS=6 (metros), $MEASUREMENT=1 (métrico) -- mas tomado ao pé da
      letra isso implicaria peças de até 6000×1500 METROS, fisicamente
      absurdo para corte de chapa. Conclusão: quase certamente um default
      do gerador/pipeline dos autores (comum em DXF gerado
      programaticamente), não uma declaração deliberada de escala -- o
      cabeçalho NÃO é uma fonte confiável aqui.

  (b) Plausibilidade dimensional, testada contra 4 hipóteses de unidade nas
      148/148 instâncias (maior dimensão do bounding box por instância,
      contra a faixa de bitola comercial real de chapa metálica,
      200-8000mm): unidade=mm (k=1): 148/148 (100%) plausíveis, mediana
      2000mm, min 500mm, max 6000mm -- e 90.5% ainda dentro da faixa mais
      estrita de bancada típica (300-4000mm), com os "fora da faixa" sendo
      as maiores instâncias de propósito (categoria "Combined parts",
      grandes por design, não outliers aleatórios). unidade=cm (k=10):
      13/148 (8.8%). unidade=polegada (k=25.4): 0/148 (0%). unidade=metro
      literal do cabeçalho (k=1000): 0/148 (0%). unidade=0.1mm (k=0.1):
      85/148 (57%, mediana 200mm -- plausível mas menos consistente).
      unidade=0.01mm (k=0.01): 0/148 (0%).

  CONCLUSÃO desta investigação: "unidade de desenho do CPPLib = mm" é, de
  longe, a hipótese mais consistente -- 100% de acerto no corpus INTEIRO
  contra 0-9% de qualquer alternativa testada. Ainda é uma INFERÊNCIA por
  consistência interna, não uma confirmação da fonte primária (não pode
  ser descartado, por exemplo, que a escala varie por instância ou que
  exista uma unidade não testada aqui) -- mas é evidência sistemática sobre
  o corpus completo, não mais um palpite ou uma observação pontual em 6
  amostras. Ver `caso_a_corte_multitecnologia/instances/cpplib/README.md`
  para a árvore de proveniência completa da biblioteca.

  DECISÃO (30/08/2026, após "vamos para outras alternativas" do Carlos
  quando o acesso ao artigo se mostrou inviável): usar k=1 (unidade DXF =
  mm) como interpretação de trabalho para o Caso A, SEMPRE rotulada como
  inferência (nunca como fato confirmado) em qualquer lugar que reporte
  números absolutos derivados dela -- e complementada por uma análise de
  sensibilidade a k (ver rodar_caso_a_plasma.py) para não depender de um
  único ponto de escala. Ver ESCALA_DXF_MM_POR_UNIDADE abaixo.
"""
from dataclasses import dataclass, field
from typing import Dict, Tuple

# Interpretação de trabalho para a escala das coordenadas do CPPLib -- ver
# a nota "QUESTÃO DA ESCALA FÍSICA" acima do módulo para o histórico
# completo da investigação. k=1.0 significa "1 unidade de coordenada DXF =
# 1mm". NÃO é uma confirmação da fonte primária -- é a hipótese mais
# consistente entre as testadas (100% de plausibilidade dimensional no
# corpus completo de 148 instâncias, contra 0-9% de qualquer alternativa).
# Qualquer resultado numérico absoluto derivado desta constante deve
# rotular explicitamente essa origem (inferência, não fato confirmado).
ESCALA_DXF_MM_POR_UNIDADE = 1.0


@dataclass(frozen=True)
class PerfilTecnologia:
    nome: str
    v_cut: float                  # velocidade de corte -- MESMA escala/unidade das coordenadas da instância
    v_air: float                  # velocidade de deslocamento em vazio -- mesma escala
    tempo_perfuracao: float = 0.0  # custo FIXO por contorno (pierce/perfuração) -- mesma unidade de tempo
    fonte: str = ""
    observacoes: str = ""


# ---------------------------------------------------------------------------
# Perfil original (laser) -- reproduz EXATAMENTE as constantes do código
# original. Usar este perfil deve reproduzir bit-a-bit os resultados já
# publicados (ver validar_regressao() abaixo) -- é o teste de sanidade antes
# de qualquer coisa nova ser considerada válida.
# ---------------------------------------------------------------------------
LASER_ORIGINAL = PerfilTecnologia(
    nome="laser_original_lcpp",
    v_cut=100.0 / 6.0,   # ≈ 16.666...
    v_air=400.0,
    tempo_perfuracao=0.0,
    fonte="heuristic_core.py:101-102 / local_search_tree.py:77-78 / main.py:122 (LCPP-main)",
    observacoes="Perfil de controle/regressão -- não deve ser alterado.",
)

# ---------------------------------------------------------------------------
# Dados de referência para corte a plasma (aço-carbono, bocal 45A,
# Hypertherm Duramax) -- convertidos de IPM (polegadas/min, dado original do
# fabricante) para mm/s. AINDA EM UNIDADES FÍSICAS REAIS -- não convertido
# para a escala interna das instâncias (ver questão em aberto acima).
#
# Fonte: tabela do fabricante Hypertherm Duramax, 45A, aço-carbono,
# consultada via garagewelding.com/plasma-cutting-steel-thickness-chart-amps-ipm-air-requirements
# (acesso 13/08/2026). O próprio fabricante alerta que não há tabela
# universal segura -- valores variam por equipamento; usar como referência
# de ORDEM DE GRANDEZA, não como calibração definitiva.
# ---------------------------------------------------------------------------
_POLEGADA_PARA_MM = 25.4

# Velocidade de deslocamento em vazio (rapid traverse) para mesas de corte a
# plasma CNC -- fonte: fichas técnicas de fabricante, 1.000 ipm (=25.400
# mm/min ≈ 423,3 mm/s), confirmado de forma consistente em DUAS fontes
# independentes: PlasmaCam (plasmacam.com/machspecs.php, "Cutting/rapid
# (X/Y)...0.1 to 1,000 ipm") e Machitech Gold Cut
# (machitech.com/gold-cut, "1,000 ipm (25400 mm/min)", com nota de que
# 3.500ipm é alcançável com opção extra "X-Motion" -- não usado aqui por
# ser upgrade, não padrão). Mesma ressalva das demais fichas de fabricante
# neste módulo: valor de ORDEM DE GRANDEZA/referência, não calibração
# definitiva de um equipamento específico. Acesso 30/08/2026.
V_AIR_PLASMA_REFERENCIA_MM_S = 1000.0 * _POLEGADA_PARA_MM / 60.0  # ≈ 423.33 mm/s

PLASMA_ACO_45A_REFERENCIA_MM_S: Dict[str, Tuple[float, float]] = {
    # espessura aproximada: (velocidade de corte em mm/s, atraso de perfuração em s)
    "24GA (~0.6mm)":   (325 * _POLEGADA_PARA_MM / 60, 0.0),
    "16GA (~1.5mm)":   (249 * _POLEGADA_PARA_MM / 60, 0.1),
    "14GA (~1.9mm)":   (225 * _POLEGADA_PARA_MM / 60, 0.2),
    "10GA (~3.4mm)":   (129 * _POLEGADA_PARA_MM / 60, 0.4),
    "3/16in (~4.8mm)": (85  * _POLEGADA_PARA_MM / 60, 0.5),
    "1/4in (~6.4mm)":  (48  * _POLEGADA_PARA_MM / 60, 0.6),
    "3/8in (~9.5mm)":  (33  * _POLEGADA_PARA_MM / 60, 0.8),
    "1/2in (~12.7mm)": (18  * _POLEGADA_PARA_MM / 60, 1.0),
}


def perfil_plasma_por_espessura(espessura: str, v_air_mm_s: float = V_AIR_PLASMA_REFERENCIA_MM_S) -> PerfilTecnologia:
    """Constrói um PerfilTecnologia de plasma para uma espessura específica.

    v_air_mm_s (velocidade de deslocamento em vazio / rapid traverse): default
    agora é V_AIR_PLASMA_REFERENCIA_MM_S (≈423,3 mm/s = 1.000 ipm, fonte:
    PlasmaCam + Machitech, ver comentário acima da constante) -- pode ser
    sobrescrito explicitamente se um valor de outro equipamento for preferível.
    Mantido como parâmetro (não hardcoded) para não esconder a suposição.
    """
    if espessura not in PLASMA_ACO_45A_REFERENCIA_MM_S:
        raise KeyError(f"Espessura '{espessura}' não está na tabela de referência. "
                        f"Opções: {list(PLASMA_ACO_45A_REFERENCIA_MM_S)}")
    v_cut, pierce = PLASMA_ACO_45A_REFERENCIA_MM_S[espessura]
    return PerfilTecnologia(
        nome=f"plasma_aco_45a_{espessura}",
        v_cut=v_cut,
        v_air=v_air_mm_s,
        tempo_perfuracao=pierce,
        fonte="Hypertherm Duramax 45A (corte) + PlasmaCam/Machitech (deslocamento), acesso 13-30/08/2026",
        observacoes="Em mm/s -- assume ESCALA_DXF_MM_POR_UNIDADE=1.0 (unidade DXF do CPPLib = mm, "
                     "inferência por consistência dimensional, não confirmação da fonte primária). "
                     "Ver nota 'QUESTÃO DA ESCALA FÍSICA' no topo do módulo.",
    )


def validar_regressao() -> None:
    """Confere que LASER_ORIGINAL reproduz exatamente as constantes do
    código original. Roda sozinho, sem depender de dados de instância --
    é só a checagem rápida dos números-base (constantes), não o teste de
    regressão completo.

    O teste de regressão completo (ponta a ponta: chama
    heuristic_core.run_heuristic nas instâncias CPPLib reais e compara FO)
    JÁ EXISTE e JÁ PASSOU -- ver
    caso_a_corte_multitecnologia/validar_regressao_perfil_tecnologia.py.
    Não é chamado automaticamente daqui para manter este módulo livre de
    dependência de heuristic_core.py/dxf_parser.py (perfil_tecnologia.py
    permanece um módulo de dados puro, sem lógica de pipeline). Resultado
    da última execução completa (30/08/2026): FO idêntica (delta=0.0,
    bit-a-bit) em 84/84 instâncias válidas da categoria "com precedência"
    do CPPLib, com v_cut/v_air/tempo_perfuracao=LASER_ORIGINAL comparado
    contra os defaults embutidos em heuristic_core._DEFAULT_CONFIG, além de
    cobertura de todos os 5 pontos de chamada internos (edge_swap, root
    enumerate, child_order permutation/2opt, vertex enumerate,
    precedence_strategy sequential/sequential_2opt/hybrid) e de uma checagem
    de sanidade de que tempo_perfuracao>0 aumenta a FO exatamente em
    n_perfurações × tempo_perfuração. Ver docs/00_log_cronologico.md,
    entrada de 30/08/2026, para o relato completo.
    """
    assert abs(LASER_ORIGINAL.v_cut - (100.0 / 6.0)) < 1e-12, "v_cut não bate com o original"
    assert LASER_ORIGINAL.v_air == 400.0, "v_air não bate com o original"
    assert LASER_ORIGINAL.tempo_perfuracao == 0.0, "modelo original não tem custo de perfuração"
    print("OK -- LASER_ORIGINAL reproduz as constantes originais do LCPP-main.")
    print("Teste de regressão completo (ponta a ponta, instâncias reais): já rodado e OK.")
    print("Ver validar_regressao_perfil_tecnologia.py e docs/00_log_cronologico.md (30/08/2026).")


if __name__ == "__main__":
    validar_regressao()
    print()
    print(f"Escala de trabalho: 1 unidade DXF = {ESCALA_DXF_MM_POR_UNIDADE}mm (inferência por "
          f"consistência dimensional em 148/148 instâncias CPPLib -- não confirmação da fonte "
          f"primária; ver nota 'QUESTÃO DA ESCALA FÍSICA' no topo do módulo).")
    print(f"v_air de plasma (default): {V_AIR_PLASMA_REFERENCIA_MM_S:.2f} mm/s (1.000 ipm, PlasmaCam/Machitech).")
    print()
    print("Perfis de plasma disponíveis (aço-carbono, bocal 45A Hypertherm Duramax):")
    for espessura, (v_cut, pierce) in PLASMA_ACO_45A_REFERENCIA_MM_S.items():
        print(f"  {espessura:>18s}  v_cut={v_cut:7.2f} mm/s   pierce={pierce:.1f}s")
