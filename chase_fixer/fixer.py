import copy
import csv
import re

from qfxtoxml import QfxToXml, StatementWalker, AbstractStatementVisitor, xmlToQfxString


__author__ = 'Darien Hager'


def print_debug_linelengths(self, lines):
    print " 00000000001111111111222222222233 "
    print " 01234567890123456789012345678901 "
    for line in lines:
        print "|" + line + "|"
    print "\n"


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
            csvStr = row[self.fieldNames["DESC"]].lower()
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
    def __init__(self, matchingRows=None):
        super(MyStatementFixer, self).__init__()
        self.debug = True
        if matchingRows is None:
            matchingRows = {}
        self.matchingRows = matchingRows

        # In order of testing. Put "strict" versions that expect good data ahead of "last-ditch-effort" ones
        self.regexes = [
            (
                # Move extra ATM withdrawal stuff to memo so that we have one payee
                # ex> ATM WITHDRAWAL                       123456  12/3110550 NE ST'
                r"^ATM WITHDRAWAL\s+(\d{6})\s+(\d{2}/\d{2})(.*)$",
                lambda m: ("ATM Withdrawal", "%s %s %s" % m.group(1, 2, 3))
            ), (
                # Move extra ATM deposit stuff to memo, which is mainly date/location data
                # ex> ATM CHECK DEPOSIT 12/31 123 SW 123TH STREET CITY WA
                r"^ATM CHECK DEPOSIT(.*)$",
                lambda m: ("ATM Check Deposit", m.group(1))
            ), (
                # (Expects CSV-quality description)
                # Fix online bill-pay where the transaction ID is (for some reason) always part of the name field
                # ex>
                r"^Online Payment (\d{10}) To (.*?) (\d\d/\d\d)$",
                lambda m: (m.group(2), "Online payment %s on %s" % m.group(1, 3))
            ), (
                # (Expects CSV-quality description)
                # Fix the rare transfers where the transaction ID is too early and duplicated.
                # End date may or may not be present.
                # ex> 'Online Transfer 1234567890 to Otherbank ########1234 transaction #: 1234567890 12/31'
                r"^Online Transfer (\d{10}) (to|from) (.+?) transaction\s*#:\s*(\d{10})(.*)$",
                lambda m: (m.group(3), "Transfer (%s) trans# %s or %s %s" % m.group(2, 1, 4, 5))
            ), (
                # Fix the rare transfers where the transaction ID is too early and move it to the memo.
                # ex> Online Transfer to SAV ...1234 transaction#: 1234567890 12/23
                r"^Online Transfer (\d{10}) (to|from) (.*)$",
                lambda m: ("Online transfer %s %s" % m.group(2, 3), m.group(1))
            ), (
                # Pull out payee from transfers
                # End date may or may not be present.
                # ex> Online Transfer to SAV ...1234 transaction#: 1234567890 12/23
                r"^Online Transfer (to|from) (.+?)\s+transaction\s*#:\s*(\d{10})(.*)$",
                lambda m: (m.group(2), "Online Transfer (%s) trans# %s %s" % m.group(1, 3, 4))
            ), (
                # (Expects CSV-quality description)
                # ex> 'Credit Return: Online Payment 1234567890 To Somebody'
                r"^Credit Return: Online Payment (\d{10}) To (.*)$",
                lambda m: (m.group(2), "Credit return from online payment %s" % m.group(1))
            )
        ]

        # Compile regex strings
        self.regexes = [(re.compile(pat, re.IGNORECASE), func) for (pat, func) in self.regexes]

    def visit(self, values, stmtNode):
        row = None
        if stmtNode in self.matchingRows.keys():
            row = self.matchingRows[stmtNode]

        name = values.get("NAME", "")
        memo = values.get("MEMO", "")

        if row is not None:
            combined = row['Description']
        else:
            if len(name) > 32:
                raise Exception("Unexpected name of >32 chars")
            combined = name + " " + memo

        fixedUp = False
        for (rex, func) in self.regexes:
            matches = rex.match(combined)
            if matches:
                (name, memo) = func(matches)
                fixedUp = True
                break

        if not fixedUp and row is not None:
            # Just in case we don't match anything but DO have CSV data,
            # re-implement Chase's splitting but without the problematic
            # whitespace trim or post-64-char truncation
            splitpoint = min(32, len(combined))
            name = combined[0:splitpoint]
            memo = combined[splitpoint:]

        values["NAME"] = name
        values["MEMO"] = memo
