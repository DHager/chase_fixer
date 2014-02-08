"""
Used for IDE-debugging runs
"""
from ChaseFixer import commandlineRun
import io
import sys
import os.path


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

if __name__ == "__main__":

    qfxdir = "./dataset/"

    src = os.path.join(qfxdir, "JPMC.qfx")
    csv = os.path.join(qfxdir, "JPMC.csv")
    mid = os.path.join(qfxdir, "JPMC.xml")
    dst = os.path.join(qfxdir, "JPMC_fixed.qfx")

    args = AttrDict({
        "pause": False,
        "temp": mid,
        "csvsrc": io.open(csv, "r"),
        "src": io.open(src, "r", encoding="cp1252"),
        "dst": io.open(dst, "w", encoding="cp1252")
    })

    commandlineRun(args)

