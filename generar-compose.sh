#!/bin/bash

MAX_ARGS=2

if [[ $# -ne $MAX_ARGS ]] ; then
    echo "ERROR: Mala invocación"
    exit 1
elif [[ $2 -lt 0 ]] ; then
    echo "ERROR: Cantidad de clientes no permitida"
    exit 1
else
    echo "Nombre del archivo de salida: $1"
    echo "Cantidad de clientes: $2"
    python3 ./compose-file-generator/compose_file_generator.py $1 $2
fi
exit 0
