from ChaseFixer import *
import io
import os.path

if __name__ == "__main__":

    qfxdir = "C:\\Users\\Darien\\Documents\\YNAB\\chase_export\\example\\checking\\"

    src = os.path.join(qfxdir, "JPMC.qfx")
    mid = os.path.join(qfxdir, "JPMC.xml")
    dst = os.path.join(qfxdir, "JPMC_fixed.qfx")

    qx = QfxToXml()
    qx.handleFile(io.open(src, 'r', encoding='cp1252'))

    qx.write(file(mid, "wb"))
    tree = ET.parse(mid)
    root = tree.getroot()
    walker = StatementWalker(root)
    walker.walk(MyStatementFixer())

    file(mid, "wb").write(ET.tostring(root))
    file(dst, "wb").write(xmlToQfxString(root))

    # Future thoughts:
    #
    # Perhaps the best way to do this is to download the QFX **AND** the CSV and sythesize them, or possibly
    # generate the QFX entirely from the CSV if applicable.
    #
    # First check whether QFX files are allowed to have longer strings, since it might not entirely be JPMC's fault