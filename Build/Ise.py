##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler, Waldemar Koprek
##############################################################################

########################################################################################################################
# Import Statements
########################################################################################################################
import os
import sys
from PsiPyUtils.EnvVariables import AddToPathVariable
from PsiPyUtils.FileOperations import OpenWithWildcard, AbsPathLinuxStyle
from PsiPyUtils.TempFile import TempFile
from PsiPyUtils.TempWorkDir import TempWorkDir
from PsiPyUtils.ExtAppCall import ExtAppCall

########################################################################################################################
# Class Defintion
########################################################################################################################
class Ise:
    """
    This class allows using various ISE from the command line
    """
    ####################################################################################################################
    # Public Methods
    ####################################################################################################################
    def __init__(self, isePathEnv : str, version : str):
        """
        Constructor

        :param isePathEnv:    Environment variable that points to the ISE installation. Example: C:/Xilinx/14.7
        :param version:       Toolversion in the form "14.7". This version string may be used in future for the case that
                              commands or paths change between versions.
        """
        if version != "14.7":
            raise Exception("ISE Version {} is not supported".format(version))
        if isePathEnv not in os.environ:
            raise Exception("Enviromental variable {} does not exists. Please specify it".format(isePathEnv))
        self._version = version
        self._isePath = os.environ[isePathEnv].replace('"', '')
        self._timingScore = None
        if sys.platform.startswith("win"):
            AddToPathVariable("XILINX", "{}/ISE_DS/ISE".format(self._isePath))
            AddToPathVariable("PATH",   "{}/ISE_DS/ISE/bin/nt64".format(self._isePath))
        elif sys.platform.startswith("linux"):
            AddToPathVariable("XILINX", "{}/ISE_DS/ISE".format(self._isePath))
            AddToPathVariable("PATH",   "{}/ISE_DS/ISE/bin/lin64".format(self._isePath))
        else:
            raise Exception("OS {} not supported".format(sys.platform))



    ####################################################################################################################
    # Public Properties
    ####################################################################################################################
    def BuildProject(self, xisePath : str, logFile : str, buildTimeoutSec : int = 60*45):
        """
        Build the complete project and generate programming file

        :param xisePath: Path of the .xise file to build
        :param logFile: File to write ISE output into
        :param buildTimeoutSec: Timeout for bitstream generation
        """
        #Reset timing score to ensure it is not 0 after an abortted build
        self._timingScore = None
        #Build
        logFileAbs = os.path.abspath(logFile)
        prjPath = AbsPathLinuxStyle(os.path.dirname(xisePath))
        prjName = os.path.basename(xisePath)
        with TempWorkDir(prjPath):
            with TempFile("__ise.tcl") as tcl:
                #Write TCL file
                tcl.write("project open {}\n".format(prjName))
                tcl.write("set result [ process run \"Generate Programming File\" -force rerun_all ]\n")
                tcl.write("exit\n")
                tcl.flush()

                #Call ISE TCL shell
                call = ExtAppCall(".", "xtclsh __ise.tcl")
                call.run_sync()
                with open(logFileAbs, "w+") as f:
                    f.write(call.get_stdout())
                #Checks
                if call.get_exit_code() != 0:
                    raise Exception("XTCLSH exitetd with Non-Zero return code")
                #StdErr cannot be checked since it always contains some entries. So we check stdout for errors
                if "ERROR:" in call.get_stdout():
                    raise Exception("Errors occured. See log file for details.")
                #Ensure that bitstream generation succeeded (to prevent silent-crashes from staying undetected)
                if "Process \"Generate Programming File\" completed successfully" not in call.get_stdout():
                    raise Exception("Bitstream was not generated")

            #Check Timing
            with OpenWithWildcard(".", ".*\.twr") as f:
                content = f.read()
            summaryToEnd = content.split("Timing summary:")[1]
            scoreToEnd = summaryToEnd.split("Score:")[1]
            scoreNr = scoreToEnd.split("(")[0]
            self._timingScore = int(scoreNr.strip())

    ####################################################################################################################
    # Public Properties
    ####################################################################################################################
    @property
    def TimingScore(self):
        """
        Get the timing score after a build. Returns None if the score is not available.
        """
        return self._timingScore

