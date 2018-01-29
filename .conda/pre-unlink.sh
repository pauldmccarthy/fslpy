if [ -z ${FSLDIR} ]; then exit; fi
scripts="atlasquery imcp immv imglob"
for script in $scripts; do
    if [ -f ${FSLDIR}/bin/${script} ]; then rm ${FSLDIR}/bin/${script}; fi
done
