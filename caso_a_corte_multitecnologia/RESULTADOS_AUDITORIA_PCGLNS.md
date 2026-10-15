# Auditoria do PCGLNS nas instâncias de Ekstedt & Salman (PCGTSPLIB) — T = 120 s, sementes (123, 0, 1)

Custo do PCGLNS upstream (nosso) × custo da saída do PCGLNS guardada no repositório `ukoloff/PCGTSP-BnB` (semente 123, limite 3600 s) × ótimo exato (DP; só onde cabe em 60000 estados). **O que se confronta é a saída do PCGLNS dos mantenedores do repositório (mesmo solver), não as tabelas dos artigos.**

| instância | guardado | nosso s123 | nosso melhor (3 sem.) | nosso pior | ótimo (DP) | viável | s123 = guardado | melhor ≤ guardado |
|---|---:|---:|---:|---:|---:|:--:|:--:|:--:|
| ESC07 | 1730 | 1730 | 1730 | 1730 | 1730 | sim | sim | sim |
| ESC12 | 1390 | 1390 | 1390 | 1390 | 1390 | sim | sim | sim |
| ESC25 | 1418 | 1383 | 1383 | 1435 | -- | sim | não | sim |
| ESC47 | 1399 | 1431 | 1431 | 1507 | -- | sim | não | NÃO |
| ESC63 | 62 | 62 | 62 | 62 | -- | sim | sim | sim |
| ESC78 | 14832 | 14871 | 14871 | 14890 | -- | sim | não | NÃO |
| br17.12 | 43 | 43 | 43 | 43 | 43 | sim | sim | sim |
| ft53.1 | 6207 | 6200 | 6194 | 6207 | -- | sim | não | sim |
| ft53.2 | 6653 | 6653 | 6630 | 6653 | -- | sim | sim | sim |
| ft53.3 | 8446 | 8446 | 8446 | 8446 | -- | sim | sim | sim |
| ft53.4 | 11822 | 11822 | 11822 | 11822 | -- | sim | sim | sim |
| ft70.1 | 32848 | 32854 | 32742 | 33018 | -- | sim | não | sim |
| ft70.2 | 33486 | 33590 | 33541 | 33590 | -- | sim | não | NÃO |
| ft70.3 | 35309 | 35248 | 35248 | 35271 | -- | sim | não | sim |
| ft70.4 | 44497 | 44492 | 44492 | 44515 | -- | sim | não | sim |
| kro124p.1 | 33320 | 32835 | 32835 | 33305 | -- | sim | não | sim |
| kro124p.2 | 35321 | 35282 | 34729 | 35284 | -- | sim | não | sim |
| kro124p.3 | 41340 | 40931 | 40931 | 41419 | -- | sim | não | sim |
| kro124p.4 | 62818 | 62818 | 62818 | 62818 | -- | sim | sim | sim |
| p43.1 | 22545 | 22545 | 22545 | 22545 | -- | sim | sim | sim |
| p43.2 | 22841 | 22850 | 22844 | 22850 | -- | sim | não | NÃO |
| p43.3 | 23122 | 23127 | 23123 | 23127 | -- | sim | não | NÃO |
| p43.4 | 66857 | 66873 | 66848 | 66873 | 66848 | sim | não | sim |
| prob.100 | 1474 | 1530 | 1488 | 1594 | -- | sim | não | NÃO |
| prob.42 | 232 | 210 | 207 | 227 | -- | sim | não | sim |
| rbg048a | 282 | 282 | 282 | 282 | -- | sim | sim | sim |
| rbg050c | 378 | 378 | 378 | 378 | -- | sim | sim | sim |
| rbg109a | 848 | 851 | 848 | 851 | 848 | sim | não | sim |
| ry48p.1 | 13135 | 13154 | 13135 | 13154 | -- | sim | não | sim |
| ry48p.2 | 13802 | 13802 | 13802 | 13802 | -- | sim | sim | sim |
| ry48p.3 | 16540 | 16533 | 16533 | 16540 | -- | sim | não | sim |
| ry48p.4 | 25977 | 25977 | 25977 | 25977 | -- | sim | sim | sim |

Instâncias: 32. Semente 123 igual ao custo guardado em 13; nosso melhor de 3 sementes ≤ guardado em 26; pior que o guardado em 6; soluções inviáveis: 0.


---

# Auditoria do PCGLNS nas instâncias de Ekstedt & Salman (PCGTSPLIB) — T = 300 s, sementes (123, 0, 1)

Custo do PCGLNS upstream (nosso) × custo da saída do PCGLNS guardada no repositório `ukoloff/PCGTSP-BnB` (semente 123, limite 3600 s) × ótimo exato (DP; só onde cabe em 1 estados). **O que se confronta é a saída do PCGLNS dos mantenedores do repositório (mesmo solver), não as tabelas dos artigos.**

| instância | guardado | nosso s123 | nosso melhor (3 sem.) | nosso pior | ótimo (DP) | viável | s123 = guardado | melhor ≤ guardado |
|---|---:|---:|---:|---:|---:|:--:|:--:|:--:|
| rbg150a | 1415 | 1415 | 1415 | 1415 | -- | sim | sim | sim |
| rbg174a | 1644 | 1642 | 1642 | 1643 | -- | sim | não | sim |
| rbg253a | 2376 | 2383 | 2379 | 2383 | -- | sim | não | NÃO |
| rbg323a | 2547 | 2628 | 2610 | 2628 | -- | sim | não | NÃO |
| rbg341a | 2101 | 2260 | 2245 | 2260 | -- | sim | não | NÃO |
| rbg358a | 2080 | 2223 | 2202 | 2238 | -- | sim | não | NÃO |
| rbg378a | 2307 | 2441 | 2410 | 2442 | -- | sim | não | NÃO |

Instâncias: 7. Semente 123 igual ao custo guardado em 1; nosso melhor de 3 sementes ≤ guardado em 2; pior que o guardado em 5; soluções inviáveis: 0.


**Leitura das instâncias grandes (T = 300 s):** a saída guardada das quatro maiores (rbg323a-rbg378a) usou 3600 s e parou por tempo; a de rbg253a levou 1192 s; a de rbg150a/174a convergiu em 145/246 s. O PCGLNS nosso parou por tempo em todas as execuções a partir de rbg253a (e em 1 de 3 em rbg174a). Logo: concordância comprovada só até ~175 clusters; acima disso, a diferença de até +6,9% reflete o orçamento (12x menor), não necessariamente o solver.
