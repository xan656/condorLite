#!/bin/bash

############################################### Environment Setup

if [[ -z "${_CONDOR_SCRATCH_DIR}" ]]; then
    _CONDOR_SCRATCH_DIR=`mktemp -d`
    echo _CONDOR_SCRATCH_DIR was not set, setting it to $_CONDOR_SCRATCH_DIR
else
    echo CONDOR_SCRATCH_DIR is $_CONDOR_SCRATCH_DIR
fi
cd $_CONDOR_SCRATCH_DIR
mkdir workdir
chmod -R 777 workdir
cp -r /home/z/cmssw/* workdir/
############################################### Creates the container_runScript.sh

cat >container_runScript.sh <<EOL
set  -e
cd /code
echo "Setting up \${CMSSW_VERSION}"
source \${CMS_INSTALL_DIR}/cmsset_default.sh
scramv1 project CMSSW \${CMSSW_VERSION}
cd \${CMSSW_VERSION}/src
eval \`scramv1 runtime -sh\`
echo "CMSSW should now be available."
echo "This is a standalone image for \${CMSSW_VERSION} \${SCRAM_ARCH}."
export LD_LIBRARY_PATH=\${UPDATE_PATH}/lib:\${UPDATE_PATH}/lib64:\${LD_LIBRARY_PATH}
export PATH=\${UPDATE_PATH}/bin:\${PATH}
export GIT_EXEC_PATH=\${UPDATE_PATH}/libexec/git-core
## -- ##

cd $_CONDOR_SCRATCH_DIR
cmsRun /code/CMSSW_7_6_7/src/JetAlgo/Analysis/test/new_runAnalysis_cfg.py inputFile=@@INFNAME outName=@@OUTFNAME isMC=@@ISMC maxEvts=@@MAXEVENTS globalTag=@@GLOBALTAG
EOL

################################################# Run the container script
echo \n"cmsRun /code/CMSSW_7_6_7/src/JetAlgo/Analysis/test/new_runAnalysis_cfg.py inputFile=@@INFNAME outName=@@OUTFNAME isMC=@@ISMC maxEvts=@@MAXEVENTS globalTag=@@GLOBALTAG"\n
chmod +x container_runScript.sh

apptainer exec --writable-tmpfs --bind $_CONDOR_SCRATCH_DIR --bind workdir/:/code --bind @@DESTINATION /home/z/jetalgo.sif  ./container_runScript.sh
echo exit code from the execution in container : $?
cp *.root @@DESTINATION
rm -rf workdir
