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

import sys
import json
import random

from collections import OrderedDict

from pwem.protocols import ProtImportMovies
from pwem.protocols import ProtUnionSet
from pwem.protocols import ProtBoxSizeParameters
from pwem.protocols import ProtManualCheckpoint
from pwem.protocols import ProtExtractCoords
from pwem.protocols import ProtClassesSelector

from gautomatch.protocols import ProtGautomatch


from pyworkflow.object import Pointer
import pyworkflow.utils as pwutils

from pyworkflow.project.manager import Manager


try:  # Xmipp plugin is mandatory to run this workflow
    from xmipp3.protocols import (
        XmippProtCTFMicrographs,
        XmippProtCTFConsensus,
        XmippProtPreprocessMicrographs,
        XmippProtConsensusPicking,
        XmippProtTriggerData,
        XmippProtEliminateEmptyParticles,
        XmippProtScreenParticles,
        XmippProtStrGpuCrrSimple,
        XmippProtEliminateEmptyClasses,
        XmippProtCenterParticles,
    )
#                                  XmippProtDeepMicrographScreen)
except Exception as exc:
    raise
    pwutils.pluginNotFound("xmipp", errorMsg=exc, doRaise=True)

from motioncorr.protocols import ProtMotionCorr
from cistem.protocols import CistemProtCTFFind
from gctf.protocols import ProtGctf
from sphire.protocols import SphireProtCRYOLOPicking
from sphire.protocols import SphireProtCRYOLOTraining
from relion.protocols import ProtRelionAutopickLoG
from relion.protocols import ProtRelionClassify2D
from relion.protocols.protocol_select_classes import ProtRelionSelectClasses2D
from relion.protocols import ProtRelionExtractParticles

if "v3_dev" in __file__:
    sys.path.insert(0, "/opt/pxsoft/scipion/v3_dev/ubuntu20.04/scipion-em-esrf")

from esrf.protocols import ProtMonitorISPyB_ESRF


QUEUE_PARAMS_WITH_1_GPU_4_CPU = (
    "gpu",
    {
        "JOB_TIME": "150",  # in hours
        "JOB_MEMORY": "100000",  # in Mb
        "QUEUE_FOR_JOBS": "N",
        "JOB_GPU": "--gres=gpu:1",
        "JOB_THREADS": 4,
    },
)

QUEUE_PARAMS_WITH_1_GPU_15_CPU = (
    "gpu",
    {
        "JOB_TIME": "150",  # in hours
        "JOB_MEMORY": "100000",  # in Mb
        "QUEUE_FOR_JOBS": "N",
        "JOB_GPU": "--gres=gpu:1",
        "JOB_THREADS": 15,
    },
)

QUEUE_PARAMS_WITH_2_GPU_16_CPU = (
    "gpu",
    {
        "JOB_TIME": "150",  # in hours
        "JOB_MEMORY": "100000",  # in Mb
        "QUEUE_FOR_JOBS": "N",
        "JOB_GPU": "--gres=gpu:2",
        "JOB_THREADS": 16,
    },
)

QUEUE_PARAMS_WITHOUT_GPU_16_CPU = (
    "gpu",
    {
        "JOB_TIME": "150",  # in hours
        "JOB_MEMORY": "100000",  # in Mb
        "QUEUE_FOR_JOBS": "N",
        "JOB_GPU": "",
        "JOB_THREADS": 16,
    },
)


def getNewScipionProjectName(scipionProjectName, index):
    return "{0}_{1}".format(scipionProjectName, index)


