#!/usr/bin/python

import io
import re
import os.path
from ChaseQfx import QfxToXml, StatementWalker, AbstractStatementVisitor, xmlToQfxString
import xml.etree.ElementTree as ET


class MyStatementFixer(AbstractStatementVisitor):

    def __init__(self):
        super(MyStatementFixer, self).__init__()
        self.debug = True

        self.regexes = [
            (
                re.compile(r"^ATM WITHDRAWAL\s+(\d{6})\s+(\d{2}/\d{6})\s*(.*)$"),
                lambda m: ("ATM WITHDRAWAL", " ".join([m.group(1), m.group(2), m.group(3)]))
            ),
            (
                re.compile(r"^ATM CHECK DEPOSIT(.*)$"),
                lambda m: ("ATM CHECK DEPOSIT", m.group(1))
            ),
            (
                re.compile(r"^Online Payment (\d{10}) To (\S+) (.*)$"),
                lambda m: (m.group(2) + m.group(3), "Online payment " + m.group(1))
            ),
            (
                re.compile(r"^Online Transfer (\d{10}) (to|from) (.*)"),
                self._fixOnlineTransfer
            ),

        ]

    def _fixOnlineTransfer(self, m):
        name = "Online transfer " + m.group(2) + " " + m.group(3)
        memo = m.group(1)
        return name, memo

    def _display32(self, lines):
        print " 00000000001111111111222222222233 "
        print " 01234567890123456789012345678901 "
        for line in lines:
            print "|" + line + "|"
        print "\n"

    def visit(self, values):
        name = values.get("NAME", "")
        memo = values.get("MEMO", "")

        if len(name) > 32:
            raise Exception("Unexpected name of >32 chars")

        combined = name + " " + memo

        for (rex, func) in self.regexes:
            matches = rex.match(combined)
            if matches:
                (name, memo) = func(matches)
                break

        values["NAME"] = name
        values["MEMO"] = memo


__author__ = 'Darien Hager'
if __name__ == "__main__":
    pass # TODO command-line tool implemntation, content moved to TestRun
