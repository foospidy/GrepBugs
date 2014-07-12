#!/usr/bin/python

import os
import sys
import urllib2
import json
import sqlite3 as lite
from subprocess import call
import subprocess
import cgi

dbfile   = os.path.dirname(os.path.abspath(__file__)) + '/data/grepbugs.db'
jfile    = os.path.dirname(os.path.abspath(__file__)) + '/data/grepbugs.json'
clocsql  = os.path.dirname(os.path.abspath(__file__)) + '/data/grepbugs.sql'
cloctxt  = os.path.dirname(os.path.abspath(__file__)) + '/data/cloc.txt'
htmlfile = os.path.dirname(os.path.abspath(__file__)) + '/out/index.html'
cindex   = os.path.dirname(os.path.abspath(__file__)) + '/third-party/codesearch/cindex'
csearch  = os.path.dirname(os.path.abspath(__file__)) + '/third-party/codesearch/csearch'
grepext   = os.path.dirname(os.path.abspath(__file__)) + '/grepext'
srcdir   = sys.argv[1]

if 3 == len(sys.argv):
	htmlfile = os.path.dirname(os.path.abspath(__file__)) + '/out/' + sys.argv[2] + '.html'

try:
	db  = lite.connect(dbfile)
	cur = db.cursor()

except lite.Error, e:
	print 'Error connecting to db file'
	sys.exit(1)

# get latest greps
try:
	url = 'http://grepbugs.com/json'
	f   = urllib2.urlopen(url)
	j   = f.read()
	with open(jfile, 'wb') as jsonfile:
		jsonfile.write(j)

except urllib2.URLError:
	print 'Error retreiving grep rules'

# clean database
cur.execute("DROP TABLE IF EXISTS metadata;");
cur.execute("DROP TABLE IF EXISTS t;");

# execute cloc
call(["cloc", "--sql=" + clocsql, "--sql-project=" + srcdir, srcdir])
# run sql script
f = open(clocsql, 'r')
cur.executescript(f.read())
f.close

# execute clock again
call(["cloc", "--quiet", "-out=" + cloctxt, srcdir])
# save data
f = open(cloctxt, 'r')
clocout = f.read()
f.close

#proc = subprocess.Popen(["cloc", "-out=" + cloctxt, srcdir], stdout=subprocess.PIPE)
#cloc = proc.communicate()

# execute cindex
call([cindex, "-reset"])
call([cindex, srcdir])

# load json data
json_file = open(jfile, "r")
data      = json.load(json_file)
json_file.close()

# query database
cur.execute("SELECT DISTINCT Language FROM t;")
rows = cur.fetchall()

# prep html file for output
h = 'ICAgX19fX19fICAgICAgICAgICAgICAgIF9fX18KICAvIF9fX18vX19fX19fXyAgX19fXyAgLyBfXyApX18gIF9fX19fXyBfX19fX18KIC8gLyBfXy8gX19fLyBfIFwvIF9fIFwvIF9fICAvIC8gLyAvIF9fIGAvIF9fXy8KLyAvXy8gLyAvICAvICBfXy8gL18vIC8gL18vIC8gL18vIC8gL18vIChfXyAgKQpcX19fXy9fLyAgIFxfX18vIC5fX18vX19fX18vXF9fLF8vXF9fLCAvX19fXy8KICAgICAgICAgICAgICAvXy8gICAgICAgICAgICAgICAgL19fX18v'

o = open(htmlfile, 'w')
o.write("<pre>\n" + h.decode('base64') + "</pre>")
o.write("<pre>\n" + str(clocout).replace("\n", "<br>") + "</pre>")
o.close()

# grep all the bugs and output to file
o = open(htmlfile, 'a')
for row in rows:
	o.write('<div>')
	count = 0
	for i in range(0, len(data)):
		if row[0] == data[i]["language"]:
			if 0 == count:
				o.write('<h4>' + row[0] + '</h4>')

			ext    = ''
			proc   = subprocess.Popen([grepext, row[0]], stdout=subprocess.PIPE)
			ext    = proc.communicate()

			result = ''
			filter = ".*(" + str(ext[0]) + ")$"
			#print filter
			#call(['echo', csearch, "-f", filter, '"' + str(data[i]["regex"]) + '"']) 
			proc   = subprocess.Popen([csearch, "-i", "-f", filter, data[i]["regex"]], stdout=subprocess.PIPE)
			result = proc.communicate()

			if len(result[0]):
				o.write('<div>')
				o.write('<a href="#" onclick="javascript:o=document.getElementById(\'r' + str(i) + '\');if(o.style.display==\'none\'){ o.style.display=\'block\';} else {o.style.display=\'none\';}">+</a> ' +  cgi.escape(data[i]["regex"]) + " - " + data[i]["description"]) 
				o.write('<div id="r' + str(i) + '" style="display:none;"><pre>' + cgi.escape(str(result[0])).replace("\n", "<br>") + '</pre></div>')
				o.write('</div>')
			count += 1
		else:
			count = 0

	o.write('</div>')

o.close()
db.close()

