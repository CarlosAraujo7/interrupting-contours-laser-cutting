# Robustez: heurística reexecutada em máquina livre e referência de peça com mais sementes e tempo (`docs/24`)

## (a) Heurística reexecutada em máquina livre — 282 instâncias

- Diferença da FO formal (reexecução ÷ rodada gravada − 1) em t = 0: mediana **+0.0000%**, média +0.0003%, |máx.| 0.231%; nova rodada menor em 14, igual em 246, maior em 22.
- A t = 1 s: mediana +0.0000%, |máx.| 4.919%.
- **Vitórias sobre o PCGLNS por peça** (t = 0): formal 277 → 279; poligonal 253 → 254 (rodada gravada → reexecução).

## (b) Referência de peça: 3 sementes × 60 s contra 1 semente × 20 s — 60 instâncias

- Melhor das sementes ÷ referência original − 1: mediana **-0.0000%**, mín. -0.1055%, máx. +0.0000%; melhor em 18, igual em 42, pior em 0.
- Dispersão entre sementes (máx ÷ mín − 1): mediana 0.0047%, máx. 0.118%.
- **Vitórias da heurística (formal, t = 0) sobre a referência de peça:** 60 → 60 de 60 (referência original → melhor das sementes); poligonal: 54 → 53.
