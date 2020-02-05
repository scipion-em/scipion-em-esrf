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
import shutil
import argparse
import datetime
import tempfile
from pyworkflow.project.manager import Manager
from pyworkflow.protocol import getProtocolFromDb

from esrf.utils.esrf_utils_ispyb import UtilsISPyB
from esrf.utils.esrf_utils_path import UtilsPath
from esrf.utils.esrf_utils_serialem import UtilsSerialEM

# if not 'SCIPION_ESRF_CONFIG' in os.environ:
#     # Set up config for DB and ISPyB
#     modulePath = os.path.dirname(__file__)
#     installPath = os.path.dirname(modulePath)
#     configPath = os.path.join(installPath, 'config', 'esrf.properties')
#     if not os.path.exists(configPath):
#         raise RuntimeError(
#             'No configuration file found at {0}!'.format(configPath)
#         )
#     print(configPath)
#     os.environ['SCIPION_ESRF_CONFIG'] = configPath


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


# usage = "\nUsage: cryoemProcess --directory <dir> " + \
#         "[--filesPattern <filesPattern>]  " + \
#         "[--scipionProjectName <name>]  " + \
#         "--protein <name>  " + \
#         "--sample <name>  " + \
#         "--doseInitial <dose>  " + \
#         "--dosePerFrame <dose>  " + \
#         "[--samplingRate <samplingRate>]  " + \
#         "[--startMotioncorFrame startFrame]  " + \
#         "[--endMotioncorFrame endFrame]" + \
#         "[--phasePlateData]" + \
#         "[--onlyISPyB]" + \
#         "\n"

parser = argparse.ArgumentParser(
    description="Application for starting Scipion workflow for CM01")
parser._action_groups.pop()
required = parser.add_argument_group('required arguments')
optional = parser.add_argument_group('optional arguments')
required.add_argument(
    "--directory",
    action="store",
    help="top EM directory",
    required=True
)
required.add_argument(
    "--protein",
    action="store",
    help="Protein acronym, must be the one used in the A-form.",
    required=True
)
required.add_argument(
    "--sample",
    action="store",
    help="Sample name, for example 'grid1'.",
    required=True
)
required.add_argument(
    "--dosePerFrame",
    action="store",
    help="Dose per frame.",
    required=True
)
optional.add_argument(
    "--samplingRate",
    action="store",
    help="Sampling rate.",
    default=None,
    required=True
)
optional.add_argument(
    "--filesPattern",
    action="store",
    help="file pattern for finding EM movies, default pattern " +
         "'Images-Disc1/GridSquare_*/Data/FoilHole_*-*.mrc'",
    default=None
)
optional.add_argument(
    "--scipionProjectName",
    action="store",
    help="Scipion project name, is only used internally in Scipion."
)
optional.add_argument(
    "--doseInitial",
    action="store",
    help="Initial dose, default zero.",
    default=0.0
)
optional.add_argument(
    "--startMotioncorFrame",
    action="store",
    help="Start frame for motion correction, default 1.",
    default=1
)
optional.add_argument(
    "--endMotioncorFrame",
    action="store",
    help="End frame for motion correction, default last frame.",
    default=0
)
optional.add_argument(
    "--superResolution",
    action="store_true",
    help="Super resolution used, default 'False'.",
    default=False
)
optional.add_argument(
    "--magnification",
    action="store",
    help="Nominal magnification.",
    default=None
)
optional.add_argument(
    "--imagesCount",
    action="store",
    help="Number of images per movie.",
    default=None
)
optional.add_argument(
    "--voltage",
    action="store",
    help="Voltage [V]",
    default=None
)
optional.add_argument(
    "--phasePlateData",
    action="store_true",
    help="Phase plate used, default 'False'.",
    default=False
)
optional.add_argument(
    "--onlyISPyB",
    action="store_true",
    help="Only upload data to ISPyB i.e. no processing, default 'False'.",
    default=False
)
optional.add_argument(
    "--defectMapPath",
    action="store",
    help="Defect map file path",
    default=None
)
optional.add_argument(
    "--gainFilePath",
    action="store",
    help="Gain file path",
    default=None
)
optional.add_argument(
    "--noISPyB",
    action="store_true",
    help="Don't upload to ISPyB or iCAT, default 'False'.",
    default=False
)
results = parser.parse_args()

