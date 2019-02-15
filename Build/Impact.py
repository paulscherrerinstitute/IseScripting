##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler
##############################################################################

########################################################################################################################
# Set path to libraries
########################################################################################################################
import sys
import os

########################################################################################################################
# Import Statements
########################################################################################################################
from PsiPyUtils.EnvVariables import AddToPathVariable
from PsiPyUtils import ExtAppCall

class Impact:
    """
    This class allows various actions using Xilinx Impact tool
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
        self._timingScore = None
        if version != "14.7":
            raise Exception("ISE Version {} is not supported".format(version))
        self._version = version
        if isePathEnv not in os.environ:
            raise Exception("Enviromental variable {} does not exists. Please specify it".format(isePathEnv))
        self._isePath = os.environ[isePathEnv].replace('"', '')
        if sys.platform.startswith("win"):
            AddToPathVariable("XILINX", "{}/ISE_DS/ISE".format(self._isePath))
            AddToPathVariable("PATH",   "{}/ISE_DS/ISE/bin/nt64".format(self._isePath))
        elif sys.platform.startswith("linux"):
            AddToPathVariable("XILINX", "{}/ISE_DS/ISE".format(self._isePath))
            AddToPathVariable("PATH",   "{}/ISE_DS/ISE/bin/lin64".format(self._isePath))
        else:
            raise Exception("OS {} not supported".format(sys.platform))

    def ExecBatch(self, batchName : str, buildTimeoutSec : int = 360):
        """
        Run Impact in batch mode. 
        The batch file can do whatever, e.g. ACE or PROM file generation

        :param batchName: Path to the batch file for Impact
        :param logFile: File to write Impact output into
        :param buildTimeoutSec: Timeout for batch execution
        """
        # Command line syntax for Impact batch mode
        # impact.exe -batch <batch_file>
  
        logFileAbs = os.path.abspath(os.path.basename(batchName)+".log")
        batchFolder = os.path.dirname(batchName)
        batchFile = os.path.basename(batchName)
        call = ExtAppCall(batchFolder, "impact -batch "+batchFile)
        call.run_sync(timeout_sec=buildTimeoutSec)
        with open(logFileAbs, "w+") as f:
            f.write(call.get_stdout())
        #Checks
        if call.get_exit_code() != 0:
            raise Exception("Impact exitetd with Non-Zero return code")
        #StdErr cannot be checked since it always contains some entries. So we check stdout for errors
        if "ERROR:" in call.get_stdout():
            raise Exception("Errors occured. See log file for details.")
    