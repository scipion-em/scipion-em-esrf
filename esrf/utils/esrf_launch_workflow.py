#!/usr/bin/env python
# **************************************************************************
# *
# * Authors:     Olof Svensson (svensson@esrf.fr)
# *
# * European Synchrotron Radiation Facility
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

import os
import sys
import glob
import time
import getopt
import datetime
import tempfile
from pyworkflow.manager import Manager
import pyworkflow.utils as pwutils
from pyworkflow.protocol import getProtocolFromDb
from esrf_utils_ispyb import UtilsISPyB
from esrf_utils_path import UtilsPath


def getUpdatedProtocol(protocol):
    """ Retrieve the updated protocol and close db connections
        """
    prot2 = getProtocolFromDb(os.getcwd(),
                              protocol.getDbPath(),
                              protocol.getObjId())
    # Close DB connections
    prot2.getProject().closeMapper()
    prot2.closeMappers()
    return prot2


# Parse command line
usage = "\nUsage: cryoemProcess --directory <dir> [--filesPattern <filesPattern>] [--scipionProjectName <name>] --protein <name> --sample <name> --doseInitial <dose> --dosePerFrame <dose> [--samplingRate <samplingRate>] [--startMotioncorFrame startFrame] [--endMotioncorFrame endFrame]\n"    

try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["directory=", "filesPattern=", "scipionProjectName=", "protein=", "sample=", "doseInitial=", "dosePerFrame=", "samplingRate=", "startMotioncorFrame=", "endMotioncorFrame=", "help"])
except getopt.GetoptError:
    print(usage)
    sys.exit(1)

if len(args) != 0:
    print(usage)
    sys.exit(1)

dataDirectory = None
filesPattern = None
scipionProjectName = None
proteinAcronym = None
sampleAcronym = None
doseInitial = 0.0
dosePerFrame = None
samplingRate = None
dataStreaming = "true"
alignFrame0 = 1
alignFrameN = 0


for opt, arg in opts:
    if opt in ["-h", "--help"]:
        print(usage)
        sys.exit()
    elif opt in ["--directory"]:
        dataDirectory = arg
    elif opt in ["--filesPattern"]:
        filesPattern = arg
    elif opt in ["--scipionProjectName"]:
        scipionProjectName = arg
    elif opt in ["--protein"]:
        proteinAcronym = arg
    elif opt in ["--sample"]:
        sampleAcronym = arg
    elif opt in ["--doseInitial"]:
        doseInitial = float(arg)
    elif opt in ["--dosePerFrame"]:
        dosePerFrame = float(arg)
    elif opt in ["--samplingRate"]:
        samplingRate = float(arg)
    elif opt in ["--startMotioncorFrame"]:
        alignFrame0 = float(arg)
    elif opt in ["--endMotioncorFrame"]:
        alignFrameN = float(arg)

# Check mandatory parameters
if not all([dataDirectory, proteinAcronym, sampleAcronym, dosePerFrame]):
    print(usage)
    sys.exit(1)
    
if filesPattern is None:
    filesPattern = "Images-Disc1/GridSquare_*/Data/FoilHole_*-*.mrc"

print("Data directory: {0}".format(dataDirectory))
print("filesPattern: {0}".format(filesPattern))
print("Protein acronym: {0}".format(proteinAcronym))
print("Sample acronym: {0}".format(sampleAcronym))
print("Dose initial: {0}".format(doseInitial))
print("Dose per frame: {0}".format(dosePerFrame))

# Check how many movies are present on disk
listMovies = glob.glob(os.path.join(dataDirectory, filesPattern))
noMovies = len(listMovies)
if noMovies == 0:
    print("ERROR! No movies available in directory {0} with the filesPattern {1}.".format(dataDirectory, filesPattern))
    sys.exit(1)
else:
    print("Number of movies available on disk: {0}".format(noMovies))
    
# Set up location
if "RAW_DATA" in dataDirectory:
    location = dataDirectory.replace("RAW_DATA", "PROCESSED_DATA")
#elif "cm01/inhouse" in dataDirectory:
#    location = "/users/opcm01/PROCESSED_DATA"
else:
    location = tempfile.mkdtemp(prefix="ScipionUserData_")

dateTime = time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time()))

if scipionProjectName is None:
    if "*" in filesPattern or "?" in filesPattern:
        scipionProjectName = "{0}_{1}".format(os.path.basename(dataDirectory), dateTime)
    else:
        # Use movie file name as project name
        scipionProjectName = "{0}_{1}".format(os.path.splitext(filesPattern)[0], dateTime)
        dataStreaming = "false"