dataDirectory = results.directory
filesPattern = results.filesPattern
scipionProjectName = results.scipionProjectName
proteinAcronym = results.protein
sampleAcronym = results.sample
doseInitial = float(results.doseInitial)
dosePerFrame = float(results.dosePerFrame)
dataStreaming = "true"
alignFrame0 = int(results.startMotioncorFrame)
alignFrameN = int(results.endMotioncorFrame)
phasePlateData = results.phasePlateData
onlyISPyB = results.onlyISPyB
samplingRate = float(results.samplingRate)
superResolution = results.superResolution
defectMapPath = results.defectMapPath
gainFilePath = results.gainFilePath
noISPyB = results.noISPyB
nominalMagnification = int(results.magnification) if results.magnification is not None else None
imagesCount = int(results.imagesCount) if results.imagesCount is not None else None
voltage = int(results.voltage) if results.voltage is not None else None

################################################################################
#
# First find out if we use serial em or not:
#

if filesPattern is None:
    # No filesPattern, let's assume that we are dealing with EPU data
    filesPattern = "Images-Disc1/GridSquare_*/Data/FoilHole_*-*.mrc"
    # Check how many movies are present on disk
    listMovies = glob.glob(os.path.join(dataDirectory, filesPattern))
    noMovies = len(listMovies)
    if noMovies > 0:
        # We have EPU data
        serialEM = False
        print("********** EPU data **********")
    else:
        # So, no mrc movies found, let's try to find some serialEM files:
        # Look for first tif, defect file and dm4 file
        tifDir, firstTifFileName, defectFilePath, dm4FilePath = \
            UtilsPath.findSerialEMFilePaths(dataDirectory)
        if tifDir is not None:
            # We have serial EM data
            filesPattern = UtilsPath.serialEMFilesPattern(dataDirectory, tifDir)
            listMovies = glob.glob(os.path.join(dataDirectory, filesPattern))
            noMovies = len(listMovies)
            if noMovies > 0:
                # We have EPU data
                serialEM = True
                print("********** SerialEM data **********")

if noMovies == 0:
    print("ERROR! No movies available in directory {0} with the filesPattern {1}.".format(dataDirectory, filesPattern))
    sys.exit(1)

print("Number of movies available on disk: {0}".format(noMovies))
firstMovieFullPath = listMovies[0]
print("First movie full path file: {0}".format(firstMovieFullPath))

if serialEM:
    if defectFilePath is None:
        print("ERROR - No defect file path found in directory {0}!".format(tifDir))
        sys.exit(1)
    if dm4FilePath is None:
        print("ERROR - No dm4 file path found in directory {0}!".format(tifDir))
        sys.exit(1)
    # Create directory for holding defect map and gain reference image
    defectGainDir = os.path.join(dataDirectory, "Defect_and_Gain_images")
    if os.path.exists(defectGainDir):
        # Directory exists - we remove it
        print("Removing existing defect and gain maps")
        shutil.rmtree(defectGainDir)
    os.makedirs(defectGainDir, 0o755)
    defectMapPath = UtilsSerialEM.createDefectMapFile(
        defectFilePath, firstMovieFullPath, defectGainDir)
    gainFilePath = UtilsSerialEM.createGainFile(dm4FilePath, defectGainDir)
    extraParams2 = "-Gain {0} -DefectMap {1}".format(
        gainFilePath, defectMapPath
    )
else:
    if defectMapPath is not None or gainFilePath is not None:
        if not os.path.exists(defectMapPath):
            print("ERROR! Cannot find defect map file {0}".format(defectMapPath))
            sys.exit(1)
        elif not os.path.exists(gainFilePath):
            print("ERROR! Cannot find gain file {0}".format(gainFilePath))
            sys.exit(1)
        else:
            extraParams2 = "-Gain {0} -DefectMap {1}".format(
                gainFilePath, defectMapPath
            )
    else:
        extraParams2 = ""



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

try:
    if not os.path.exists(location):
        os.makedirs(location, 0o755)
    else:
        os.chmod(location, 0o755)
except OSError as e:
    print("ERROR! Cannot write into {0}".format(location))
    print("Error message: {0}".format(e))
    location = tempfile.mkdtemp(prefix=scipionProjectName)
    print("New temporary location: {0}".format(location))
        
# All param json file
allParamsJsonFile = os.path.join(location, "allParams.json")


