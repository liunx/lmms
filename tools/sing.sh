#!/bin/bash

TEMPO=90
VOL=140


NOTES="tinyNotation: 4/4 $1"

TMP=$(mktemp -d)
FROM=${TMP}/from.txt
TO=${TMP}/to.mid
C=0
P=1

echo "${NOTES}" >${FROM}
./tinynotation.py ${FROM} ${TO}
timidity --quiet=2 -A${VOL} -T ${TEMPO} -K ${C} -Ei${P} ${TO}

rm -rf ${TMP}
