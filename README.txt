GrepBugs
========

A regex based source code scanner.

Usage:
python grepbugs.py -d <source directory>
python grepbugs.py -r github -a <account>
python grepbugs.py -r github -a <account> -f

The latest regular expressions will be pulled from https://www.grepbugs.com

A basic HTML report will be generated in the out/ directory.  A 
tab-delimited file with a subset of the information is also created.

Example reports: https://www.grepbugs.com/reports

Configuration:
The `etc/grepbugs.cfg` file can be used to configure:
- MySQL database (for storing scan results)
- Path to grep binary

Dependencies:
- GNU grep (http://www.gnu.org/software/grep/)
  - On Debian run: apt-get install grep
  - On OSX, you will need to install gnu grep (see http://www.heystephenwood.com/2013/09/install-gnu-grep-on-mac-osx.html)

- cloc (http://cloc.sourceforge.net/)
  - On Debian run: apt-get install cloc
  - On OSX run: brew install cloc

- git (http://git-scm.com/)
  - On Debian run: apt-get install git
  - On OSX, configure Xcode command line tools

- svn (https://subversion.apache.org/)
  - On Debian run: apt-get install subversion
  - On OSX, configure Xcode command line tools
