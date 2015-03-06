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
The etc/grepbugs.cfg file can be used to configure:
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

- MySQL support
  - On Debian run:
    - apt-get install python-mysqldb, if this does not work then try:
      - apt-get install libmysqlclient-dev
      - pip install MySQL-python

Creating MySQL Database:
Create a database and run the following create statements.

CREATE TABLE `projects` (
  `project_id` varchar(36) NOT NULL,
  `repo` varchar(50) NOT NULL,
  `account` varchar(50) NOT NULL,
  `project` varchar(100) DEFAULT NULL,
  `last_scan` datetime DEFAULT NULL,
  PRIMARY KEY (`project_id`),
  KEY `idx_account` (`account`)
);

CREATE TABLE `results` (
  `result_id` varchar(36) NOT NULL,
  `scan_id` varchar(36) NOT NULL,
  `language` varchar(50) DEFAULT NULL,
  `regex_id` int(11) DEFAULT NULL,
  `regex_text` text,
  `description` text,
  PRIMARY KEY (`result_id`),
  KEY `idx_scan_id` (`scan_id`)
);

CREATE TABLE `results_detail` (
  `result_detail_id` varchar(36) NOT NULL,
  `result_id` varchar(36) NOT NULL,
  `file` text,
  `line` int(11) DEFAULT NULL,
  `code` text,
  PRIMARY KEY (`result_detail_id`),
  KEY `idx_result_id` (`result_id`)
);

CREATE TABLE `scans` (
  `scan_id` varchar(36) NOT NULL,
  `project_id` varchar(36) DEFAULT NULL,
  `date_time` datetime DEFAULT NULL,
  `cloc_out` text,
  PRIMARY KEY (`scan_id`),
  KEY `idx_project_id` (`project_id`)
);
