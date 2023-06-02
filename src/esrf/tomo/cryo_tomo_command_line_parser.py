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
import pprint


def getCommandlineOptions():
    parser = argparse.ArgumentParser(
        description="Application for starting Scipion Cryo ET workflow for CM01"
    )
    parser._action_groups.pop()
    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    required.add_argument(
        "--directory", action="store", help="top EM directory", required=True
    )
    required.add_argument(
        "--protein",
        action="store",
        help="Protein acronym, must be the one used in the A-form.",
        required=True,
    )
    required.add_argument(
        "--sample",
        action="store",
        help="Sample name, for example 'grid1'.",
        required=True,
    )
    required.add_argument(
        "--dosePerFrame", action="store", help="Dose per frame.", required=True
    )
    required.add_argument(
        "--magnification", action="store", help="Nominal magnification.", required=True
    )
    required.add_argument(
        "--numberOfFrames",
        action="store",
        help="Number of frames per movie.",
        required=True,
    )
    optional.add_argument(
        "--tiltAxisAngle",
        action="store",
        help="Tilt axis angle.",
        default=-175.9,
        required=False,
    )
    optional.add_argument(
        "--samplingRate",
        action="store",
        help="Sampling rate.",
        default=None,
        required=True,
    )
    optional.add_argument(
        "--filesPattern",
        action="store",
        help="File pattern for finding CRyo ET movies, default pattern, default: '*_fractions.tiff'",
        default="*_fractions.tiff"
        #         help="""
        # File pattern for finding CRyo ET movies, default pattern
        #     "{TS}_{TO}_{TA}_{DATE}_{TIME}_fractions.tiff"
        # where
        #     {TS}: tilt series identifier, which can be any UNIQUE part of the path, this must be an alpha-numeric sequence (avoid dash (-) symbol) and can not start with a number
        #     {TO}: acquisition order, an integer value (important for dose information)
        #     {TA}: tilt angle, a positive or negative float value
        #     {DATE}: date of format YYYYMMDD, e.g. 20230531
        #     {TIME}: time of format HHMMSS, e.g. 132315
        # """,
        #         default="{TS}_{TO}_{TA}_{DATE}_{TIME}_fractions.tiff",
    )
    # optional.add_argument(
    #     "--scipionProjectName",
    #     action="store",
    #     help="Scipion project name, is only used internally in Scipion.",
    # )
    optional.add_argument(
        "--doseInitial", action="store", help="Initial dose, default zero.", default=0.0
    )
    optional.add_argument(
        "--imagesCount",
        action="store",
        help="Number of images per movie.",
        default=None,
    )
    # optional.add_argument("--voltage", action="store", help="Voltage [V]", default=None)
    optional.add_argument(
        "--defectMapPath", action="store", help="Defect map file path", default=None
    )
    optional.add_argument(
        "--gainFilePath", action="store", help="Gain file path", default=None
    )
    optional.add_argument(
        "--startMotioncorFrame",
        action="store",
        help="Start frame for motion correction, default 1.",
        default=1,
    )
    optional.add_argument(
        "--endMotioncorFrame",
        action="store",
        help="End frame for motion correction, default last frame.",
        default=0,
    )
    optional.add_argument(
        "--superResolution",
        action="store_true",
        help="Super resolution used, default 'False'.",
        default=False,
    )
    optional.add_argument(
        "--onlyICAT",
        action="store_true",
        help="Only upload raw data to ICAT i.e. no processing, default 'False'.",
        default=False,
    )
    optional.add_argument(
        "--noICAT",
        action="store_true",
        help="Don't upload to ISPyB or iCAT, default 'False'.",
        default=False,
    )
    optional.add_argument(
        "--celery_worker",
        action="store",
        help="Celery worker (dgx01, cmproc3, None)",
        default="dgx01",
    )
    results = parser.parse_args()

    opt_dict = {
        "dataDirectory": results.directory,
        "filesPattern": results.filesPattern,
        "proteinAcronym": results.protein,
        "sampleAcronym": results.sample,
        "doseInitial": float(results.doseInitial),
        "magnification": int(results.magnification)
        if results.magnification is not None
        else None,
        "numberOfFrames": int(results.numberOfFrames)
        if results.numberOfFrames is not None
        else None,
        "imagesCount": int(results.imagesCount)
        if results.imagesCount is not None
        else None,
        "dosePerFrame": float(results.dosePerFrame),
        "samplingRate": float(results.samplingRate),
        "dataStreaming": True,
        "alignFrame0": int(results.startMotioncorFrame),
        "alignFrameN": int(results.endMotioncorFrame),
        "onlyICAT": results.onlyICAT,
        "noICAT": results.noICAT,
        "celery_worker": results.celery_worker,
        "defectMapPath": results.defectMapPath,
        "gainFilePath": results.gainFilePath,
        "tiltAxisAngle": results.tiltAxisAngle,
        "superResolution": results.superResolution,
    }
    pprint.pprint(opt_dict)
    return opt_dict
