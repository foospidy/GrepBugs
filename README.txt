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
- grep (http://www.gnu.org/software/grep/)
  - On Debian run: apt-get install grep
  - On OSX, you will need to install gnu grep (see http://www.heystephenwood.com/2013/09/install-gnu-grep-on-mac-osx.html)

- cloc (http://cloc.sourceforge.net/)
  - On Debian run: apt-get install cloc

- git (http://git-scm.com/)
  - On Debian run: apt-get install git

- svn (https://subversion.apache.org/)
  - On Debian run: apt-get install subversion
