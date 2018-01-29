if [ -z ${FSLDIR} ]; then exit; fi
if [ ! -d ${FSLDIR}/bin ]; then exit; fi
scripts="atlasquery imcp immv imglob"
for script in $scripts; do
    if [ -f ${FSLDIR}/bin/${script} ]; then rm ${FSLDIR}/bin/${script}; fi
    ln -s ${PREFIX}/bin/${script} ${FSLDIR}/bin/${script}
done

