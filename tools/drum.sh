#!/bin/bash

NOTES="tinyNotation: 4/4 $1"

TMP=$(mktemp -d)
FROM=${TMP}/from.txt
TO=${TMP}/to.mid


echo "${NOTES}" > ${FROM}
./tinynotation.py ${FROM} ${TO}
timidity --quiet=2 -A140 -D 1  -T 100  ${TO}

rm -rf ${TMP}
