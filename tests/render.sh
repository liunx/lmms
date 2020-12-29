#!/bin/bash

RN=rendered.cbd

python3 ../render.py $RN

if [ "$1" == "1" ]; then
    ../coderband.py play $RN
fi
