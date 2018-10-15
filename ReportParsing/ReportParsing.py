##############################################################################
#  Copyright (c) 2018 by Paul Scherrer Institute, Switzerland
#  All rights reserved.
#  Authors: Oliver Bruendler
##############################################################################
import re
from typing import Dict, List

class ReportMsg:
    """
    This class allows accessing different properties of a message easily. Xilinx messages usually come in the format
    WARNING:Xst:2042, this is interpreted as <severity>:<Tools>:<number>.
    """

    def __init__(self, Tool : str, number : int, severity : str, message : str, line : int):
        """
        Constructor

        :param Tool: Tool that issued the message
        :param number: Message number
        :param severity: Severity of the message
        :param message: Text of the message
        :param line: Line of the message in the report file
        """
        self.tool = Tool
        self.number = number
        self.severity = severity
        self.message = message
        self.line = line


class SynthesisReport:
    """
    This class represents a synthesis report ("*.syr)
    """

    def __init__(self, path : str):
        """
        Constructor (includes parsing the report file)

        :param path: Path of the report file to parse
        """
        self.messages = []
        with open(path) as f:
            line = 0
            for l in f.readlines():
                m = re.match(r"([A-Z]*):([A-Za-z]*):([0-9]*) - (.*)", l)
                if m is not None:
                    self.messages.append(ReportMsg(m.group(2), m.group(3), m.group(1), m.group(4), line))
                line+=1

    def GetMessagesAfterIdentites(self, filterTool : str = None,
                                  filterSeverity : str = None,
                                  filterNumber : int = None) -> Dict[str,List[ReportMsg]]:
        """
        Get messages ordered after their identities (<severity>:<tool>:<number>). Additionally the messages can be filtered.

        :param filterTool: Only get messages from a given tool (optional)
        :param filterSeverity: Only get messages of a given severity (optional)
        :param filterNumber: Only get a specific message number (optional)
        :return: A dictionary containing message identities ("<severity>:<tool>:<number>") as keys. Each value of the dictionary
                 is a list containing one entry per message (ReportMsg objects).
        """
        identities = {}
        for msg in self.messages:
            if filterTool != None and filterTool != msg.tool:
                continue
            if filterSeverity != None and filterSeverity != msg.severity:
                continue
            if filterNumber != None and filterNumber != msg.number:
                continue
            identity = "{}:{}:{}".format(msg.severity, msg.tool, msg.number)
            if identity not in identities:
                identities[identity] = []
            identities[identity].append(msg)
        return identities

