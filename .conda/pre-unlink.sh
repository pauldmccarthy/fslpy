if [ -e ${FSLDIR}/bin/requestFSLpythonUnlink.sh ]; then 
    $FSLDIR/bin/requestFSLpythonUnlink.sh ${PREFIX}/bin atlasquery atlasq imcp immv imglob
fi
