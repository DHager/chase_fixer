@echo off

rem Change directory to wherever you saved the CSV and QFX files
set maindir=.\dataset\

ChaseFixer.py^
 --csv "%maindir%\JPMC.csv"^
 --temp "%maindir%\JPMC.xml"^
 "%maindir%\JPMC.QFX"^
 "%maindir%\JPMC_fixed.QFX"