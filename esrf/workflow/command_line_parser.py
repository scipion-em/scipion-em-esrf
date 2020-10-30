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
        "--parts2class",
        action="store",
        help="Number of particles for classification",
        default=5000
    )
    optional.add_argument(
        "--partSize",
        action="store",
        help="Particle size for auto picking",
        default=200.0
    )
    optional.add_argument(
        "--superResolution",
        action="store_true",
        help="Super resolution used, default 'False'.",
        default=False
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

    optDict = {
        "dataDirectory": results.directory,
        "filesPattern": results.filesPattern,
        "scipionProjectName": results.scipionProjectName,
        "proteinAcronym": results.protein,
        "sampleAcronym": results.sample,
        "doseInitial": float(results.doseInitial),
        "nominalMagnification": int(results.magnification) if results.magnification is not None else None,
        "imagesCount": int(results.imagesCount) if results.imagesCount is not None else None,
        "voltage": int(results.voltage) if results.voltage is not None else None,
        "dosePerFrame": float(results.dosePerFrame),
        "dataStreaming": True,
        "alignFrame0": int(results.startMotioncorFrame),
        "alignFrameN": int(results.endMotioncorFrame),
        "phasePlateData": results.phasePlateData,
        "onlyISPyB": results.onlyISPyB,
        "noISPyB": results.noISPyB,
        "samplingRate": float(results.samplingRate),
        "superResolution": results.superResolution,
        "partSize": float(results.partSize),
        "parts2class": int(results.parts2class),
        "defectMapPath": results.defectMapPath,
        "gainFilePath": results.gainFilePath
    }

    return optDict

