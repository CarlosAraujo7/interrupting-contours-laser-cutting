# Verificacao dos metadados no Crossref (14/10/2026)

Conferido: titulo (similaridade), ano, volume, paginas/numero do artigo e a lista completa de sobrenomes dos autores. O ano do Crossref e o da publicacao online; 1 ano a mais ou a menos que o do volume e normal. Isto confere dados bibliograficos, nao o conteudo dos artigos.

| chave | como achado | titulo (sim.) | resultado |
|---|---|---:|---|
| barr1995designing | busca (DOI 10.1007/bf02430363) | 1.00 | ok |
| dewil2011tabu | DOI 10.4028/www.scientific.net/KEM.473.739 | 1.00 | ok |
| dewil2014construction | DOI 10.1080/00207543.2014.895064 | 1.00 | ok |
| dewil2015improvement | DOI 10.1080/00207543.2014.959268 | 1.00 | ano 2015 x 2014 (ano online/impresso) |
| dewil2015overlooked | DOI 10.4028/www.scientific.net/KEM.639.517 | 1.00 | ok |
| dewil2016review | DOI 10.1007/s00170-016-8609-1 | 1.00 | ok |
| eiselt1995arc | DOI 10.1287/opre.43.3.399 | 1.00 | ok |
| garcia2019piercing | DOI 10.3390/app9163231 | 1.00 | ok |
| hashemzadeh2014piercing | DOI 10.1016/j.optlaseng.2013.10.001 | 0.98 | ok |
| hoeft1997heuristics | DOI 10.1080/07408179708966382 | 1.00 | ok |
| hooker1995testing | busca (DOI 10.1007/bf02430364) | 1.00 | ok |
| huangfu2018highs | DOI 10.1007/s12532-017-0130-5 | 1.00 | ano 2018 x 2017 (ano online/impresso) |
| khachay2020pcglns | DOI 10.1007/978-3-030-62867-3_15 | 1.00 | ok |
| lenstra1976general | DOI 10.1002/net.3230060305 | 1.00 | ok |
| noon1993efficient | erro | | URLError |
| petunin2020cpplib | DOI 10.1007/978-3-030-68821-9_21 | 1.00 | ok |
| salman2020precedence | DOI 10.1016/j.orl.2020.01.009 | 1.00 | ok |
| silva2019exact | DOI 10.1016/j.cor.2019.104772 | 1.00 | ok |
| smith2017glns | DOI 10.1016/j.cor.2017.05.010 | 1.00 | ok |
| wilcoxon1945individual | busca (DOI 10.2307/3001968) | 1.00 | ok |
| zhang2024heuristic | DOI 10.1016/j.eswa.2023.121567 | 1.00 | ok |

## Nao conferidas no Crossref (conferir a mao ou na fonte)

- `amada2026ensis` (misc): {ENSIS AJe} series 3\,kW to 15\,kW fiber laser -- \url{https://www.amada.com/america/ensis-series}
- `blm2026ls7` (misc): {LS7}: 2D laser cutting machine for sheet metal, technical information -- \url{https://www.blmgroup.com/en-us/laser-sheet/ls7/technical-information}
- `bystronic2025bystarfiber` (misc): {ByStar Fiber 6225/8025}, technical data sheet -- \url{https://btp.bystronic.com/api/collection/search/1bed4bd663e65f909d73ee85da3
- `holm1979simple` (article): A simple sequentially rejective multiple test procedure -- busca nao confirmou (melhor: Correction: An Improved Sequentially Rejective Bonferroni Te)
- `lcpp1companion` (misc): Segment-Level Laser Cutting Path Planning with Dynamic Deadheading: A Hybrid Spatial--Grap -- Manuscript submitted to the European Journal of Operational Research (preprint o
- `piranha2026rapidpierce` (misc): 12\,kW fiber laser rapid pierce -- \url{https://piranhafab.com/laser/12kw-fiber-laser-rapid-pierce/}
- `prima2015platino` (misc): New and improved -- Production Engineering Solutions, 30 April 2015, \url{https://www.pesmedia.com/n
- `rodrigues2012cutting` (article): Cutting path as a rural postman problem: solutions by memetic algorithms -- busca nao confirmou (melhor: Algorithms for the rural postman problem)
- `salvagnini2026l3g4` (misc): {L3.G4} sheet metal fibre laser cutting system: technical data -- \url{https://www.salvagninigroup.com/en-INT/products/laser-systems/l3-g4}
- `salvagnini2026l5` (misc): {L5} sheet metal fibre laser cutting system: technical data -- \url{https://www.salvagninigroup.com/en-INT/products/laser-systems/L5}
- `trumpf3030fiber` (misc): {TruLaser} 3030 fiber, 3040 fiber, 3060 fiber, 3080 fiber -- \url{https://www.trumpf.com/en_US/products/machines-systems/2d-laser-cutting-mac
- `westmfg2018piercing` (misc): Major fiber laser efficiencies start with piercing -- West Manufacturing News, January 2018, \url{https://mfgnewsdigital.mydigitalpubl

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