def preprocessWorkflow(configDict):
    scipionProjectName = configDict["scipionProjectName"]
    location = configDict["location"]

    # Create a new project
    manager = Manager()

    if manager.hasProject(scipionProjectName):
        print(
            "ERROR! There is already a Scipion project with this name: '{0}'".format(
                scipionProjectName
            )
        )
        sys.exit(1)

    def _registerProt(prot, label="", toSummary=False, color=""):
        project.saveProtocol(prot)
        if label != "":
            applyLabel(prot, label, color)
        if toSummary:
            summaryList.append(prot)

    def applyLabel(prot, labelName, color=""):
        if all(l != labelName for l in labelsDict.keys()):
            if color == "":
                if len(colorsDict) < 9:
                    color = colorsDef[len(colorsDict)]
                else:
                    color = "#%s" % "".join(
                        [random.choice("0123456789abcdef") for j in range(6)]
                    )
            colorsDict.update({labelName: color})
            labelsDict.update({labelName: [prot.getObjId()]})
        else:
            labelsDict[labelName].append(prot.getObjId())

    def setExtendedInput(protDotInput, lastProt, extended, pointer=False):
        if pointer:
            pointer = Pointer(lastProt, extended=extended)
            protDotInput.setPointer(pointer)
        else:
            if isinstance(lastProt, list):
                for idx, prot in enumerate(lastProt):
                    inputPointer = Pointer(prot, extended=extended[idx])
                    protDotInput.append(inputPointer)
            else:
                protDotInput.set(lastProt)
                protDotInput.setExtended(extended)

    def getEvenPartSize(partSize):
        """Fixing an even partSize big enough:
        int(x / 2 + 1) * 2 = ceil(x / 2) * 2 = even!
        """
        return int(partSize / 2 + 1) * 2

    def setBoxSize(protDotBoxSize):
        if protPrePick:
            setExtendedInput(protDotBoxSize, protPrePick, "boxsize", True)
        else:
            protDotBoxSize.set(bxSize)

    project = manager.createProject(scipionProjectName, location=location)

    labelsDict = OrderedDict()  # key: labelName ; value: [prot1, prot2, prot3...])
    colorsDict = OrderedDict()  # key: labelName ; value: colorRGB
    random.seed(6)
    colorsDef = [
        "#e57373",
        "#4fc3f7",
        "#81c784",
        "#ff8a65",
        "#9575cd",
        "#a1887f",
        "#ffd54f",
        "#dce775",
        "#4db6ac",
    ]
    summaryList = []
    ispybUploads = []

    if configDict["secondGrid"]:
        timeout = 295200  # 72 hours
    else:
        timeout = 43200  # 12 hours

    protImport = project.newProtocol(
        ProtImportMovies,
        objLabel="Import movies",
        importFrom=ProtImportMovies.IMPORT_FROM_FILES,
        filesPath=configDict["dataDirectory"],
        filesPattern=configDict["filesPattern"],
        amplitudeContrast=0.1,
        sphericalAberration=configDict["sphericalAberration"],
        voltage=configDict["voltage"] / 1000.0,
        samplingRate=configDict["samplingRate"],
        doseInitial=configDict["doseInitial"],
        dosePerFrame=configDict["dosePerFrame"],
        magnification=configDict["magnification"],
        dataStreaming=configDict["dataStreaming"],
        blacklistFile=configDict["blacklistFile"],
        useRegexps=False,
        gainFile=configDict["gainFilePath"],
        fileTimeout=30,
        timeout=timeout,
    )
    _registerProt(protImport, label="Movies", toSummary=True)
    ispybUploads.append(protImport)

    # Stop here if --onlyISPyB
    if not configDict["onlyISPyB"]:
        # ----------- Movie Gain ----------------------------
        # protMG = project.newProtocol(
        #     XmippProtMovieGain,
        #     objLabel="xmipp3 - movie gain",
        #     estimateGain=True,
        #     estimateOrientation=True,
        #     estimateResidualGain=True,
        #     normalizeGain=True,
        #     estimateSigma=False,
        #     frameStep=5,
        #     movieStep=20,
        #     hostName="localhost",
        #     numberOfThreads=4,
        #     numberOfMpi=1,
        # )
        # setExtendedInput(protMG.inputMovies, protImport, "outputMovies")
        # _registerProt(protMG, "MovieGain")

        # ----------- MOTIONCOR ----------------------------
        protMA = project.newProtocol(
            ProtMotionCorr,
            objLabel="MotionCor2 - movie align.",
            gpuList=configDict["motioncor2Gpu"],
            numberOfThreads=configDict["motioncor2Cpu"],
            numberOfMpi=1,
            doApplyDoseFilter=True,
            doSaveUnweightedMic=True,
            doSaveAveMic=True,
            doSaveMovie=False,
            doComputeMicThumbnail=True,
            computeAllFramesAvg=False,
            patchX=5,
            patchY=5,
            useEst=True,
            gainFlip=configDict["gainFlip"],
            gainRot=configDict["gainRot"],
            alignFrame0=configDict["alignFrame0"],
            alignFrameN=configDict["alignFrameN"],
            binFactor=configDict["binFactor"],
            extraParams2=configDict["extraParams2"],
        )
        setExtendedInput(protMA.inputMovies, protImport, "outputMovies")
        _registerProt(protMA, "MotionCorr")
        ispybUploads.append(protMA)

        # ----------- Movie Max Shift ----------------------------
        # protMS = project.newProtocol(
        #     XmippProtMovieMaxShift,
        #     objLabel="xmipp3 - movie max shift",
        #     rejType=3,
        #     maxFrameShift=5.0,
        #     maxMovieShift=15.0,
        # )
        # setExtendedInput(protMS.inputMovies, protMA, "outputMicrographsDoseWeighted")
        # _registerProt(protMS, "MovieMaxShift")

        # ----------- GCTF ----------------------------
        protCTF2 = project.newProtocol(
            ProtGctf,
            objLabel="gCTF estimation",
            gpuList=configDict["gctfGpu"],
            lowRes=configDict["lowRes"],
            plotResRing=True,
            doEPA=False,
            doHighRes=True,
            convsize=configDict["convsize"],
            highRes=configDict["highRes"],
            minDefocus=configDict["minDefocus"],
            maxDefocus=configDict["maxDefocus"],
            astigmatism=configDict["astigmatism"],
            doPhShEst=configDict["doPhShEst"],
            phaseShiftL=configDict["phaseShiftL"],
            phaseShiftH=configDict["phaseShiftH"],
            phaseShiftS=configDict["phaseShiftS"],
            phaseShiftT=configDict["phaseShiftT"],
        )
        setExtendedInput(
            protCTF2.inputMicrographs, protMA, "outputMicrographsDoseWeighted"
        )
        _registerProt(protCTF2, "CTF")
        ispybUploads.append(protCTF2)

    # Only do the rest if not --onlyISPyB and not --no2dClass
    if not configDict["onlyISPyB"] and not configDict["no2dClass"]:
        #
        # # --------- CTF ESTIMATION 1 ---------------------------
        protCTF1 = project.newProtocol(
            CistemProtCTFFind,
            objLabel="Cistem - CTFfind",
            numberOfThreads=configDict["numCpus"],
            lowRes=configDict["lowRes"],
            highRes=configDict["highRes"],
            minDefocus=configDict["minDefocus"],
            maxDefocus=configDict["maxDefocus"],
            astigmatism=configDict["astigmatism"],
            doPhShEst=configDict["doPhShEst"],
            phaseShiftL=configDict["phaseShiftL"],
            phaseShiftH=configDict["phaseShiftH"],
            phaseShiftS=configDict["phaseShiftS"],
            phaseShiftT=configDict["phaseShiftT"],
        )
        setExtendedInput(
            protCTF1.inputMicrographs, protMA, "outputMicrographsDoseWeighted"
        )
        _registerProt(protCTF1, "CTF")
        #
        # # --------- CTF CONSENSUS ---------------------------
        isCtf2Xmipp = isinstance(protCTF2, XmippProtCTFMicrographs)
        protCTFs = project.newProtocol(
            XmippProtCTFConsensus,
            objLabel="Xmipp - CTF consensus",
            useDefocus=True,
            useAstigmatism=True,
            useResolution=True,
            resolution=7,
            useCritXmipp=isCtf2Xmipp,
            calculateConsensus=True,
            minConsResol=7,
        )
        setExtendedInput(protCTFs.inputCTF, protCTF2, "outputCTF")
        setExtendedInput(protCTFs.inputCTF2, protCTF1, "outputCTF")
        _registerProt(protCTFs, "CTF", True)

        # # *************   PICKING   ********************************************

        pickers = []
        pickersOuts = []

        # # --------- PREPROCESS MICS ---------------------------
        protPreMics0 = project.newProtocol(
            XmippProtPreprocessMicrographs,
            objLabel="Xmipp - preprocess Mics",
            doRemoveBadPix=True,
            doInvert=False,
        )
        setExtendedInput(protPreMics0.inputMicrographs, protCTFs, "outputMicrographs")
        _registerProt(protPreMics0, "Micrographs")

        # # Resizing to a larger sampling rate
        doDownSamp2D = 0 < configDict["sampling2D"] > configDict["samplingRate"]
        samp2D = (
            configDict["sampling2D"] if doDownSamp2D else configDict["samplingRate"]
        )
        if doDownSamp2D:
            downSampPreMics = configDict["sampling2D"] / (
                configDict["samplingRate"] * configDict["binFactor"]
            )
            protPreMics = project.newProtocol(
                XmippProtPreprocessMicrographs,
                objLabel="downSampling to 2D size",
                doDownsample=True,
                downFactor=downSampPreMics,
            )
            setExtendedInput(
                protPreMics.inputMicrographs, protPreMics0, "outputMicrographs"
            )
            _registerProt(protPreMics, "Micrographs")
        else:
            # downSampPreMics = 1
            protPreMics = protPreMics0

        # # -------- XMIPP AUTO-BOXSIZE -------------------------
        protPrePick = None
        bxSize = getEvenPartSize(configDict["partSize"] / samp2D)

        protPP2 = project.newProtocol(
            SphireProtCRYOLOPicking,
            objLabel="Sphire - CrYolo auto-picking",
            useGpu=False,
            conservPickVar=0.3,
            numCpus=16,
            streamingBatchSize=4,
        )  # CPU version installation
        protPP2._useQueue.set(True)
        protPP2._queueParams.set(json.dumps(QUEUE_PARAMS_WITHOUT_GPU_16_CPU))
        setBoxSize(protPP2.boxSize)
        setExtendedInput(
            protPP2.inputMicrographs,
            protPreMics,
            "outputMicrographs"
        )
        _registerProt(protPP2, "Picking")

        pickers.append(protPP2)
        pickersOuts.append("outputCoordinates")

        # # --------- CONSENSUS PICKING -----------------------

        consRadius = int(bxSize / 3) if bxSize else 10
        protCPand = project.newProtocol(
            XmippProtConsensusPicking,
            objLabel="Xmipp - consensus picking (AND)",
            consensusRadius=consRadius,
            consensus=-1,
        )
        setExtendedInput(protCPand.inputCoordinates, pickers, pickersOuts)
        _registerProt(protCPand, "Picking", True)

        finalPicker = protCPand
        outputCoordsStr = "consensusCoordinates"

        extracBoxSize = getEvenPartSize(bxSize * 1.25)

        protExtractNoFlip = project.newProtocol(
            ProtRelionExtractParticles,
            objLabel="Relion - extract particles",
            boxSize=extracBoxSize,
            doInvert=True,
            numberOfMpi=1,
        )
        setExtendedInput(
            protExtractNoFlip.inputCoordinates,
            finalPicker,
            outputCoordsStr
        )
        protExtractNoFlip.inputMicrographs.set(protPreMics)
        # setExtendedInput(
        #     protExtractNoFlip.inputMicrographs,
        #     protPreMics,
        #     "outputMicrographs"
        # )
        setExtendedInput(
            protExtractNoFlip.ctfRelations,
            protCTFs, "outputCTF")
        _registerProt(protExtractNoFlip, "Particles")

        if configDict["particleElimination"]:
            # ***********   CLEAN PARTICLES   ************************************

            protEEPandNoFlip = project.newProtocol(
                XmippProtEliminateEmptyParticles,
                objLabel="Xmipp - Elim. empty part. - no flip",
                threshold=0.6,
            )
            setExtendedInput(
                protEEPandNoFlip.inputParticles, protExtractNoFlip, "outputParticles"
            )
            _registerProt(protEEPandNoFlip, "Particles")

            # --------- TRIGGER PARTS AND ---------------------------

            protTRIGandNoFlip = project.newProtocol(
                XmippProtTriggerData,
                objLabel="Xmipp - trigger data to stats - no flip",
                outputSize=1000,
                delay=30,
                allImages=True,
                splitImages=False,
            )
            setExtendedInput(
                protTRIGandNoFlip.inputImages, protEEPandNoFlip, "outputParticles"
            )
            _registerProt(protTRIGandNoFlip, "Particles")

            # --------- SCREEN PARTS AND ---------------------------

            protSCRandNoFlip = project.newProtocol(
                XmippProtScreenParticles, objLabel="Xmipp - Screen particles - no flip"
            )
            protSCRandNoFlip.autoParRejection.set(
                XmippProtScreenParticles.REJ_MAXZSCORE
            )
            protSCRandNoFlip.autoParRejectionSSNR.set(
                XmippProtScreenParticles.REJ_PERCENTAGE_SSNR
            )
            protSCRandNoFlip.autoParRejectionVar.set(
                XmippProtScreenParticles.REJ_VARIANCE
            )
            setExtendedInput(
                protSCRandNoFlip.inputParticles, protTRIGandNoFlip, "outputParticles"
            )
            _registerProt(protSCRandNoFlip, "Particles", True)
        # # ----------------------------- END OF AND/SINGLE PICKING BRANCH --------

        triggers = []

        def getNoClasses(no_particles):
            no_classes = 50
            return no_classes

        for outputSize in [5000, 20000]:
            # for outputSize in [1000, 4000]:
            allAvgs = []
            classifiers = []
            # --------- TRIGGER PARTS ---------------------------

            protTRIG2NoFlip = project.newProtocol(
                XmippProtTriggerData,
                objLabel="Xmipp - trigger {0} - no flip".format(outputSize),
                outputSize=outputSize,
                delay=30,
                allImages=False,
            )
            if configDict["particleElimination"]:
                setExtendedInput(
                    protTRIG2NoFlip.inputImages, protSCRandNoFlip, "outputParticles"
                )
            else:
                setExtendedInput(
                    protTRIG2NoFlip.inputImages, protExtractNoFlip, "outputParticles"
                )
            _registerProt(protTRIG2NoFlip, "2Dclassify")
            triggers.append(protTRIG2NoFlip)

            protCL2 = project.newProtocol(
                ProtRelionClassify2D,
                objLabel="Relion - 2D classifying",
                doGpu=True,
                gpusToUse=configDict["relionGpu"],
                numberOfClasses=getNoClasses(outputSize),
                numberOfMpi=1,
                numberOfThreads=15,
                # maskDiameterA=configDict["partSize"],
                useGradientAlg=False,
                maskDiameterA=-1,
            )
            protCL2._useQueue.set(True)
            protCL2._queueParams.set(json.dumps(QUEUE_PARAMS_WITH_2_GPU_16_CPU))
            setExtendedInput(protCL2.inputParticles, protTRIG2NoFlip, "outputParticles")
            _registerProt(protCL2, "2Dclassify", True)
            classifiers.append(protCL2)
            ispybUploads.append(protCL2)
            # # Classes -> Averages
            # protCl2Av2 = project.newProtocol(
            #     XmippProtEliminateEmptyClasses,
            #     objLabel="Classes to averages (relion)",
            #     threshold=-1,
            #     usePopulation=False,
            # )
            # protCl2Av2.inputClasses.set(protCL2)
            # # setExtendedInput(protCl2Av2.inputClasses, protCL2, "outputClasses")
            # _registerProt(protCl2Av2, "2Dclassify")
            # allAvgs.append(protCl2Av2)
            #
            # protJOIN = project.newProtocol(
            #     ProtUnionSet,
            #     objLabel="Scipion - Join all Averages - {0}".format(outputSize),
            # )
            # setExtendedInput(
            #     protJOIN.inputSets, allAvgs, ["outputAverages"] * len(allAvgs)
            # )
            # _registerProt(protJOIN, "2Dclassify")
            # allAvgsOut = "outputSet"
            #
            # protCLSEL = project.newProtocol(
            #     XmippProtEliminateEmptyClasses,
            #     objLabel="Xmipp - Auto class selection - {0}".format(outputSize),
            #     threshold=-1,
            #     usePopulation=False,
            # )
            # protCLSEL.inputClasses.set(protJOIN)
            # # setExtendedInput(protCLSEL.inputClasses, protJOIN, allAvgsOut)
            # _registerProt(protCLSEL, "initVol", True)

    # # --------- SUMMARY MONITOR -----------------------
    # protMonitor = project.newProtocol(
    #     ProtMonitorSummary,
    #     objLabel='Scipion - Summary Monitor',
    #     samplingInterval=20,
    #     publishCmd="rsync -avL %(REPORT_FOLDER)s {0}".format(configDict["dataDirectory"])
    # )
    # protMonitor.inputProtocols.set(summaryList)
    # _registerProt(protMonitor, 'monitor')

    # --------- ISPyB MONITOR -----------------------
    if not configDict["noISPyB"]:
        ispybMonitor = project.newProtocol(
            ProtMonitorISPyB_ESRF,
            objLabel="ISPyB monitor",
            samplingInterval=10,
            proposal=configDict["proposal"],
            proteinAcronym=configDict["proteinAcronym"],
            sampleAcronym=configDict["sampleAcronym"],
            db=configDict["db"],
            allParamsJsonFile=configDict["allParamsJsonFile"],
            samplingRate=configDict["samplingRate"],
            doseInitial=configDict["doseInitial"],
            dosePerFrame=configDict["dosePerFrame"],
            dataType=configDict["dataType"],
            voltage=configDict["voltage"],
            imagesCount=configDict["imagesCount"],
            magnification=configDict["magnification"],
            alignFrame0=configDict["alignFrame0"],
            alignFrameN=configDict["alignFrameN"],
            defectMapPath=configDict["defectMapPath"],
            gainFilePath=configDict["gainFilePath"],
            particleSize=configDict["partSize"],
            doProcessDir=configDict["doProcessDir"],
        )
        ispybMonitor.inputProtocols.set(ispybUploads)
        _registerProt(ispybMonitor, "ispybMonitor")

    # --------- SUPPORT BRANCH ---------------------------

    # --------- MANUAL CHECKPOINT STAGE 1 ----------------------------------
    # {
    #     "object.className": "ProtManualCheckpoint",
    #     "object.id": "3472",
    #     "object.label": "pwem - manual check point (Stage 1)",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "timeout": "1h"
    # },
    protSupportBranchManualCheckpointStage1 = project.newProtocol(
        ProtManualCheckpoint,
        objLabel="pwem - manual check point (Stage 1)",
        timeout="1h",
    )
    _registerProt(protSupportBranchManualCheckpointStage1, "CheckPoint")

    # --------- MANUAL CHECKPOINT STAGE 2 ----------------------------------
    # {
    #     "object.className": "ProtManualCheckpoint",
    #     "object.id": "3502",
    #     "object.label": "pwem - manual check point (Stage 2) ",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "timeout": "1h"
    # },
    protSupportBranchManualCheckpointStage2 = project.newProtocol(
        ProtManualCheckpoint,
        objLabel="pwem - manual check point (Stage 2)",
        timeout="1h",
    )
    _registerProt(protSupportBranchManualCheckpointStage2, "CheckPoint")

    # --------- MANUAL CHECKPOINT STAGE 3 ----------------------------------
    # {
    #     "object.className": "ProtManualCheckpoint",
    #     "object.id": "3532",
    #     "object.label": "pwem - manual check point (Stage 3)",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 1,
    #     "timeout": "1h"
    # },
    protSupportBranchManualCheckpointStage3 = project.newProtocol(
        ProtManualCheckpoint,
        objLabel="pwem - manual check point (Stage 3)",
        timeout="1h",
    )
    _registerProt(protSupportBranchManualCheckpointStage3, "CheckPoint")

    # --------- TRIGGER 1 ----------------------------------
    # {
    #     "object.className": "XmippProtTriggerData",
    #     "object.id": "2888",
    #     "object.label": "xmipp3 - trigger data (initial picking)",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "triggerWait": false,
    #     "outputSize": 10,
    #     "allImages": false,
    #     "splitImages": false,
    #     "triggerSignal": false,
    #     "delay": 5,
    #     "inputImages": "2854.outputMicrographsDoseWeighted"
    # },
    protSupportBranchTrigInitPick = project.newProtocol(
        XmippProtTriggerData,
        objLabel="xmipp3 - trigger data (initial picking)",
        outputSize=10,
        delay=5,
        allImages=False,
        splitImages=False,
        triggerSignal=False,
    )
    setExtendedInput(
        protSupportBranchTrigInitPick.inputImages,
        protPreMics,
        "outputMicrographs",
    )
    _registerProt(protSupportBranchTrigInitPick, "Micrographs")

    # # --------- PREPROCESS MICS ---------------------------
    # protSupportBranchPreMics0 = project.newProtocol(
    #     XmippProtPreprocessMicrographs,
    #     objLabel="Xmipp - preprocess Mics support branch",
    #     doRemoveBadPix=True,
    #     doInvert=False,
    # )
    # setExtendedInput(
    #     protSupportBranchPreMics0.inputMicrographs,
    #     protSupportBranchTrigInitPick,
    #     "outputMicrographs"
    # )
    # _registerProt(protSupportBranchPreMics0, "Micrographs")
    #
    # # Resizing to a larger sampling rate
    # if doDownSamp2D:
    #     downSampPreMics = configDict["sampling2D"] / (
    #             configDict["samplingRate"] * configDict["binFactor"]
    #     )
    #     protSupportBranchPreMics = project.newProtocol(
    #         XmippProtPreprocessMicrographs,
    #         objLabel="DownSampling to 2D size - support branch",
    #         doDownsample=True,
    #         downFactor=downSampPreMics,
    #     )
    #     setExtendedInput(
    #         protSupportBranchPreMics.inputMicrographs,
    #         protSupportBranchPreMics0,
    #         "outputMicrographs"
    #     )
    #     _registerProt(protSupportBranchPreMics, "Micrographs")
    # else:
    #     # downSampPreMics = 1
    #     protSupportBranchPreMics = protSupportBranchPreMics0

    # --------- CRYOLO PICKING ----------------------------------
    # {
    #     "object.className": "SphireProtCRYOLOPicking",
    #     "object.id": "3108",
    #     "object.label": "sphire - cryolo picking",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "inputModelFrom": 0,
    #     "conservPickVar": 0.3,
    #     "lowPassFilter": true,
    #     "absCutOffFreq": 0.1,
    #     "numCpus": 4,
    #     "input_size": 1024,
    #     "boxSize": 0,
    #     "max_box_per_image": 600,
    #     "useGpu": true,
    #     "gpuList": "2",
    #     "boxSizeFactor": 1.0,
    #     "hostName": "localhost",
    #     "numberOfThreads": 1,
    #     "numberOfMpi": 1,
    #     "streamingWarning": null,
    #     "streamingSleepOnWait": 0,
    #     "streamingBatchSize": 16,
    #     "inputMicrographs": "2888.outputMicrographs"
    # },
    protSupportBranchCryoloPicking = project.newProtocol(
        SphireProtCRYOLOPicking,
        objLabel="sphire - cryolo picking",
        useGpu=False,
        conservPickVar=0.3,
        numCpus=16,
        streamingBatchSize=4,
        # inputModelFrom=0,
        # conservPickVar=0.3,
        # lowPassFilter=True,
        # absCutOffFreq=0.1,
        # numCpus=4,
        # input_size=1024,
        # boxSize=0,
        # max_box_per_image=600,
        # useGpu=False,
        # gpuList="2",
        # boxSizeFactor=1.0,
        # hostName="localhost",
        # numberOfThreads=1,
        # numberOfMpi=1,
        # streamingWarning=None,
        # streamingSleepOnWait=0,
        # streamingBatchSize=16,
    )
    setExtendedInput(
        protSupportBranchCryoloPicking.inputMicrographs,
        protSupportBranchTrigInitPick,
        "outputMicrographs",
    )
    _registerProt(protSupportBranchCryoloPicking, "Picking")

    # --------- BOX SIZE PARAMETERS ----------------------------------
    # {
    #     "object.className": "ProtBoxSizeParameters",
    #     "object.id": "3155",
    #     "object.label": "pwem - box size related parameters",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "boxSize": "3108.boxsize",
    #     "boolExtractPartBx": true,
    #     "factorExtractPartBx": 1.5,
    #     "boolGautomatchParams": true,
    #     "factorGautRadius": 0.75,
    #     "factorGautMinInterPartDist": 0.9,
    #     "factorGautSigmaDiameter": 1.2,
    #     "factorGautAvgDiameter": 1.5,
    #     "boolRelionParams": true,
    #     "factorMinLoGFilter": 0.95,
    #     "factorMaxLoGFilter": 1.05,
    #     "boolTopazParams": true,
    #     "factorTopazRadius": 0.45,
    #     "numPartPerImg": 300,
    #     "boolConsensusParams": true,
    #     "factorConsensusRadius": 0.9,
    #     "hostName": "localhost",
    #     "numberOfThreads": 1,
    #     "numberOfMpi": 1,
    #     "inputMicrographs": "2888.outputMicrographs"
    # },
    protSupportBranchBoxSize = project.newProtocol(
        ProtBoxSizeParameters,
        objLabel="pwem - box size related parameters",
        runName=None,
        runMode=0,
        boolExtractPartBx=True,
        factorExtractPartBx=1.5,
        boolGautomatchParams=True,
        factorGautRadius=0.75,
        factorGautMinInterPartDist=0.9,
        factorGautSigmaDiameter=1.2,
        factorGautAvgDiameter=1.5,
        boolRelionParams=True,
        factorMinLoGFilter=0.95,
        factorMaxLoGFilter=1.05,
        boolTopazParams=True,
        factorTopazRadius=0.45,
        numPartPerImg=300,
        boolConsensusParams=True,
        factorConsensusRadius=0.9,
        hostName="localhost",
        numberOfThreads=1,
        numberOfMpi=1,
        inputMicrographs="2888.outputMicrographs",
    )
    protSupportBranchBoxSize.addPrerequisites(protSupportBranchCryoloPicking.getObjId())
    setExtendedInput(
        protSupportBranchBoxSize.inputMicrographs,
        protSupportBranchTrigInitPick,
        "outputMicrographs",
    )
    setExtendedInput(
        protSupportBranchBoxSize.boxSize,
        protSupportBranchCryoloPicking,
        "boxsize",
        pointer=True,
    )
    _registerProt(protSupportBranchBoxSize, "Box Size")

    # --------- TRIGGER 2 ----------------------------------
    # {
    #     "object.className": "XmippProtTriggerData",
    #     "object.id": "3202",
    #     "object.label": "xmipp3 - trigger data (receive stop signal)",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "3472",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "triggerWait": true,
    #     "outputSize": 1,
    #     "allImages": true,
    #     "splitImages": false,
    #     "triggerSignal": false,
    #     "delay": 4,
    #     "inputImages": "3052.outputMicrographs"
    # },
    protSupportBranchTrigStopSignal = project.newProtocol(
        XmippProtTriggerData,
        objLabel="xmipp3 - trigger data (receive stop signal)",
        triggerWait=True,
        outputSize=1,
        allImages=True,
        splitImages=False,
        triggerSignal=False,
        delay=4,
    )
    # protSupportBranchTrigStopSignal._prerequisites.set(
    #     [protSupportBranchManualCheckpointStage1]
    # )
    setExtendedInput(
        protSupportBranchTrigStopSignal.inputImages,
        protPreMics,
        "outputMicrographs"
    )
    _registerProt(protSupportBranchTrigStopSignal, "Micrographs")

    # --------- CRYOLO PICKING AUTOCOMPLETED ----------------------------------
    # {
    #     "object.className": "SphireProtCRYOLOPicking",
    #     "object.id": "3241",
    #     "object.label": "sphire - cryolo picking (autocompleted)",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "3155",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "inputModelFrom": 0,
    #     "conservPickVar": 0.3,
    #     "lowPassFilter": true,
    #     "absCutOffFreq": 0.1,
    #     "numCpus": 4,
    #     "input_size": 1024,
    #     "boxSize": "3155.boxSizeEven",
    #     "max_box_per_image": 600,
    #     "useGpu": true,
    #     "gpuList": "2",
    #     "boxSizeFactor": 1.0,
    #     "hostName": "localhost",
    #     "numberOfThreads": 1,
    #     "numberOfMpi": 1,
    #     "streamingWarning": null,
    #     "streamingSleepOnWait": 0,
    #     "streamingBatchSize": 16,
    #     "inputMicrographs": "3202.outputMicrographs"
    # },
    protSupportBranchCryoloPickingAutocompleted = project.newProtocol(
        SphireProtCRYOLOPicking,
        objLabel="sphire - cryolo picking (autocompleted)",
        useGpu=False,
        conservPickVar=0.3,
        numCpus=16,
        streamingBatchSize=4,
        # inputModelFrom=0,
        # conservPickVar=0.3,
        # lowPassFilter=True,
        # absCutOffFreq=0.1,
        # numCpus=16,
        # input_size=1024,
        # boxSize=0,
        # max_box_per_image=600,
        # useGpu=False,
        # # gpuList="2",
        # boxSizeFactor=1.0,
        # hostName="localhost",
        # numberOfThreads=1,
        # numberOfMpi=1,
        # streamingWarning=None,
        # streamingSleepOnWait=0,
        # streamingBatchSize=16,
    )
    protSupportBranchCryoloPickingAutocompleted._useQueue.set(True)
    protSupportBranchCryoloPickingAutocompleted._queueParams.set(json.dumps(QUEUE_PARAMS_WITHOUT_GPU_16_CPU))
    setExtendedInput(
        protSupportBranchCryoloPickingAutocompleted.inputMicrographs,
        protPreMics,
        "outputMicrographs",
    )
    setExtendedInput(
        protSupportBranchCryoloPickingAutocompleted.boxSize,
        protSupportBranchBoxSize,
        "boxSizeEven",
        pointer=True,
    )
    _registerProt(protSupportBranchCryoloPickingAutocompleted, "Picking")

    # --------- RELION AUTO PICK LOG ----------------------------------
    # {
    #     "object.className": "ProtRelionAutopickLoG",
    #     "object.id": "3288",
    #     "object.label": "relion - auto-picking LoG (autocompleted)",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "3155",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "boxSize": "3155.boxSizeEven",
    #     "minDiameter": "3155.minLoGFilterRelion",
    #     "maxDiameter": "3155.maxLoGFilterRelion",
    #     "areParticlesWhite": false,
    #     "maxResolution": 20.0,
    #     "threshold": 0.0,
    #     "threshold2": 999.0,
    #     "extraParams": "",
    #     "streamingWarning": null,
    #     "streamingSleepOnWait": 0,
    #     "streamingBatchSize": 1,
    #     "hostName": "localhost",
    #     "numberOfMpi": 4,
    #     "inputMicrographs": "3202.outputMicrographs"
    # },
    protSupportBranchRelionAutopickLoG = project.newProtocol(
        ProtRelionAutopickLoG,
        objLabel="relion - auto-picking LoG (autocompleted",
        areParticlesWhite=False,
        maxResolution=20.0,
        threshold=0.0,
        threshold2=999.0,
        extraParams="",
        streamingWarning=None,
        streamingSleepOnWait=0,
        streamingBatchSize=1,
        hostName="localhost",
        numberOfMpi=4,
    )
    setExtendedInput(
        protSupportBranchRelionAutopickLoG.inputMicrographs,
        protPreMics,
        "outputMicrographs",
    )
    setExtendedInput(
        protSupportBranchRelionAutopickLoG.boxSize,
        protSupportBranchBoxSize,
        "boxSizeEven",
        pointer=True,
    )
    setExtendedInput(
        protSupportBranchRelionAutopickLoG.minDiameter,
        protSupportBranchBoxSize,
        "minLoGFilterRelion",
        pointer=True,
    )
    setExtendedInput(
        protSupportBranchRelionAutopickLoG.maxDiameter,
        protSupportBranchBoxSize,
        "maxLoGFilterRelion",
        pointer=True,
    )
    _registerProt(protSupportBranchRelionAutopickLoG, "Picking")

    # --------- GAUTOMATCH ----------------------------------
    # {
    #     "object.className": "ProtGautomatch",
    #     "object.id": "3330",
    #     "object.label": "gautomatch - auto-picking (autocompleted)",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "3155",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "invertTemplatesContrast": true,
    #     "angStep": 5,
    #     "micrographsSelection": 0,
    #     "micrographsNumber": 10,
    #     "threshold": 0.05,
    #     "particleSize": "3155.radiusGautomatch",
    #     "gpuList": "3",
    #     "advanced": false,
    #     "boxSize": "3155.boxSizeEven",
    #     "minDist": "3155.minIntPartDistanceGautomatch",
    #     "speed": 2,
    #     "advLabel": null,
    #     "localSigmaCutoff": 1.2,
    #     "localSigmaDiam": "3155.sigmaDiameterGautomatch",
    #     "localAvgMin": -1.0,
    #     "localAvgMax": 1.0,
    #     "localAvgDiam": "3155.averageDiameterGautomatch",
    #     "lowPass": 30,
    #     "highPass": 1000,
    #     "preFilt": false,
    #     "prelowPass": 8,
    #     "prehighPass": 1000,
    #     "detectIce": true,
    #     "templateNorm": 1,
    #     "doBandpass": true,
    #     "exclusive": false,
    #     "writeCC": false,
    #     "writeFilt": false,
    #     "writeBg": false,
    #     "writeBgSub": false,
    #     "writeSigma": false,
    #     "writeMsk": false,
    #     "streamingWarning": null,
    #     "streamingSleepOnWait": 0,
    #     "streamingBatchSize": 1,
    #     "hostName": "localhost",
    #     "numberOfThreads": 1,
    #     "numberOfMpi": 1,
    #     "inputMicrographs": "3202.outputMicrographs"
    # },
    protSupportBranchGautomatch = project.newProtocol(
        ProtGautomatch,
        objLabel="gautomatch - auto-picking (autocompleted)",
        invertTemplatesContrast=True,
        angStep=5,
        micrographsSelection=0,
        micrographsNumber=10,
        threshold=0.05,
        gpuList="0",
        advanced=False,
        speed=2,
        advLabel=None,
        localSigmaCutoff=1.2,
        localAvgMin=-1.0,
        localAvgMax=1.0,
        lowPass=30,
        highPass=1000,
        preFilt=False,
        prelowPass=8,
        prehighPass=1000,
        detectIce=True,
        templateNorm=1,
        doBandpass=True,
        exclusive=False,
        writeCC=False,
        writeFilt=False,
        writeBg=False,
        writeBgSub=False,
        writeSigma=False,
        writeMsk=False,
        streamingWarning=None,
        streamingSleepOnWait=0,
        streamingBatchSize=1,
        hostName="localhost",
        numberOfThreads=1,
        numberOfMpi=1,
        minDist=300,
    )
    # inputMicrographs = "3202.outputMicrographs"
    setExtendedInput(
        protSupportBranchGautomatch.inputMicrographs,
        protPreMics,
        "outputMicrographs",
    )
    # particleSize = "3155.radiusGautomatch",
    setExtendedInput(
        protSupportBranchGautomatch.particleSize,
        protSupportBranchBoxSize,
        "radiusGautomatch",
        pointer=True,
    )
    # boxSize = "3155.boxSizeEven",
    setExtendedInput(
        protSupportBranchGautomatch.boxSize,
        protSupportBranchBoxSize,
        "boxSizeEven",
        pointer=True,
    )
    # minDist = "3155.minIntPartDistanceGautomatch",
    # setExtendedInput(
    #     protSupportBranchGautomatch.minDist,
    #     protSupportBranchBoxSize,
    #     "minIntPartDistanceGautomatch",
    #     pointer=True,
    # )
    # localSigmaDiam = "3155.sigmaDiameterGautomatch",
    setExtendedInput(
        protSupportBranchGautomatch.localSigmaDiam,
        protSupportBranchBoxSize,
        "sigmaDiameterGautomatch",
        pointer=True,
    )
    # localAvgDiam = "3155.averageDiameterGautomatch",
    setExtendedInput(
        protSupportBranchGautomatch.localAvgDiam,
        protSupportBranchBoxSize,
        "averageDiameterGautomatch",
        pointer=True,
    )
    _registerProt(protSupportBranchGautomatch, "Picking")

    # --------- CRYO EM WORKFLOW VIEWER DEPOSITOR ----------------------------------
    # {
    #     "object.className": "CryoEMWorkflowViewerDepositor",
    #     "object.id": "3404",
    #     "object.label": "datamanager - CryoEM Workflow Viewer deposition",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "apitoken": "c67548969b4036f8f57f926281338ba3a7d8de3e",
    #     "update": false,
    #     "entryid": null,
    #     "entrytitle": "Biennal Conference",
    #     "public": false
    # },

    # --------- CONSENSUS PICKING ----------------------------------
    # {
    #     "object.className": "XmippProtConsensusPicking",
    #     "object.id": "3439",
    #     "object.label": "xmipp3 - picking consensus (n=2, autocompleted)",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "inputCoordinates": [
    #         "3288.outputCoordinates",
    #         "3330.outputCoordinates",
    #         "3241.outputCoordinates"
    #     ],
    #     "consensusRadius": "3155.radiusConsensus",
    #     "consensus": 2,
    #     "mode": 0
    # },
    protSupportBranchConsensusPicking = project.newProtocol(
        XmippProtConsensusPicking,
        objLabel="xmipp3 - picking consensus (n=2, autocompleted)",
        runName=None,
        runMode=0,
        consensus=2,
        mode=0,
    )
    setExtendedInput(
        protSupportBranchConsensusPicking.inputCoordinates,
        [
            protSupportBranchRelionAutopickLoG,
            protSupportBranchGautomatch,
            protSupportBranchCryoloPickingAutocompleted,
        ],
        ["outputCoordinates", "outputCoordinates", "outputCoordinates"],
    )
    setExtendedInput(
        protSupportBranchConsensusPicking.consensusRadius,
        protSupportBranchBoxSize,
        "radiusConsensus",
        pointer=True,
    )
    _registerProt(protSupportBranchConsensusPicking, "Picking")


    # ----------- RELION EXTRACT PARTICLES ---------------------------------
    # {
    #     "object.className": "ProtRelionExtractParticles",
    #     "object.id": "5430",
    #     "object.label": "relion - particles extraction (autocompletion)",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "downsampleType": 0,
    #     "boxSize": "3155.boxSizeExtraction",
    #     "doRescale": false,
    #     "rescaledSize": 128,
    #     "saveFloat16": false,
    #     "doInvert": true,
    #     "doNormalize": true,
    #     "backDiameter": -1,
    #     "stddevWhiteDust": -1.0,
    #     "stddevBlackDust": -1.0,
    #     "streamingWarning": null,
    #     "streamingSleepOnWait": 0,
    #     "streamingBatchSize": 0,
    #     "hostName": "localhost",
    #     "numberOfMpi": 4,
    #     "inputCoordinates": "3439.consensusCoordinates"
    # }
    protSupportBranchRelionExtractParticles = project.newProtocol(
        ProtRelionExtractParticles,
        objLabel="relion - particles extraction (autocompletion)",
        downsampleType=0,
        doRescale=False,
        rescaledSize=128,
        saveFloat16=False,
        doInvert=True,
        doNormalize=True,
        backDiameter=-1,
        stddevWhiteDust=-1.0,
        stddevBlackDust=-1.0,
        streamingWarning=None,
        streamingSleepOnWait=10,
        streamingBatchSize=1,
        hostName="localhost",
        numberOfMpi=1,
        # boxSize=402,
    )
    #  "boxSize": "3155.boxSizeExtraction",
    setExtendedInput(
        protSupportBranchRelionExtractParticles.boxSize,
        protSupportBranchBoxSize,
        "boxSizeExtraction",
        pointer = True
    )
    #     "ctfRelations": "3052.outputCTF",
    setExtendedInput(
        protSupportBranchRelionExtractParticles.ctfRelations,
        protCTFs,
        "outputCTF"
    )
    #  "inputCoordinates": "3439.consensusCoordinates"
    setExtendedInput(
        protSupportBranchRelionExtractParticles.inputCoordinates,
        protSupportBranchConsensusPicking,
        "consensusCoordinates",
    )
    setExtendedInput(
        protSupportBranchRelionExtractParticles.inputMicrographs,
        protPreMics,
        "outputMicrographs"
    )
    _registerProt(protSupportBranchRelionExtractParticles, "Particles")

    # --------- TRIGGER DATA - SEND SIGNAL ----------------------------------
    # {
    #     "object.className": "XmippProtTriggerData",
    #     "object.id": "3610",
    #     "object.label": "xmipp3 - trigger data (send stop signal) ",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "triggerWait": false,
    #     "outputSize": 10000,
    #     "allImages": false,
    #     "splitImages": false,
    #     "triggerSignal": true,
    #     "delay": 4,
    #     "triggerProt": "3202.",
    #     "inputImages": "5430.outputParticles"
    # },
    protSupportBranchTriggerData = project.newProtocol(
        XmippProtTriggerData,
        objLabel="xmipp3 - trigger data (send stop signal)",
        triggerWait=False,
        outputSize=5000,
        allImages=False,
        splitImages=False,
        triggerSignal=True,
        delay=4,
    )
    #     "triggerProt": "3202.",
    # setExtendedInput(
    #     protSupportBranchTriggerData,
    #     protSupportBranchTrigStopSignal,
    #     "triggerProt",
    #     pointer=True
    # )
    # "inputImages": "5430.outputParticles"
    protSupportBranchTriggerData.inputImages.set(protSupportBranchRelionExtractParticles)
    # setExtendedInput(
    #     protSupportBranchTriggerData.inputImages,
    #     protSupportBranchRelionExtractParticles,
    #     "outputParticles",
    # )
    _registerProt(protSupportBranchTriggerData, "CheckPoint")

    # --------- RELION 2D CLASSIFICATION ----------------------------------
    # {
    #     "object.className": "ProtRelionClassify2D",
    #     "object.id": "3649",
    #     "object.label": "relion - 2D classification ",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "isClassify": true,
    #     "is2D": true,
    #     "doContinue": false,
    #     "copyAlignment": false,
    #     "alignmentAsPriors": false,
    #     "fillRandomSubset": true,
    #     "maskDiameterA": -1,
    #     "maskZero": 0,
    #     "continueIter": "last",
    #     "continueMsg": "True",
    #     "doCTF": true,
    #     "haveDataBeenPhaseFlipped": null,
    #     "ignoreCTFUntilFirstPeak": false,
    #     "doCtfManualGroups": false,
    #     "defocusRange": 1000.0,
    #     "numParticles": 10.0,
    #     "numberOfClasses": 50,
    #     "regularisationParamT": 2.0,
    #     "useGradientAlg": false,
    #     "numberOfVDAMBatches": 200,
    #     "centerAvg": true,
    #     "numberOfIterations": 25,
    #     "limitResolEStep": -1.0,
    #     "doImageAlignment": true,
    #     "inplaneAngularSamplingDeg": 6.0,
    #     "offsetSearchRangePix": 5.0,
    #     "offsetSearchStepPix": 1.0,
    #     "allowCoarserSampling": false,
    #     "useParallelDisk": true,
    #     "pooledParticles": 3,
    #     "allParticlesRam": false,
    #     "scratchDir": null,
    #     "combineItersDisc": false,
    #     "doGpu": true,
    #     "gpusToUse": "",
    #     "oversampling": 1,
    #     "extraParams": "",
    #     "hostName": "localhost",
    #     "numberOfThreads": 1,
    #     "numberOfMpi": 3,
    #     "inputParticles": "3610.outputParticles"
    # },
    protSupportBranchRelionClassify2D = project.newProtocol(
        ProtRelionClassify2D,
        objLabel="relion - 2D classification ",
        isClassify=True,
        is2D=True,
        doContinue=False,
        copyAlignment=False,
        alignmentAsPriors=False,
        fillRandomSubset=True,
        maskDiameterA=-1,
        maskZero=0,
        continueIter="last",
        continueMsg="True",
        doCTF=True,
        haveDataBeenPhaseFlipped=None,
        ignoreCTFUntilFirstPeak=False,
        doCtfManualGroups=False,
        defocusRange=1000.0,
        numParticles=10.0,
        numberOfClasses=50,
        regularisationParamT=2.0,
        useGradientAlg=False,
        numberOfVDAMBatches=200,
        centerAvg=True,
        numberOfIterations=25,
        limitResolEStep=-1.0,
        doImageAlignment=True,
        inplaneAngularSamplingDeg=6.0,
        offsetSearchRangePix=5.0,
        offsetSearchStepPix=1.0,
        allowCoarserSampling=False,
        useParallelDisk=True,
        pooledParticles=3,
        allParticlesRam=False,
        scratchDir=None,
        combineItersDisc=False,
        doGpu=True,
        gpusToUse=configDict["relionGpu"],
        oversampling=1,
        extraParams="",
        hostName="localhost",
        numberOfThreads=15,
        numberOfMpi=1,
        inputParticles="3610.outputParticles",
    )
    #     "inputParticles": "3610.outputParticles"
    setExtendedInput(
        protSupportBranchRelionClassify2D.inputParticles,
        protSupportBranchTriggerData,
        "outputParticles",
    )
    _registerProt(protSupportBranchRelionClassify2D, "Classify2D")

    # --------- RELION 2D CLASS RANKER ----------------------------------
    # {
    #     "object.className": "ProtRelionSelectClasses2D",
    #     "object.id": "3723",
    #     "object.label": "relion - 2D class ranker",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "3649",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 1,
    #     "minThreshold": 0.5,
    #     "minParts": -1,
    #     "minCls": -1,
    #     "inputProtocol": "3649."
    # },

    protSupportBranchRelionSelectClasses2D = project.newProtocol(
        ProtRelionSelectClasses2D,
        objLabel="relion - 2D class ranker",
        minThreshold=0.5,
        minParts=-1,
        minCls=-1,
    )
    #     "inputProtocol": "3649."
    setExtendedInput(
        protSupportBranchRelionSelectClasses2D.inputProtocol,
        protSupportBranchRelionClassify2D,
        "outputClasses",
    )
    _registerProt(protSupportBranchRelionSelectClasses2D, "CheckPoint")

    # --------- XMIPP CENTER PARTICLES ----------------------------------
    # {
    #     "object.className": "XmippProtCenterParticles",
    #     "object.id": "3757",
    #     "object.label": "xmipp3 - center particles",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 1,
    #     "hostName": "localhost",
    #     "inputMics": "3202.outputMicrographs",
    #     "inputClasses": "3723.outputClasses"
    # },
    protSupportBranchCenterParticles = project.newProtocol(
        XmippProtCenterParticles,
        objLabel="xmipp3 - center particles",
        hostName="localhost",
        minParts=-1,
        minCls=-1,
    )
    #     "inputMics": "3202.outputMicrographs",
    setExtendedInput(
        protSupportBranchCenterParticles.inputMics,
        protSupportBranchTrigStopSignal,
        "outputMicrographs",
    )
    #     "inputClasses": "3723.outputClasses"
    setExtendedInput(
        protSupportBranchCenterParticles.inputClasses,
        protSupportBranchRelionSelectClasses2D,
        "outputClasses",
    )
    _registerProt(protSupportBranchCenterParticles, "Particle")

    # --------- PWEM EXTRACR COORDINATES COPY 2 ----------------------------------
    # {
    #     "object.className": "ProtExtractCoords",
    #     "object.id": "3790",
    #     "object.label": "pwem - extract coordinates (copy 2)",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 1,
    #     "applyShifts": false,
    #     "hostName": "localhost",
    #     "inputMicrographs": "3202.outputMicrographs",
    #     "inputParticles": "3757.outputParticles"
    # },
    protSupportBranchExtractCoords = project.newProtocol(
        ProtExtractCoords,
        objLabel="pwem - extract coordinates (copy 2)",
        applyShifts=False,
        hostName="localhost",
    )
    #     "inputMicrographs": "3202.outputMicrographs",
    setExtendedInput(
        protSupportBranchExtractCoords.inputMicrographs,
        protSupportBranchTrigStopSignal,
        "outputMicrographs",
    )
    #     "inputParticles": "3757.outputParticles"
    setExtendedInput(
        protSupportBranchExtractCoords.inputParticles,
        protSupportBranchCenterParticles,
        "outputParticles",
    )
    _registerProt(protSupportBranchExtractCoords, "Particle")

    # --------- CRYOLO TRAINING ----------------------------------
    # {
    #     "object.className": "SphireProtCRYOLOTraining",
    #     "object.id": "3824",
    #     "object.label": "sphire - cryolo training ",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 1,
    #     "input_size": 1024,
    #     "boxSize": "3155.boxSizeEven",
    #     "doFineTune": true,
    #     "inputModelFrom": 0,
    #     "numCpus": 4,
    #     "eFlagParam": 10,
    #     "max_box_per_image": 600,
    #     "nb_epochVal": 50,
    #     "learning_rates": 0.0001,
    #     "lowPassFilter": true,
    #     "absCutOffFreq": 0.1,
    #     "batchSize": 4,
    #     "gpuList": "2",
    #     "hostName": "localhost",
    #     "numberOfThreads": 1,
    #     "numberOfMpi": 1,
    #     "inputMicrographs": "3202.outputMicrographs",
    #     "inputCoordinates": "3790.outputCoordinates"
    # },
    protSupportBranchCRYOLOTraining = project.newProtocol(
        SphireProtCRYOLOTraining,
        objLabel="sphire - cryolo training ",
        input_size=1024,
        doFineTune=True,
        inputModelFrom=0,
        numCpus=4,
        eFlagParam=10,
        max_box_per_image=600,
        nb_epochVal=50,
        learning_rates=0.0001,
        lowPassFilter=True,
        absCutOffFreq=0.1,
        batchSize=4,
        gpuList="2",
        hostName="localhost",
        numberOfThreads=1,
        numberOfMpi=1,
    )
    #     "inputMicrographs": "3202.outputMicrographs",
    setExtendedInput(
        protSupportBranchCRYOLOTraining.inputMicrographs,
        protSupportBranchTrigStopSignal,
        "outputMicrographs",
    )
    #     "boxSize": "3155.boxSizeEven",
    setExtendedInput(
        protSupportBranchCRYOLOTraining.boxSize,
        protSupportBranchBoxSize,
        "boxSizeEven",
        pointer=True,
    )
    #     "inputCoordinates": "3790.outputCoordinates"
    setExtendedInput(
        protSupportBranchCRYOLOTraining.inputCoordinates,
        protSupportBranchExtractCoords,
        "outputCoordinates",
    )
    _registerProt(protSupportBranchCRYOLOTraining, "Particle")

    # --------- CRYOLO PICKING ----------------------------------
    # {
    #     "object.className": "SphireProtCRYOLOPicking",
    #     "object.id": "3872",
    #     "object.label": "sphire - cryolo picking (trained model) ",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "3502",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 1,
    #     "inputModelFrom": 2,
    #     "conservPickVar": 0.3,
    #     "lowPassFilter": true,
    #     "absCutOffFreq": 0.1,
    #     "numCpus": 4,
    #     "input_size": 1024,
    #     "boxSize": "3155.boxSizeEven",
    #     "max_box_per_image": 600,
    #     "useGpu": true,
    #     "gpuList": "3",
    #     "boxSizeFactor": 1.0,
    #     "hostName": "localhost",
    #     "numberOfThreads": 1,
    #     "numberOfMpi": 1,
    #     "streamingWarning": null,
    #     "streamingSleepOnWait": 0,
    #     "streamingBatchSize": 16,
    #     "inputMicrographs": "3052.outputMicrographs",
    #     "inputModel": "3824.outputModel"
    # },
    protSupportBranchCRYOLOPicking = project.newProtocol(
        SphireProtCRYOLOPicking,
        objLabel="sphire - cryolo picking (trained model) ",
        inputModelFrom=2,
        conservPickVar=0.3,
        lowPassFilter=True,
        absCutOffFreq=0.1,
        numCpus=4,
        input_size=1024,
        max_box_per_image=600,
        useGpu=True,
        gpuList="3",
        boxSizeFactor=1.0,
        hostName="localhost",
        numberOfThreads=1,
        numberOfMpi=1,
        streamingWarning=None,
        streamingSleepOnWait=0,
        streamingBatchSize=16,
    )
    #     "inputMicrographs": "3052.outputMicrographs",
    setExtendedInput(
        protSupportBranchCRYOLOPicking.inputMicrographs, protCTFs, "outputMicrographs"
    )
    #     "boxSize": "3155.boxSizeEven",
    setExtendedInput(
        protSupportBranchCRYOLOPicking.boxSize,
        protSupportBranchBoxSize,
        "boxSizeEven",
        pointer=True,
    )
    #     "inputModel": "3824.outputModel"
    setExtendedInput(
        protSupportBranchCRYOLOPicking.inputModel,
        protSupportBranchCRYOLOTraining,
        "outputModel",
    )
    _registerProt(protSupportBranchCRYOLOPicking, "Particle")

    # --------- RELION EXTRACT PARTICLES ----------------------------------
    # {
    #     "object.className": "ProtRelionExtractParticles",
    #     "object.id": "3919",
    #     "object.label": "relion - particles extraction",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 1,
    #     "downsampleType": 0,
    #     "boxSize": "3155.boxSizeExtraction",
    #     "doRescale": false,
    #     "rescaledSize": 128,
    #     "saveFloat16": false,
    #     "doInvert": false,
    #     "doNormalize": true,
    #     "backDiameter": -1,
    #     "stddevWhiteDust": -1.0,
    #     "stddevBlackDust": -1.0,
    #     "streamingWarning": null,
    #     "streamingSleepOnWait": 0,
    #     "streamingBatchSize": 0,
    #     "hostName": "localhost",
    #     "numberOfMpi": 4,
    #     "ctfRelations": "3052.outputCTF",
    #     "inputCoordinates": "3872.outputCoordinates"
    # },
    protSupportBranchRelionExtractParticles2 = project.newProtocol(
        ProtRelionExtractParticles,
        objLabel="relion - particles extraction",
        downsampleType=0,
        doRescale=False,
        rescaledSize=128,
        saveFloat16=False,
        doInvert=True,
        doNormalize=True,
        backDiameter=-1,
        stddevWhiteDust=-1.0,
        stddevBlackDust=-1.0,
        streamingWarning=None,
        streamingSleepOnWait=0,
        streamingBatchSize=0,
        hostName="localhost",
        numberOfMpi=4,
    )
    #     "boxSize": "3155.boxSizeExtraction",
    setExtendedInput(
        protSupportBranchRelionExtractParticles2.boxSize,
        protSupportBranchBoxSize,
        "boxSizeExtraction",
        pointer=True,
    )
    #     "ctfRelations": "3052.outputCTF",
    setExtendedInput(
        protSupportBranchRelionExtractParticles2.ctfRelations, protCTFs, "outputCTF"
    )
    #     "inputCoordinates": "3872.outputCoordinates"
    setExtendedInput(
        protSupportBranchRelionExtractParticles2.inputCoordinates,
        protSupportBranchCRYOLOPicking,
        "outputCoordinates",
    )
    _registerProt(protSupportBranchRelionExtractParticles2, "Particles")

    # --------- CLASSES SELECTOR ----------------------------------
    # {
    #     "object.className": "ProtClassesSelector",
    #     "object.id": "3967",
    #     "object.label": "pwem - numeric classes extractor (SetAverages) ",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 1,
    #     "extractRepresentative": true,
    #     "firstNElements": 100,
    #     "inputClasses": "3649.outputClasses"
    # },
    protSupportBranchClassesSelector = project.newProtocol(
        ProtClassesSelector,
        objLabel="pwem - numeric classes extractor (SetAverages) ",
        extractRepresentative=True,
        firstNElements=100,
    )
    #     "inputClasses": "3649.outputClasses"
    setExtendedInput(
        protSupportBranchClassesSelector.inputClasses,
        protSupportBranchRelionClassify2D,
        "outputClasses",
    )
    _registerProt(protSupportBranchClassesSelector, "Classes")

    # --------- XMIPP GPU CRR SIMPLE ----------------------------------
    # {
    #     "object.className": "XmippProtStrGpuCrrSimple",
    #     "object.id": "4000",
    #     "object.label": "xmipp3 - gl2d static",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 1,
    #     "gpuList": "2",
    #     "maxShift": 10,
    #     "keepBest": 1,
    #     "inputParticles": "3919.outputParticles",
    #     "inputRefs": "3967.output"
    # },
    protSupportBranchStrGpuCrrSimple = project.newProtocol(
        XmippProtStrGpuCrrSimple,
        objLabel="xmipp3 - gl2d static",
        gpuList="2",
        maxShift=10,
        keepBest=1,
    )
    #     "inputParticles": "3919.outputParticles",
    setExtendedInput(
        protSupportBranchStrGpuCrrSimple.inputParticles,
        protSupportBranchRelionExtractParticles2,
        "outputClasses",
    )
    #     "inputRefs": "3967.output"
    setExtendedInput(
        protSupportBranchStrGpuCrrSimple.inputRefs,
        protSupportBranchClassesSelector,
        "output",
    )
    _registerProt(protSupportBranchStrGpuCrrSimple, "Classes")

    # --------- SUMMARY ----------------------------------
    # {
    #     "object.className": "ProtMonitorSummary",
    #     "object.id": "4366",
    #     "object.label": "emfacilities - monitor summary ",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "inputProtocols": [
    #         "2699",
    #         "2854",
    #         "2927"
    #     ],
    #     "samplingInterval": 60,
    #     "stddevValue": 0.04,
    #     "ratio1Value": 1.15,
    #     "ratio2Value": 4.5,
    #     "maxDefocus": 40000.0,
    #     "minDefocus": 1000.0,
    #     "astigmatism": 1000.0,
    #     "monitorTime": 30000.0,
    #     "cpuAlert": 101.0,
    #     "memAlert": 101.0,
    #     "swapAlert": 101.0,
    #     "doGpu": false,
    #     "gpusToUse": "0",
    #     "doNetwork": false,
    #     "netInterfaces": 1,
    #     "doDiskIO": false,
    #     "doMail": false,
    #     "emailFrom": "from@from.fakeadress.com",
    #     "emailTo": "to@to.fakeadress.com",
    #     "smtp": "smtp.fakeadress.com",
    #     "doInflux": false,
    #     "publishCmd": ""
    # },