# Get meta data like phasePlateUsed

doPhaseShiftEstimation = "false"


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
    if proposal == "mx415" or proposal == "mx2112":
        # Use valid data base
        print("ISPyB valid data base used")
        db = 1
    else:
        # Use productiond data base
        print("ISPyB production data base used")
        db = 0


if nominalMagnification is None or voltage is None or imagesCount is None:
    if serialEM:
        jpeg, mdoc, gridSquareSnapshot = UtilsPath.getSerialEMMovieJpegMdoc(dataDirectory, firstMovieFullPath)
        if mdoc is None:
            print("*"*80)
            print("*"*80)
            print("*"*80)
            print("Error! Cannot find metadata files in the directory which contains the following movie:")
            print(firstMovieFullPath)
            print("*"*80)
            print("*"*80)
            print("*"*80)
            sys.exit(1)
        dictResults = UtilsPath.getMdocMetaData(mdoc)
        nominalMagnification = int(dictResults["Magnification"])
        voltage = int(dictResults["accelerationVoltage"])
        imagesCount = int(dictResults["numberOffractions"])

    else:
        jpeg, mrc, xml, gridSquareThumbNail = UtilsPath.getMovieJpegMrcXml(firstMovieFullPath)

        if xml is None:
            print("*"*80)
            print("*"*80)
            print("*"*80)
            print("Error! Cannot find metadata files in the directory which contains the following movie:")
            print(firstMovieFullPath)
            print("")
            print("You must provide all these parameters on the command line: voltage, magnification and imagesCount")
            print("")
            print("*"*80)
            print("*"*80)
            print("*"*80)
            sys.exit(1)

        dictResults = UtilsPath.getXmlMetaData(xml)
        doPhaseShiftEstimation = dictResults["phasePlateUsed"]
        nominalMagnification = int(dictResults["nominalMagnification"])
        voltage = int(dictResults["Voltage"])
        imagesCount = int(dictResults["NumSubFrames"])
else:
    jpeg = None
    mdoc = None
    xml = None
    gridSquareSnapshot = None

if alignFrameN == 0:
    alignFrameN = imagesCount

if not phasePlateData and doPhaseShiftEstimation:
    print("!"*100)
    print("WARNING! Phase plate data detected but doPhShEst set to false")
    print("!"*100)

if phasePlateData:
    sphericalAberration = 0.0
    minDefocus = 0.1
    maxDefocus = 2.0
    astigmatism = 1000.0
    convsize = 25
    doPhShEst = "true"
    phaseShiftL = 0.0
    phaseShiftH = 180.0
    phaseShiftS = 5.0
    phaseShiftT = 1
    lowRes = samplingRate / 15.0
    highRes = samplingRate / 4.0
else:
    sphericalAberration = 2.7
    minDefocus = 0.25
    maxDefocus = 4.0
    astigmatism = 100.0
    convsize = 85
    doPhShEst = "false"
    phaseShiftL = 0.0
    phaseShiftH = 180.0
    phaseShiftS = 10.0
    phaseShiftT = 0
    lowRes = samplingRate / 30.0
    highRes = samplingRate / 4.0

if superResolution:
    binFactor = 2.0
else:
    binFactor = 1.0
    
