from gettext import gettext
import io
import sys
import argparse
import tempfile
import xml.etree.ElementTree as ET

from qfxtoxml import QfxToXml, StatementWalker, xmlToQfxString
from fixer import CsvCorrelator, MyStatementFixer

__author__ = 'Darien Hager'


class EncodingAwareFileType(object):
    """
    Subtly hacked up version of argparse.FileType that takes an encoding and uses io.open
    """
    def __init__(self, mode='r', bufsize=-1, encoding="utf-8"):
        self._mode = mode
        self._bufsize = bufsize
        self._encoding = encoding

    def __call__(self, string):
        # the special argument "-" means sys.std{in,out}
        if string == '-':
            if 'r' in self._mode:
                return sys.stdin
            elif 'w' in self._mode:
                return sys.stdout
            else:
                msg = gettext('argument "-" with mode %r') % self._mode
                raise ValueError(msg)

        # all other arguments are used as file names
        try:
            return io.open(string, self._mode, self._bufsize, encoding=self._encoding)
        except IOError as e:
            message = gettext("can't open '%s': %s")
            raise argparse.ArgumentTypeError(message % (string, e))

    def __repr__(self):
        args = self._mode, self._bufsize
        args_str = ', '.join(repr(arg) for arg in args if arg != -1)
        return '%s(%s)' % (type(self).__name__, args_str)

def shell_entry():
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description='Attempt to fix up a Chase QFX file')
    parser.add_argument('src', type=EncodingAwareFileType('r', encoding="cp1252"),
                        help='Filename of QFX file to read, usually called JPMC.QFX')
    parser.add_argument('dst', type=EncodingAwareFileType('w', encoding="cp1252"), nargs='?',
                        default=sys.stdout,
                        help='Filename of output file. If not present, prints to screen.')
    parser.add_argument('--pause', dest='pause',
                        action='store_true', default=False,
                        help='If present, the program will pause before converting its temporary XML file back to QFX.')
    parser.add_argument('--temp', type=str,
                        default=None, dest='temp', metavar="PATH",
                        help='Override location of temporary XML file.')
    parser.add_argument('--csv', type=argparse.FileType('r'),
                        default=None, dest='csvsrc', metavar="PATH",
                        help='Optional CSV copy of the same transactions, which can be read for greater accuracy.'
                             ' Usually called JPMC.CSV.')

    # Parse arguments, throwing an error if necessary
    args = parser.parse_args()
    # If everything looks OK, jump to main program logic
    main(args);


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

if __name__ == "__main__":
    shell_entry()

