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
    )
#                                  XmippProtDeepMicrographScreen)
except Exception as exc:
    raise
    pwutils.pluginNotFound("xmipp", errorMsg=exc, doRaise=True)

from motioncorr.protocols import ProtMotionCorr
from gctf.protocols import ProtGctf

from esrf.protocols import ProtMonitorISPyB_ESRF

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
        fileTimeout=30,
        timeout=timeout,
    )
    _registerProt(protImport, label="Movies", toSummary=True)
    ispybUploads.append(protImport)

    # Stop here if --onlyISPyB
    # --------- ISPyB MONITOR -----------------------
    if not config_dict["noISPyB"]:
        ispybMonitor = project.newProtocol(
            ProtMonitorISPyB_ESRF,
            objLabel="ISPyB monitor",
            samplingInterval=10,
            proposal=config_dict["proposal"],
            proteinAcronym=config_dict["proteinAcronym"],
            sampleAcronym=config_dict["sampleAcronym"],
            db=config_dict["db"],
            allParamsJsonFile=config_dict["allParamsJsonFile"],
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
            particleSize=config_dict["partSize"],
            doProcessDir=config_dict["doProcessDir"],
        )
        ispybMonitor.inputProtocols.set(ispybUploads)
        _registerProt(ispybMonitor, "ispybMonitor")

