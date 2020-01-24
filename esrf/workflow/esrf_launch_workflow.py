#!/usr/bin/env python
# **************************************************************************
# *
# * Author:     Olof Svensson (svensson@esrf.fr) [1]
# *
# * [1] European Synchrotron Radiation Facility
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
import pprint
import datetime
import tempfile

from pyworkflow.project.manager import Manager
from pyworkflow.project import Project
from pyworkflow.protocol import getProtocolFromDb

from esrf.utils.esrf_utils_ispyb import UtilsISPyB
from esrf.utils.esrf_utils_path import UtilsPath
from esrf.utils.esrf_utils_serialem import UtilsSerialEM
from esrf.workflow.command_line_parser import getCommandlineOptions
from esrf.workflow.workflow import preprocessWorkflow

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


configDict = getCommandlineOptions()
pprint.pprint(configDict)

################################################################################
#
# First find out if we use serial em or not:
#

if configDict["filesPattern"] is None:
    # No filesPattern, let's assume that we are dealing with EPU data
    configDict["filesPattern"] = "Images-Disc1/GridSquare_*/Data/FoilHole_*-*.mrc"

# Check how many movies are present on disk
listMovies = glob.glob(os.path.join(configDict["dataDirectory"], configDict["filesPattern"]))
noMovies = len(listMovies)
if noMovies > 0:
    # We have EPU data
    configDict["serialEM"] = False
    print("********** EPU data **********")
else:
    # So, no mrc movies found, let's try to find some serialEM files:
    # Look for first tif, defect file and dm4 file
    tifDir, firstTifFileName, defectFilePath, dm4FilePath = \
        UtilsPath.findSerialEMFilePaths(configDict["dataDirectory"])
    if tifDir is not None:
        # We have serial EM data
        configDict["filesPattern"] = UtilsPath.serialEMFilesPattern(configDict["dataDirectory"], tifDir)
        listMovies = glob.glob(os.path.join(configDict["dataDirectory"], configDict["filesPattern"]))
        noMovies = len(listMovies)
        if noMovies > 0:
            # We have EPU data
            configDict["serialEM"] = True
            print("********** SerialEM data **********")

if noMovies == 0:
    print("ERROR! No movies available in directory {0} with the filesPattern {1}.".format(configDict["dataDirectory"], configDict["filesPattern"]))
    sys.exit(1)

print("Number of movies available on disk: {0}".format(noMovies))
firstMovieFullPath = listMovies[0]
print("First movie full path file: {0}".format(firstMovieFullPath))

if configDict["serialEM"]:
    if defectFilePath is None:
        print("ERROR - No defect file path found in directory {0}!".format(tifDir))
        sys.exit(1)
    if dm4FilePath is None:
        print("ERROR - No dm4 file path found in directory {0}!".format(tifDir))
        sys.exit(1)
    # Create directory for holding defect map and gain reference image
    defectGainDir = os.path.join(configDict["dataDirectory"], "Defect_and_Gain_images")
    if os.path.exists(defectGainDir):
        # Directory exists - we remove it
        print("Removing existing defect and gain maps")
        shutil.rmtree(defectGainDir)
    os.makedirs(defectGainDir, 0o755)
    defectMapPath = UtilsSerialEM.createDefectMapFile(
        defectFilePath, firstMovieFullPath, defectGainDir)
    gainFilePath = UtilsSerialEM.createGainFile(dm4FilePath, defectGainDir)
    configDict["extraParams2"] = "-Gain {0} -DefectMap {1}".format(
        gainFilePath, defectMapPath
    )
else:
    configDict["extraParams2"] = ""



# Set up location
if "RAW_DATA" in configDict["dataDirectory"]:
    location = configDict["dataDirectory"].replace("RAW_DATA", "PROCESSED_DATA")
#elif "cm01/inhouse" in dataDirectory:
#    location = "/users/opcm01/PROCESSED_DATA"
else:
    location = tempfile.mkdtemp(prefix="ScipionUserData_")

dateTime = time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time()))

