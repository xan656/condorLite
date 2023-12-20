#!/usr/bin/env python 
from __future__ import print_function
import os,glob
import copy,json
import argparse

condorScriptString="\
executable = $(filename)\n\
output = $Fp(filename)run.$(Cluster).stdout\n\
error = $Fp(filename)run.$(Cluster).stderr\n\
log = $Fp(filename)run.$(Cluster).log\n\
+JobFlavour = \"longlunch\"\n\
"
pwd=os.environ['PWD']
HOME=os.environ['HOME']

maxMeterialize=100
RESULT_BASE=f'{pwd}/results'
JOB_TYPE='odw_poet'

parser = argparse.ArgumentParser()
parser.add_argument('-s',"--submit", help="Submit file to condor pool", action='store_true' )
parser.add_argument('-r',"--resubmit", help="Re-Submit file to condor pool", action='store_true' )
parser.add_argument('-t',"--test", help="Test Job", action='store_true' )
parser.add_argument('-p',"--printOnly", help="Only Print the commands", action='store_true' )
parser.add_argument(     "--isData"     , help="is the job running over datafiles ?", action='store_true' )
parser.add_argument('-j',"--njobs", help="Number of jobs to make",default='-6000')
parser.add_argument('-n',"--nFilesPerJob", help="Number of files to process per job",default=1,type=int)
parser.add_argument('-e',"--nevts", help="Number of events per job",default='-1')
parser.add_argument('-f',"--flist", help="Files to process",default=None)
parser.add_argument("--run_template", help="RunScript Template",default='')
parser.add_argument("--tag", help="Tag or vesion of the job",default='condor')

args = parser.parse_args()


njobs=int(args.njobs)
maxevents=int(args.nevts)
max_meterialize=250
jobsToProcess=None
submit2Condor=args.submit
resubmit2Condor=args.resubmit
isTest=args.test
onlyPrint=args.printOnly
nfilesPerJob=args.nFilesPerJob
job_hash=f'poetV1_{args.tag}'

if isTest :
    njobs=10
    maxevents=5000


print(" submit jobs ",submit2Condor)
print(" resubmit jobs ",resubmit2Condor)
print(" isTest ",isTest)
print(" printOnly ",onlyPrint)
print(" njobs ",njobs)
print(" maxEvt ",maxevents)

if submit2Condor or resubmit2Condor:
    choice=input("Do you really want to submit the jobs to condor pool ? ")
    if 'y' not in choice.lower():
        print("Exiting ! ")
        exit(0)


templateCMD=""

allCondorSubFiles=[]


if True:
    htag=job_hash
    runScriptTemplate = args.run_template
    runScriptTxt=[]
    with open(runScriptTemplate,'r') as f:
        runScriptTxt=f.readlines()
    runScriptTxt=''.join(runScriptTxt)
    
    fileList=[]
    with open(args.flist,'r') as f:
        txt=f.readlines()
        fileList=[l[:-1] for l in txt ]

    head=pwd+f'/Condor/{JOB_TYPE}/{job_hash}/'
    print(f"Making Jobs in {runScriptTemplate} for files from {args.flist}")
    jobid=0
    while fileList and jobid < njobs: 
        jobid+=1
        flsToProcess=[]
        for i in range(nfilesPerJob):
            if not fileList:
                break
            flsToProcess.append(fileList.pop())

        fileNames=','.join(flsToProcess)
        dirName  =f'{head}/Job_{jobid}/'
        if not os.path.exists(dirName):
            os.system('mkdir -p '+dirName)
        destination=f'{RESULT_BASE}/{JOB_TYPE}/{job_hash}/'
        if not os.path.exists(destination):
            os.system('mkdir -p '+destination)
 
        runScriptName=dirName+f'/{htag}_{jobid}_run.sh'
        if os.path.exists(runScriptName+'.sucess'):
           os.system('rm '+runScriptName+'.sucess')
        runScript=open(runScriptName,'w')
        tmp=runScriptTxt.replace("@@DIRNAME",dirName)
        tmp=tmp.replace("@@TAG",str(args.tag))
        tmp=tmp.replace("@@ISDATA",str(args.isData))
        tmp=tmp.replace("@@PWD",pwd)
        tmp=tmp.replace("@@IDX",str(jobid))
        tmp=tmp.replace("@@FNAMES",fileNames)
        tmp=tmp.replace("@@MAXEVENTS",str(maxevents))
        tmp=tmp.replace("@@RUNSCRIPT",runScriptName)
        tmp=tmp.replace("@@DESTINATION",destination)
        runScript.write(tmp)
        runScript.close()
        os.system('chmod +x '+runScriptName)
    

    print()
    condorScriptName=head+'/job'+htag+'.sub'
    with open(condorScriptName,'w') as condorScript:
        condorScript.write(condorScriptString)
        condorScript.write("queue filename matching ("+head+"/*/*.sh)\n")
        print(f"Condor {jobid} Jobs made !\n\t submit file  : {condorScriptName}")
    allCondorSubFiles.append(condorScriptName)

print("")
print("")
print("Condor Jobs can now be submitted by executing : ")
for fle in allCondorSubFiles:
    print('condor_submit '+fle)
    if submit2Condor or resubmit2Condor:
        os.system('condor_submit '+fle)
print("")
