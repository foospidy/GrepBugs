GrepBugs
========

A regex based source code scanner.

Usage:
python grepbugs.py -d <source directory>
python grepbugs.py -r github -a <account>
python grepbugs.py -r github -a <account> -f

The latest regular expressions will be pulled from http://www.grepbugs.com
A basic HTML report will be generated in the out/ directory.
Example reports: https://www.grepbugs.com/reports

Dependencies:
- cindex & csearch from (http://swtch.com/~rsc/regexp/regexp4.html). These binaries are included in the third-party/ directory.

- cloc (http://cloc.sourceforge.net/). On Debian run: apt-get install cloc