if not os.path.exists(location):
    os.makedirs(location, 0755)
else:
    os.chmod(location, 0755)
        
# All param json file
allParamsJsonFile = os.path.join(location, "allParams.json")

print("Scipion project name: {0}".format(scipionProjectName))
print("Scipion user data location: {0}".format(location))
print("All param json file: {0}".format(allParamsJsonFile))

# Get meta data like phasePlateUsed

doPhaseShiftEstimation = "false"

firstMovieFullPath = listMovies[0]
print("First movie full path file: {0}".format(firstMovieFullPath))

# Check proposal
# db=0: production
# db=1: valid
# db=2: lindemaria
# db=3: localhost
proposal = UtilsISPyB.getProposal(firstMovieFullPath)
if proposal is None:
    print("WARNING! No valid proposal could be found for movie {0}.".format(firstMovieFullPath))
    print("")
    answer = raw_input("Would you like to enter a valid proposal name now (yes/no)? ")
    while answer != "yes" and answer !="no":
        print("")
        answer = raw_input("Please answer 'yes' or 'no'. Would you like to enter a valid proposal name now? ")
    if answer == "yes":
        proposal = raw_input("Please enter a valid proposal name: ")
        code, number = UtilsISPyB.splitProposalInCodeAndNumber(proposal)
        while code is None:
            print("'{0}' is not a valid proposal name.".format(proposal))
            print("")
            proposal = raw_input("Please enter a valid proposal name (mxXXXX, ih-lsXXXX etc): ")
            code, number = UtilsISPyB.splitProposalInCodeAndNumber(proposal)
    else:
        proposal = None

if proposal is None:
    print("WARNING! No data will be uploaded to ISPyB.")
    db = 3
else:
    print("Proposal: {0}".format(proposal))
    if proposal == "mx415":
        # Use valid data base
        print("ISPyB valid data base used")
        db = 1
    else:
        # Use productiond data base
        print("ISPyB production data base used")
        db = 0

jpeg, mrc, xml, gridSquareThumbNail =  UtilsPath.getMovieJpegMrcXml(firstMovieFullPath)

print("Metadata file: {0}".format(xml))


dictResults = UtilsPath.getXmlMetaData(xml)
doPhaseShiftEstimation = dictResults["phasePlateUsed"]
nominalMagnification = int(dictResults["nominalMagnification"])
superResolutionFactor = int(dictResults["superResolutionFactor"])

if samplingRate is None:
    samplingRate = 1.1 / float(superResolutionFactor)

print("doPhaseShiftEstimation: {0}".format(doPhaseShiftEstimation))
print("nominalMagnification: {0}".format(nominalMagnification))
print("superResolutionFactor: {0}".format(superResolutionFactor))
print("samplingRate: {0}".format(samplingRate))
print("dataStreaming: {0}".format(dataStreaming))

# Create json file

