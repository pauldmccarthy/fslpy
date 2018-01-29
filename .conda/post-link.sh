if [ -z ${FSLDIR} ]; then exit; fi
if [ ! -d ${FSLDIR}/bin ]; then exit; fi
scripts="atlasquery imcp immv imglob"
for script in $scripts; do
    if [ -f ${FSLDIR}/bin/${file} ]; then rm ${FSLDIR}/bin/${file}; fi
    ln -s ${PREFIX}/bin/${file} ${FSLDIR}/bin/${file}
done

