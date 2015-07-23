#!/usr/bin/python

import sys
import os
import xml.etree.ElementTree as ET
import subprocess
import backuplib

def usageMsg():
	print 'install.py - GoodBackup installation utility'
	print 'Usage: install.py [path-to-config-file] [path-to-log-file]'
	print

def parseArgs(argv):
	parsedArgs = None
	if len(argv) == 3:
		parsedArgs = [argv[1], argv[2]]
	return parsedArgs

def main(argv):
	# Read cmd arguments.
	parsedArgs = parseArgs(argv)
	if parsedArgs is None:
		usageMsg()
		return

	# Convert to absolute path up front to save us some headache.
	parsedArgs[0] = os.path.abspath(parsedArgs[0])
	parsedArgs[1] = os.path.abspath(parsedArgs[1])

	# Validate inputs.
	if not os.path.isfile(parsedArgs[0]):
		print 'Couldn\'t find config file: {0}. Aborting installation.'.format(parsedArgs[0])
		return
	tree = ET.parse(parsedArgs[0])
	root = tree.getroot()
	if not backuplib.validateConfig(root):
		print 'Invalid config file: {0}. Aborting installation.'.format(parsedArgs[0])
		return
	if not os.path.isdir(os.path.dirname(parsedArgs[1])):
		print 'Logging directory doesn\'t exist: {0}. Aborting installation.'.format(os.path.dirname(parsedArgs[1]))
		return
	if not os.path.isdir(root.find('./output').get('path')):
		print 'Backup directory doesn\'t exist: {0}. Aborting installation.'.format(root.find('./output').get('path'))
		return
	
	# Check for existing installations.
	crontab = subprocess.Popen(["crontab", "-l"], stdout=subprocess.PIPE).communicate()[0]
	existingEntries = []
	for entry in crontab.split('\n'):
		if '0\t*\t*\t*\t*' in entry and 'backup.py' in entry:
			existingEntries.append(entry)

	choice = 'y'
	if len(existingEntries) > 0:
		print 'Existing GoodBackup entries were detected in the crontab:'
		for entry in existingEntries:
			print entry
		print
		choice = ''
		while not choice in ['n', 'N', 'y', 'Y', 'q', 'Q']:
			choice = raw_input('Continue installing? (y/n):')

	# Append to crontab.
	if choice in ['y', 'Y']:
		line = '0\t*\t*\t*\t*\t{0} {1} >> {2} 2>&1'.format(os.path.dirname(os.path.realpath(__file__)) + '/backup.py', parsedArgs[0], parsedArgs[1])
		if len(crontab) > 0:
			cronEntries = crontab.split('\n')
			cronEntries = [entry for entry in cronEntries if entry != '']
			cronEntries.append(line)
			crontab = '\n'.join(cronEntries) + '\n'
		else:
			crontab = line + '\n'
		print 'Installing new crontab.'
		cronfile = open('goodbackupcron.txt', 'w')
		cronfile.write(crontab)
		cronfile.close()
		os.system('crontab goodbackupcron.txt ; rm goodbackupcron.txt')
		print 'Installation complete.'

main(sys.argv)
