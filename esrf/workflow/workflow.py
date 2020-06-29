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

import random
from collections import OrderedDict

from pyworkflow.em.protocol import ProtImportMovies
from pyworkflow.em.protocol import ProtUnionSet
from pyworkflow.em.protocol import ProtMonitorSummary
from esrf.protocols.protocol_monitor_ispyb_esrf import ProtMonitorISPyB_ESRF

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


QUEUE_PARAMS = (u'gpu', {u'JOB_TIME': u'1',  # in hours
                         u'JOB_MEMORY': u'2048',  # in Mb
                         u'QUEUE_FOR_JOBS': u'N', })

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

    timeout = 43200

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
                                     magnification=configDict["nominalMagnification"],
                                     dataStreaming=configDict["dataStreaming"],
                                     timeout=timeout)
    _registerProt(protImport, label='Movies', toSummary=True)

    # ----------- MOTIONCOR ----------------------------
    mcMpi = 1
    protMA = project.newProtocol(importPlugin('ProtMotionCorr'),
                                 objLabel='MotionCor2 - movie align.',
                                 gpuList=configDict["motioncor2Gpu"],
                                 numberOfThreads=mcMpi,
                                 doApplyDoseFilter=True,
                                 doSaveUnweightedMic=True,
                                 doSaveAveMic=True,
                                 doSaveMovie=False,
                                 doComputeMicThumbnail=True,
                                 computeAllFramesAvg=False,
                                 patchX=5, patchY=5,
                                 useEst=True,
                                 alignFrame0=configDict["alignFrame0"],
                                 alignFrameN=configDict["alignFrameN"],
                                 binFactor=configDict["binFactor"],
                                 extraParams2=configDict["extraParams2"])
    setExtendedInput(protMA.inputMovies, protImport, 'outputMovies')
    _registerProt(protMA, 'Movies')

    # ----------- MAX SHIFT -----------------------------
    protMax = project.newProtocol(XmippProtMovieMaxShift,
                                  objLabel='Xmipp - max shift')
    setExtendedInput(protMax.inputMovies, protMA, 'outputMovies')
    _registerProt(protMax, 'Movies', True)

    protCTF2 = project.newProtocol(importPlugin('ProtGctf'),
                                   objLabel='gCTF estimation',
                                   gpuList=configDict["gctfGpu"],
                                   lowRes=configDict["lowRes"],
                                   plotResRing=True,
                                   doEPA=True,
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
                     protMax, 'outputMicrographsDoseWeighted')
    _registerProt(protCTF2, 'CTF')

    # --------- CTF ESTIMATION 1 ---------------------------
    protCTF1 = project.newProtocol(importPlugin('ProtCTFFind'),
                                   objLabel='GrigorieffLab - CTFfind',
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
                     protMax, 'outputMicrographsDoseWeighted')
    _registerProt(protCTF1, 'CTF')

    # --------- CTF CONSENSUS ---------------------------
    isCtf2Xmipp = isinstance(protCTF2, XmippProtCTFMicrographs)
    protCTFs = project.newProtocol(XmippProtCTFConsensus,
                                   objLabel='Xmipp - CTF consensus',
                                   useDefocus=True,
                                   useAstigmatism=True,
                                   useResolution=True,
                                   resolution=5,
                                   useCritXmipp=isCtf2Xmipp,
                                   calculateConsensus=True,
                                   minConsResol=7)
    setExtendedInput(protCTFs.inputCTF, protCTF2, 'outputCTF')
    setExtendedInput(protCTFs.inputCTF2, protCTF1, 'outputCTF')
    _registerProt(protCTFs, 'CTF', True)

    # *************   PICKING   ********************************************

    pickers = []
    pickersOuts = []

    # --------- PREPROCESS MICS ---------------------------
    protPreMics0 = project.newProtocol(XmippProtPreprocessMicrographs,
                                       objLabel='Xmipp - preprocess Mics',
                                       doRemoveBadPix=True,
                                       doInvert=False)
    setExtendedInput(protPreMics0.inputMicrographs,
                     protCTFs, 'outputMicrographs')
    _registerProt(protPreMics0, 'Micrographs')

    # Resizing to a larger sampling rate
    doDownSamp2D = 0 < configDict["sampling2D"] > configDict["samplingRate"]
    samp2D = configDict["sampling2D"] if doDownSamp2D else configDict["samplingRate"]
    if doDownSamp2D:
        downSampPreMics = configDict["sampling2D"] / configDict["samplingRate"]
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

    # -------- XMIPP AUTO-BOXSIZE -------------------------
    waitManualPick = False
    protPrePick = None
    # protPrePick = project.newProtocol(XmippProtParticleBoxsize,
    #                                   objLabel='Xmipp - particle boxsize')
    # setExtendedInput(protPrePick.inputMicrographs,
    #                  protCTFs, 'outputMicrographs')
    # _registerProt(protPrePick, 'Picking')
    bxSize = getEvenPartSize(configDict["partSize"]/samp2D)

    protPP2 = project.newProtocol(importPlugin('SphireProtCRYOLOPicking'),
                                  objLabel='Sphire - CrYolo auto-picking',
                                  gpuList=configDict["cryoloGpu"],
                                  conservPickVar=0.03,
                                  streamingBatchSize=4,
                                  gpuList='0')  # CPU version installation
    setBoxSize(protPP2.boxSize)
    setExtendedInput(protPP2.inputMicrographs, protPreMics, 'outputMicrographs')
    if waitManualPick:
        protPP2.addPrerequisites(protPrePick.getObjId())
    _registerProt(protPP2, 'Picking')

    pickers.append(protPP2)
    pickersOuts.append('outputCoordinates')

    protPP4 = project.newProtocol(importPlugin('ProtRelionAutopickLoG'),
                                  objLabel='Relion - LoG auto-picking',
                                  conservPickVar=0.03,
                                  minDiameter=bxSize - 20,
                                  maxDiameter=bxSize + 10,
                                  maxResolution=-1,
                                  threshold=-1,
                                  streamingBatchSize=4)
    setBoxSize(protPP4.boxSize)
    setExtendedInput(protPP4.inputMicrographs, protPreMics, 'outputMicrographs')
    if waitManualPick:
        protPP4.addPrerequisites(protPrePick.getObjId())
    _registerProt(protPP4, 'Picking')

    pickers.append(protPP4)
    pickersOuts.append('outputCoordinates')

    # --------- CONSENSUS PICKING -----------------------

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

    protExtractAnd = project.newProtocol(XmippProtExtractParticles,
                                         objLabel='Xmipp - extract particles',
                                         boxSize=-1,
                                         downsampleType=1,  # Other to avoid a bug
                                         doRemoveDust=True,
                                         doNormalize=True,
                                         doInvert=True,
                                         doFlip=True)
    setExtendedInput(protExtractAnd.inputCoordinates, finalPicker, outputCoordsStr)
    setExtendedInput(protExtractAnd.inputMicrographs,
                     protPreMics, 'outputMicrographs')
    setExtendedInput(protExtractAnd.ctfRelations, protCTFs, 'outputCTF')
    _registerProt(protExtractAnd, 'Particles')

    # ***********   CLEAN PARTICLES   ************************************
    # --------- ELIM EMPTY PARTS AND ---------------------------
    protEEPand = project.newProtocol(XmippProtEliminateEmptyParticles,
                                     objLabel='Xmipp - Elim. empty part.',
                                     threshold=0.6)
    setExtendedInput(protEEPand.inputParticles, protExtractAnd, 'outputParticles')
    _registerProt(protEEPand, 'Particles')

    # --------- TRIGGER PARTS AND ---------------------------
    protTRIGand = project.newProtocol(XmippProtTriggerData,
                                      objLabel='Xmipp - trigger data to stats',
                                      outputSize=1000, delay=30,
                                      allImages=True,
                                      splitImages=False)
    setExtendedInput(protTRIGand.inputImages, protEEPand, 'outputParticles')
    _registerProt(protTRIGand, 'Particles')

    # --------- SCREEN PARTS AND ---------------------------
    protSCRand = project.newProtocol(XmippProtScreenParticles,
                                     objLabel='Xmipp - Screen particles')
    protSCRand.autoParRejection.set(XmippProtScreenParticles.REJ_MAXZSCORE)
    protSCRand.autoParRejectionSSNR.set(XmippProtScreenParticles.REJ_PERCENTAGE_SSNR)
    protSCRand.autoParRejectionVar.set(XmippProtScreenParticles.REJ_VARIANCE)
    setExtendedInput(protSCRand.inputParticles, protTRIGand, 'outputParticles')
    _registerProt(protSCRand, 'Particles', True)
    # ----------------------------- END OF AND/SINGLE PICKING BRANCH --------

    allAvgs = []
    classifiers = []
    # --------- TRIGGER PARTS ---------------------------
    protTRIG2 = project.newProtocol(XmippProtTriggerData,
                                    objLabel='Xmipp - trigger data to classify',
                                    outputSize=configDict["parts2class"],
                                    delay=30,
                                    allImages=False)
    setExtendedInput(protTRIG2.inputImages, protSCRand, 'outputParticles')
    _registerProt(protTRIG2, '2Dclassify')

    protCL = project.newProtocol(XmippProtCL2D,
                                 objLabel='Xmipp - CL2D',
                                 doCore=False,
                                 numberOfClasses=16,
                                 numberOfMpi=configDict["numCpus"] - 8)

    setExtendedInput(protCL.inputParticles, protTRIG2, 'outputParticles')
    _registerProt(protCL, '2Dclassify', True)
    classifiers.append(protCL)
    # Classes -> Averages
    protCl2Av1 = project.newProtocol(XmippProtEliminateEmptyClasses,
                                     objLabel='Classes to averages (xmipp)',
                                     threshold=-1,
                                     usePopulation=False)
    setExtendedInput(protCl2Av1.inputClasses, protCL, 'outputClasses')
    _registerProt(protCl2Av1, '2Dclassify')
    allAvgs.append(protCl2Av1)

    protCL2 = project.newProtocol(importPlugin('ProtRelionClassify2D'),
                                  objLabel='Relion - 2D classifying',
                                  doGpu=True,
                                  gpusToUse=configDict["relionGpu"],
                                  numberOfClasses=16,
                                  relionCPUs=3)
    setExtendedInput(protCL2.inputParticles, protTRIG2, 'outputParticles')
    _registerProt(protCL2, '2Dclassify', True)
    classifiers.append(protCL2)
    # Classes -> Averages
    protCl2Av2 = project.newProtocol(XmippProtEliminateEmptyClasses,
                                     objLabel='Classes to averages (relion)',
                                     threshold=-1,
                                     usePopulation=False)
    setExtendedInput(protCl2Av2.inputClasses, protCL2, 'outputClasses')
    _registerProt(protCl2Av2, '2Dclassify')
    allAvgs.append(protCl2Av2)

    protJOIN = project.newProtocol(ProtUnionSet,
                                   objLabel='Scipion - Join all Averages')
    setExtendedInput(protJOIN.inputSets,
                     allAvgs, ['outputAverages'] * len(allAvgs))
    _registerProt(protJOIN, '2Dclassify')
    allAvgsOut = 'outputSet'

    protCLSEL = project.newProtocol(XmippProtEliminateEmptyClasses,
                                    objLabel='Xmipp - Auto class selection',
                                    threshold=12,
                                    usePopulation=False)
    setExtendedInput(protCLSEL.inputClasses, protJOIN, allAvgsOut)
    _registerProt(protCLSEL, 'initVol', True)

    # --------- SUMMARY MONITOR -----------------------
    protMonitor = project.newProtocol(ProtMonitorSummary,
                                      objLabel='Scipion - Summary Monitor',
                                      samplingInterval=20,
                                      publishCmd="rsync -avL %(REPORT_FOLDER)s {0}".format(configDict["dataDirectory"]))
    protMonitor.inputProtocols.set(summaryList)
    _registerProt(protMonitor, 'monitor')

    # --------- ISPyB MONITOR -----------------------
    if not configDict["noISPyB"]:
        ispybMonitor = project.newProtocol(ProtMonitorISPyB_ESRF,
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
                                           serialEM=configDict["serialEM"],
                                           voltage=configDict["voltage"],
                                           imagesCount=configDict["imagesCount"],
                                           magnification=configDict["nominalMagnification"],
                                           alignFrame0=configDict["alignFrame0"],
                                           alignFrameN=configDict["alignFrameN"]
                                           )
        ispybMonitor.inputProtocols.set([protImport, protMA, protCTF2])
        _registerProt(ispybMonitor, 'ispybMonitor')