if configDict["scipionProjectName"] is None:
    if "*" in configDict["filesPattern"] or "?" in configDict["filesPattern"]:
        configDict["scipionProjectName"] = "{0}_{1}".format(os.path.basename(configDict["dataDirectory"]), dateTime)
    else:
        # Use movie file name as project name
        configDict["scipionProjectName"] = "{0}_{1}".format(os.path.splitext(configDict["filesPattern"])[0], dateTime)
        configDict["dataStreaming"] = False

if not os.path.exists(location):
    os.makedirs(location, 0755)
else:
    os.chmod(location, 0755)
        
# All param json file
configDict["allParamsJsonFile"] = os.path.join(location, "allParams.json")
configDict["location"] = location


# Get meta data like phasePlateUsed

configDict["doPhaseShiftEstimation"] = False


# Check proposal
# db=0: production
# db=1: valid
# db=2: linsvensson
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

configDict["proposal"] = proposal
configDict["db"] = db

if configDict["nominalMagnification"] is None:
    if configDict["serialEM"]:
        jpeg, mdoc, gridSquareSnapshot = UtilsPath.getSerialEMMovieJpegMdoc(configDict["dataDirectory"], firstMovieFullPath)
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
        configDict["nominalMagnification"] = int(dictResults["Magnification"])

    else:
        jpeg, mrc, xml, gridSquareThumbNail = UtilsPath.getMovieJpegMrcXml(firstMovieFullPath)

        if xml is None:
            print("*"*80)
            print("*"*80)
            print("*"*80)
            print("Error! Cannot find metadata files in the directory which contains the following movie:")
            print(firstMovieFullPath)
            print("*"*80)
            print("*"*80)
            print("*"*80)
            sys.exit(1)

        dictResults = UtilsPath.getXmlMetaData(xml)
        configDict["doPhaseShiftEstimation"] = dictResults["phasePlateUsed"]
        configDict["nominalMagnification"] = int(dictResults["nominalMagnification"])
else:
    jpeg = None
    mdoc = None
    xml = None
    gridSquareSnapshot = None

if not configDict["phasePlateData"] and configDict["doPhaseShiftEstimation"]:
    print("!"*100)
    print("WARNING! Phase plate data detected but doPhShEst set to false")
    print("!"*100)

if configDict["phasePlateData"]:
    configDict["sphericalAberration"] = 0.0
    configDict["minDefocus"] = 0.1
    configDict["maxDefocus"] = 2.0
    configDict["astigmatism"] = 1000.0
    configDict["convsize"] = 25
    configDict["doPhShEst"] = True
    configDict["phaseShiftL"] = 0.0
    configDict["phaseShiftH"] = 180.0
    configDict["phaseShiftS"] = 5.0
    configDict["phaseShiftT"] = 1
    configDict["lowRes"] = configDict["samplingRate"] / 15.0
    configDict["highRes"] = configDict["samplingRate"] / 4.0
else:
    configDict["sphericalAberration"] = 2.7
    configDict["minDefocus"] = 0.25
    configDict["maxDefocus"] = 4.0
    configDict["astigmatism"] = 100.0
    configDict["convsize"] = 85
    configDict["doPhShEst"] = False
    configDict["phaseShiftL"] = 0.0
    configDict["phaseShiftH"] = 180.0
    configDict["phaseShiftS"] = 10.0
    configDict["phaseShiftT"] = 0
    configDict["lowRes"] = configDict["samplingRate"] / 30.0
    configDict["highRes"] = configDict["samplingRate"] / 4.0

if configDict["superResolution"]:
    configDict["binFactor"] = 2.0
else:
    configDict["binFactor"] = 1.0

configDict["motioncor2Gpu"] = "0"
configDict["gctfGpu"] = "0"
configDict["gl2dGpu"] = "0"
configDict["relionGpu"] = "1"
configDict["numCpus"] = 16
configDict["sampling2D"] = 3.0

