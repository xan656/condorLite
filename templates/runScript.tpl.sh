#!/bin/bash
if [[ -z "${_CONDOR_SCRATCH_DIR}" ]]; then
    _CONDOR_SCRATCH_DIR=`mktemp -d`
    echo _CONDOR_SCRATCH_DIR was not set, setting it to $_CONDOR_SCRATCH_DIR
else
    echo CONDOR_SCRATCH_DIR is $_CONDOR_SCRATCH_DIR
fi
cd $_CONDOR_SCRATCH_DIR
mkdir workdir
chmod -R 777 workdir
cat >container_runScript.sh <<EOL
## -- ## from /opt/cms/entrypoint.sh 
set  -e
cd /code
echo "Setting up \${CMSSW_VERSION}"
source \${CMS_INSTALL_DIR}/cmsset_default.sh
scramv1 project CMSSW \${CMSSW_VERSION}
cd \${CMSSW_VERSION}/src
eval \`scramv1 runtime -sh\`
echo "CMSSW should now be available."
echo "This is a standalone image for ${CMSSW_VERSION} ${SCRAM_ARCH}."
export LD_LIBRARY_PATH=\${UPDATE_PATH}/lib:\${UPDATE_PATH}/lib64:\${LD_LIBRARY_PATH}
export PATH=\${UPDATE_PATH}/bin:\${PATH}
export GIT_EXEC_PATH=\${UPDATE_PATH}/libexec/git-core
## -- ##

git clone -b 2015MiniAOD https://github.com/cms-opendata-analyses/PhysObjectExtractorTool.git
scram b -j 4
cd $_CONDOR_SCRATCH_DIR
cmsRun /code/CMSSW_7_6_7/src/PhysObjectExtractorTool/PhysObjectExtractor/python/poet_cfg.py  @@ISDATA inputFiles=@@FNAMES maxEvents=@@MAXEVENTS outputFile=outfile_@@IDX.root tag=@@TAG
cp *.root @@DESTINATION  
EOL
cat container_runScript.sh
chmod +x container_runScript.sh
apptainer exec --writable-tmpfs --bind $_CONDOR_SCRATCH_DIR --bind workdir/:/code --bind @@DESTINATION docker://cmsopendata/cmssw_7_6_7-slc6_amd64_gcc493 ./container_runScript.sh
echo exit code from the execution in container : $?
rm container_runScript.sh
