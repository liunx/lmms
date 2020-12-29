#!/bin/bash

SRC=$1

RN=xxx.cbd
../coderband.py conv $SRC -o $RN

if [ "$2" == "1" ]; then
    ../coderband.py play $RN
fi
