#!/usr/bin/python

import os
import sys
import xml.etree.ElementTree as ET
import backuplib

def usageMsg():
	print 'validate.py - GoodBackup config file validation utility'
	print 'Usage: validate.py <path-to-config-file>'
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
	
	# Validate configuration file.
	tree = ET.parse(parsedArgs[0])
	root = tree.getroot()
	print 'Configuration file is valid. {0} backup targets detected.'.format(len(root.findall('./targets/target'))) if backuplib.validateConfig(root) else 'Error - configuration file failed schema validation.'

	# Check backup directory existence.
	if not os.path.isdir(root.find('./output').get('path')):
		print 'Warning: backup directory doesn\'t exist: {0}. Please create it before installing.'.format(root.find('./output').get('path'))
	
main(sys.argv)
