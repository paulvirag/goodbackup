#!/usr/bin/python

import sys
import os
import xml.etree.ElementTree as ET
import time
import datetime

#
# XML helper functions.
#

def isString(val):
	return (not (val is None) and isinstance(val, str) and len(val) > 0)

def isInt(val):
	try:
		return (
			not (val is None) and (
				isinstance(val, int) or (
					isinstance(val, str) and
					len(val) > 0 and
					isinstance(int(val), int)
				)
			)
		)
	except:
		return False

def validateRequiredSection(root, xpath):
	return len(root.findall(xpath)) > 0

def validateUniqueSection(root, xpath):
	return len(root.findall(xpath)) <= 1

def validateRequiredAttribute(root, xpath, attrName):
	for node in root.findall(xpath):
		if not isString(node.get(attrName)):
			return False
	return True

def validateIntAttribute(root, xpath, attrName):
	for node in root.findall(xpath):
		if not isInt(node.get(attrName)):
			return False
	return True

def validateUniqueAttribute(root, xpath, attrName):
	vals = set()
	for node in root.findall(xpath):
		if node.get(attrName) in vals:
			return False
		vals.add(node.get(attrName))
	return True

def validateAttributeReference(root, xpathReferer, attrReferer, xpathReferred, attrReferred):
	for referer in root.findall(xpathReferer):
		found = False
		for referred in root.findall(xpathReferred):
			if referer.get(attrReferer) == referred.get(attrReferred):
				found = True
				break
		if not found:
			return False
	return True

#
# Backup helper methods.
#

def dumpDatabase(dbname, username, password, outfile):
	os.system("mysqldump --user={1} --password={2} --single-transaction --add-drop-database --add-drop-table --hex-blob {0} > {3}".format(dbname, username, password, outfile))

def log(line):
	startTime = time.time()
	timestamp = datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S.%f')
	print '[{0}] {1}'.format(timestamp, line)
	sys.stdout.flush()

#
# Public API methods.
#

def validateConfig(root):
	# Check top-level sections are intact.
	if root.tag != 'settings' \
		or not validateUniqueSection(root, './credentials') \
		or not validateUniqueSection(root, './targets') \
		or not validateRequiredSection(root, './output') \
		or not validateUniqueSection(root, './output') \
		or not validateRequiredAttribute(root, './output', 'path'):
		return False
	
	# Check 'credentials' section is well-formed, with no duplicates.
	if not validateRequiredAttribute(root, './credentials/credential', 'name') \
		or not validateRequiredAttribute(root, './credentials/credential', 'username') \
		or not validateRequiredAttribute(root, './credentials/credential', 'password') \
		or not validateUniqueAttribute(root, './credentials/credential', 'name'):
		return False
	
	# Check 'targets' section is well-formed, with no duplicates.
	if not validateRequiredAttribute(root, './targets/target', 'name') \
		or not validateIntAttribute(root, './targets/target', 'intervalHours') \
		or not validateRequiredAttribute(root, './targets/target/folder', 'path') \
		or not validateRequiredAttribute(root, './targets/target/file', 'path') \
		or not validateRequiredAttribute(root, './targets/target/database', 'name') \
		or not validateRequiredAttribute(root, './targets/target/database', 'credential') \
		or not validateUniqueAttribute(root, './targets/target', 'name'):
		return False

	# Check each target for duplicate entities.
	for target in root.findall('./targets/target'):
		if not validateUniqueAttribute(target, './folder', 'path') \
			or not validateUniqueAttribute(target, './file', 'path') \
			or not validateUniqueAttribute(target, './database', 'name'):
			return False

	# Cross-reference database credentials against the credential list.
	if not validateAttributeReference(root, './targets/target/database', 'credential', './credentials/credential', 'name'):
		return False

	return True

def doBackup(root):
	startTime = time.time()
	timestamp = datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d.%H-%M-%S.%f')
	outputDir = root.find('output').get('path')
	if not os.path.isdir(outputDir):
		log("Error: No such path: {0}. Aborting backup.".format(outputDir))
		return

	found = False
	for target in root.findall('./targets/target'):
		if int(startTime / 60 / 60) % int(target.get('intervalHours')) == 0:
			sources = []
			tempFiles = []
			found = True
			log('Starting backup for "{0}".'.format(target.get('name')))
			
			# Add folder targets to source list.
			for folder in target.findall('./folder'):
				if os.path.isdir(folder.get('path')):
					sources.append(folder.get('path'))
				else:
					log("Warning: Could not find folder " + folder.get('path') + ".")
					
			# Add database targets to source list.
			for database in target.findall('./database'):
				for elem in root.findall('./credentials/credential'):
					if elem.get('name') == database.get('credential'):
						credential = elem
						break
				dumpFile = "{0}/{1}.{2}.sql".format(outputDir, database.get('name'), timestamp)
				dumpDatabase(database.get('name'), credential.get('username'), credential.get('password'), dumpFile)
				sources.append(dumpFile)
				tempFiles.append(dumpFile)
			
			# Add file targets to source list.
			for file in target.findall('./file'):
				if os.path.isfile(file.get('path')):
					sources.append(file.get('path'))
				else:
					log("Warning: Could not find file " + file.get('path') + ".")

			# Create the archive.
			outfile = outputDir + '/' + target.get('name') + 'backup' + timestamp + '.tar'
			for source in sources:
				os.system('tar rf {0} -C $(dirname {1}) $(basename {1})'.format(outfile, source))
			if os.path.isfile(outfile):
				os.system('gzip ' + outfile)

			# Clean up.
			for tempFile in tempFiles:
				os.remove(tempFile)

			log('Backup complete for "{0}".'.format(target.get('name')))

	if not found:
		log('No targets need to be backed up right now ({0} targets considered).'.format(len(root.findall('./targets/target'))))
