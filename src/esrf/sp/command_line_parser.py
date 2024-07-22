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

import argparse


def getCommandlineOptions():
    parser = argparse.ArgumentParser(
        description="Application for starting Scipion workflow for CM01"
    )
    parser._action_groups.pop()
    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    required.add_argument(
        "--directory", action="store", help="top EM directory", required=True
    )
    required.add_argument(
        "--protein",
        type=str,
        help="Protein acronym, must be the one used in the A-form.",
        required=True,
    )
    required.add_argument(
        "--sample",
        type=str,
        help="Sample name, for example 'grid1'.",
        required=True,
    )
    required.add_argument(
        "--magnification", type=int, help="Nominal magnification.", default=None
    )
    required.add_argument(
        "--dosePerFrame", type=float, help="Dose per frame.", required=True
    )
    required.add_argument(
        "--imagesCount",
        type=int,
        help="Number of images per movie.",
        default=None,
    )
    required.add_argument(
        "--samplingRate",
        type=float,
        help="Sampling rate.",
        default=None,
        required=True,
    )
    optional.add_argument(
        "--dataType",
        type=str,
        help="Type of data: tiff or eer, default tiff",
        default="tiff",
    )
    optional.add_argument(
        "--EER_fractionation",
        type=int,
        help="The number of hardware frames to group into one "
        + "fraction. This option is relevant only for Falcon 4 "
        + "movies in the EER format.",
        default="30",
    )
    optional.add_argument(
        "--filesPattern",
        type=str,
        help="file pattern for finding EM movies, default pattern "
        + "Images-Disc*/GridSquare_*/Data/FoilHole_*_fractions.tiff",
        default=None,
    )
    # optional.add_argument(
    #     "--scipionProjectName",
    #     action="store",
    #     help="Scipion project name, is only used internally in Scipion.",
    # )
    optional.add_argument(
        "--doseInitial", type=float, help="Initial dose, default zero.", default=0.0
    )
    # optional.add_argument("--voltage", action="store", help="Voltage [V]", default=None)
    optional.add_argument(
        "--startMotioncorFrame",
        type=int,
        help="Start frame for motion correction, default 1.",
        default=1,
    )
    optional.add_argument(
        "--endMotioncorFrame",
        type=int,
        help="End frame for motion correction, default last frame.",
        default=0,
    )
    optional.add_argument(
        "--partSize",
        type=float,
        help="Particle size for auto picking",
        default=200.0,
    )
    optional.add_argument(
        "--superResolution",
        action="store_true",
        help="Super resolution used, default 'False'.",
        default=False,
    )
    optional.add_argument(
        "--phasePlateData",
        action="store_true",
        help="Phase plate used, default 'False'.",
        default=False,
    )
    optional.add_argument(
        "--no2dClass",
        action="store_true",
        help="Only movie import, MotioCor2 and Gctf, no 2D classification",
        default=False,
    )
    optional.add_argument(
        "--onlyISPyB",
        action="store_true",
        help="Only upload data to ISPyB i.e. no processing, default 'False'.",
        default=False,
    )
    optional.add_argument(
        "--noISPyB",
        action="store_true",
        help="Don't upload to ISPyB or iCAT, default 'False'.",
        default=False,
    )
    optional.add_argument(
        "--defectMapPath", type=str, help="Defect map file path", default=None
    )
    optional.add_argument(
        "--gainFilePath", type=str, help="Gain file path", default=None
    )
    optional.add_argument(
        "--particleElimination",
        action="store_true",
        help="Don't eliminate particles after extract particles.",
        default=False,
    )
    optional.add_argument(
        "--secondGrid",
        action="store_true",
        help="If set: timeout increased to 72 h, GPUs 4-7 used",
        default=False,
    )
    optional.add_argument(
        "--thirdGrid",
        action="store_true",
        help="If set: timeout increased to 72 h, GPUs 0-3 used",
        default=False,
    )
    optional.add_argument(
        "--doProcessDir",
        action="store_true",
        help="If set: copy of micrographs to RAW_DATA",
        default=False,
    )
    optional.add_argument(
        "--celery_worker",
        type=str,
        help="Celery worker (dgx01, cmproc3, None)",
        default="cmproc5",
    )
    optional.add_argument(
        "--debug",
        action="store_true",
        help="If set: only do 5000 and 20000 particle triggers for 2D class",
        default=False,
    )
    results = parser.parse_args()

    opt_dict = {
        "dataDirectory": results.directory,
        "filesPattern": results.filesPattern,
        "dataType": 0 if results.dataType == "tiff" else 1,
        "EER_fractionation": results.EER_fractionation,
        "proteinAcronym": results.protein,
        "sampleName": results.sample,
        "doseInitial": results.doseInitial,
        "magnification": (
            results.magnification if results.magnification is not None else None
        ),
        "imagesCount": results.imagesCount if results.imagesCount is not None else None,
        # "voltage": int(results.voltage) if results.voltage is not None else None,
        "dosePerFrame": results.dosePerFrame,
        "dataStreaming": True,
        "alignFrame0": results.startMotioncorFrame,
        "alignFrameN": results.endMotioncorFrame,
        "phasePlateData": results.phasePlateData,
        "no2dClass": results.no2dClass,
        "onlyISPyB": results.onlyISPyB,
        "noISPyB": results.noISPyB,
        "particleElimination": results.particleElimination,
        "samplingRate": results.samplingRate,
        "superResolution": results.superResolution,
        "partSize": results.partSize,
        "defectMapPath": results.defectMapPath,
        "gainFilePath": results.gainFilePath,
        "secondGrid": results.secondGrid,
        "thirdGrid": results.thirdGrid,
        "doProcessDir": results.doProcessDir,
        "celery_worker": results.celery_worker,
        "debug": results.debug,
    }

    return opt_dict
