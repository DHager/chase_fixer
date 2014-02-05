__author__ = 'Darien'

import re
import xml.etree.ElementTree as ET
import xml.sax.saxutils as saxutils
from StringIO import StringIO


class FormatInfo(object):
    complexTags = [
        "AVAILBAL",
        "BANKACCTFROM",
        "BANKMSGSRSV1",
        "BANKTRANLIST",
        "FI",
        "LEDGERBAL",
        "OFX",
        "SIGNONMSGSRSV1",
        "SONRS",
        "STATUS",
        "STMTRS",
        "STMTTRN",
        "STMTTRNRS"
    ]
    metaRex = re.compile(r"^([^:<]+):(.*)$")
    startTagRex = re.compile(r"^<([^/>]+)>(.*)$")
    endTagRex = re.compile(r"^</([^/>]+)>$")


class QfxWalker(object):
    def __init__(self):
        self.debug = False

        self.lineNumber = -1
        self.currentLine = ""
        self.stack = []
        self.meta = {}
        self.statement = {}

    def echo(self, *args):
        if not self.debug:
            return
        s = '\t'.join(str(i) for i in args)
        print(s)

    def handleFile(self, f):
        self.lineNumber = 0
        self.currentLine = ""

        for l in f:
            self.currentLine = l
            self.lineNumber += 1
            self.handleLine(l)

    def handleLine(self, l):
        l = l.lstrip()
        if len(l) == 0:
            return

        match = FormatInfo.metaRex.match(l)
        if match:
            self.handleMeta(match.group(1), match.group(2))
            return

        match = FormatInfo.startTagRex.match(l)
        if match:
            tagname = match.group(1)
            if tagname in FormatInfo.complexTags:
                self.handleStart(tagname)
            else:
                self.handleItem(tagname, match.group(2))
            return

        match = FormatInfo.endTagRex.match(l)
        if match:
            self.handleEnd(match.group(1))
            return

    def handleMeta(self, key, val):
        self.meta[key] = val
        self.echo("META: ", key, val)
        if key == "VERSION":
            if val != 102:
                # Assumes SGML format for Chase files, as of Jan 2014 (version 102, charset 1252)
                self.echo("WARN: This code has not been tested with version " + val + ".")

    def handleStart(self, tagname):
        self.stack.append(tagname)
        self.echo("PUSH: ", tagname)

    def handleItem(self, tagname, content):
        self.echo("ITEM: ", tagname, content)

    def handleEnd(self, tagname):
        old = self.stack.pop()
        if old != tagname:
            raise Exception(
                "Tag mismatch, cannot close " + old + " with " + tagname + " on line " + str(self.lineNumber))
        self.echo("POP: ", old)


class QfxToXml(QfxWalker):
    def __init__(self):
        super(QfxToXml, self).__init__()
        self.debug = False
        self.stack2 = []
        self.tree = None

    def handleFile(self, f):
        root = ET.Element("root")
        self.tree = ET.ElementTree(root)
        self.stack2.append(root)
        super(QfxToXml, self).handleFile(f)
        self.stack2.pop()

    def handleMeta(self, key, val):
        super(QfxToXml, self).handleMeta(key, val)
        child = ET.SubElement(self.stack2[-1], 'meta')
        child.set("key", key)
        child.text = val

    def handleStart(self, tagname):
        super(QfxToXml, self).handleStart(tagname)
        child = ET.SubElement(self.stack2[-1], tagname)
        self.stack2.append(child)

    def handleItem(self, tagname, content):
        super(QfxToXml, self).handleItem(tagname, content)
        child = ET.SubElement(self.stack2[-1], tagname)
        # Things like &amp; are already escaped in source, we don't want
        # to accidentally double-scape them
        child.text = saxutils.unescape(content)

    def handleEnd(self, tagname):
        super(QfxToXml, self).handleEnd(tagname)
        self.stack2.pop()

    def write(self, dest):
            self.tree.write(dest)

    def tostring(self):
        return ET.tostring(self.tree.getroot())


class StatementWalker(object):
    def __init__(self, root):
        """
        :param root:
        :type root: xml.etree.Element
        """
        self.root = root

    def walk(self, visitor):
        """
        :param visitor:
        :type visitor: AbstractStatementVisitor
        """
        statementNodes = self.root.findall("./OFX/BANKMSGSRSV1/STMTTRNRS/STMTRS/BANKTRANLIST/STMTTRN")
        for statementNode in statementNodes:
            values = {}
            for childNode in statementNode:
                values[childNode.tag] = childNode.text

            visitor.visit(values)

            for tag in values:
                modified = False
                for childNode in statementNode:
                    if childNode.tag == tag:
                        if values.get(tag) is None:
                            statementNode.remove(childNode)
                        else:
                            childNode.text = values.get(tag)
                        modified = True
                        break  # Assume no duplicate entries

                if not modified:
                    childNode = ET.SubElement(statementNode, tag)
                    childNode.text = values.get(tag)


class AbstractStatementVisitor(object):
    def visit(self, values):
        """
        :param values:
        :type values: dict
        :raise: NotImplementedError
        """
        raise NotImplementedError()


def __recur(buf, node):
    buf.write("<")
    buf.write(node.tag)
    buf.write(">")
    if node.text is not None:
        buf.write(saxutils.escape(node.text))
    buf.write("\n")
    if node.tag in FormatInfo.complexTags:
        for child in node:
            __recur(buf, child)
        buf.write("</")
        buf.write(node.tag)
        buf.write(">\n")


def xmlToQfxString(root):
    """
    :param root:
    :type root: xml.etree.Element
    """
    buf = StringIO()
    buf.write("\n")

    metas = root.findall("./meta")
    for metaNode in metas:
        buf.write(metaNode.attrib["key"])
        buf.write(":")
        buf.write(metaNode.text)
        buf.write("\n")

    main = root.find("./OFX")
    __recur(buf, main)
    return buf.getvalue()
