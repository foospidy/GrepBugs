#!/usr/bin/python
# GrepBugs Copyright (c) 2014-2015 GrepBugs.com
#
# GrepBugs is licensed under GPL v2.0 or later; please see the main
# LICENSE file in the installation folder for more information.
#

import os
import sys
import shutil
import argparse
import uuid
import requests
import json
import datetime
import sqlite3 as lite
from subprocess import call
import subprocess
import cgi
import time
import logging
import ConfigParser

cfgfile = os.path.dirname(os.path.abspath(__file__)) + '/etc/grepbugs.cfg'
dbfile  = os.path.dirname(os.path.abspath(__file__)) + '/data/grepbugs.db'
gbfile  = os.path.dirname(os.path.abspath(__file__)) + '/data/grepbugs.json'
logfile = os.path.dirname(os.path.abspath(__file__)) + '/log/grepbugs.log'

# get configuration
gbconfig  = ConfigParser.ConfigParser()
gbconfig.read(cfgfile)

# determine which grep binary to use
grepbin = gbconfig.get('grep', 'binary')

# BSD and OS X grep do not support -P; change this to path to GNU grep; e.g. /usr/local/bin/grep, ggrep, etc.
# http://www.heystephenwood.com/2013/09/install-gnu-grep-on-mac-osx.html
if 'darwin' == sys.platform:
	for root, dirnames, filenames in os.walk('/usr/local/Cellar/grep'):
		for filename in filenames:
			if 'ggrep' == filename:
				grepbin = os.path.join(root, filename)

# print "Debug: grepbin = " + grepbin  # uncomment to debug your grep path

# setup logging; create directory if it doesn't exist, and configure logging
if not os.path.exists(os.path.dirname(logfile)):
	os.makedirs(os.path.dirname(logfile))

logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def local_scan(srcdir, repo='none', account='local_scan', project='none'):
	"""
	Perform a scan of local files
	"""
	# new scan so new scan_id
	scan_id = str(uuid.uuid1())
	clocsql = '/tmp/gb.cloc.' + scan_id + '.sql'
	basedir = os.path.dirname(os.path.abspath(__file__)) + '/' + srcdir.rstrip('/')
	logging.info('Using grep binary ' + grepbin)
	logging.info('Starting local scan with scan id ' + scan_id)

	# get db connection
	if 'mysql' == gbconfig.get('database', 'database'):
		try:
			import MySQLdb
			mysqldb  = MySQLdb.connect(host=gbconfig.get('database', 'host'), user=gbconfig.get('database', 'dbuname'), passwd=gbconfig.get('database', 'dbpword'), db=gbconfig.get('database', 'dbname'))
			mysqlcur = mysqldb.cursor()
		except Exception as e:
			print 'Error connecting to MySQL! See log file for details.'
			logging.debug('Error connecting to MySQL: ' + str(e))
			sys.exit(1)

	try:
		db  = lite.connect(dbfile)
		cur = db.cursor()

	except lite.Error as e:
		print 'Error connecting to db file! See log file for details.'
		logging.debug('Error connecting to db file: ' + str(e))
		sys.exit(1)
	except Exception as e:
		print 'CRITICAL: Unhandled exception occured! Quiters gonna quit! See log file for details.'
		logging.critical('Unhandled exception: ' + str(e))
		sys.exit(1)

	if args.u == True:
		print 'Scanning with existing rules set'
		logging.info('Scanning with existing rules set')
	else:
		# get latest greps
		try:
			url = 'https://grepbugs.com/json'
			print 'retreiving rules...'
			logging.info('Retreiving rules from ' + url)

			# if request fails, try 3 times
			count     = 0
			max_tries = 3
			while count < max_tries:
				try:
					headers = {'User-agent': 'GrepBugs for Python (1.0)'}
					r       = requests.get(url, headers=headers)

					with open(gbfile, 'wb') as jsonfile:
						jsonfile.write(r.text)

					print 'got rules!'

					# no exceptions so break out of while loop
					break
				except requests.ConnectionError as e:
					count = count + 1
					if count <= max_tries:
						logging.warning('Error retreiving grep rules: ConnectionError (attempt ' + str(count) + ' of ' + str(max_tries) + '): ' + str(e))
						time.sleep(3)
				
				except requests.HTTPError as e:
					count = count + 1
					if count <= max_tries:
						logging.warning('Error retreiving grep rules: HTTPError (attempt ' + str(count) + ' of ' + str(max_tries) + '): ' + str(e))
						time.sleep(3)
			
				except requests.Timeout as e:
					count = count + 1
					if count <= max_tries:
						logging.warning('Error retreiving grep rules: Timeout (attempt ' + str(count) + ' of ' + str(max_tries) + '): ' + str(e))
						time.sleep(3)
				
				except Exception as e:
					print 'CRITICAL: Unhandled exception occured! Quiters gonna quit! See log file for details.'
					logging.critical('Unhandled exception: ' + str(e))
					sys.exit(1)

			if count == max_tries:
				# grep rules were not retrieved, could be working with old rules.
				logging.debug('Error retreiving grep rules (no more tries left. could be using old grep rules.): ' + str(e))
					
		except Exception as e:
			print 'CRITICAL: Unhandled exception occured! Quiters gonna quit! See log file for details.'
			logging.critical('Unhandled exception: ' + str(e))
			sys.exit(1)

	# prep db for capturing scan results
	try:
		# clean database
		cur.execute("DROP TABLE IF EXISTS metadata;");
		cur.execute("DROP TABLE IF EXISTS t;");
		cur.execute("VACUUM");

		# update database with new project info
		if 'none' == project:
			project = srcdir

		# query database
		params     = [repo, account, project]
		if 'mysql' == gbconfig.get('database', 'database'):
			mysqlcur.execute("SELECT project_id FROM projects WHERE repo=%s AND account=%s AND project=%s LIMIT 1;", params)
			rows = mysqlcur.fetchall()
		else:
			cur.execute("SELECT project_id FROM projects WHERE repo=? AND account=? AND project=? LIMIT 1;", params)
			rows = cur.fetchall()

		# assume new project by default
		newproject = True

		for row in rows:
			# not so fast, not a new project
			newproject = False
			project_id = row[0]

		if True == newproject:
			project_id = str(uuid.uuid1())
			params     = [project_id, repo, account, project]
			if 'mysql' == gbconfig.get('database', 'database'):
				mysqlcur.execute("INSERT INTO projects (project_id, repo, account, project) VALUES (%s, %s, %s, %s);", params)
			else:
				cur.execute("INSERT INTO projects (project_id, repo, account, project) VALUES (?, ?, ?, ?);", params)

		# update database with new scan info
		params  = [scan_id, project_id]
		if 'mysql' == gbconfig.get('database', 'database'):
			mysqlcur.execute("INSERT INTO scans (scan_id, project_id) VALUES (%s, %s);", params)
			mysqldb.commit()
		else:
			cur.execute("INSERT INTO scans (scan_id, project_id) VALUES (?, ?);", params)
			db.commit()

	except Exception as e:
		print 'CRITICAL: Unhandled exception occured! Quiters gonna quit! See log file for details.'
		logging.critical('Unhandled exception: ' + str(e))
		sys.exit(1)

	# execute cloc to get sql output
	try:
		print 'counting source files...'
		logging.info('Running cloc for sql output.')
		return_code = call(["cloc", "--skip-uniqueness", "--quiet", "--sql=" + clocsql, "--sql-project=" + srcdir, srcdir])
		if 0 != return_code:
			logging.debug('WARNING: cloc did not run normally. return code: ' + str(return_code))

		# run sql script generated by cloc to save output to database
		f = open(clocsql, 'r')
		cur.executescript(f.read())
		db.commit()
		f.close
		os.remove(clocsql)

	except Exception as e:
		print 'Error executing cloc sql! Aborting scan! See log file for details.'
		logging.debug('Error executing cloc sql (scan aborted). It is possible there were no results from running cloc.: ' + str(e))
		return scan_id

	# query cloc results
	cur.execute("SELECT Language, count(File), SUM(nBlank), SUM(nComment), SUM(nCode) FROM t GROUP BY Language ORDER BY Language;")
	
	rows    = cur.fetchall()
	cloctxt =  '-------------------------------------------------------------------------------' + "\n"
	cloctxt += 'Language                     files          blank        comment           code' + "\n"
	cloctxt += '-------------------------------------------------------------------------------' + "\n"
	
	sum_files   = 0
	sum_blank   = 0
	sum_comment = 0
	sum_code    = 0

	for row in rows:
		cloctxt += '{0:20}  {1:>12}  {2:>13} {3:>14} {4:>14}'.format(str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4])) + "\n"
		sum_files   += row[1]
		sum_blank   += row[2]
		sum_comment += row[3]
		sum_code    += row[4]
	
	cloctxt += '-------------------------------------------------------------------------------' + "\n"
	cloctxt += '{0:20}  {1:>12}  {2:>13} {3:>14} {4:>14}'.format('Sum', str(sum_files), str(sum_blank), str(sum_comment), str(sum_code)) + "\n"
	cloctxt += '-------------------------------------------------------------------------------' + "\n"

	# execute clock again to get txt output
	try:
		params = [cloctxt, scan_id]
		if 'mysql' == gbconfig.get('database', 'database'):
			mysqlcur.execute("UPDATE scans SET date_time=NOW(), cloc_out=%s WHERE scan_id=%s;", params)
			mysqldb.commit()
		else:
			cur.execute("UPDATE scans SET cloc_out=? WHERE scan_id=?;", params)
			db.commit()

	except Exception as e:
		print 'Error saving cloc txt! Aborting scan! See log file for details.'
		logging.debug('Error saving cloc txt (scan aborted): ' + str(e))
		return scan_id

	# load json data
	try:
		logging.info('Reading grep rules from json file.')
		json_file = open(gbfile, "r")
		greps     = json.load(json_file)
		json_file.close()
	except Exception as e:
		print 'CRITICAL: Unhandled exception occured! Quiters gonna quit! See log file for details.'
		logging.critical('Unhandled exception: ' + str(e))
		sys.exit(1)

	# query database
	cur.execute("SELECT DISTINCT Language FROM t ORDER BY Language;")
	rows = cur.fetchall()

	# grep all the bugs and output to file
	print 'grepping for bugs...'
	logging.info('Start grepping for bugs.')

	# get cloc extensions and create extension array
	clocext  = ''
	proc     = subprocess.Popen(["cloc", "--show-ext"], stdout=subprocess.PIPE)
	ext      = proc.communicate()
	extarray = str(ext[0]).split("\n")
	
	# override some extensions
	extarray.append('inc -> PHP')
	
	# loop through languages identified by cloc
	for row in rows:
		count = 0
		# loop through all grep rules for each language identified by cloc
		for i in range(0, len(greps)):
				# if the language matches a language in the gb rules file then do stuff
				if row[0] == greps[i]['language']:

					# get all applicable extensions based on language
					extensions = []
					for ii in range(0, len(extarray)):
						lang = str(extarray[ii]).split("->")
						if len(lang) > 1:							
							if str(lang[1]).strip() == greps[i]['language']:
								extensions.append(str(lang[0]).strip())

					# search with regex, filter by extensions, and capture result
					result = ''
					filter = []

					# build filter by extension
					for e in extensions:
						filter.append('--include=*.' + e)

					try:
						proc   = subprocess.Popen([grepbin, "-n", "-r", "-P"] +  filter + [greps[i]['regex'], srcdir], stdout=subprocess.PIPE)
						result = proc.communicate()

						if len(result[0]):	
							# update database with new results info
							result_id = str(uuid.uuid1())
							params    = [result_id, scan_id, greps[i]['language'], greps[i]['id'], greps[i]['regex'], greps[i]['description']]
							if 'mysql' == gbconfig.get('database', 'database'):
								mysqlcur.execute("INSERT INTO results (result_id, scan_id, language, regex_id, regex_text, description) VALUES (%s, %s, %s, %s, %s, %s);", params)
								mysqldb.commit()
							else:
								cur.execute("INSERT INTO results (result_id, scan_id, language, regex_id, regex_text, description) VALUES (?, ?, ?, ?, ?, ?);", params)
								db.commit()

							perline = str(result[0]).split("\n")
							for r in range(0, len(perline) - 1):
								try:
									rr = str(perline[r]).replace(basedir, '').split(':', 1)
									# update database with new results_detail info
									result_detail_id = str(uuid.uuid1())
									code             = str(rr[1]).split(':', 1)
									params           = [result_detail_id, result_id, rr[0], code[0], str(code[1]).strip()]

									if 'mysql' == gbconfig.get('database', 'database'):
										mysqlcur.execute("INSERT INTO results_detail (result_detail_id, result_id, file, line, code) VALUES (%s, %s, %s, %s, %s);", params)
										mysqldb.commit()
									else:
										cur.execute("INSERT INTO results_detail (result_detail_id, result_id, file, line, code) VALUES (?, ?, ?, ?, ?);", params)
										db.commit()

								except lite.Error, e:
									print 'SQL error! See log file for details.'
									logging.debug('SQL error with params ' + str(params) + ' and error ' + str(e))
								except Exception as e:
									print 'Error parsing result! See log file for details.'
									logging.debug('Error parsing result: ' + str(e))
							
					except Exception as e:
						print 'Error calling grep! See log file for details'
						logging.debug('Error calling grep: ' + str(e))

	params = [project_id]
	if 'mysql' == gbconfig.get('database', 'database'):
		mysqlcur.execute("UPDATE projects SET last_scan=NOW() WHERE project_id=%s;", params)
		mysqldb.commit()
		mysqldb.close()
	else:
		cur.execute("UPDATE projects SET last_scan=datetime('now') WHERE project_id=?;", params)
		db.commit()
		db.close()

	html_report(scan_id)

	return scan_id

