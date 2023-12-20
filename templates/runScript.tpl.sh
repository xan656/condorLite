#!/bin/bash
if [[ -z "${_CONDOR_SCRATCH_DIR}" ]]; then
    _CONDOR_SCRATCH_DIR=`mktemp -d`
    echo _CONDOR_SCRATCH_DIR was not set, setting it to $_CONDOR_SCRATCH_DIR
else
    echo CONDOR_SCRATCH_DIR is $_CONDOR_SCRATCH_DIR
fi

set -x
export JOBDIR=@@DIRNAME
export DESTINATION=@@DESTINATION
echo $PWD
cd $_CONDOR_SCRATCH_DIR
mkdir workdir
chmod -R 777 workdir
cat >container_runScript.sh <<EOL
cd /code
source /cvmfs/cms.cern.ch/cmsset_default.sh
scram p CMSSW_7_6_7
cd CMSSW_7_6_7/src/
git clone -b 2015MiniAOD https://github.com/ats2008/PhysObjectExtractorTool.git
scram b -j 4
cmsenv
cd $_CONDOR_SCRATCH_DIR
cmsRun /code/CMSSW_7_6_7/src/PhysObjectExtractorTool/PhysObjectExtractor/python/poet_cfg.py  @@ISDATA inputFiles=@@FNAMES maxEvents=@@MAXEVENTS outputFile=outfile_@@IDX.root
pwd
ls
cp *.root $DESTINATION  
exit 1
EOL
cat container_runScript.sh
chmod +x container_runScript.sh
apptainer exec --writable-tmpfs --bind $_CONDOR_SCRATCH_DIR --bind workdir/:/code --bind @@DESTINATION docker://cmsopendata/cmssw_7_6_7-slc6_amd64_gcc493 ./container_runScript.sh
echo is Sucess $?
rm container_runScript.sh
pwd
ls
