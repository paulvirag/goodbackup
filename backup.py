#!/usr/bin/python

import sys
import xml.etree.ElementTree as ET
import backuplib

def usageMsg():
	print 'backup.py - GoodBackup core backup utility (install using install.py)'
	print 'Usage: backup.py <path-to-config-file>'
	print

def parseArgs(argv):
	parsedArgs = None
	if len(argv) == 2 and argv[1] not in ['--h', '-?', '/?', '--help']:
		parsedArgs = [argv[1]]
	return parsedArgs

def main(argv):
	# Read cmd arguments.
	parsedArgs = parseArgs(argv)
	if parsedArgs is None:
		usageMsg()
		return
	
	# Read configuration file.
	tree = ET.parse(parsedArgs[0])
	root = tree.getroot()

	# Do the backup tasks.
	backuplib.log('********Starting backup routine.********')
	if backuplib.validateConfig(root):
		backuplib.doBackup(root)
	else:
		backuplib.log('Invalid configuration file. Aborting backup.')
	backuplib.log('********Backup routine complete.********')
	
main(sys.argv)
