#!/usr/bin/python

import io
import copy
import csv
import tempfile
import re
from ChaseQfx import QfxToXml, StatementWalker, AbstractStatementVisitor, xmlToQfxString
import xml.etree.ElementTree as ET

__author__ = 'Darien Hager'

class CsvCorrelator(AbstractStatementVisitor):
    def __init__(self, src):
        super(CsvCorrelator, self).__init__()
        self.qfxRe = re.compile(r'^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\[(\d+):(\w+)]$')
        self.src = src
        self.reader = csv.DictReader(src, delimiter=',', quotechar='"')
        self.fieldNames = {
            "DATE": "Post Date",
            "DESC": "Description",
            "AMT": "Amount"
        }
        self.rows = []
        self.matchingRows = {}

        for fname in self.fieldNames.values():
            if fname not in self.reader.fieldnames:
                raise Exception("CSV file is missing expected field '" + fname + "'")
        self._loadCsvRows()

    def _loadCsvRows(self):
        while True:
            try:
                n = self.reader.next()
                self.rows.append(n)
            except StopIteration:
                break

    def _convertQfxDate(self, qdate):
        matches = self.qfxRe.match(qdate)
        if not matches:
            raise Exception("Invalid QFX date encountered: " + qdate)
        year = matches.group(1)
        month = matches.group(2)
        day = matches.group(3)

        # To format expected in CSV
        return month + "/" + day + "/" + year

    def _findRow(self, date, amt, name, memo):
        wsRe = re.compile(r'\s+')

        for row in self.rows:
            if row[self.fieldNames["DATE"]] != date:
                continue
            if float(row[self.fieldNames["AMT"]]) != amt:
                continue

            # Ignore case...
            csvStr= row[self.fieldNames["DESC"]].lower()
            qfxStr = (name + memo).lower()

            # Ignore whitespace...
            csvStr = re.sub(wsRe, '', csvStr)
            qfxStr = re.sub(wsRe, '', qfxStr)

            assert(len(qfxStr) <= len(csvStr))
            # Compare that one is inside the other
            if csvStr.find(qfxStr, 0, len(qfxStr)) < 0:
                continue

            return row

        return None

    def visit(self, values, stmtNode):

        date = values.get("DTPOSTED", "00000000120000[0:GMT]")
        date = self._convertQfxDate(date)

        amt = float(values.get("TRNAMT", "0.0"))

        row = self._findRow(
            date,
            amt,
            values.get("NAME", ""),
            values.get("MEMO", "")
        )
        if row is None:
            self.matchingRows[stmtNode] = None
            return  # Should this get logged?

        self.matchingRows[stmtNode] = row

    def getMatchedRows(self):
        return copy.copy(self.matchingRows)


class MyStatementFixer(AbstractStatementVisitor):
    def __init__(self, matchingRows={}):
        super(MyStatementFixer, self).__init__()
        self.debug = True
        self.matchingRows = matchingRows

        self.regexes = [
            (
                # Move extra ATM withdrawal stuff to memo so that we have one payee
                re.compile(r"^ATM WITHDRAWAL\s+(\d{6})\s+(\d{2}/\d{6})\s*(.*)$"),
                lambda m: ("ATM WITHDRAWAL", " ".join([m.group(1), m.group(2), m.group(3)]))
            ),
            (
                # Move extra ATM deposit stuff to memo, which is mainly location-based metadata anyway
                re.compile(r"^ATM CHECK DEPOSIT(.*)$"),
                lambda m: ("ATM CHECK DEPOSIT", m.group(1))
            ),
            (
                # Fix online bill-pay where the transaction ID is (for some reason) always part of the name field
                re.compile(r"^Online Payment (\d{10}) To (.*?) (\d\d/\d\d)$"),
                lambda m: (m.group(2), "Online payment " + m.group(1) + " on " + m.group(3))
            ),
            (
                # Fix the rare transfers where the transaction ID is too early and move it to the memo.
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

    def visit(self, values, stmtNode):
        row = None
        if stmtNode in self.matchingRows.keys():
            row = self.matchingRows[stmtNode]

        name = values.get("NAME", "")
        memo = values.get("MEMO", "")

        if row is not None:
            combined = row['Description']
            # Just in case we don't match anything, re-implement Chase's splitting but
            # without the whitespace trim or truncation
            splitpoint = min(32, len(combined))
            name = combined[0:splitpoint]
            memo = combined[splitpoint:]
            pass
        else:
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


def main(args):

    if args.temp is None:
        (handle, tempPath) = tempfile.mkstemp(suffix=".xml")
        args.temp = tempPath

    # Read QFX file
    qx = QfxToXml()
    qx.handleFile(args.src)

    # Write to temporary XML
    qx.write(io.open(args.temp, "wb"))

    # Prepare walker for taking visitors to statements
    tree = ET.parse(args.temp)
    root = tree.getroot()
    walker = StatementWalker(root)

    matchedRows = {}
    if args.csvsrc is not None:
        csv_visitor = CsvCorrelator(args.csvsrc)  # Tries to acquire original name+memo string from JPMC.csv dumps
        walker.walk(csv_visitor)
        matchedRows = csv_visitor.getMatchedRows()

    fix_visitor = MyStatementFixer(matchedRows)  # Fix up name and memo values based on available information
    walker.walk(fix_visitor)

    # Write our changes back to XML file
    changedXmlString = ET.tostring(root);
    io.open(args.temp, "w", encoding='utf-8').write(unicode(changedXmlString))

    # Maybe give user a chance to modify the XML before we translate it back
    if args.pause:
        print "Temporary file located at: " + args.temp
        raw_input("Pausing in case you want to modify it with other tools. Press enter to continue...")
        pass

    # Convert XML to QFX and save the result
    args.dst.write(xmlToQfxString(root))

