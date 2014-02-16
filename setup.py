import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "Chase QFX Fixer",
    version = "0.5.0",
    author = "Darien Hager",
    author_email = "project+chasefixer@technofovea.com",
    description = "Scripts to clean up Chase QFX transaction files.",
    license = "Creative Commons Attribution-ShareAlike 4.0 International License",
    keywords = "jp morgan chase qfx quicken ofx account transaction xml",
    url = "http://github.com/DHager/chasefixer",
    packages=['chase_fixer'],
    long_description=read('readme.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Environment :: Console",
        ],
    entry_points = {
        'console_scripts': ['fixchaseqfx=chase_fixer.command_line:shell_entry'],
        }
    )