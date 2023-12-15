# condorLite
A lightweight setup to scale your analysis using Condor.

Documentation is aligned towards analysis targeting [Opendata](http://opendata.cern.ch/) releases from CERN.

* current setup assumes a cluster like environment with a common filesysem mount for the condor worker nodes.

## Setup the working environment.
Following tutorials familiarizes one to containers and tools for analyzing opendata releases from [cms](https://cms.cern).
* [Docker Pre-Exercises](https://cms-opendata-workshop.github.io/workshop2023-lesson-docker/)
* [POET Pre-Exercises](https://cms-opendata-workshop.github.io/workshop2023-lesson-physics-objects/01-intro-poet/index.html)

For `singularity` / `apptainer` user following  commands will be useful.
* Spawn a shell in the container.
```
apptainer shell --bind /grid_mnt/t3home/athachay/opendata_wshop/soft_dev:/code docker://cmsopendata/cmssw_7_6_7-slc6_amd64_gcc493
```
* pull the docker container into a local `sif` file. This file can be later used to make container rather than pulling the container all the time.
```
apptainer pull cmssw_7_6_7-slc6_amd64_gcc493.sif docker://cmsopendata/cmssw_7_6_7-slc6_amd64_gcc493
```
* run a script inside the container 
```
echo "Hello ! I am indside container ! " > runMe.sh
echo "ls " >> runMe.sh
chmod +x runMe.sh

apptainer exec  docker://cmsopendata/cmssw_7_6_7-slc6_amd64_gcc493 ./runMe.sh
```
* setup the default cms enviroment on a writeable directory mount
```
mkdir soft_dev
chmod -R 777 soft_dev
apptainer run --bind soft_dev:/code docker://cmsopendata/cmssw_7_6_7-slc6_amd64_gcc493 /bin/bash
```
    - currently this step fails to launch the container interactively and drop a shell in the container environment
    - This command but succeeds in setting up the proper environment / cmssw files
* clone the `POET` repo in the target destination (This is a workaround for the issue of having `git clone` not running inside the container ).
```
cd soft_dev/CMSSW_7_6_7/src/
git clone -b 2015MiniAOD https://github.com/cms-opendata-analyses/PhysObjectExtractorTool.git
```
Now one can drop into the container shell to develop and compile the code.

## Scaling up your Analysis.
First step in running your code over the dataset is to make a self-contained shell script  that can run your workflow. Here we provide an example script. ( _test.sh_ )
```
cd soft_dev/CMSSW_7_6_7/src/
source /cvmfs/cms.cern.ch/cmsset_default.sh
cmsenv
cmsRun PhysObjectExtractorTool/PhysObjectExtractor/python/poet_cfg.py
mv *.root /results
exit
```
Try the script inside your container.
```
apptainer exec --bind soft_dev/:/code --bind results:/results docker://cmsopendata/cmssw_7_6_7-slc6_amd64_gcc493 ./test.sh
```
To scale the analysis to multiple files , we can use `condor/makeCondorJobs.py`. This script is driven by 2 files a `filelist` file and a `run_template` file. 
 - The `flelist` has a list of files over which the analysis need to be ran. 
 - The `run_template` file is a standalone customizable script that can can execute our analysis workflow.This  file  can have placeholders that  can be customized by `condor/makeCondorJobs.py` script ( eg. with filename, number events to process, or any other parameters that we would like to pass on to the script). 

A sample `filelist` and `run_template` file can be found as `filelists/DYJetsToLL_13TeV_MINIAODSIM.fls` and `templates/runScript.tpl.sh`

For making a set of analysis jobs run 
```
python3 scripts/makeCondorJobs.py  -f filelists/DYJetsToLL_13TeV_MINIAODSIM.fls --run_template templates/runScript.tpl.sh  -v v1 -j 5 -e 2000
```
see `python3 scripts/makeCondorJobs.py -h` for more details

#### TODOs
* Add support for a sample analysis.C / analysis.py  and its outputs. 
* update instructions for getting the file-list. 
* update setup for completely detached file system in condor worker nodes. 
