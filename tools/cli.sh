#!/bin/bash

CLI=$(basename $0)
DIR=$(dirname $0)

PRJ=${DIR}/projects/proj

WAV=${PRJ}.wav
MMP=${PRJ}.mmp
JSON=${PRJ}.json
MAIN=${DIR}/main.py

LMMS=${HOME}/Work/apps/lmms-1.2.2-linux-x86_64.AppImage 

if [ "${CLI}" == "play" ] ; then
    play ${WAV}
fi

if [ "${CLI}" == "build" ] ; then
    cd ${DIR}
    ${MAIN} ${JSON}
    ${LMMS} -l -f wav -r ${MMP} -o ${WAV} >> /tmp/log.txt
    play ${WAV}
fi

