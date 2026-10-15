# E-A0 -- perfil qualidade x tempo (piloto: 11 instancias comparaveis de 12; referencia = PCGLNS a 30 s)

Gap medio (%) sobre a FO media do PCGLNS(30 s), no nivel de peca; (entre parenteses) tempo medio de parede por execucao em s, maquina compartilhada. PCGLNS inclui ~10-12 s de partida do Julia. Ver o docstring de `perfil_anytime_ea0.py`.

| metodo | T = 2 s | T = 5 s | T = 10 s | T = 30 s |
|---|---:|---:|---:|---:|
| PCGLNS | +0.12% (10.8 s; n=11) | +0.00% (12.3 s; n=11) | +0.00% (13.3 s; n=11) | +0.00% (14.5 s; n=11) |
| VNS-Pi (a partir do NearestFirst-Pi) | +0.12% (2.2 s; n=11) | +0.10% (5.2 s; n=11) | +0.08% (10.2 s; n=11) | +0.05% (30.2 s; n=11) |
| heuristica + VNS | +0.16% (2.5 s; n=11) | +0.12% (5.5 s; n=11) | +0.11% (10.5 s; n=11) | +0.09% (30.5 s; n=11) |

Metodos sem orcamento de tempo:

| metodo | gap medio | tempo medio (s) | #instancias |
|---|---:|---:|---:|
| heuristica (so construcao) | +0.74% | 0.7 | 11 |
| heuristica + busca local (descida) | +0.21% | 1.2 | 11 |
