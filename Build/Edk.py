##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler, Waldemar Koprek
##############################################################################

########################################################################################################################
# Import Statements
########################################################################################################################
import sys
from PsiPyUtils.FileOperations import RemoveWithWildcard, OpenWithWildcard, AbsPathLinuxStyle
from PsiPyUtils.TempFile import TempFile
from PsiPyUtils.TempWorkDir import TempWorkDir
from PsiPyUtils.EnvVariables import AddToPathVariable
from PsiPyUtils.ExtAppCall import ExtAppCall
import os


########################################################################################################################
# Class Defintion
########################################################################################################################
class Edk:
    """
    This class allows building EDK projects from the command line.
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
            AddToPathVariable("PATH",   "{}/ISE_DS/EDK/bin/nt64".format(self._isePath))
            AddToPathVariable("PATH",   "{}/ISE_DS/ISE/bin/nt64".format(self._isePath))
        elif sys.platform.startswith("linux"):
            AddToPathVariable("XILINX", "{}/ISE_DS/ISE".format(self._isePath))
            AddToPathVariable("PATH",   "{}/ISE_DS/EDK/bin/lin64".format(self._isePath))
            AddToPathVariable("PATH",   "{}/ISE_DS/ISE/bin/lin64".format(self._isePath))
        else:
            raise Exception("OS {} not supported".format(sys.platform))


    def CleanBuild(self, xmpPath : str, logFile : str, buildTimeoutSec : int = 3600):
        """
        Clean EDK project and build it

        :param xmpPath: Path of the .xmp file to build
        :param logFile: File to write EDK output into
        :param buildTimeoutSec: Timeout for bitstream generation
        """
        #Reset timing score to ensure it is not 0 after an abortted build
        self._timingScore = None
        #Build
        logFileAbs = os.path.abspath(logFile)
        prjPath = AbsPathLinuxStyle(os.path.dirname(xmpPath))
        prjName = os.path.basename(xmpPath)
        with TempWorkDir(prjPath):
            with TempFile("__edk.tcl") as tcl:
                #Write TCL file
                tcl.write("xload xmp {}\n".format(prjName))
                tcl.write("run netlistclean\n")
                tcl.write("run bits\n")
                tcl.write("exit\n")
                tcl.flush()

                #Call ISE TCL shell
                call = ExtAppCall(".", "xps -nw -scr __edk.tcl")
                call.run_sync(timeout_sec=buildTimeoutSec)
                with open(logFileAbs, "w+") as f:
                    f.write(call.get_stdout())
                #Checks
                if call.get_exit_code() != 0:
                    raise Exception("EDK build exitetd with Non-Zero return code")
                #StdErr cannot be checked since it always contains some entries. So we check stdout for errors
                if "ERROR:" in call.get_stdout():
                    raise Exception("Errors occured. See log file for details.")
                #Ensure that bitstream generation succeeded (to prevent silent-crashes from staying undetected)
                if "Bitstream generation is complete." not in call.get_stdout():
                    raise Exception("Bitstream was not generated")


        #Check Timing
        implDir = os.path.dirname(xmpPath) + "/implementation"
        with OpenWithWildcard(implDir, ".*\.twr") as f:
            content = f.read()
        summaryToEnd = content.split("Timing summary:")[1]
        scoreToEnd = summaryToEnd.split("Score:")[1]
        scoreNr = scoreToEnd.split("(")[0]
        self._timingScore = int(scoreNr.strip())

    def ExportHw(self, xmpPath : str, exportDir : str, logFile : str):
        """
        Export HW to SDK

        :param xmpPath: Path of the .xmp file of the project to export
        :param exportDir: Export directory (the code is exported to <exportDir>/hw)
        :param logFile: Path of the log-file containing all EDK output
        """

        #name-prefix
        xmpFileName = os.path.basename(xmpPath).split(".")[0]

        #Delete existing export files (
        RemoveWithWildcard(exportDir + "/hw", "{}.*\.bmm".format(xmpFileName))
        RemoveWithWildcard(exportDir + "/hw", "{}.*\.html".format(xmpFileName))
        RemoveWithWildcard(exportDir + "/hw", "{}.xml".format(xmpFileName))
        RemoveWithWildcard(exportDir + "/hw", "{}.bit".format(xmpFileName))

        #Export
        logFileAbs = os.path.abspath(logFile)
        prjPath = AbsPathLinuxStyle(os.path.dirname(xmpPath))
        prjName = os.path.basename(xmpPath)
        exportAbs = AbsPathLinuxStyle(exportDir)
        with TempWorkDir(prjPath):
            with TempFile("__edk.tcl") as tcl:
                # Write TCL file
                tcl.write("xload xmp {}\n".format(prjName))
                tcl.write("xset sdk_export_bmm_bit 1\n")
                tcl.write("xset sdk_export_dir {}\n".format(exportAbs))
                tcl.write("run exporttosdk\n")
                tcl.write("exit\n")
                tcl.flush()

                # Call ISE TCL shell
                call = ExtAppCall(".", "xps -nw -scr __edk.tcl")
                call.run_sync(timeout_sec=120)
                #os.system(call.command)
                with open(logFileAbs, "w+") as f:
                    f.write(call.get_stdout())
                # Checks
                if call.get_exit_code() != 0:
                    raise Exception("EDK Export exitetd with Non-Zero return code")
                # StdErr cannot be checked since it always contains some entries. So we check stdout for errors
                if "ERROR:" in call.get_stdout():
                    raise Exception("Errors occured. See log file for details.")

    ####################################################################################################################
    # Public Properties
    ####################################################################################################################
    @property
    def TimingScore(self):
        """
        Get the timing score after a build. Returns None if the score is not available.
        """
        return self._timingScore

    ####################################################################################################################
    # Private Methods
    ####################################################################################################################
    @staticmethod
    def _ExecutePexpect(obj, command : str, expOut : str, timeout : int, file) -> str:
        """
        Execute pexpect and write output into log file

        :param obj: pexpect.spawn object to use
        :param command: Command to execute
        :param expOut: output to wait for (usually the prompt)
        :param timeout: Timeout of the command
        :param file: File to write output into
        :return: command output
        """
        file.write("\n############################################################\n")
        file.write("### {}\n".format(command))
        file.write("############################################################\n")
        obj.sendline(command)
        try:
            obj.expect(expOut, timeout=timeout)
        finally:
            output = obj.before.decode("utf-8", "ignore") + obj.after.decode("utf-8", "ignore")
            file.write(output)
            file.flush()
            return output