GrepBugs
========

A regex based source code scanner.

these scripts depend on and require
- cindex & csearch from (http://swtch.com/~rsc/regexp/regexp4.html). These binaries are included in the third-party/ directory.
- cloc (http://cloc.sourceforge.net/)

The regular expressions used for grepping are sourced from http://www.grepbugs.com

Usage:
python grepbugs.py -d <source directory>
python grepbugs.py -r github -a <account>

For the above commands a basic HTML report will be generated in the out/ directory.

