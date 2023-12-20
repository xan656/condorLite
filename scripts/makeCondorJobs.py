#!/usr/bin/env python 
from __future__ import print_function
import os,glob
import copy,json
import argparse
import subprocess

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
parser.add_argument(     "--isData"     , help="is the job running over datafiles ?", action='store_true' )
parser.add_argument('-j',"--njobs", help="Number of jobs to make",default=-1,type=int)
parser.add_argument('-n',"--nFilesPerJob", help="Number of files to process per job",default=1,type=int)
parser.add_argument('-e',"--maxevents", help="Number of events per job",default=-1, type=int)
parser.add_argument('-f',"--flist", help="Files to process",default=None)
parser.add_argument(     "--recid", help="recid of the dataset to process",default=None)
parser.add_argument("--run_template", help="RunScript Template",default='')
parser.add_argument("--tag", help="Tag or vesion of the job",default='condor')

args = parser.parse_args()

job_hash=f'poetV1_{args.tag}'

if args.test :
    args.njobs=10
    maxevents=200

if args.submit or args.resubmit:
    choice=input("Do you really want to submit the jobs to condor pool ? ")
    if 'y' not in choice.lower():
        print("Exiting ! ")
        exit(0)

destination=f'{RESULT_BASE}/{JOB_TYPE}/{job_hash}/'

print(" Number of jobs to be made "        ,args.njobs)
print(" Number of events to process per job  "       ,args.maxevents)
print(" Tag for the job ", args.tag )
print(" Output files will be stored at ", destination )
if args.flist:
   print(" File list to process : ",args.flist)
elif args.recid:
   print(" recid to process : ",args.recid)
else:
   print("Please provide a file list or a recid")

templateCMD=""
allCondorSubFiles=[]


htag=job_hash

filelistName=''
fileList=[]

if args.flist:
    filelistName=args.flist
elif args.recid:	
    cmd=f'cernopendata-client get-file-locations --recid {args.recid} --protocol xrootd'
    print("querying database using cernopendata-client for the filelist ")
    print(f"   > []$ {cmd}")
    proc_out=subprocess.run([cmd], shell=True ,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if proc_out.returncode !=0:
        print(proc_out.stdout.decode('UTF-8'))
        print(proc_out.stderr.decode('UTF-8'))
        exit(proc_out.returncode )
    cmd=f'cernopendata-client get-metadata --recid {args.recid} --output-value title '
    print(f"   > []$ {cmd}")
    proc_out2=subprocess.run([cmd], shell=True ,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    filelistName=f'fileList_{args.recid}.fls'
    title=proc_out2.stdout.decode('UTF-8')[:-1]
    fls=proc_out.stdout.decode('UTF-8').splitlines()
    print(f"Obtained details for recid {args.recid} " )
    print(f" > Title : {title}")	 	
    print(f" > {len(fls)} files in filelist")	 	
    with open(filelistName,'w') as f:
        f.write(proc_out.stdout.decode('UTF-8'))
        print(f"Filelist has been exported to {filelistName}")
else:
    exit()    

with open(filelistName,'r') as f:
    txt=f.readlines()
    fileList=[l[:-1] for l in txt ]

runScriptTemplate = args.run_template
runScriptTxt=[]
with open(runScriptTemplate,'r') as f:
    runScriptTxt=f.readlines()
runScriptTxt=''.join(runScriptTxt)


head=pwd+f'/Condor/{JOB_TYPE}/{job_hash}/'
print()
print(f"Making Jobs in {runScriptTemplate} for files from {filelistName}")
jobid=0
while fileList and jobid < args.njobs: 
    jobid+=1
    flsToProcess=[]
    for i in range(args.nFilesPerJob):
        if not fileList:
            break
        flsToProcess.append(fileList.pop())

    fileNames=','.join(flsToProcess)
    dirName  =f'{head}/Job_{jobid}/'
    if not os.path.exists(dirName):
        os.system('mkdir -p '+dirName)
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
    tmp=tmp.replace("@@MAXEVENTS",str(args.maxevents))
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
    print(f"{jobid} Jobs made !\n\t submit file  : {condorScriptName}")
allCondorSubFiles.append(condorScriptName)

print("")
print("")
print("Condor Jobs can now be submitted by executing : ")
for fle in allCondorSubFiles:
    print('condor_submit '+fle)
    if args.submit or args.resubmit:
        os.system('condor_submit '+fle)
print("")