jsonString = """[
    {
        "object.className": "ProtImportMovies",
        "object.id": "2",
        "object.label": "scipion - import movies",
        "object.comment": "",
        "runName": null,
        "runMode": 0,
        "importFrom": 0,
        "filesPath": "%s",
        "filesPattern": "%s",
        "copyFiles": false,
        "haveDataBeenPhaseFlipped": false,
        "acquisitionWizard": null,
        "voltage": 300.0,
        "sphericalAberration": 2.7,
        "amplitudeContrast": 0.1,
        "magnification": %d,
        "samplingRateMode": 0,
        "samplingRate": %f,
        "scannedPixelSize": 5.0,
        "doseInitial": %f,
        "dosePerFrame": %f,
        "gainFile": null,
        "darkFile": null,
        "dataStreaming": %s,
        "timeout": 86400,
        "fileTimeout": 30,
        "inputIndividualFrames": false,
        "numberOfIndividualFrames": null,
        "stackFrames": false,
        "writeMoviesInProject": false,
        "movieSuffix": "_frames.mrcs",
        "deleteFrames": false,
        "streamingSocket": false,
        "socketPort": 5000
    },
    {
        "object.className": "ProtMotionCorr",
        "object.id": "77",
        "object.label": "motioncorr - motioncorr alignment",
        "object.comment": "",
        "runName": null,
        "runMode": 0,
        "gpuMsg": "True",
        "GPUIDs": "[0,1]",
        "alignFrame0": %d,
        "alignFrameN": %d,
        "useAlignToSum": true,
        "sumFrame0": 1,
        "sumFrameN": 0,
        "binFactor": 1.0,
        "cropOffsetX": 0,
        "cropOffsetY": 0,
        "cropDimX": 0,
        "cropDimY": 0,
        "doSaveAveMic": true,
        "doSaveMovie": false,
        "doComputePSD": false,
        "doComputeMicThumbnail": true,
        "computeAllFramesAvg": false,
        "extraParams": "",
        "useMotioncor2": true,
        "doApplyDoseFilter": true,
        "patchX": 5,
        "patchY": 5,
        "group": 1,
        "tol": 0.5,
        "doMagCor": false,
        "useEst": true,
        "scaleMaj": 1.0,
        "scaleMin": 1.0,
        "angDist": 0.0,
        "extraParams2": "",
        "doSaveUnweightedMic": true,
        "hostName": "localhost",
        "numberOfThreads": 1,
        "numberOfMpi": 1,
        "inputMovies": "2.outputMovies"
    },
    {
        "object.className": "ProtGctf",
        "object.id": "195",
        "object.label": "gctf - CTF estimation on GPU",
        "object.comment": "",
        "runName": null,
        "runMode": 0,
        "recalculate": false,
        "sqliteFile": null,
        "ctfDownFactor": 1.0,
        "lowRes": 0.05,
        "highRes": 0.35,
        "minDefocus": 0.25,
        "maxDefocus": 4.0,
        "astigmatism": 100.0,
        "windowSize": 512,
        "plotResRing": true,
        "GPUCore": 0,
        "doEPA": true,
        "EPAsmp": 4,
        "doBasicRotave": false,
        "bfactor": 150,
        "overlap": 0.5,
        "convsize": 85,
        "doHighRes": true,
        "HighResL": 30.0,
        "HighResH": 5.0,
        "HighResBf": 50,
        "doValidate": false,
        "doPhShEst": %s,
        "phaseShiftL": 0.0,
        "phaseShiftH": 180.0,
        "phaseShiftS": 10.0,
        "phaseShiftT": 0,
        "inputMicrographs": "77.outputMicrographs"
    },
    {
        "object.className": "ProtMonitorISPyB_ESRF",
        "object.id": "259",
        "object.label": "ispyb - monitor to ISPyB at the ESRF",
        "object.comment": "",
        "runName": null,
        "runMode": 0,
        "inputProtocols": ["2", "77", "195"],
        "samplingInterval": 10,
        "proposal": "%s",
        "proteinAcronym": "%s",
        "sampleAcronym": "%s",
        "db": %d,
        "allParamsJsonFile": "%s",
        "samplingRate": "%s",
        "doseInitial": "%s",
        "dosePerFrame": "%s"
    }
]""" % (dataDirectory, filesPattern, nominalMagnification, samplingRate,
        doseInitial, dosePerFrame, dataStreaming, alignFrame0, alignFrameN,  
        doPhaseShiftEstimation, proposal,
        proteinAcronym, sampleAcronym, db, allParamsJsonFile,
        samplingRate, doseInitial, dosePerFrame)

# Write json file
fd, jsonFile = tempfile.mkstemp(suffix=".json", prefix="scipion_workflow_", dir=location)
os.write(fd, jsonString)
os.close(fd)
os.chmod(jsonFile, 0644)
print("Scipion project json fFile: {0}".format(jsonFile))


# Create a new project
manager = Manager()

def getNewScipionProjectName(scipionProjectName, index):
    return "{0}_{1}".format(scipionProjectName, index)

if manager.hasProject(scipionProjectName):
    print("WARNING! There is already a Scipion project with this name: '{0}'".format(scipionProjectName))
    # Try to find an unique project name
    index = 1
    newScipionProjectName = getNewScipionProjectName(scipionProjectName, index)
    while manager.hasProject(newScipionProjectName):
        index += 1
        newScipionProjectName = getNewScipionProjectName(scipionProjectName, index)
    scipionProjectName = newScipionProjectName
    print("New Scipion project name: '{0}'".format(scipionProjectName))

project = manager.createProject(scipionProjectName, location=location)

if jsonFile is not None:
    protDict = project.loadProtocols(jsonFile)
    
# Start the project
runs = project.getRuns()

# Now assuming that there is no dependencies between runs
# and the graph is lineal
for prot in runs:
    project.scheduleProtocol(prot)


# Monitor the execution:
doContinue = True
while doContinue:
    doContinue = False
    updatedRuns = [getUpdatedProtocol(p) for p in runs]
    print("") 
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')) 
    for prot in updatedRuns:
        print("{0} status: {1}".format(prot.getRunName(), prot.getStatusMessage()))
        if prot.isActive():
            doContinue = True
    time.sleep(5)
        
    