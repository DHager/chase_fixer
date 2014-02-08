from ChaseFixer import main
from gettext import gettext
import io
import sys

__author__ = 'Darien Hager'
if __name__ == "__main__":

    import argparse

    class EncodingAwareFileType(object):
        """
        Hacked up version of argparse.FileType that takes an encoding and uses io.open
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