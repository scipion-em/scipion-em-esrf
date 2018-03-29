# coding: utf-8
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

import unittest
from esrf_utils_ispyb import UtilsISPyB

class Test(unittest.TestCase):

    def test_getProposal(self):
        movieFilePath = "/data/visitor/mx2001/cm01/20171124/RAW_DATA/Data-hug-grid1/Images-Disc1/GridSquare_24748253/Data/FoilHole_24762814_Data_24757346_24757347_20171126_0223-4929.mrc"
        proposal = UtilsISPyB.getProposal(movieFilePath)
        self.assertEqual("mx2001", proposal)
        movieFilePath = "/data/cm01/inhouse/Hons/IH-LS-2975/RAW_DATA"
        proposal = UtilsISPyB.getProposal(movieFilePath)
        self.assertEqual("ihls2975", proposal)

    def test_getClient(self):
        client = UtilsISPyB.getClient(1)
        self.assertIsNotNone(client)        

    def test_updateProposalFromSMIS(self):
        UtilsISPyB.updateProposalFromSMIS(1, "mx415")

    def test_splitProposalInCodeAndNumber(self):
        self.assertEqual(("mx", "415"), UtilsISPyB.splitProposalInCodeAndNumber("mx415"))
        self.assertEqual(("blc", "11258"), UtilsISPyB.splitProposalInCodeAndNumber("blc11258"))

    def test_findSessions(self):
        sessions = UtilsISPyB.findSessions(1, "mx415", "CM01")
        self.assertTrue(len(sessions) > 0)
        
    def test_findPropsal(self):
        proposal = UtilsISPyB.findProposal(1, "mx415")
        self.assertEqual("MX", proposal.code)
        
    def tes_createSession(self):
        sessions = UtilsISPyB.createSession(1, "mx415", "cm01")
        print(sessions)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()