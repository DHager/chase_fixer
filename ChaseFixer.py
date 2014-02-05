#!/usr/bin/python

import tempfile
import sys
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

    import argparse

    # Set up command-line arguments
    parser = argparse.ArgumentParser(description='Attempt to fix up a Chase QFX file')
    parser.add_argument('src', type=argparse.FileType('r'),
                        help='Filename of QFX file to read.')
    parser.add_argument('dst', type=argparse.FileType('w'), nargs='?',
                        default=sys.stdout,
                        help='Filename of output file. If not present, prints to screen.')
    parser.add_argument('--pause', dest='pause',
                        action='store_true', default=False,
                        help='If present, the program will pause before converting its temporary XML file back to QFX.')
    parser.add_argument('--temp', type=str, nargs='?',
                        default=None, dest='temp', metavar="PATH",
                        help='Override location of temporary XML file.')
    args = parser.parse_args()

    # Read from command-line arguments and establish some of the defaults
    if args.temp is None:
        (handle, tempPath) = tempfile.mkstemp(suffix=".xml")
        args.temp = tempPath

    # Read QFX file
    qx = QfxToXml()
    qx.handleFile(args.src)

    # Write to temporary XML
    qx.write(file(args.temp, "wb"))

    # Traverse XML file with fixup code
    tree = ET.parse(args.temp)
    root = tree.getroot()
    walker = StatementWalker(root)
    walker.walk(MyStatementFixer())

    # Write our changes back to XML file
    file(args.temp, "wb").write(ET.tostring(root))

    # Maybe give user a chance to modify the XML before we translate it back
    if args.pause:
        print "Temporary file located at: " + args.temp
        raw_input("Pausing in case you want to modify it with other tools. Press enter to continue...")
        pass

    # Convert XML to QFX and save the result
    args.dst.write(xmlToQfxString(root))

    # Future thoughts:
    #
    # Perhaps the best way to do this is to download the QFX **AND** the CSV and sythesize them, or possibly
    # generate the QFX entirely from the CSV if applicable.
    #
    # First check whether QFX files are allowed to have longer strings, since it might not entirely be JPMC's fault
