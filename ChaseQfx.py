__author__ = 'Darien'

import re
from xml.sax.saxutils import XMLGenerator


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
        l = l.strip()
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
    def __init__(self, dest):
        super(QfxToXml, self).__init__()
        self.debug = False
        self.generator = XMLGenerator(dest, 'utf-8')

    def handleFile(self, f):
        self.generator.startDocument()
        self.generator.startElement("root", {})
        super(QfxToXml, self).handleFile(f)
        self.generator.endElement("root")
        self.generator.endDocument()

    def handleMeta(self, key, val):
        super(QfxToXml, self).handleMeta(key, val)
        self.generator.startElement("meta", {"key": key})
        self.generator.characters(val)
        self.generator.endElement("meta")

    def handleStart(self, tagname):
        super(QfxToXml, self).handleStart(tagname)
        self.generator.startElement(tagname, {})

    def handleItem(self, tagname, content):
        super(QfxToXml, self).handleItem(tagname, content)
        self.generator.startElement(tagname, {})
        self.generator.characters(content)
        self.generator.endElement(tagname)

    def handleEnd(self, tagname):
        super(QfxToXml, self).handleEnd(tagname)
        self.generator.endElement(tagname)


class XmlToQfx:
    pass