# Reotimização dos dois níveis com tempo de voo não linear (`docs/26`; análise pré-registrada)

Instâncias com resultado: LASER: 60/60, DEWIL16: 60/60.

## LASER (n = 60; t_av = 0)

- **S/P − 1** (segmento × peça, ambos reotimizados): mediana **-0.067%** (IC 95% [-0.111%; -0.024%]; mín. -5.97%, máx. +0.03%); S < P em **51/60**, S > P em 9.
- S/G − 1 (reotimizado × rota guardada ciente do reinício, avaliada na curva): mediana -0.085% (IC [-0.143%; -0.064%]); S ≤ G em 54/60.
- P/P0 − 1 (peça reotimizado × peça otimizado para tempo linear): mediana -0.083% (IC [-0.108%; -0.062%]); P < P0 em 59/60.
- Referências sem reotimizar: H/P − 1 = +0.075% e G/P − 1 = +0.029% (medianas).
- Movimentos em vazio (mediana): S 43; P 34; corridas de S 42; violações de Π no nível de peça: 0.

## DEWIL16 (n = 60; t_av = 0)

- **S/P − 1** (segmento × peça, ambos reotimizados): mediana **-0.102%** (IC 95% [-0.424%; -0.022%]; mín. -7.98%, máx. +0.10%); S < P em **40/60**, S > P em 20.
- S/G − 1 (reotimizado × rota guardada ciente do reinício, avaliada na curva): mediana -0.213% (IC [-0.493%; -0.099%]); S ≤ G em 57/60.
- P/P0 − 1 (peça reotimizado × peça otimizado para tempo linear): mediana -0.264% (IC [-0.383%; -0.129%]); P < P0 em 60/60.
- Referências sem reotimizar: H/P − 1 = +0.106% e G/P − 1 = +0.090% (medianas).
- Movimentos em vazio (mediana): S 42; P 34; corridas de S 41; violações de Π no nível de peça: 0.

## Validação do nível de peça próprio (LIN)

Tempo LIN do nível de peça próprio × FO honesto guardado do pipeline do LCPP-1: |diferença| mediana 0.0113%, máx. 0.270%; dentro de 0,05% em 49/60.

## Predições (`docs/26`)

- H-R1 (DEWIL16: mediana de S/P − 1 em [−0,15%; +0,05%]): -0.102% → SUSTENTADA.
- H-R2 (LASER: mediana de S/P − 1 em [−0,15%; +0,05%]): -0.067% → SUSTENTADA.
- H-R3 (DEWIL16: S ≤ G em ≥ 75%): 95.0% → SUSTENTADA.
- H-R4 (descritiva; DEWIL16: nº médio de movimentos de S ≤ 40): 51.4 → fora.
- H-R5 (descritiva; validação do nível de peça): 49/60 dentro de 0,05% → fora.
- H-R6 (descritiva; DEWIL16: mediana de P/P0 − 1 ≤ 0): -0.264% (P < P0 em 60/60) → dentro.
