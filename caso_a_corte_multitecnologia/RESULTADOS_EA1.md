# E-A1 nao trivial -- regret entre perfis com tempo de voo trapezoidal (84 instancias, PCGLNS T = 10 s, sementes por perfil: ate 3)

Perfis (ordem de grandeza de folhas tecnicas; k = 1 mm/unidade): LIN: v = 400 mm/s, sem aceleracao; LASER: v = 1667 mm/s, a = 10000 mm/s^2; PLASMA: v = 423 mm/s, a = 760 mm/s^2; PLASMA_A300: v = 423 mm/s, a = 300 mm/s^2. Regret(A -> B) = T_B(melhor rota para A) / T_B(melhor rota para B) - 1 (%), por instancia; mediana [mediana, % de instancias com regret > 0,1% / > 1%].

| rota otimizada para \ avaliada em | LIN | LASER | PLASMA | PLASMA_A300 |
|---|---:|---:|---:|---:|
| LIN | -- | +4.122% [100% / 99%] | +3.887% [100% / 100%] | +4.956% [100% / 100%] |
| LASER | +2.472% [98% / 88%] | -- | +0.000% [5% / 0%] | +0.003% [36% / 0%] |
| PLASMA | +2.258% [98% / 82%] | +0.000% [5% / 0%] | -- | +0.082% [46% / 1%] |
| PLASMA_A300 | +2.936% [99% / 96%] | +0.000% [29% / 1%] | +0.029% [40% / 2%] | -- |

Piso de ruido (variacao entre sementes no proprio perfil: mediana das sementes / melhor - 1): LIN: mediana 0.000%; LASER: mediana 0.000%; PLASMA: mediana 0.000%; PLASMA_A300: mediana 0.000%.

Maior regret observado: +12.07% (LIN -> PLASMA_A300).
Violacoes de Pi em todas as rotas: 0.
