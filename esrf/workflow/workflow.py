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
import random
from collections import OrderedDict

from pwem.protocols import ProtImportMovies
from pwem.protocols import ProtUnionSet
# from pwem.protocols import ProtMonitorSummary
from esrf.protocols import ProtMonitorISPyB_ESRF

from pyworkflow.object import Pointer
import pyworkflow.utils as pwutils

from pyworkflow.project.manager import Manager
from pyworkflow.project import Project
from pyworkflow.protocol import getProtocolFromDb
import json


try:  # Xmipp plugin is mandatory to run this workflow
    from xmipp3.protocols import (XmippProtOFAlignment, XmippProtMovieGain,
                                  XmippProtMovieMaxShift, XmippProtCTFMicrographs,
                                  XmippProtMovieCorr, XmippProtCTFConsensus,
                                  XmippProtPreprocessMicrographs, XmippProtParticleBoxsize,
                                  XmippProtParticlePicking, XmippParticlePickingAutomatic,
                                  XmippProtConsensusPicking, XmippProtCL2D,
                                  XmippProtExtractParticles, XmippProtTriggerData,
                                  XmippProtEliminateEmptyParticles,
                                  XmippProtScreenParticles,
                                  XmippProtReconstructSignificant, XmippProtRansac,
                                  XmippProtAlignVolume, XmippProtReconstructSwarm,
                                  XmippProtStrGpuCrrSimple, XmippProtGpuCrrCL2D,
                                  XmippProtCropResizeVolumes, XmippProtEliminateEmptyClasses)
#                                  XmippProtDeepMicrographScreen)
except Exception as exc:
    raise
    pwutils.pluginNotFound('xmipp', errorMsg=exc, doRaise=True)

protPlugins = {'ProtMotionCorr': 'motioncorr.protocols',
               'ProtCTFFind': 'grigoriefflab.protocols',
               'ProtGctf': 'gctf.protocols',
               'DogPickerProtPicking': 'appion.protocols',
               'SparxGaussianProtPicking': 'eman2.protocols',
               'EmanProtInitModel': 'eman2.protocols',
               'SphireProtCRYOLOPicking': 'sphire.protocols',
               'ProtRelion2Autopick': 'relion.protocols',
               'ProtRelionAutopickLoG': 'relion.protocols',
               'ProtRelionExtractParticles': 'relion.protocols',
               'ProtRelionClassify2D': 'relion.protocols',
               'ProtRelionRefine3D': 'relion.protocols',
               'ProtRelionClassify3D': 'relion.protocols',
               # 'ProtCryo2D': 'cryosparc2.protocols',
               # 'ProtCryoSparcInitialModel': 'cryosparc2.protocols'
               }

from motioncorr.protocols import ProtMotionCorr
from cistem.protocols import CistemProtCTFFind
from gctf.protocols import ProtGctf
from sphire.protocols import SphireProtCRYOLOPicking
from relion.protocols import ProtRelionAutopickLoG
from relion.protocols import ProtRelionClassify2D
from relion.protocols import ProtRelionExtractParticles
from emfacilities.protocols import ProtMonitorSummary

from pwem.protocols.protocol_import import ProtImportParticles

QUEUE_PARAMS_WITH_1_GPU_4_CPU = ('gpu', {'JOB_TIME': '150',  # in hours
                                 'JOB_MEMORY': '100000',  # in Mb
                                 'QUEUE_FOR_JOBS': 'N',
                                 'JOB_GPU': '--gres=gpu:1',
                                 'JOB_THREADS': 4})

QUEUE_PARAMS_WITH_1_GPU_15_CPU = ('gpu', {'JOB_TIME': '150',  # in hours
                                 'JOB_MEMORY': '100000',  # in Mb
                                 'QUEUE_FOR_JOBS': 'N',
                                 'JOB_GPU': '--gres=gpu:1',
                                 'JOB_THREADS': 15})

QUEUE_PARAMS_WITH_2_GPU_16_CPU = ('gpu', {'JOB_TIME': '150',  # in hours
                                 'JOB_MEMORY': '100000',  # in Mb
                                 'QUEUE_FOR_JOBS': 'N',
                                 'JOB_GPU': '--gres=gpu:2',
                                 'JOB_THREADS': 16})