print("")
print("Parameters:")
print("")
print("{0:30s}{1:>8s}".format("proposal", proposal))
print("{0:30s}{1:8s}".format("dataDirectory", dataDirectory))
print("{0:30s}{1:>8s}".format("filesPattern", filesPattern))
print("{0:30s}{1:>8s}".format("proteinAcronym", proteinAcronym))
print("{0:30s}{1:>8s}".format("sampleAcronym", sampleAcronym))
print("{0:30s}{1:8.2f}".format("doseInitial", doseInitial))
print("{0:30s}{1:8.2f}".format("voltage", voltage))
print("{0:30s}{1:8.2f}".format("imagesCount", imagesCount))
print("{0:30s}{1:8.2f}".format("dosePerFrame", dosePerFrame))
print("{0:30s}{1:8.1f}".format("sphericalAberration", sphericalAberration))
print("{0:30s}{1:8.2f}".format("minDefocus", minDefocus))
print("{0:30s}{1:8.2f}".format("maxDefocus", maxDefocus))
print("{0:30s}{1:8.1f}".format("astigmatism", astigmatism))
print("{0:30s}{1:8d}".format("convsize", convsize))
print("{0:30s}{1:>8s}".format("doPhShEst", doPhShEst))
print("{0:30s}{1:8.1f}".format("phaseShiftL", phaseShiftL))
print("{0:30s}{1:8.1f}".format("phaseShiftH", phaseShiftH))
print("{0:30s}{1:8.1f}".format("phaseShiftS", phaseShiftS))
print("{0:30s}{1:8.1f}".format("phaseShiftT", phaseShiftT))
print("{0:30s}{1:8.3f}".format("lowRes", lowRes))
print("{0:30s}{1:8.3f}".format("highRes", highRes))
print("{0:30s}{1:8.0f}".format("nominalMagnification", nominalMagnification))
print("{0:30s}{1:8.2f}".format("samplingRate", samplingRate))
print("{0:30s}{1:8.1f}".format("binFactor", binFactor))
print("{0:30s}{1:8.1f}".format("alignFrame0", alignFrame0))
print("{0:30s}{1:8.1f}".format("alignFrameN", alignFrameN))
print("{0:30s}{1:>8s}".format("dataStreaming", dataStreaming))
print("")
print("Scipion project name: {0}".format(scipionProjectName))
print("Scipion user data location: {0}".format(location))
print("All param json file: {0}".format(allParamsJsonFile))
print("")

if serialEM:
    print("SerialEM specific parameters:")
    print("Metadata file: {0}".format(mdoc))
    print("DefectMap file: {0}".format(defectMapPath))
    print("Gain file: {0}".format(gainFilePath))
else:
    print("EPU specific parameters:")
    print("Metadata file: {0}".format(xml))


if onlyISPyB:
    inputProtocols = """["2"]"""
else:
    inputProtocols = """["2", "77", "195"]"""


# Create json file

if serialEM:
    doSerialEM = "true"
else:
    doSerialEM = "false"

protImportMovies = """
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
    }""" % (dataDirectory, filesPattern, nominalMagnification, samplingRate,
        doseInitial, dosePerFrame, dataStreaming)

protMotionCorr = """
    {
        "object.className": "ProtMotionCorr",
        "object.id": "77",
        "object.label": "motioncorr - motioncorr alignment",
        "object.comment": "",
        "runName": null,
        "runMode": 0,
        "gpuMsg": "True",
        "gpuList": "0 1",
        "alignFrame0": %d,
        "alignFrameN": %d,
        "useAlignToSum": true,
        "sumFrame0": 1,
        "sumFrameN": 0,
        "binFactor": %f,
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
        "extraParams2": "%s",
        "doSaveUnweightedMic": true,
        "hostName": "localhost",
        "numberOfThreads": 1,
        "numberOfMpi": 1,
        "inputMovies": "2.outputMovies"
    }"""  % (alignFrame0, alignFrameN, binFactor, extraParams2)

protGctf = """
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
        "lowRes": %f,
        "highRes": %f,
        "minDefocus": %f,
        "maxDefocus": %f,
        "astigmatism": %f,
        "windowSize": 512,
        "plotResRing": true,
        "GPUCore": 0,
        "doEPA": true,
        "EPAsmp": 4,
        "doBasicRotave": false,
        "bfactor": 150,
        "overlap": 0.5,
        "convsize": %f,
        "doHighRes": true,
        "HighResL": 30.0,
        "HighResH": 5.0,
        "HighResBf": 50,
        "doValidate": false,
        "doPhShEst": %s,
        "phaseShiftL": %f,
        "phaseShiftH": %f,
        "phaseShiftS": %f,
        "phaseShiftT": %f,
        "inputMicrographs": "77.outputMicrographs"
    }"""  % (lowRes, highRes, minDefocus, maxDefocus, astigmatism, 
        convsize, doPhShEst, phaseShiftL, phaseShiftH, phaseShiftS, phaseShiftT)