def repo_scan(repo, account, force):
	"""
	Check code out from a remote repo and scan import
	"""
	try:
		db  = lite.connect(dbfile)
		cur = db.cursor()

	except lite.Error as e:
		print 'Error connecting to db file'
		logging.debug('Error connecting to db file' + str(e))
		sys.exit(1)

	params = [repo]
	cur.execute("SELECT command, checkout_url, api_url FROM repo_sites WHERE site=? LIMIT 1;", params)
	rows = cur.fetchall()

	for row in rows:
		api_url = row[2].replace('ACCOUNT', account)

		if 'github' == repo:
			page = 1
			
			# call api_url
			# if request fails, try 3 times
			count     = 0
			max_tries = 3
			logging.info('Calling github api for ' + api_url)
			while count < max_tries:
				try:
					r    = requests.get(api_url + '?page=' + str(page) + '&per_page=100')
					data = r.json()

					# no exceptions so break out of while loop
					break
				except requests.ConnectionError as e:
					count = count + 1
					if count <= max_tries:
						logging.warning('Error retreiving grep rules: ConnectionError (attempt ' + str(count) + ' of ' + str(max_tries) + '): ' + str(e))
						time.sleep(3) # take a break, throttle a bit
				
				except requests.HTTPError as e:
					count = count + 1
					if count <= max_tries:
						logging.warning('Error retreiving grep rules: HTTPError (attempt ' + str(count) + ' of ' + str(max_tries) + '): ' + str(e))
						time.sleep(3) # take a break, throttle a bit
			
				except requests.Timeout as e:
					count = count + 1
					if count <= max_tries:
						logging.warning('Error retreiving grep rules: Timeout (attempt ' + str(count) + ' of ' + str(max_tries) + '): ' + str(e))
						time.sleep(3) # take a break, throttle a bit

				except Exception as e:
					print 'CRITICAL: Unhandled exception occured! Quiters gonna quit! See log file for details.'
					logging.critical('Unhandled exception: ' + str(e))
					sys.exit(1)

			if count == max_tries:
				# grep rules were not retrieved, could be working with old rules.
				logging.critical('Error retreiving data from github api (no more tries left. could be using old grep rules.): ' + str(e))
				sys.exit(1)

			while len(data):
				print 'Get page: ' + str(page)
				for i in range(0, len(data)):
					do_scan      = True
					project_name = data[i]["name"]
					last_scanned = last_scan(repo, account, project_name)
					last_changed = datetime.datetime.strptime(data[i]['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
					checkout_url = 'https://github.com/' + account + '/' + project_name + '.git'
					cmd          = 'git'

					print project_name + ' last changed on ' + str(last_changed) + ' and last scanned on ' + str(last_scanned)

					if None != last_scanned:
						if last_changed < last_scanned:
							do_scan = False
							time.sleep(1) # throttle requests; github could be temperamental

					if True == force:
							do_scan = True

					if True == do_scan:
						checkout_code(cmd, checkout_url, account, project_name)
						# scan local files
						local_scan(os.path.dirname(os.path.abspath(__file__)) + '/remotesrc/' + account + '/' + project_name, repo, account, project_name)
						# clean up because of big projects and stuff
						call(['rm', '-rf', os.path.dirname(os.path.abspath(__file__)) + '/remotesrc/' + account + '/' + project_name])
						
				# get next page of projects
				page += 1
				r    = requests.get(api_url + '?page=' + str(page) + '&per_page=100')
				data = r.json()

		elif 'bitbucket' == repo:
			# call api_url
			r    = requests.get(api_url)
			data = r.json()
			
			for j in range(0, len(data["values"])):
				value =  data["values"][j]

				if 'git' == value['scm']:
					do_scan      = True
					project_name = str(value['full_name']).split('/')[1]
					last_scanned = last_scan(repo, account, project_name)
					date_split   = str(value['updated_on']).split('.')[0]
					last_changed = datetime.datetime.strptime(date_split, "%Y-%m-%dT%H:%M:%S")
					checkout_url = 'https://bitbucket.org/' + value['full_name']
					cmd          = 'git'

					print project_name + ' last changed on ' + str(last_changed) + ' and last scanned on ' + str(last_scanned)

					if None != last_scanned:
						if last_changed < last_scanned:
							do_scan = False

					if True == do_scan:
						checkout_code(cmd, checkout_url, account, project_name)
						# scan local files
						local_scan(os.path.dirname(os.path.abspath(__file__)) + '/remotesrc/' + account + '/' + project_name, repo, account, project_name)

		elif 'sourceforge' == repo:
			# call api_url
			r    = requests.get(api_url)
			data = r.json()
			
			for i in data['projects']:
				do_scan      = True
				project_name = i["url"].replace('/p/', '').replace('/', '')
				cmd          = None 
				r            = requests.get('https://sourceforge.net/rest' + i['url'])
				project_json = r.json()
				for j in project_json:
					for t in project_json['tools']:
						if 'code' == t['mount_point']:
							if 'git' == t['name']:
								cmd          = 'git'
								checkout_url = 'git://git.code.sf.net/p/' + str(project_name).lower() + '/code'
							elif 'svn' == t['name']:
								cmd          = 'svn'
								checkout_url = 'svn://svn.code.sf.net/p/' + str(project_name).lower() + '/code'

				last_scanned = last_scan(repo, account, project_name)
				date_split   = i['last_updated'].split('.')[0]
				last_changed = datetime.datetime.strptime(date_split, "%Y-%m-%d %H:%M:%S")

				print project_name + ' last changed on ' + str(last_changed) + ' and last scanned on ' + str(last_scanned)

				if None != last_scanned:
					if last_changed < last_scanned:
						do_scan = False

				if True == do_scan:
					if None != cmd:
						checkout_code(cmd, checkout_url, account, project_name)
						# scan local files
						local_scan(os.path.dirname(os.path.abspath(__file__)) + '/remotesrc/' + account + '/' + project_name, repo, account, project_name)
					else:
						print 'No sourceforge repo for ' + account + ' ' + project_name

		db.close()
		# clean up
		shutil.rmtree(os.path.abspath(__file__) + '/remotesrc/' + account)
		print 'SCAN COMPLETE!'

def checkout_code(cmd, checkout_url, account, project):
	account_folder = os.path.dirname(os.path.abspath(__file__)) + '/remotesrc/' + account

	if not os.path.exists(account_folder):
		os.makedirs(account_folder)

	# checkout code
	call(['rm', '-rf', account_folder + '/' + project])
	if 'git' == cmd:
		# in cases where auth is required inject credentials into checkout_url.
		# clone does not require auth so injecting credentials has no impact.
		# however if an account is locked (e.g. github.com locks an account for copyright violations)
		# the clone command will be prompted for credentials. The default credentials are intended
		# to fail auth in this scenario.
		split_checkout_url = checkout_url.split('://')
		print 'git clone...'
		call(['git', 'clone', split_checkout_url[0] + '://' + args.repo_user + ':' + args.repo_pass + '@' + split_checkout_url[1], account_folder + '/' + project])
	elif 'svn' == cmd:
		# need to do a lot of craziness for svn, no wonder people use git now.
		print 'svn checkout...'
		found_trunk = False

		call(['svn', '-q', 'checkout', '--depth', 'immediates', checkout_url, account_folder + '/tmp/' + project])

		# look for first level trunks
		for path, dirs, files in os.walk(os.path.abspath(account_folder + '/tmp/' + project)):
			for i in range(0, len(dirs)):
				if 'trunk' == dirs[i]:
					if os.path.isdir(path + '/' + dirs[i]):
						found_trunk = True
						print 'co ' + checkout_url + '/' + dirs[i]
						call(['svn', '-q', 'checkout', checkout_url + '/' + dirs[i], account_folder + '/' + project])

		if False == found_trunk:
			# try looking for tunk in second level
			path = os.path.abspath(account_folder + '/tmp/' + project)
			for n in os.listdir(path):
				if os.path.isdir(path + '/' + n):
					if '.svn' != n:
						print 'co ' + checkout_url + '/' + n + '/trunk'
						return_code = call(['svn', '-q', 'checkout', checkout_url + '/' + n + '/trunk', account_folder + '/' + project])
						if 0 == return_code:
							found_trunk = True

		if False == found_trunk:
			# didn't find a trunk, so checkout of last resort
			print 'WARNING: no trunk found so checking out everything. This could take a while and consume disk space if there are many branches.'
			call(['svn', '-q', 'checkout', checkout_url, account_folder + '/' + project])

		# remove temp checkout
		call(['rm', '-rf', os.path.abspath(account_folder + '/tmp/')])

def last_scan(repo, account, project):
	if 'mysql' == gbconfig.get('database', 'database'):
		try:
			import MySQLdb
			mysqldb  = MySQLdb.connect(host=gbconfig.get('database', 'host'), user=gbconfig.get('database', 'dbuname'), passwd=gbconfig.get('database', 'dbpword'), db=gbconfig.get('database', 'dbname'))
			mysqlcur = mysqldb.cursor()
		except Exception as e:
			print 'Error connecting to MySQL! See log file for details.'
			logging.debug('Error connecting to MySQL: ' + str(e))
			sys.exit(1)

	else:
		try:
			db  = lite.connect(dbfile)
			cur = db.cursor()
			
		except lite.Error as e:
			print 'Error connecting to db file! See log file for details.'
			logging.debug('Error connecting to db file: ' + str(e))
			sys.exit(1)
		except Exception as e:
			print 'CRITICAL: Unhandled exception occured! Quiters gonna quit! See log file for details.'
			logging.critical('Unhandled exception: ' + str(e))
			sys.exit(1)

	params = [repo, account, project]
	if 'mysql' == gbconfig.get('database', 'database'):
		mysqlcur.execute("SELECT last_scan FROM projects WHERE repo=%s AND account=%s and project=%s;", params)
		rows = mysqlcur.fetchall()
	else:
		cur.execute("SELECT last_scan FROM projects WHERE repo=? AND account=? and project=?;", params)
		rows = cur.fetchall()

	last_scan = None
	
	for row in rows:
		if None != row[0]:
			last_scan = datetime.datetime.strptime(str(row[0]), "%Y-%m-%d %H:%M:%S")

	if 'mysql' == gbconfig.get('database', 'database'):
		mysqldb.close()
	else:
		db.close()

	return last_scan

def html_report(scan_id):
	"""
	Create html report for a given scan_id
	"""
	
	if 'mysql' == gbconfig.get('database', 'database'):
		try:
			import MySQLdb
			mysqldb  = MySQLdb.connect(host=gbconfig.get('database', 'host'), user=gbconfig.get('database', 'dbuname'), passwd=gbconfig.get('database', 'dbpword'), db=gbconfig.get('database', 'dbname'))
			mysqlcur = mysqldb.cursor()
		except Exception as e:
			print 'Error connecting to MySQL! See log file for details.'
			logging.debug('Error connecting to MySQL: ' + str(e))
			sys.exit(1)

	else:
		try:
			import sqlite3 as lite
			db  = lite.connect(dbfile)
			cur = db.cursor()

		except lite.Error as e:
			print 'Error connecting to db file! See log file for details.'
			logging.debug('Error connecting to db file: ' + str(e))
			sys.exit(1)
		except Exception as e:
			print 'CRITICAL: Unhandled exception occured! Quiters gonna quit! See log file for details.'
			logging.critical('Unhandled exception: ' + str(e))
			sys.exit(1)

	html   = ''
	h      = 'ICAgX19fX19fICAgICAgICAgICAgICAgIF9fX18KICAvIF9fX18vX19fX19fXyAgX19fXyAgLyBfXyApX18gIF9fX19fXyBfX19fX18KIC8gLyBfXy8gX19fLyBfIFwvIF9fIFwvIF9fICAvIC8gLyAvIF9fIGAvIF9fXy8KLyAvXy8gLyAvICAvICBfXy8gL18vIC8gL18vIC8gL18vIC8gL18vIChfXyAgKQpcX19fXy9fLyAgIFxfX18vIC5fX18vX19fX18vXF9fLF8vXF9fLCAvX19fXy8KICAgICAgICAgICAgICAvXy8gICAgICAgICAgICAgICAgL19fX18v'
	params = [scan_id]

	if 'mysql' == gbconfig.get('database', 'database'):
		mysqlcur.execute("SELECT a.repo, a.account, a.project, b.scan_id, b.date_time, b.cloc_out FROM projects a, scans b WHERE a.project_id=b.project_id AND b.scan_id=%s LIMIT 1;", params)
		rows = mysqlcur.fetchall()
	else:
		cur.execute("SELECT a.repo, a.account, a.project, b.scan_id, b.date_time, b.cloc_out FROM projects a, scans b WHERE a.project_id=b.project_id AND b.scan_id=? LIMIT 1;", params)
		rows = cur.fetchall()

	# for loop on rows, but only one row
	for row in rows:
		print 'writing report...'
		htmlfile = os.path.dirname(os.path.abspath(__file__)) + '/out/' + row[0] + '.' + row[1] + '.' + row[2].replace("/", "_") + '.' + row[3] + '.html'
		tabfile  = os.path.dirname(os.path.abspath(__file__)) + '/out/' + row[0] + '.' + row[1] + '.' + row[2].replace("/", "_") + '.' + row[3] + '.tabs.csv'

		if not os.path.exists(os.path.dirname(htmlfile)):
			os.makedirs(os.path.dirname(htmlfile))
		
		# include repo/account/project link
		if 'github' == row[0]:
			project_base_url = 'https://github.com/' + row[1] + '/' + row[2]
			link             = '(<a href="' + project_base_url + '" target="_new">' + project_base_url + '</a>)'
		else:
			project_base_url = ''
			link             = '';

		o = open(htmlfile, 'w')
		o.write("""<!DOCTYPE html><head>
<style>
	pre { font-size: 90%; }
	.t { color: darkgreen;  font-size: 150%;  font-weight: 900; text-shadow: 3px 3px darkgreen; }    /* title */
	h3 { margin-left: 15px;    font-variant: small-caps; } /* language */
	.d { margin-left:15px;   color: darkred; }    /* descriptive problem */
	.r { font-weight:bold;      margin-left:15px; }    /* regex */
	pre.f { margin-left: 50px; }  /* finding */
	pre.f span {color: grey; }  /* finding title */
</style></head><body>""")
		o.write("<pre class=\"t\">\n" + h.decode('base64') + "</pre>")
		o.write("\n\n<pre>"
				+ "\nrepo:     " + row[0]
				+ "\naccount:  " + row[1]
				+ "\nproject:  " + row[2] + "   " + link
				+ "\nscan id:  " + row[3]
				+ "\ndate:     " + str(row[4]) + "</pre>\n")
		#o.write("<pre>\n" + str(row[5]).replace("\n", "<br>") + "</pre>")
		o.write("<pre>\n" + row[5] + "</pre>")
		o.close()
		
		t = open(tabfile, 'w')
		t.write("GrepBugs\n")
		t.write("repo:\t" + row[0] + "\naccount:\t" + row[1] + "\nproject:\t" + row[2] + " " + link + "\nscan id:\t" + row[3] + "\ndate:\t" + str(row[4]) + "\n")
		t.close()

		if 'mysql' == gbconfig.get('database', 'database'):
			mysqlcur.execute("SELECT b.language, b.regex_text, b.description, c.result_detail_id, c.file, c.line, c.code FROM scans a, results b, results_detail c WHERE a.scan_id=%s AND a.scan_id=b.scan_id AND b.result_id=c.result_id ORDER BY b.language, b.regex_id, c.file;", params)
			rs = mysqlcur.fetchall()
		else:
			cur.execute("SELECT b.language, b.regex_text, b.description, c.result_detail_id, c.file, c.line, c.code FROM scans a, results b, results_detail c WHERE a.scan_id=? AND a.scan_id=b.scan_id AND b.result_id=c.result_id ORDER BY b.language, b.regex_id, c.file;", params)
			rs = cur.fetchall()

		o        = open(htmlfile, 'a')
		t        = open(tabfile, 'a')
		html     = "\n\n"
		tabs     = "\n\nlang\tdescription\tfile\tline\tc.code\n"
		language = ''
		regex    = ''
		count    = 0
		
		# loop through all results, do some fancy coordination for output
		for r in rs:
			tab_lang = r[0].replace("\t"," ").replace("\n","  ").replace("\r","  ")
			#tab_regex = r[1].replace("\t"," ").replace("\n","  ").replace("\r","  ")
			tab_desc = r[2].replace("\t"," ").replace("\n","  ").replace("\r","  ")
			#tab_id = r[3].replace("\t"," ").replace("\n","  ").replace("\r","  ")
			tab_file = r[4].replace("\t"," ").replace("\n","  ").replace("\r","  ")
			tab_line = str(r[5])
			tab_code = r[6].replace("\t"," ").replace("\n","  ").replace("\r","  ")
		
			tabs += tab_lang +"\t"+ tab_desc +"\t"+ tab_file +"\t"+ tab_line +"\t"+ tab_code +"\n"
			
			if regex != r[1]:
				if 0 != count:
					html += '	</div>' + "\n"; # end result set for regex

			if language != r[0]:
				html += '<h3>' + r[0] + '</h3>' + "\n"

			if regex != r[1]:
				html += '	<div class="d"><a style="cursor: pointer;" onclick="javascript:o=document.getElementById(\'r' + str(r[3]) + '\');if(o.style.display==\'none\'){ o.style.display=\'block\';} else {o.style.display=\'none\';}">+ ' + r[2] + "</a></div>\n"
				html += '	<div id="r' + str(r[3]) + '" style="display:none;margin-left:15px;">' + "\n" # description
				html += '		<div class="r"><pre>' +  cgi.escape(r[1]) + '</pre></div>' + "\n" #regex

			# determine the number of occurrences of account in the path, set begin to the position to the last occurrence
			account_occurrences = r[4].count(row[1])
			begin               = 0			
			for occurance in range(0, account_occurrences):
				begin = r[4].index(row[1], begin)
				if(account_occurrences > 1 and occurance + 1 != account_occurrences):
					begin = begin + 1
			
			# include repo/account/project/file link
			if 'github' == row[0]:
				file_link   = '<a href="https://github.com/' + r[4][r[4].index(row[1], begin):].replace(row[1] + '/' + row[2] + '/', row[1] + '/' + row[2] + '/blob/master/') + '#L' + str(r[5]) + '" target="_new">' + str(r[5]) + '</a>'
				ltrim_by    = row[1]
				ltrim_begin = begin
			else:
				file_link   = str(r[5]);
				ltrim_by    = row[2]
				ltrim_begin = 0

			html += '		<pre class="f"><span>' + r[4][r[4].index(ltrim_by, ltrim_begin):] + ' ' + file_link + ':</span> &nbsp; ' + cgi.escape(r[6]) + '</pre>' + "\n" # finding

			count   += 1
			language = r[0]
			regex    = r[1]

		if 0 == count:
			html += '<h3>No bugs found!</h3><div>Contribute regular expressions to find bugs in this code at <a href="https://grepbugs.com">GrepBugs.com</a></div>';
			tabs += "No bugs found\n\nContribute regular expressions to find bugs in this code at https://GrepBugs.com\n";
		else:
			html += '	</div>' + "\n"
			tabs += "\n"
		
		html += '</html>'
		o.write(html)
		o.close()
		t.write(tabs)
		t.close()

	if 'mysql' == gbconfig.get('database', 'database'):
		mysqldb.close()
	else:
		db.close()

"""
Handle and process command line arguments
"""
parser = argparse.ArgumentParser(description='At minimum, the -d or -r options must be specified.')
parser.add_argument('-d', help='specify a LOCAL directory to scan.')
parser.add_argument('-f', help='force scan even if project has not been modified since last scan.', default=False, action="store_true")
parser.add_argument('-u', help='Use existing rules, do not download updated set.', default=False, action="store_true")

group = parser.add_argument_group('REMOTE Repository Scanning')
group.add_argument('-r', help='specify a repo to scan (e.g. github, bitbucket, or sourceforge).')
group.add_argument('-a', help='specify an account for the specified repo.')
group.add_argument('-repo_user', help='specify a username to be used in authenticating to the specified repo (default: grepbugs).', default='grepbugs')
group.add_argument('-repo_pass', help='specify a password to be used in authenticating to the specified repo (default: grepbugs).', default='grepbugs')

args = parser.parse_args()

if None == args.d and None == args.r:
	parser.print_help()
	sys.exit(1)

if None != args.d:
	print 'scan directory: ' + args.d
	scan_id = local_scan(args.d)
elif None != args.r:
	if None == args.a:
		print 'an account must be specified! use -a to specify an account.'
		sys.exit(1)

	print 'scan repo: ' + args.r + ' ' + args.a
	scan_id = repo_scan(args.r, args.a, args.f)
