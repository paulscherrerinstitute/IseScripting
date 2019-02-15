##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler
##############################################################################

########################################################################################################################
# Import Statements
########################################################################################################################
import os
import sys
from typing import Dict
from PsiPyUtils import ExtAppCall
from PsiPyUtils.EnvVariables import AddToPathVariable

########################################################################################################################
# Exceptions
########################################################################################################################
class ToolErrNotEmpty(Exception):
    pass

class ToolExitCodeNotZero(Exception):
    pass

########################################################################################################################
# Class Defintion
########################################################################################################################
class Tools:
    """
    This class allows using various ISE commandline tools
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
        self._version = version
        self._isePath = os.environ[isePathEnv].replace('"', '')
        self._lastStdout = ""
        self._lastStderr = ""
        if sys.platform.startswith("win"):
            AddToPathVariable("XILINX",  "{}/ISE_DS/ISE".format(self._isePath))
            AddToPathVariable("PATH",    "{}/ISE_DS/ISE/bin/nt64".format(self._isePath))
        elif sys.platform.startswith("linux"):
            AddToPathVariable("XILINX",  "{}/ISE_DS/ISE".format(self._isePath))
            AddToPathVariable("PATH",    "{}/ISE_DS/ISE/bin/lin64".format(self._isePath))
        else:
            raise Exception("OS {} not supported".format(sys.platform))

    def Promgen(self, outFile : str, bitstreams : Dict[str, str],
                device : str = None, fmt : str = "bin",
                disableByteSwap : bool = False):
        """
        Promgen abstraction

        :param outFile: Name of the output file
        :param bitstreams: Dictionary in the form {address : bitstream_path} containing the bitstreams and the memory offsets
                           they shall be written to. Address and path are both given as strings.
        :param device: Device type (optional, only for Xililnx PROM devices)
        :param fmt: Output format (optional, default is "bin", values: mcs, exo, hex, tek, bin, ieee1532, ufp)
        :param disableByteSwap: Bitswap can be disabled (-b option of promgen)
        """
        #Generate Command
        cmdList = ["promgen"]
        if (device != None):
            cmdList.append("-x {}".format(device))
        if disableByteSwap:
            cmdList.append("-b")
        cmdList.append("-w")
        cmdList.append("-p {}".format(fmt))
        cmdList.append("-o {}".format(outFile))
        for addr, bitstr in bitstreams.items():
            cmdList.append("-u {} {}".format(addr, bitstr))

        #Execute call
        call = ExtAppCall("."," ".join(cmdList))
        call.run_sync(timeout_sec=60)
        self._UpdateStdOut(call)

    ####################################################################################################################
    # Public Properties
    ####################################################################################################################
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
    def _UpdateStdOut(self, call : ExtAppCall):
        self._lastStderr = call.get_stderr()
        self._lastStdout = call.get_stdout()
        #Remove expected error messages
        stderr = self._lastStderr
        if len(stderr) != 0:
            raise ToolErrNotEmpty("STDERR not empty:\n<includes expected errors!>\n" + self._lastStderr)
        if call.get_exit_code() != 0:
            raise ToolExitCodeNotZero("Command exited with code {}".format(call.get_exit_code()))