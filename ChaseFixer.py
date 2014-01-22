#!/usr/bin/python
## ASSUMES SGML FORMAT FOR CHASE QFX FILES AS OF JAN 2014 (v 102, charset 1252)

import io
import sys
from ChaseQfx import QfxToXml, QfxWalker


class ChaseFixer(QfxWalker):
    def __init__(self):
        super(ChaseFixer, self).__init__()
        self.debug = False
        self.transaction = None

    def handleStart(self, tagname):
        super(ChaseFixer, self).handleStart(tagname)
        if tagname == "STMTTRN":
            self.transaction = {}
            self.transaction["NAME"] = ""
            self.transaction["MEMO"] = ""

    def handleItem(self, tagname, content):
        super(ChaseFixer, self).handleItem(tagname, content)
        if self.transaction is not None:
            if tagname in self.transaction:
                self.transaction[tagname] += content
            else:
                self.transaction[tagname] = content

    def handleEnd(self, tagname):
        super(ChaseFixer, self).handleEnd(tagname)
        if tagname == "STMTTRN":
            combined = self.transaction["NAME"].strip() + " " + self.transaction["MEMO"].strip()
            #self.transaction["NAME"] = combined
            #self.transaction["MEMO"] = ""
            print combined
            self.transaction = None


__author__ = 'Darien Hager'
if __name__ == "__main__":
    src = io.open('C:\Users\Darien\Documents\YNAB\chase_export\example\checking\JPMC.qfx', 'r', encoding='cp1252')
    dest = file('out.xml', 'wb')
    #dest = sys.stdout

    #cf = ChaseFixer()
    #cf.handleFile(f)

    qx = QfxToXml(dest)
    qx.handleFile(src)







