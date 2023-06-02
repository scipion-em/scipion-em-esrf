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
import random

from collections import OrderedDict
from pwem.protocols import ProtImportMovies
from motioncorr.protocols import ProtMotionCorr
from gctf.protocols import ProtGctf
from tomo.protocols.protocol_compose_TS import ProtComposeTS
from aretomo.protocols import ProtAreTomoAlignRecon

from pyworkflow.object import Pointer
from pyworkflow.project.manager import Manager

# Xmipp plugin is mandatory to run this workflow
from xmipp3.protocols import XmippProtCTFMicrographs


from esrf.protocols import ProtMonitorIcatTomo

QUEUE_PARAMS_WITH_1_GPU_4_CPU = (
    "cm-gpu",
    {
        "JOB_TIME": "24",  # in hours
        "JOB_MEMORY": "100000",  # in Mb
        "QUEUE_FOR_JOBS": "N",
        "JOB_GPU": "--gres=gpu:1",
        "JOB_THREADS": 4,
    },
)

QUEUE_PARAMS_WITH_1_GPU_15_CPU = (
    "cm-gpu",
    {
        "JOB_TIME": "24",  # in hours
        "JOB_MEMORY": "100000",  # in Mb
        "QUEUE_FOR_JOBS": "N",
        "JOB_GPU": "--gres=gpu:1",
        "JOB_THREADS": 15,
    },
)

QUEUE_PARAMS_WITH_2_GPU_16_CPU = (
    "cm-gpu",
    {
        "JOB_TIME": "24",  # in hours
        "JOB_MEMORY": "100000",  # in Mb
        "QUEUE_FOR_JOBS": "N",
        "JOB_GPU": "--gres=gpu:2",
        "JOB_THREADS": 16,
    },
)

QUEUE_PARAMS_WITHOUT_GPU_16_CPU = (
    "mx",
    {
        "JOB_TIME": "24",  # in hours
        "JOB_MEMORY": "50000",  # in Mb
        "QUEUE_FOR_JOBS": "N",
        "JOB_GPU": "",
        "JOB_THREADS": 16,
    },
)


def getNewScipionProjectName(scipionProjectName, index):
    return "{0}_{1}".format(scipionProjectName, index)


