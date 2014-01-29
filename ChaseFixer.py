#!/usr/bin/python

import io
import sys
from ChaseQfx import QfxToXml, QfxWalker, XmlToQfx
import xml.etree.ElementTree as ET


def fixNameAndMemo(name,memo):
    return name + memo, ""


def getNodeText(statementNode, tag):
    xpath = "./" + tag
    child = statementNode.find(xpath)
    if child is None:
        return ""
    else:
        return child.text


def setNodeText(statementNode, tag, val):
    xpath = "./" + tag
    child = statementNode.find(xpath)
    if child is None:
        child = ET.SubElement(statementNode, tag)
    child.text = val

__author__ = 'Darien Hager'
if __name__ == "__main__":
    
    dir = "C:\\Users\\Darien\\Documents\\YNAB\\chase_export\\example\\checking\\"
    fid = "JPMC";
    src = dir + fid + ".qfx"
    mid = dir + fid + ".xml"
    fin = dir + fid + "_fixed.qfx"

    print src
    print mid

    qx = QfxToXml()
    qx.handleFile(io.open(src,'r', encoding='cp1252'))
    qx.getXml(file(mid, 'wb'))

    tree = ET.parse(file(mid, 'rb'))
    statementNodes = tree.findall("./OFX/BANKMSGSRSV1/STMTTRNRS/STMTRS/BANKTRANLIST/STMTTRN")
    for sn in statementNodes:
        n = getNodeText(sn, "NAME")
        m = getNodeText(sn, "MEMO")
        (n, m) = fixNameAndMemo(n, m)
        setNodeText(sn,"NAME",n)
        setNodeText(sn,"MEMO",m)

    tree.write(file(mid, 'wb'))

    # TODO write to fin
    xq = XmlToQfx();
    #xq.write(file(mid, 'rb'), file(fin, 'wb'))







