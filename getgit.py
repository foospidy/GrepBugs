#!/usr/bin/python

import os
import sys
import json
from subprocess import call

repofile = os.path.dirname(os.path.abspath(__file__)) + '/' + sys.argv[1] + '/repos'
srcdir   = os.path.dirname(os.path.abspath(__file__)) + '/' + sys.argv[1]

r        = open(repofile, 'r')
data     = json.load(r)

r.close() 

for i in range(0, len(data)):
	call(['rm', '-rf', srcdir + '/' + data[i]['name']])
	call(['git', 'clone', data[i]['clone_url'], srcdir + '/' + data[i]['name']])