def preprocessWorkflow(config_dict):
    scipionProjectName = config_dict["scipionProjectName"]
    location = config_dict["location"]

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
        if all(label_key != labelName for label_key in labelsDict.keys()):
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

    # def setBoxSize(protDotBoxSize):
    #     if protPrePick:
    #         setExtendedInput(protDotBoxSize, protPrePick, "boxsize", True)
    #     else:
    #         protDotBoxSize.set(bxSize)

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

    timeout = 43200  # 12 hours

    protImport = project.newProtocol(
        ProtImportMovies,
        objLabel="Import movies",
        importFrom=ProtImportMovies.IMPORT_FROM_FILES,
        filesPath=config_dict["dataDirectory"],
        filesPattern=config_dict["filesPattern"],
        amplitudeContrast=0.1,
        sphericalAberration=config_dict["sphericalAberration"],
        voltage=config_dict["voltage"] / 1000.0,
        samplingRate=config_dict["samplingRate"],
        doseInitial=config_dict["doseInitial"],
        dosePerFrame=config_dict["dosePerFrame"],
        magnification=config_dict["magnification"],
        dataStreaming=config_dict["dataStreaming"],
        blacklistFile=config_dict["blacklistFile"],
        useRegexps=False,
        gainFile=config_dict["gainFilePath"],
        fileTimeout=30,
        timeout=timeout,
    )
    _registerProt(protImport, label="Movies", toSummary=True)
    ispybUploads.append(protImport)

    # Stop here if --onlyICAT
    if not config_dict["onlyICAT"]:
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
            gpuList=config_dict["motioncor2Gpu"],
            numberOfThreads=config_dict["motioncor2Cpu"],
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
            gainFlip=config_dict["gainFlip"],
            gainRot=config_dict["gainRot"],
            alignFrame0=config_dict["alignFrame0"],
            alignFrameN=config_dict["alignFrameN"],
            binFactor=config_dict["binFactor"],
            extraParams2=config_dict["extraParams2"],
        )
        setExtendedInput(protMA.inputMovies, protImport, "outputMovies")
        _registerProt(protMA, "MotionCorr")
        ispybUploads.append(protMA)

        # ----------- GCTF ----------------------------
        protCTF2 = project.newProtocol(
            ProtGctf,
            objLabel="gCTF estimation",
            gpuList=config_dict["gctfGpu"],
            lowRes=config_dict["lowRes"],
            plotResRing=True,
            doEPA=False,
            doHighRes=True,
            convsize=config_dict["convsize"],
            highRes=config_dict["highRes"],
            minDefocus=config_dict["minDefocus"],
            maxDefocus=config_dict["maxDefocus"],
            astigmatism=config_dict["astigmatism"],
            doPhShEst=config_dict["doPhShEst"],
            phaseShiftL=config_dict["phaseShiftL"],
            phaseShiftH=config_dict["phaseShiftH"],
            phaseShiftS=config_dict["phaseShiftS"],
            phaseShiftT=config_dict["phaseShiftT"],
        )
        setExtendedInput(
            protCTF2.inputMicrographs, protMA, "outputMicrographsDoseWeighted"
        )
        _registerProt(protCTF2, "CTF")
        ispybUploads.append(protCTF2)

    # {
    #     "object.className": "ProtComposeTS",
    #     "object.id": "201",
    #     "object.label": "tomo - Compose Tilt Serie",
    #     "object.comment": "",
    #     "_useQueue": false,
    #     "_prerequisites": "",
    #     "_queueParams": null,
    #     "runName": null,
    #     "runMode": 0,
    #     "filesPath": "/data/visitor/mx2112/cm01/20230417/RAW_DATA/grid1_1",
    #     "mdoc_bug_Correction": false,
    #     "dataStreaming": true,
    #     "time4NextTilt": 180,
    #     "time4NextMic": 12,
    #     "time4NextTS": 1800,
    #     "hostName": "localhost",
    #     "numberOfThreads": 3,
    #     "numberOfMpi": 1,
    #     "inputMicrographs": "66.outputMicrographsDoseWeighted"
    # }

    # ----------- Prot Compose Time-Series ----------------------------
    protComposeTS = project.newProtocol(
        ProtComposeTS,
        objLabel="tomo - Compose Tilt Serie",
        filesPath=config_dict["dataDirectory"],
        mdoc_bug_Correction=False,
        dataStreaming=True,
        time4NextTilt=180,
        time4NextMic=12,
        time4NextTS=1800,
        hostName="localhost",
        numberOfThreads=3,
        numberOfMpi=1,
    )
    setExtendedInput(
        protComposeTS.inputMicrographs, protMA, "outputMicrographsDoseWeighted"
    )
    _registerProt(protComposeTS, "ComposeTs")
    # ispybUploads.append(protComposeTS)

    # -------- Prot AreTomo tilt series align ----------------
    # {
    #         "object.className": "ProtAreTomoAlignRecon",
    #         "object.id": "406",
    #         "object.label": "aretomo - tilt-series align and reconstruct",
    #         "object.comment": "",
    #         "_useQueue": false,
    #         "_prerequisites": "",
    #         "_queueParams": null,
    #         "runName": null,
    #         "runMode": 0,
    #         "tiltAxisAngle": 0.0,
    #         "skipAlign": false,
    #         "makeTomo": false,
    #         "saveStack": true,
    #         "useInputProt": false,
    #         "binFactor": 2,
    #         "alignZ": 800,
    #         "tomoThickness": 1200,
    #         "refineTiltAngles": 1,
    #         "refineTiltAxis": 1,
    #         "doDW": false,
    #         "reconMethod": 0,
    #         "SARTiter": 15,
    #         "SARTproj": 5,
    #         "flipInt": false,
    #         "flipVol": true,
    #         "roiArea": "",
    #         "sampleType": 0,
    #         "coordsFn": "",
    #         "patchX": 5,
    #         "patchY": 5,
    #         "darkTol": 0.7,
    #         "extraParams": "",
    #         "gpuList": "0",
    #         "inputSetOfTiltSeries": "201.TiltSeries"
    #     }
    protAreTomoAlignRecon = project.newProtocol(
        ProtAreTomoAlignRecon,
        objLabel="aretomo - tilt-series align",
        filesPath=config_dict["dataDirectory"],
        skipAlign=False,
        makeTomo=False,
    )
    setExtendedInput(
        protAreTomoAlignRecon.inputSetOfTiltSeries, protComposeTS, "TiltSeries"
    )
    _registerProt(protAreTomoAlignRecon, "ComposeTs")
    # ispybUploads.append(protComposeTS)

    # --------- ISPyB MONITOR -----------------------
    if not config_dict["noICAT"]:
        icat_tomo_monitor = project.newProtocol(
            ProtMonitorIcatTomo,
            objLabel="ICAT Tomo monitor",
            samplingInterval=10,
            proposal=config_dict["proposal"],
            proteinAcronym=config_dict["proteinAcronym"],
            sampleAcronym=config_dict["sampleAcronym"],
            db=config_dict["db"],
            all_params_json_file=config_dict["all_params_json_file"],
            samplingRate=config_dict["samplingRate"],
            doseInitial=config_dict["doseInitial"],
            dosePerFrame=config_dict["dosePerFrame"],
            dataType=config_dict["dataType"],
            voltage=config_dict["voltage"],
            imagesCount=config_dict["imagesCount"],
            magnification=config_dict["magnification"],
            alignFrame0=config_dict["alignFrame0"],
            alignFrameN=config_dict["alignFrameN"],
            defectMapPath=config_dict["defectMapPath"],
            gainFilePath=config_dict["gainFilePath"],
        )
        icat_tomo_monitor.inputProtocols.set(ispybUploads)
        _registerProt(icat_tomo_monitor, "icatTomoMonitor")
