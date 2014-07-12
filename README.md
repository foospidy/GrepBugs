GrepBugs
========

A regex based source code scanner.

these scripts depend on and require
- cindex & csearch from (http://swtch.com/~rsc/regexp/regexp4.html). These binaries are included in the third-party/ directory.
- cloc (http://cloc.sourceforge.net/)

The regular expressions used for grepping are sourced from http://www.grepbugs.com

Usage:
python grepbugs.py &lt;directory containing source code&gt;

This can also be used to scan entire github accounts by specifying the account username with the grepgit script

Usage:
./grepgit

For the above commands a basic HTML report will be generated in the out/ directory.
