from ChaseFixer import commandlineRun
import sys
import os.path


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

if __name__ == "__main__":

    qfxdir = "C:\\Users\\Darien\\Documents\\YNAB\\chase_export\\example\\checking\\"

    src = os.path.join(qfxdir, "JPMC.qfx")
    csv = os.path.join(qfxdir, "JPMC.csv")
    mid = os.path.join(qfxdir, "JPMC.xml")
    dst = os.path.join(qfxdir, "JPMC_fixed.qfx")

    args = AttrDict({
        "pause": False,
        "temp": mid,
        "csvsrc": open(csv, "rb"),
        "src": open(src, "r"),  # WARNING: RB mode breaks
        "dst": sys.stdout  # open(dst,"wb"),
    })

    commandlineRun(args)

