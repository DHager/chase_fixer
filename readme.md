## Prerequisites

These scripts require Python 2.7 or above to run, but have no additional dependencies.

## Installing

You can optionally install this tool using Distutils: Running `setup.py install` will create a `fixchaseqfx` command. Installing this way is not required, it just makes it more convenient to use.

If you merely want to experiment a bit, you can access the command-line interface by running `chase_fixer/command_line.py` .

## Quick-and-dirty running on Windows

Change `example.bat` so that its `maindir` value is the directory where you have saved `JPMC.csv` and `JPMC.qfx` files. Running the batch file should cause `JPMC_fixed.qfx` to be created.

## Developing

### New memo/name pattern matching

You may add new patterns and replacements to the class `MyStatementFixer` inside `chase_fixer/fixer.py`.

### New statement-visitors

Subclass your own `AbstractStatementVisitor` and alter the `main()` method in `command_line.py` so that it walks through statements.

### External or non-python tinkering

The script generates a temporary XML file that you can modify before it generates the final QFX output. Simply pass the `--pause` argument and it will pause so that you can make your own changes.

## Getting your files from Chase

For best accuracy, you will want to download not only a QFX file but also a CSV version of activity on your account.

(TODO: Find exact wording on Chase website)