protMonitorISPyB_ESRF = """
    {
        "object.className": "ProtMonitorISPyB_ESRF",
        "object.id": "259",
        "object.label": "ispyb - monitor to ISPyB at the ESRF",
        "object.comment": "",
        "runName": null,
        "runMode": 0,
        "inputProtocols": %s,
        "samplingInterval": 10,
        "proposal": "%s",
        "proteinAcronym": "%s",
        "sampleAcronym": "%s",
        "db": %d,
        "allParamsJsonFile": "%s",
        "samplingRate": "%s",
        "doseInitial": "%s",
        "dosePerFrame": "%s",
        "serialEM": "%s",
        "voltage": %d,
        "imagesCount": %d,
        "magnification": %d,
        "alignFrame0": %d,
        "alignFrameN": %d
    }"""  % (inputProtocols, proposal, proteinAcronym, sampleAcronym, db,
             allParamsJsonFile, samplingRate, doseInitial, dosePerFrame,
             doSerialEM, voltage, imagesCount, nominalMagnification,
             alignFrame0, alignFrameN)

if onlyISPyB:
    jsonString = """[{0},
    {1}
    ]
    """.format(protImportMovies, protMonitorISPyB_ESRF)
    
elif noISPyB:
    jsonString = """[{0},
    {1},
    {2}
    ]
    """.format(protImportMovies, protMotionCorr, protGctf)
else:
    jsonString = """[{0},
    {1},
    {2},
    {3}
    ]
    """.format(protImportMovies, protMotionCorr, protGctf, protMonitorISPyB_ESRF)

# Write json file
fd, jsonFile = tempfile.mkstemp(suffix=".json", prefix="scipion_workflow_", dir=location)
os.write(fd, jsonString)
os.close(fd)
os.chmod(jsonFile, 0644)
print("Scipion project json file: {0}".format(jsonFile))
print("Project location: {0}".format(location))



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

projectLocation = os.path.join(location, scipionProjectName)
if not os.path.exists(projectLocation):
    os.makedirs(projectLocation, 0o755)
os.chdir(projectLocation)
project = manager.createProject(scipionProjectName, location=os.path.abspath(location))

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
        
    
# # Parse command line
# usage = "\nUsage: cryoemProcess --directory <dir> " + \
#         "[--filesPattern <filesPattern>]  " + \
#         "[--scipionProjectName <name>]  " + \
#         "--protein <name>  " + \
#         "--sample <name>  " + \
#         "--doseInitial <dose>  " + \
#         "--dosePerFrame <dose>  " + \
#         "[--samplingRate <samplingRate>]  " + \
#         "[--startMotioncorFrame startFrame]  " + \
#         "[--endMotioncorFrame endFrame]" + \
#         "[--phasePlateData]" + \
#         "[--onlyISPyB]" + \
#         "\n"

# try:
#     opts, args = getopt.getopt(
#         sys.argv[1:],
#         "",
#         [
#             "directory=",
#             "filesPattern=",
#             "scipionProjectName=",
#             "protein=",
#             "sample=",
#             "doseInitial=",
#             "dosePerFrame=",
#             "samplingRate=",
#             "startMotioncorFrame=",
#             "endMotioncorFrame=",
#             "phasePlateData",
#             "onlyISPyB",
#             "help"
#         ]
#     )
# except getopt.GetoptError:
#     print(usage)
#     sys.exit(1)
#
# if len(args) != 0:
#     print(usage)
#     sys.exit
# for opt, arg in opts:
#     if opt in ["-h", "--help"]:
#         print(usage)
#         sys.exit()
#     elif opt in ["--directory"]:
#         dataDirectory = arg
#     elif opt in ["--filesPattern"]:
#         filesPattern = arg
#     elif opt in ["--scipionProjectName"]:
#         scipionProjectName = arg
#     elif opt in ["--protein"]:
#         proteinAcronym = arg
#     elif opt in ["--sample"]:
#         sampleAcronym = arg
#     elif opt in ["--doseInitial"]:
#         doseInitial = float(arg)
#     elif opt in ["--dosePerFrame"]:
#         dosePerFrame = float(arg)
#     elif opt in ["--samplingRate"]:
#         samplingRate = float(arg)
#     elif opt in ["--startMotioncorFrame"]:
#         alignFrame0 = float(arg)
#     elif opt in ["--endMotioncorFrame"]:
#         alignFrameN = float(arg)
#     elif opt in ["--phasePlateData"]:
#         phasePlateData = True
#     elif opt in ["--onlyISPyB"]:
#         onlyISPyB = True

# # Check mandatory parameters
# if not all([dataDirectory, proteinAcronym, sampleAcronym, dosePerFrame]):
#     print(usage)
#     sys.exit(1)
