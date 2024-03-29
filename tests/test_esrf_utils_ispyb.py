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

import os
import unittest
from esrf.utils.esrf_utils_ispyb import UtilsISPyB


class Test(unittest.TestCase):
    def test_getProposal(self):
        movie_file_path = (
            "/data/visitor/mx2001/cm01/20171124/RAW_DATA/Data-hug-grid1/"
            + "Images-Disc1/GridSquare_24748253/Data/"
            + "FoilHole_24762814_Data_24757346_24757347_20171126_0223-4929.mrc"
        )
        proposal = UtilsISPyB.getProposal(movie_file_path)
        self.assertEqual("mx2001", proposal)
        movie_file_path = "/data/cm01/inhouse/BLC11341/20180410/RAW_DATA/EPU_BLC11341"
        proposal = UtilsISPyB.getProposal(movie_file_path)
        self.assertEqual("blc11341", proposal)
        movie_file_path = "/data/cm01/inhouse/ih-ls3046/20180410/RAW_DATA/EPU_BLC11341"
        proposal = UtilsISPyB.getProposal(movie_file_path)
        self.assertEqual("ih-ls3046", proposal)
        movie_file_path = (
            "/data/cm01/cmihr1/IH-LS3214/20190220/RAW_DATA/"
            + "EPU-IHLS3214-comp-grid1/Images-Disc1/GridSquare_19849110/Data/"
            + "FoilHole_19853578_Data_19852496_19852497_20190221_0414-0634.mrc"
        )
        proposal = UtilsISPyB.getProposal(movie_file_path)
        self.assertEqual("ih-ls3214", proposal)
        movie_file_path = "/data/visitor/mx2112/cm01/20220426/PROCESSED_DATA/igm-grid3-2"
        proposal = UtilsISPyB.getProposal(movie_file_path)
        self.assertEqual("mx2112", proposal)

    def test_getProposalInhouse(self):
        movie_file_path = "/data/visitor/ihls3404/cm01/20220707/RAW_DATA/IHLS_3404_FluPol/. "
        proposal = UtilsISPyB.getProposal(movie_file_path)
        self.assertEqual("ih-ls3404", proposal)
        movie_file_path = "/data/visitor/ihmx3404/cm01/20220707/RAW_DATA/IHLS_3404_FluPol/. "
        proposal = UtilsISPyB.getProposal(movie_file_path)
        self.assertEqual("ih-mx3404", proposal)
        movie_file_path = "/data/visitor/ihsc3404/cm01/20220707/RAW_DATA/IHLS_3404_FluPol/. "
        proposal = UtilsISPyB.getProposal(movie_file_path)
        self.assertEqual("ih-sc3404", proposal)

    def test_getClient(self):
        urlBase = UtilsISPyB.getUrlBase(1)
        url = os.path.join(urlBase, "UpdateFromSMISWebService?wsdl")
        client = UtilsISPyB.getClient(url)
        self.assertIsNotNone(client)

    def test_splitProposalInCodeAndNumber(self):
        self.assertEqual(
            ("mx", "415"), UtilsISPyB.splitProposalInCodeAndNumber("mx415")
        )
        self.assertEqual(
            ("blc", "11258"), UtilsISPyB.splitProposalInCodeAndNumber("blc11258")
        )
        self.assertEqual(
            ("opcm", "01"), UtilsISPyB.splitProposalInCodeAndNumber("opcm01")
        )
        self.assertEqual(
            ("ih-ls", "3046"), UtilsISPyB.splitProposalInCodeAndNumber("ih-ls3046")
        )
        self.assertEqual(
            ("ih-mx", "129"), UtilsISPyB.splitProposalInCodeAndNumber("ih-mx129")
        )
        self.assertEqual((None, None), UtilsISPyB.splitProposalInCodeAndNumber(None))
        self.assertEqual(
            (None, None), UtilsISPyB.splitProposalInCodeAndNumber("abc123")
        )
        self.assertEqual(
            (None, None), UtilsISPyB.splitProposalInCodeAndNumber("mxx123")
        )

    # def test_findSessions(self):
    #     sessions = UtilsISPyB.findSessions(1, "opcm01", "cm01")
    #     self.assertTrue(len(sessions) > 0)

    def test_findProposal(self):
        proposal = UtilsISPyB.findProposal(1, "mx415")
        self.assertEqual("MX", proposal.code)
        proposal = UtilsISPyB.findProposal(1, "MX415")
        self.assertEqual("MX", proposal.code)
        proposal = UtilsISPyB.findProposal(1, "opcm01")
        self.assertEqual("OPCM", proposal.code)
        self.assertEqual("01", proposal.number)
        proposal = UtilsISPyB.findProposal(1, "OPCM01")
        self.assertEqual("OPCM", proposal.code)
        self.assertEqual("01", proposal.number)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