QUEUE_PARAMS_WITHOUT_GPU = ('gpu', {'JOB_TIME': '150',  # in hours
                                     'JOB_MEMORY': '100000',  # in Mb
                                     'QUEUE_FOR_JOBS': 'N',
                                     'JOB_GPU': '',
                                     'JOB_THREADS': 1})

def getNewScipionProjectName(scipionProjectName, index):
    return "{0}_{1}".format(scipionProjectName, index)


def importPlugin(protocol):
    if protocol not in protPlugins:
        raise Exception("'%s' protocol from plugin not found. Please, "
                        "include it at the available protocol list.\n"
                        "(at the beginning of %s)"
                        % (protocol, os.path.abspath(__file__)))
    return pwutils.importFromPlugin(protPlugins[protocol], protocol,
                                    doRaise=True)


def preprocessWorkflow(configDict):
    scipionProjectName = configDict["scipionProjectName"]
    location = configDict["location"]

    # Create a new project
    manager = Manager()

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

    def _registerProt(prot, label='', toSummary=False, color=''):
        project.saveProtocol(prot)
        if label != '':
            applyLabel(prot, label, color)
        if toSummary:
            summaryList.append(prot)

    def applyLabel(prot, labelName, color=''):
        if all(l != labelName for l in labelsDict.keys()):
            if color == '':
                if len(colorsDict) < 9:
                    color = colorsDef[len(colorsDict)]
                else:
                    color = "#%s" % ''.join([random.choice('0123456789abcdef')
                                             for j in range(6)])
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
        """ Fixing an even partSize big enough:
            int(x / 2 + 1) * 2 = ceil(x / 2) * 2 = even!
        """
        return int(partSize / 2 + 1) * 2

    def setBoxSize(protDotBoxSize):
        if protPrePick:
            setExtendedInput(protDotBoxSize, protPrePick, 'boxsize', True)
        else:
            protDotBoxSize.set(bxSize)

    # projectLocation = os.path.join(location, scipionProjectName)
    # if not os.path.exists(projectLocation):
    #     os.makedirs(projectLocation, 0o755)
    # os.chdir(projectLocation)
    # project = manager.createProject(scipionProjectName, location=os.path.abspath(location))

    project = manager.createProject(scipionProjectName, location=location)

    labelsDict = OrderedDict()  # key: labelName ; value: [prot1, prot2, prot3...])
    colorsDict = OrderedDict()  # key: labelName ; value: colorRGB
    random.seed(6)
    colorsDef = ["#e57373", "#4fc3f7", "#81c784", "#ff8a65", "#9575cd",
                 "#a1887f", "#ffd54f", "#dce775", "#4db6ac"]
    summaryList = []
    ispybUploads = []

    if configDict["secondGrid"]:
        timeout = 295200 # 72 hours
    else:
        timeout = 43200 # 12 hours

    protImport = project.newProtocol(ProtImportMovies,
                                     objLabel='Import movies',
                                     importFrom=ProtImportMovies.IMPORT_FROM_FILES,
                                     filesPath=configDict["dataDirectory"],
                                     filesPattern=configDict["filesPattern"],
                                     amplitudeContrast=0.1,
                                     sphericalAberration=configDict["sphericalAberration"],
                                     voltage=configDict["voltage"]/1000.0,
                                     samplingRate=configDict["samplingRate"],
                                     doseInitial=configDict["doseInitial"],
                                     dosePerFrame=configDict["dosePerFrame"],
                                     magnification=configDict["magnification"],
                                     dataStreaming=configDict["dataStreaming"],
                                     blacklistFile=configDict["blacklistFile"],
                                     useRegexps=False,
                                     gainFile=configDict["gainFilePath"],
                                     fileTimeout=30,
                                     timeout=timeout)
    _registerProt(protImport, label='Movies', toSummary=True)
    ispybUploads.append(protImport)

    # ----------- MOTIONCOR ----------------------------
    protMA = project.newProtocol(ProtMotionCorr,
                                 objLabel='MotionCor2 - movie align.',
                                 gpuList=configDict["motioncor2Gpu"],
                                 numberOfThreads=configDict["motioncor2Cpu"],
                                 numberOfMpi=1,
                                 doApplyDoseFilter=True,
                                 doSaveUnweightedMic=True,
                                 doSaveAveMic=True,
                                 doSaveMovie=False,
                                 doComputeMicThumbnail=True,
                                 computeAllFramesAvg=False,
                                 patchX=5, patchY=5,
                                 useEst=True,
                                 gainFlip=configDict["gainFlip"],
                                 gainRot=configDict["gainRot"],
                                 alignFrame0=configDict["alignFrame0"],
                                 alignFrameN=configDict["alignFrameN"],
                                 binFactor=configDict["binFactor"],
                                 extraParams2=configDict["extraParams2"])
    setExtendedInput(protMA.inputMovies, protImport, 'outputMovies')
    _registerProt(protMA, 'Movies')
    ispybUploads.append(protMA)
    #
    # # ----------- MAX SHIFT -----------------------------
    # protMax = project.newProtocol(XmippProtMovieMaxShift,
    #                               objLabel='Xmipp - max shift')
    # setExtendedInput(protMax.inputMovies, protMA, 'outputMovies')
    # _registerProt(protMax, 'Movies', True)
    # ispybUploads.append(protMax)

    protCTF2 = project.newProtocol(ProtGctf,
                                   objLabel='gCTF estimation',
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
    setExtendedInput(protCTF2.inputMicrographs,
                     protMA, 'outputMicrographsDoseWeighted')
    _registerProt(protCTF2, 'CTF')
    ispybUploads.append(protCTF2)

    #
    # # --------- CTF ESTIMATION 1 ---------------------------
    protCTF1 = project.newProtocol(CistemProtCTFFind,
                                   objLabel='Cistem - CTFfind',
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
    setExtendedInput(protCTF1.inputMicrographs,
                     protMA, 'outputMicrographsDoseWeighted')
    _registerProt(protCTF1, 'CTF')
    #
    # # --------- CTF CONSENSUS ---------------------------
    isCtf2Xmipp = isinstance(protCTF2, XmippProtCTFMicrographs)
    protCTFs = project.newProtocol(XmippProtCTFConsensus,
                                   objLabel='Xmipp - CTF consensus',
                                   useDefocus=True,
                                   useAstigmatism=True,
                                   useResolution=True,
                                   resolution=7,
                                   useCritXmipp=isCtf2Xmipp,
                                   calculateConsensus=True,
                                   minConsResol=7)
    setExtendedInput(protCTFs.inputCTF, protCTF2, 'outputCTF')
    setExtendedInput(protCTFs.inputCTF2, protCTF1, 'outputCTF')
    _registerProt(protCTFs, 'CTF', True)

    # # *************   PICKING   ********************************************

    pickers = []
    pickersOuts = []

    # # --------- PREPROCESS MICS ---------------------------
    protPreMics0 = project.newProtocol(XmippProtPreprocessMicrographs,
                                       objLabel='Xmipp - preprocess Mics',
                                       doRemoveBadPix=True,
                                       doInvert=False)
    setExtendedInput(protPreMics0.inputMicrographs,
                     protCTFs, 'outputMicrographs')
    _registerProt(protPreMics0, 'Micrographs')

    # # Resizing to a larger sampling rate
    doDownSamp2D = 0 < configDict["sampling2D"] > configDict["samplingRate"]
    samp2D = configDict["sampling2D"] if doDownSamp2D else configDict["samplingRate"]
    if doDownSamp2D:
        downSampPreMics = configDict["sampling2D"] / ( configDict["samplingRate"] * configDict["binFactor"])
        protPreMics = project.newProtocol(XmippProtPreprocessMicrographs,
                                          objLabel='downSampling to 2D size',
                                          doDownsample=True,
                                          downFactor=downSampPreMics)
        setExtendedInput(protPreMics.inputMicrographs,
                         protPreMics0, 'outputMicrographs')
        _registerProt(protPreMics, 'Micrographs')
    else:
        # downSampPreMics = 1
        protPreMics = protPreMics0

    # # -------- XMIPP AUTO-BOXSIZE -------------------------
    waitManualPick = False
    protPrePick = None
    # protPrePick = project.newProtocol(XmippProtParticleBoxsize,
    #                                   objLabel='Xmipp - particle boxsize')
    # setExtendedInput(protPrePick.inputMicrographs,
    #                  protCTFs, 'outputMicrographs')
    # _registerProt(protPrePick, 'Picking')
    bxSize = getEvenPartSize(configDict["partSize"]/samp2D)

    protPP2 = project.newProtocol(SphireProtCRYOLOPicking,
                                  objLabel='Sphire - CrYolo auto-picking',
                                  useGpu=False,
                                  conservPickVar=0.3,
                                  numCpus=16,
                                  streamingBatchSize=4)  # CPU version installation
    # protPP2._useQueue.set(True)
    # protPP2._queueParams.set(json.dumps(QUEUE_PARAMS_WITH_1_GPU_4_CPU))
    setBoxSize(protPP2.boxSize)
    setExtendedInput(protPP2.inputMicrographs, protPreMics, 'outputMicrographs')
    if waitManualPick:
        protPP2.addPrerequisites(protPrePick.getObjId())
    _registerProt(protPP2, 'Picking')

    pickers.append(protPP2)
    pickersOuts.append('outputCoordinates')

    # protPP4 = project.newProtocol(ProtRelionAutopickLoG,
    #                               objLabel='Relion - LoG auto-picking',
    #                               conservPickVar=0.3,
    #                               minDiameter=configDict["partSize"] * 0.8,
    #                               maxDiameter=configDict["partSize"] * 1.2,
    #                               maxResolution=20,
    #                               threshold=0.0,
    #                               streamingBatchSize=4)
    # protPP4._useQueue.set(True)
    # protPP4._queueParams.set(json.dumps(QUEUE_PARAMS_WITHOUT_GPU))
    # setBoxSize(protPP4.boxSize)
    # setExtendedInput(protPP4.inputMicrographs, protPreMics, 'outputMicrographs')
    # if waitManualPick:
    #     protPP4.addPrerequisites(protPrePick.getObjId())
    # _registerProt(protPP4, 'Picking')
    #
    # pickers.append(protPP4)
    # pickersOuts.append('outputCoordinates')

    # # --------- CONSENSUS PICKING -----------------------

    consRadius = int(bxSize / 3) if bxSize else 10
    protCPand = project.newProtocol(XmippProtConsensusPicking,
                                    objLabel='Xmipp - consensus picking (AND)',
                                    consensusRadius=consRadius,
                                    consensus=-1)
    setExtendedInput(protCPand.inputCoordinates, pickers, pickersOuts)
    _registerProt(protCPand, 'Picking', True)

    finalPicker = protCPand
    outputCoordsStr = 'consensusCoordinates'
    outCPor = 'consensusCoordinates'

    extracBoxSize = getEvenPartSize(bxSize * 1.25)

    # protExtractFlip = project.newProtocol(XmippProtExtractParticles,
    #                                      objLabel='Xmipp - extract particles - flip',
    #                                      boxSize=extracBoxSize,
    #                                      downsampleType=1,  # Other to avoid a bug
    #                                      doRemoveDust=True,
    #                                      doNormalize=True,
    #                                      doInvert=True,
    #                                      doFlip=True)
    # setExtendedInput(protExtractFlip.inputCoordinates, finalPicker, outputCoordsStr)
    # setExtendedInput(protExtractFlip.inputMicrographs,
    #                  protPreMics, 'outputMicrographs')
    # setExtendedInput(protExtractFlip.ctfRelations, protCTFs, 'outputCTF')
    # _registerProt(protExtractFlip, 'Particles')

    # protExtractNoFlip = project.newProtocol(XmippProtExtractParticles,
    #                                         objLabel='Xmipp - extract particles - no flip',
    #                                         boxSize=extracBoxSize,
    #                                         downsampleType=1,  # Other to avoid a bug
    #                                         doRemoveDust=True,
    #                                         doNormalize=True,
    #                                         doInvert=True,
    #                                         doFlip=False)
    # setExtendedInput(protExtractNoFlip.inputCoordinates, finalPicker, outputCoordsStr)
    # setExtendedInput(protExtractNoFlip.inputMicrographs,
    #                  protPreMics, 'outputMicrographs')
    # setExtendedInput(protExtractNoFlip.ctfRelations, protCTFs, 'outputCTF')
    # _registerProt(protExtractNoFlip, 'Particles')

    protExtractNoFlip = project.newProtocol(ProtRelionExtractParticles,
                                   objLabel='Relion - extract particles',
                                   boxSize=extracBoxSize,
                                   doInvert=True,
                                   numberOfMpi=1)
    setExtendedInput(protExtractNoFlip.inputCoordinates, finalPicker, outputCoordsStr)
    setExtendedInput(protExtractNoFlip.inputMicrographs,
                     protPreMics, 'outputMicrographs')
    setExtendedInput(protExtractNoFlip.ctfRelations, protCTFs, 'outputCTF')
    _registerProt(protExtractNoFlip, 'Particles')


    if configDict["particleElimination"]:
        # ***********   CLEAN PARTICLES   ************************************
        # --------- ELIM EMPTY PARTS AND ---------------------------
        # protEEPandFlip = project.newProtocol(XmippProtEliminateEmptyParticles,
        #                                  objLabel='Xmipp - Elim. empty part. - flip',
        #                                  threshold=0.6)
        # setExtendedInput(protEEPandFlip.inputParticles, protExtractFlip, 'outputParticles')
        # _registerProt(protEEPandFlip, 'Particles')

        protEEPandNoFlip = project.newProtocol(XmippProtEliminateEmptyParticles,
                                         objLabel='Xmipp - Elim. empty part. - no flip',
                                         threshold=0.6)
        setExtendedInput(protEEPandNoFlip.inputParticles, protExtractNoFlip, 'outputParticles')
        _registerProt(protEEPandNoFlip, 'Particles')

        # --------- TRIGGER PARTS AND ---------------------------
        # protTRIGandFlip = project.newProtocol(XmippProtTriggerData,
        #                                   objLabel='Xmipp - trigger data to stats - flip',
        #                                   outputSize=1000, delay=30,
        #                                   allImages=True,
        #                                   splitImages=False)
        # setExtendedInput(protTRIGandFlip.inputImages, protEEPandFlip, 'outputParticles')
        # _registerProt(protTRIGandFlip, 'Particles')

        protTRIGandNoFlip = project.newProtocol(XmippProtTriggerData,
                                          objLabel='Xmipp - trigger data to stats - no flip',
                                          outputSize=1000, delay=30,
                                          allImages=True,
                                          splitImages=False)
        setExtendedInput(protTRIGandNoFlip.inputImages, protEEPandNoFlip, 'outputParticles')
        _registerProt(protTRIGandNoFlip, 'Particles')

        # --------- SCREEN PARTS AND ---------------------------
        # protSCRandFlip = project.newProtocol(XmippProtScreenParticles,
        #                                  objLabel='Xmipp - Screen particles - flip')
        # protSCRandFlip.autoParRejection.set(XmippProtScreenParticles.REJ_MAXZSCORE)
        # protSCRandFlip.autoParRejectionSSNR.set(XmippProtScreenParticles.REJ_PERCENTAGE_SSNR)
        # protSCRandFlip.autoParRejectionVar.set(XmippProtScreenParticles.REJ_VARIANCE)
        # setExtendedInput(protSCRandFlip.inputParticles, protTRIGandFlip, 'outputParticles')
        # _registerProt(protSCRandFlip, 'Particles', True)

        protSCRandNoFlip = project.newProtocol(XmippProtScreenParticles,
                                         objLabel='Xmipp - Screen particles - no flip')
        protSCRandNoFlip.autoParRejection.set(XmippProtScreenParticles.REJ_MAXZSCORE)
        protSCRandNoFlip.autoParRejectionSSNR.set(XmippProtScreenParticles.REJ_PERCENTAGE_SSNR)
        protSCRandNoFlip.autoParRejectionVar.set(XmippProtScreenParticles.REJ_VARIANCE)
        setExtendedInput(protSCRandNoFlip.inputParticles, protTRIGandNoFlip, 'outputParticles')
        _registerProt(protSCRandNoFlip, 'Particles', True)
    # # ----------------------------- END OF AND/SINGLE PICKING BRANCH --------

    triggers = []
    def getNoClasses(no_particles):
        no_classes = 50
        return no_classes

    for outputSize in [20000, 50000, 100000, 200000]:
        allAvgs = []
        classifiers = []
        # --------- TRIGGER PARTS ---------------------------
        # protTRIG2Flip = project.newProtocol(XmippProtTriggerData,
        #                                 objLabel='Xmipp - trigger {0} - flip'.format(outputSize),
        #                                 outputSize=outputSize,
        #                                 delay=30,
        #                                 allImages=False)
        # if configDict["particleElimination"]:
        #     setExtendedInput(protTRIG2Flip.inputImages, protSCRandFlip, 'outputParticles')
        # else:
        #     setExtendedInput(protTRIG2Flip.inputImages, protExtractFlip, 'outputParticles')
        # _registerProt(protTRIG2Flip, '2Dclassify')
        # triggers.append(protTRIG2Flip)

        protTRIG2NoFlip = project.newProtocol(XmippProtTriggerData,
                                        objLabel='Xmipp - trigger {0} - no flip'.format(outputSize),
                                        outputSize=outputSize,
                                        delay=30,
                                        allImages=False)
        if configDict["particleElimination"]:
            setExtendedInput(protTRIG2NoFlip.inputImages, protSCRandNoFlip, 'outputParticles')
        else:
            setExtendedInput(protTRIG2NoFlip.inputImages, protExtractNoFlip, 'outputParticles')
        _registerProt(protTRIG2NoFlip, '2Dclassify')
        triggers.append(protTRIG2NoFlip)

        # protCL = project.newProtocol(XmippProtCL2D,
        #                              objLabel='Xmipp - CL2D',
        #                              doCore=False,
        #                              numberOfClasses=getNoClasses(outputSize),
        #                              numberOfMpi=16)

        # protCL._useQueue.set(True)
        # protCL._queueParams.set(json.dumps(QUEUE_PARAMS_WITHOUT_GPU))
        # setExtendedInput(protCL.inputParticles, protTRIG2Flip, 'outputParticles')
        # _registerProt(protCL, '2Dclassify', True)
        # classifiers.append(protCL)
        # ispybUploads.append(protCL)
        # # # Classes -> Averages
        # protCl2Av1 = project.newProtocol(XmippProtEliminateEmptyClasses,
        #                                  objLabel='Classes to averages (xmipp)',
        #                                  threshold=-1,
        #                                  usePopulation=False)
        # setExtendedInput(protCl2Av1.inputClasses, protCL, 'outputClasses')
        # _registerProt(protCl2Av1, '2Dclassify')
        # allAvgs.append(protCl2Av1)

        protCL2 = project.newProtocol(ProtRelionClassify2D,
                                      objLabel='Relion - 2D classifying',
                                      doGpu=True,
                                      gpusToUse=configDict["relionGpu"],
                                      numberOfClasses=getNoClasses(outputSize),
                                      numberOfMpi=1,
                                      numberOfThreads=15,
                                      maskDiameterA=configDict["partSize"])
        protCL2._useQueue.set(True)
        protCL2._queueParams.set(json.dumps(QUEUE_PARAMS_WITH_2_GPU_16_CPU))
        setExtendedInput(protCL2.inputParticles, protTRIG2NoFlip, 'outputParticles')
        _registerProt(protCL2, '2Dclassify', True)
        classifiers.append(protCL2)
        ispybUploads.append(protCL2)
        # # Classes -> Averages
        protCl2Av2 = project.newProtocol(XmippProtEliminateEmptyClasses,
                                         objLabel='Classes to averages (relion)',
                                         threshold=-1,
                                         usePopulation=False)
        setExtendedInput(protCl2Av2.inputClasses, protCL2, 'outputClasses')
        _registerProt(protCl2Av2, '2Dclassify')
        allAvgs.append(protCl2Av2)

        protJOIN = project.newProtocol(ProtUnionSet,
                                       objLabel='Scipion - Join all Averages - {0}'.format(outputSize))
        setExtendedInput(protJOIN.inputSets,
                         allAvgs, ['outputAverages'] * len(allAvgs))
        _registerProt(protJOIN, '2Dclassify')
        allAvgsOut = 'outputSet'

        protCLSEL = project.newProtocol(XmippProtEliminateEmptyClasses,
                                        objLabel='Xmipp - Auto class selection - {0}'.format(outputSize),
                                        threshold=-1,
                                        usePopulation=False)
        setExtendedInput(protCLSEL.inputClasses, protJOIN, allAvgsOut)
        _registerProt(protCLSEL, 'initVol', True)

    # # --------- SUMMARY MONITOR -----------------------
    # protMonitor = project.newProtocol(ProtMonitorSummary,
    #                                   objLabel='Scipion - Summary Monitor',
    #                                   samplingInterval=20,
    #                                   publishCmd="rsync -avL %(REPORT_FOLDER)s {0}".format(configDict["dataDirectory"]))
    # protMonitor.inputProtocols.set(summaryList)
    # _registerProt(protMonitor, 'monitor')

    # --------- ISPyB MONITOR -----------------------
    if not configDict["noISPyB"]:
        ispybMonitor = project.newProtocol(
            ProtMonitorISPyB_ESRF,
            objLabel='ISPyB monitor',
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
            particleSize=configDict["partSize"]
        )
        ispybMonitor.inputProtocols.set(ispybUploads)
        _registerProt(ispybMonitor, 'ispybMonitor')
