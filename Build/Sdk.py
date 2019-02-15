##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler, Waldemar Koprek
##############################################################################

########################################################################################################################
# Import Statements
########################################################################################################################
import sys
import os
import time
from PsiPyUtils.EnvVariables import AddToPathVariable
from PsiPyUtils import ExtAppCall
from PsiPyUtils.FileOperations import *
import shutil
from typing import List
import re

########################################################################################################################
# Constants
########################################################################################################################
EXPECTED_ERRORS = [
    # KW82: The LibGen for PowerPC prints to stderr an info message of content like:
    # "powerpc-eabi-ar: creating ../../../lib/libxil.a"
    # The If below filters it out
    "[^\n]*powerpc-eabi-ar[^\n]+creating[^\n]+libxil.a[\n]?",

    #possibly more messages to come
]

########################################################################################################################
# Exceptions
########################################################################################################################
class SdkStdErrNotEmpty(Exception):
    pass

class SdkExitCodeNotZero(Exception):
    pass

########################################################################################################################
# Class Defintion
########################################################################################################################
class Sdk:
    """
    This class allows building SDK projects from the command line.
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
        self._fullStdout = ""
        self._lastStdout = ""
        self._lastStderr = ""
        if sys.platform.startswith("win"):
            AddToPathVariable("XILINX",     "{}/ISE_DS/ISE".format(self._isePath))
            # Is not necessary. It only confuses the next call of xps in the Edk class
            # AddToPathVariable("XILINX_EDK", "{}/ISE_DS/ISE".format(self._isePath))
            AddToPathVariable("PATH",       "{}/ISE_DS/EDK/gnuwin/bin".format(self._isePath))
            AddToPathVariable("PATH",       "{}/ISE_DS/EDK/gnu/microblaze/nt/bin".format(self._isePath))
            AddToPathVariable("PATH",       "{}/ISE_DS/EDK/gnu/powerpc-eabi/nt/bin".format(self._isePath))
            AddToPathVariable("PATH",       "{}/ISE_DS/EDK/bin/nt64".format(self._isePath))
            AddToPathVariable("PATH",       "{}/ISE_DS/ISE/bin/nt64".format(self._isePath))
            self._eclipseCmd = '"{}/ISE_DS/EDK/eclipse/nt64/eclipse/eclipse"'.format(self._isePath)
            self._jrePath    = '"{}/ISE_DS/ISE/java6/nt64/jre/bin"'.format(self._isePath)
        elif sys.platform.startswith("linux"):
            AddToPathVariable("XILINX",     "{}/ISE_DS/ISE".format(self._isePath))
            # AddToPathVariable("XILINX_EDK", "{}/ISE_DS/ISE".format(self._isePath))
            AddToPathVariable("PATH",       "{}/ISE_DS/EDK/gnu/microblaze/lin/bin".format(self._isePath))
            AddToPathVariable("PATH",       "{}/ISE_DS/EDK/gnu/powerpc-eabi/lin/bin".format(self._isePath))
            AddToPathVariable("PATH",       "{}/ISE_DS/EDK/bin/lin64".format(self._isePath))
            AddToPathVariable("PATH",       "{}/ISE_DS/ISE/bin/lin64".format(self._isePath))
            self._eclipseCmd = '"{}/ISE_DS/EDK/eclipse/lin64/eclipse/eclipse"'.format(self._isePath)
            self._jrePath    = '"{}/ISE_DS/ISE/java6/lin64/jre/bin"'.format(self._isePath)
        else:
            raise Exception("OS {} not supported".format(sys.platform))

    def CreateNewWs(self, hwPrjPath : str, bspPrjPath : str, appPrjPath : str, workspacePath : str):
        """
        Create a new workspace and import projects

        :param hwPrjPath: HW Project to import
        :param bspPrjPath:  BSP Project to import
        :param appPrjPath: Application Project to import
        :param workspacePath: Path of the workspace (if it exists, the existing workspace will be deleted!)
        """
        #Store data
        self._lastWs_path = AbsPathLinuxStyle(workspacePath)
        self._lastWs_bspName = os.path.basename(bspPrjPath)
        self._lastWs_appName = os.path.basename(appPrjPath)
        self._lastWs_hwPath = AbsPathLinuxStyle(hwPrjPath)
        self._lastWs_bspPath = AbsPathLinuxStyle(bspPrjPath)

        #Delete workspace if it already exists
        shutil.rmtree(workspacePath, ignore_errors=True)        
        # KW82 - Problem on Windows, need to wait a few seconds until the folder is deleted
        time.sleep(5)
        os.mkdir(workspacePath)

        #Create new workspace
        cmd = self._SdkHeadlessCommand(["-import {} ".format(os.path.abspath(hwPrjPath)),
                                        "-import {} ".format(os.path.abspath(bspPrjPath)),
                                        "-import {} ".format(os.path.abspath(appPrjPath)),
                                        "-data {} ".format(os.path.abspath(workspacePath))])
        call = ExtAppCall(".", cmd)        
        call.run_sync(timeout_sec=60)
        self._UpdateStdOut(call)

    def GenerateBspForCreatedWs(self, cpuInstName : str, timeoutSec = 120):
        """
        Generate BSP for the last workspace created using CreateNewWs()

        :param cpuInstName: Name of the microblaze instance (e.g. microblaze_inst, ppc440_inst)
        :param timeoutSec: Timeout for the BSP build process
        """
        #Find system name
        sysName = FindWithWildcard(self._lastWs_hwPath, ".*\.xml")[0].split(".")[0]

        #Generate bsp
        call = ExtAppCall(self._lastWs_bspPath, "libgen -hw {hwxml} -pe {proc} {mss}".format(
                                hwxml=(self._lastWs_hwPath + "/" + sysName + ".xml"),
                                proc=cpuInstName,
                                mss=sysName + ".mss"))
        call.run_sync(timeout_sec=timeoutSec)
        self._UpdateStdOut(call)

    def BuildCreatedWs(self, timeoutSec = 300):
        """
        Generate BSP for the last workspace created using CreateNewWs(). Note that the BSP must already exist before
        BuildCreatedWs() is called.

        COMMON PROBLE: the elfcheck can fail because the default settings in SDK are not correct. To fix this issue,
        change the Hardware Specification path for elfcheckt relative to $(ProjDirPath) for all build configurations (not
        only one).
        Example: -hw ${ProjDirPath}/../hw/system.xml
        AppProject > Properties > C/C++ Build > Settings > Tool Settings > Xilinx ELF Check > Options > Hardware Specification

        :param timeoutSec: Timeout for the build
        """
        #Clean and Build Projects
        cmd = self._SdkHeadlessCommand(["-cleanBuild all",
                                        "-data {}".format(self._lastWs_path)])
        call = ExtAppCall(".", cmd)
        call.run_sync(timeout_sec=timeoutSec)
        self._UpdateStdOut(call)

    def CreateBitstreamWithSw(self, bmmPath : str, bitPath : str, elfPath : str, outputPath : str):
        """
        Merge logic bitstream and ELF into one bitstream

        :param bmmPath: Path to the .bmm file (usually in HW)
        :param bitPath: Path to the .bit file (usually in HW)
        :param elfPath: Path to the .elf file (usually in APP/<config>)
        :param outputPath: Output file path
        """
        call = ExtAppCall(".","data2mem -bm {} -bt {} -bd {} -o b {}".format(bmmPath, bitPath, elfPath, outputPath))
        call.run_sync(timeout_sec=60)
        self._UpdateStdOut(call)

    def ClearFullStdout(self):
        """
        The property FullStdOut contains the full standard-output since the Sdk object was created. To clear it (e.g.
        between different builds) the function ClearFullSTdout can be used.
        """
        self._fullStdout = ""

    ####################################################################################################################
    # Public Properties
    ####################################################################################################################
    @property
    def FullStdOut(self):
        """
        The property FullStdOut contains the full standard-output since the Sdk object was created. To clear it (e.g.
        between different builds) the function ClearFullSTdout can be used.
        """
        return self._fullStdout

    @property
    def StdOut(self):
        """
        Get standard output of the last command executed
        :return:
        """
        return self._lastStdout

    @property
    def StdErr(self):
        """
        Get standard error of the last command executed
        :return:
        """
        return self._lastStderr


    ####################################################################################################################
    # Private Methods
    ####################################################################################################################
    def _SdkHeadlessCommand(self, options : List[str]):
        cmdBase = "{eclipse} -vm {vm} -nosplash -application org.eclipse.cdt.managedbuilder.core.headlessbuild".format(eclipse=self._eclipseCmd, vm=self._jrePath)
        options = " ".join(options)
        cmdEnd = "-vmargs -Dorg.eclipse.cdt.core.console=org.eclipse.cdt.core.systemConsole"
        return " ".join([cmdBase, options, cmdEnd])

    @classmethod
    def _RemoveExpectedMessagesFromStderr(cls, stderr : str) -> str:
        for msg in EXPECTED_ERRORS:
            stderr = re.sub(msg, "", stderr)
        return stderr

    def _UpdateStdOut(self, call : ExtAppCall):
        self._lastStderr = self._RemoveExpectedMessagesFromStderr(call.get_stderr())
        self._lastStdout = call.get_stdout()
        self._fullStdout += "\n##################################################################\n"
        self._fullStdout += "### {}\n".format(call.command)
        self._fullStdout += "##################################################################\n"
        self._fullStdout += self._lastStdout
        stderr = self._lastStderr
        exitCode = call.get_exit_code()
        if len(stderr) != 0:
            raise SdkStdErrNotEmpty("STDERR not empty:\n<includes expected errors!>\n" + self._lastStderr)
        if exitCode != 0:
            raise SdkExitCodeNotZero("Command exited with code {}".format(exitCode))
