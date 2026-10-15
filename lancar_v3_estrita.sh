#!/usr/bin/env bash
# lancar_v3_estrita.sh -- V3 (docs/19) e depois a sensibilidade estrita x fechamento (docs/21), em sequencia, com pre-voo (maquina ociosa? na tomada?) e manifesto.
# Uso (na raiz do projeto):  bash lancar_v3_estrita.sh [--forcar]
# Pede para: deixar o notebook NA TOMADA e sem outros trabalhos pesados (~5-8 h no total). Idempotente: pula o que ja tem JSON; pode ser interrompido e relancado.
set -u
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8
export EZDXF_DISABLE_C_EXT=1
python caso_a_corte_multitecnologia/preparar_v3.py "$@" || exit 1
cd caso_a_corte_multitecnologia
nohup sh -c "python -u rodar_v3.py rodar --workers 3 --ts 0.25,1.0 --rodadas 2 > v3_completo.log 2>&1; python -u rodar_estrita.py rodar --workers 3 --ts 0,1 --rodadas 2 > estrita_completo.log 2>&1" > /dev/null 2>&1 &
echo "V3 + estrita lancados (PID $!); acompanhe com: tail -f caso_a_corte_multitecnologia/v3_completo.log  (depois estrita_completo.log)"
