#!/usr/bin/python

import io
import os.path
from ChaseQfx import QfxToXml, StatementWalker, AbstractStatementVisitor
import xml.etree.ElementTree as ET


class StatementVisitor(AbstractStatementVisitor):
    def visit(self, values):
        combined = values.get("NAME","") + values.get("MEMO","")
        values["NAME"] = combined
        values["MEMO"] = "blanked"


__author__ = 'Darien Hager'
if __name__ == "__main__":
    
    qfxdir = "C:\\Users\\Darien\\Documents\\YNAB\\chase_export\\example\\checking\\"

    src = os.path.join(qfxdir, "JPMC.qfx")
    dst = os.path.join(qfxdir, "JPMC.qfx")

    qx = QfxToXml()
    qx.handleFile(io.open(src, 'r', encoding='cp1252'))
    xml = qx.tostring()  # Can also use .write(f) to save to file

    root = ET.fromstring(xml)
    walker = StatementWalker(root)
    visitor = StatementVisitor()
    walker.walk(visitor)

    print ET.tostring(root)
    # TODO write to dst
    # etreeToQfx(tree, file(fin, 'wb'))