print("")
print("Parameters:")
print("")
print("{0:30s}{1:>8s}".format("proposal",configDict["proposal"]))
print("{0:30s}{1:8s}".format("dataDirectory",configDict["dataDirectory"]))
print("{0:30s}{1:>8s}".format("filesPattern",configDict["filesPattern"]))
print("{0:30s}{1:>8s}".format("proteinAcronym",configDict["proteinAcronym"]))
print("{0:30s}{1:>8s}".format("sampleAcronym",configDict["sampleAcronym"]))
print("{0:30s}{1:8.2f}".format("doseInitial",configDict["doseInitial"]))
print("{0:30s}{1:8.2f}".format("dosePerFrame",configDict["dosePerFrame"]))
print("{0:30s}{1:8.1f}".format("sphericalAberration",configDict["sphericalAberration"]))
print("{0:30s}{1:8.2f}".format("minDefocus",configDict["minDefocus"]))
print("{0:30s}{1:8.2f}".format("maxDefocus",configDict["maxDefocus"]))
print("{0:30s}{1:8.1f}".format("astigmatism",configDict["astigmatism"]))
print("{0:30s}{1:8d}".format("convsize",configDict["convsize"]))
print("{0:30s}{1:>8}".format("doPhShEst",configDict["doPhShEst"]))
print("{0:30s}{1:8.1f}".format("phaseShiftL",configDict["phaseShiftL"]))
print("{0:30s}{1:8.1f}".format("phaseShiftH",configDict["phaseShiftH"]))
print("{0:30s}{1:8.1f}".format("phaseShiftS",configDict["phaseShiftS"]))
print("{0:30s}{1:8.1f}".format("phaseShiftT",configDict["phaseShiftT"]))
print("{0:30s}{1:8.3f}".format("lowRes",configDict["lowRes"]))
print("{0:30s}{1:8.3f}".format("highRes",configDict["highRes"]))
print("{0:30s}{1:8.0f}".format("nominalMagnification",configDict["nominalMagnification"]))
print("{0:30s}{1:8.2f}".format("samplingRate",configDict["samplingRate"]))
print("{0:30s}{1:8.2f}".format("sampling2D",configDict["sampling2D"]))
print("{0:30s}{1:8.2f}".format("partSize",configDict["partSize"]))
print("{0:30s}{1:8.1f}".format("binFactor",configDict["binFactor"]))
print("{0:30s}{1:>8}".format("dataStreaming",configDict["dataStreaming"]))
print("{0:30s}{1:>8s}".format("motioncor2Gpu",configDict["motioncor2Gpu"]))
print("{0:30s}{1:>8s}".format("gctfGpu",configDict["gctfGpu"]))
print("{0:30s}{1:>8s}".format("gl2dGpu",configDict["gl2dGpu"]))
print("{0:30s}{1:8d}".format("numCpus",configDict["numCpus"]))
print("")
print("Scipion project name: {0}".format(configDict["scipionProjectName"]))
print("Scipion user data location: {0}".format(location))
print("All param json file: {0}".format(configDict["allParamsJsonFile"]))
print("")

if configDict["serialEM"]:
    print("SerialEM specific parameters:")
    print("Metadata file: {0}".format(mdoc))
    print("DefectMap file: {0}".format(defectMapPath))
    print("Gain file: {0}".format(gainFilePath))
else:
    print("EPU specific parameters:")
    print("Metadata file: {0}".format(xml))

preprocessWorkflow(configDict)

# if jsonFile is not None:
#     protDict = project.loadProtocols(jsonFile)

# the project may be a soft link which may be unavailable to the cluster so get the real path
manager = Manager()
try:
    projectPath = os.readlink(manager.getProjectPath(configDict["scipionProjectName"]))
except:
    projectPath = manager.getProjectPath(configDict["scipionProjectName"])

project = Project(projectPath)
project.load()

# Start the project
runs = project.getRuns()

# Now assuming that there is no dependencies between runs
# and the graph is lineal
# for prot in runs:
#     project.scheduleProtocol(prot)
for prot in runs:
    protClassName = prot.getClassName()
    protLabelName = prot.getObjLabel()
    if (protClassName not in sys.argv[3:] and
        protLabelName not in sys.argv[3:]):
        project.scheduleProtocol(prot)
    else:
        print(pwutils.yellowStr("\nNot scheduling '%s' protocol named '%s'.\n"
                                % (protClassName, protLabelName)))



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
        
    
