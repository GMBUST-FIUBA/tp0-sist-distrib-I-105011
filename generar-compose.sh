#!/bin/bash
if [[ $2 -le 0 ]] ; then
    echo "ERROR: Cantidad de clientes no permitida"
    exit 1
else
    echo "Nombre del archivo de salida: $1"
    echo "Cantidad de clientes: $2"
    python3 ./compose-file-generator/compose_file_generator.py $1 $2
fi
exit 0
