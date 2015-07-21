#!/usr/bin/python

import os
import sys
import backuplib
import xml.etree.ElementTree as ET
import shutil

#
# Types.
#

class TestVerbosity:
	Silent = 1
	Summary = 2
	Detailed = 3
	Verbose = 4

#
# Globals.
#

testVerbosity = TestVerbosity.Detailed

#
# Test library methods.
#

def doTest(func, args, expected, testText):
	if len(args) == 1:
		res = func(args[0])
	elif len(args) == 2:
		res = func(args[0], args[1])
	elif len(args) == 3:
		res = func(args[0], args[1], args[2])
	elif len(args) == 4:
		res = func(args[0], args[1], args[2], args[3])
	elif len(args) == 5:
		res = func(args[0], args[1], args[2], args[3], args[4])
	else:
		print 'Method not tested. TODO support more args for test methods.'
		return False
	
	didPass = (res == expected)

	# Print stuff
	if testVerbosity >= TestVerbosity.Verbose:
		print "".join([
			("PASS" if didPass else "FAIL") + ": " + testText + " ",
			"(args: " + str(args),
			(")" if didPass else ", expected: " + str(expected) + ", actual: " + str(res) + ")")
		])

	return didPass

def doTestMethod(testMethod, methodText):
	res = testMethod()
	if testVerbosity >= TestVerbosity.Detailed:
		print ("PASS" if res else "FAIL") + ": " + methodText
	return res

#
# Test methods.
#

def testValidateRequiredSection():
	# Test cases.
	passTests = [
		('<root><mySection /></root>', './mySection'),
		('<node><child><grandchild /></child></node>', './child/grandchild'),
	]
	failTests = [
		('<root><nodeOne /><nodeTwo /><nodeTwo /></root>', './nodeThree')
	]

	# Do tests
	res = True
	for test in passTests:
		res &= doTest(backuplib.validateRequiredSection, [ET.fromstring(test[0]), test[1]], True, "Ensure we correctly detect required sections.")
	for test in failTests:
		res &= doTest(backuplib.validateRequiredSection, [ET.fromstring(test[0]), test[1]], False, "Ensure we correctly detect when required sections are absent.")

	return res

def testValidateUniqueSection():
	# Test cases.
	passTests = [
		('<root><mySection /></root>', './mySection'),
		('<node><child><grandchild /></child></node>', './child/grandchild'),
		('<container><inner><sectionOne /><sectionTwo /></inner></container>', './inner/sectionTwo')
	]
	failTests = [
		('<root><nodeOne /><nodeTwo /><nodeTwo /></root>', './nodeTwo'),
		('<root><page><paragraph /><paragraph /></page></root>', './page/paragraph'),
		('<contacts><contact name="kyle"><phone number="1234567"/></contact><contact name="jane"><phone number="7653421"/></contact></contacts>', './contact/phone')
	]

	# Do tests
	res = True
	for test in passTests:
		res &= doTest(backuplib.validateUniqueSection, [ET.fromstring(test[0]), test[1]], True, "Ensure we correctly detect when sections are unique.")
	for test in failTests:
		res &= doTest(backuplib.validateUniqueSection, [ET.fromstring(test[0]), test[1]], False, "Ensure we correctly detect when sections aren't unique.")

	return res

def testValidateRequiredAttribute():
	# Test cases.
	passTests = [
		('<root><section name="mySection"/><section name="yourSection"/></root>', './section', 'name'),
		('<site><page><widget title="calendar"/></page><page><widget title="mail"/></page></site>', './page/widget', 'title'),
		('<settings></settings>', './section', 'name')
	]
	failTests = [
		('<site><page><widget title="calendar"/></page><page><widget name="mail"/></page></site>', './page/widget', 'name'),
		('<states><state abbr="NM"><city population="100"/></state><state abbr="MI"><city /></state></states>', './state/city', 'abbr'),
		('<site><page name="home" /><page name="" /></site>', './page', 'name')
	]

	# Do tests
	res = True
	for test in passTests:
		res &= doTest(backuplib.validateRequiredAttribute, [ET.fromstring(test[0]), test[1], test[2]], True, "Ensure we detect when attributes are present.")
	for test in failTests:
		res &= doTest(backuplib.validateRequiredAttribute, [ET.fromstring(test[0]), test[1], test[2]], False, "Ensure we detect when attributes are missing.")

	return res

def testValidateIntAttribute():
	# Test cases.
	passTests = [
		('<root><section id="524"/><section id="10004"/></root>', './section', 'id')
	]
	failTests = [
		('<site><page><widget id="10034"/></page><page><widget id="32443.5"/></page></site>', './page/widget', 'id'),
		('<states><state><city population="100"/></state><state><city population="twelve"/></state></states>', './state/city', 'population')
	]

	# Do tests
	res = True
	for test in passTests:
		res &= doTest(backuplib.validateIntAttribute, [ET.fromstring(test[0]), test[1], test[2]], True, "Ensure we detect integer attributes")
	for test in failTests:
		res &= doTest(backuplib.validateIntAttribute, [ET.fromstring(test[0]), test[1], test[2]], False, "Ensure we detect invalid integer attributes")

	return res

def testValidateUniqueAttribute():
	# Test cases.
	passTests = [
		('<root><section name="mySection"/><section name="yourSection"/></root>', './section', 'name'),
		('<site><page><widget title="calendar"/></page><page><widget title="mail"/></page></site>', './page/widget', 'title'),
		('<settings></settings>', './section', 'name')
	]
	failTests = [
		('<site><page><widget title="calendar"/></page><page><widget title="calendar"/></page></site>', './page/widget', 'title'),
		('<states><state abbr="NM"><city population="100"/></state><state abbr="WA"/><state abbr="NM"><city /></state></states>', './state', 'abbr')
	]

	# Do tests
	res = True
	for test in passTests:
		res &= doTest(backuplib.validateUniqueAttribute, [ET.fromstring(test[0]), test[1], test[2]], True, "Ensure we can detect attribute uniqueness.")
	for test in failTests:
		res &= doTest(backuplib.validateUniqueAttribute, [ET.fromstring(test[0]), test[1], test[2]], False, "Ensure we detect when attributes fail to be unique.")

	return res

def testValidateAttributeReference():
	# Test cases.
	doc = '<doc><images><image name="logo" url="/logo.png" /><image name="banner" url="/banner.png" /></images><scripts><script path="/container.js" /></scripts><pages><page name="home"><scriptRef src="/container.js"/><imageRef name="logo"/></page><page name="contact"><imageRef name="banner"/></page><page name="badPage"><imageRef name="invalid"/><scriptRef src="undefined"/></page></pages></doc>'

	passTests = [
		('./pages/page[@name="home"]/imageRef', 'name', './images/image', 'name'),
		('./pages/page[@name="home"]/scriptRef', 'src', './scripts/script', 'path'),
		('./pages/page[@name="contact"]/imageRef', 'name', './images/image', 'name')
	]
	failTests = [
		('./pages/page[@name="badPage"]/imageRef', 'name', './images/image', 'name'),
		('./pages/page[@name="badPage"]/scriptRef', 'src', './scripts/script', 'path')
	]

	# Do tests
	res = True
	for test in passTests:
		res &= doTest(backuplib.validateAttributeReference, [ET.fromstring(doc), test[0], test[1], test[2], test[3]], True, "Ensure we can resolve attribute references.")
	for test in failTests:
		res &= doTest(backuplib.validateAttributeReference, [ET.fromstring(doc), test[0], test[1], test[2], test[3]], False, "Ensure we can detect broken attribute references.")

	return res

def testValidateTopLevelXml():
	# Test cases. (We don't need to try malformed XML - just our schema validations)
	passTests = [
		'<settings><output path="~/backups" /></settings>',
		'<settings><output path="~/backups" /><credentials><credential name="foo" username="bar" password="secret" /></credentials></settings>',
		'<settings><output path="~/backups" /><targets></targets></settings>'
	]
	failTests = [
		'<root></root>', # Missing top-level 'settings' node
		'<settings><credentials /><targets /></settings>', # Missing output section
		'<settings><output path="~/backups" /><credentials section="first" /><credentials section="second" /></settings>', # Duplicate credentials sections
		'<settings><output path="~/backups" /><targets section="first" /><targets section="second" /></settings>' # Duplicate targets sections
	]

	# Do tests.
	res = True
	for test in passTests:
		res &= doTest(backuplib.validateConfig, [ET.fromstring(test)], True, "Ensure valid XML is accepted")
	for test in failTests:
		res &= doTest(backuplib.validateConfig, [ET.fromstring(test)], False, "Ensure bad XML is rejected")

	return res

def testValidateInnerXml():
	# Test cases.
	template = """<?xml version="1.0"?>
			<settings>
				<output path="~/backups" />
				<credentials>
					<credential name="database" username="user" password="pass" />
					{0}
				</credentials>
				<targets>
					<target name="app1" intervalHours="24">
						<folder path="/app1" />
						<folder path="/app1data" />
						<database name="app1" credential="database" />
					</target>
					<target name="app2" intervalHours="72">
						<folder path="/app2" />
						<database name="app2" credential="database" />
					</target>
					<target name="app3" intervalHours="168" />
					{1}
				</targets>
			</settings>"""
	passCredential = '<credential name="backup" username="backup_user" password="123456" />'
	failCredentials = [
		'<credential username="sqluser" password="pass"/>',
		'<credential name="localDB" username="localuser" />',
	]
	passTarget = '<target name="app4" intervalHours="24"><database name="app4" credential="database" /></target>'
	failTargets = [
		'<target intervalHours="24" />', # Missing name
		'<target name="app4" intervalHours="24"><folder name="My Documents"/></target>', # Missing folder path
		'<target name="app4" intervalHours="24"><database credential="database"/></target>', # Missing database name
		'<target name="app4" intervalHours="24"><database name="myDB" credential="remoteDB" /></target>', # Invalid credential reference
		'<target name="app4" />', # Missing interval
		'<target name="app4" intervalHours="24"><database name="app4" credential="database" /><database name="app4" credential="backup" /></target>', # Duplicate database
		'<target name="app4" intervalHours="24"><file path="~/documents/mydoc.txt" /><file path="~/documents/mydoc.txt" /></target>' # Duplicate file path
	]

	# Do passing tests.
	res = True
	res &= doTest(backuplib.validateConfig, [ET.fromstring(template.format(passCredential, passTarget))], True, "Ensure valid inner XML is accepted")
	
	# Do failing tests.
	failTests = [[template.format(passCredential, target) for target in failTargets], [template.format(credential, passTarget) for credential in failCredentials]]
	for test in [elem for vec in failTests for elem in vec]:
		res &= doTest(backuplib.validateConfig, [ET.fromstring(test)], False, "Ensure bad inner XML is rejected")

	return res

def mockDumpDatabase(dbname, username, password, outfile):
	if os.path.isfile(outfile):
		os.remove(outfile)
	os.system('echo {0} >> {1}'.format(dbname, outfile))
	os.system('echo {0} >> {1}'.format(username, outfile))
	os.system('echo {0} >> {1}'.format(password, outfile))

def mockLog(line):
	pass

def testBackup():
	# Set up filesystem.
	os.system('echo test > testfile1.txt')
	os.system('mkdir testfolder1')
	os.system('echo me > testfolder1/testfile2.txt')
	os.system('mkdir testfolder2')
	os.system('echo pretty > testfolder2/testfile3.txt')
	os.system('echo please > testfolder2/testfile4.txt')
	os.system('mkdir testoutputdir')

	# Create test configuration.
	config = """<?xml version="1.0"?>
				<settings>
					<output path="testoutputdir" />
					<credentials>
						<credential name="database" username="user" password="pass" />
					</credentials>
					<targets>
						<target name="testapp1" intervalHours="1">
							<file path="testfile1.txt" />
							<folder path="testfolder2" />
							<database name="testapp1" credential="database" />
						</target>
						<target name="testapp2" intervalHours="1">
							<file path="testfolder1/testfile2.txt" />
							<database name="testapp2" credential="database" />
						</target>
					</targets>
				</settings>"""

	# Mock out the MySQL dump routine and logging statements.
	backuplib.dumpDatabase = mockDumpDatabase
	backuplib.log = mockLog

	# Do backup.
	backuplib.doBackup(ET.fromstring(config))

	# Clean up input files.
	os.remove('testfile1.txt')
	os.remove('testfolder1/testfile2.txt')
	os.remove('testfolder2/testfile3.txt')
	os.remove('testfolder2/testfile4.txt')
	os.rmdir('testfolder1')
	os.rmdir('testfolder2')

	# Pop open the first archive and verify filesystem state.
	res = True
	os.system('tar xzf testoutputdir/testapp1*')
	res &= os.path.isfile('testfile1.txt') # Verify file existence
	res &= os.path.isfile('testfolder2/testfile3.txt') # Verify file existence
	testfile1 = open('testfile1.txt')
	res &= (testfile1.read() == 'test\n') # Verify file contents
	testfile4 = open('testfolder2/testfile4.txt')
	res &= (testfile4.read() == 'please\n') # Verify file contents
	sqlFiles = [sqlFile for sqlFile in os.listdir('.') if '.sql' in sqlFile and 'testapp1' in sqlFile]
	res &= len(sqlFiles) == 1 # Verify SQL file existence
	if len(sqlFiles) == 1:
		sqlFile1 = open(sqlFiles[0])
		res &= (sqlFile1.read() == 'testapp1\nuser\npass\n') # Verify SQL file contents
		sqlFile1.close()
	res &= not os.path.isfile('testfile2.txt') # Verify this file isn't in the testapp1 backup

	# Pop open the second archive.
	os.system('tar xzf testoutputdir/testapp2*')
	res &= os.path.isfile('testfile2.txt') # Verify file was in the testapp2 backup
	testfile2 = open('testfile2.txt')
	res &= (testfile2.read() == 'me\n') # Verify file contents
	sqlFiles = [sqlFile for sqlFile in os.listdir('.') if '.sql' in sqlFile and 'testapp2' in sqlFile]
	res &= len(sqlFiles) == 1 # Verify SQL file existence
	if len(sqlFiles) == 1:
		sqlFile2 = open(sqlFiles[0])
		res &= (sqlFile2.read() == 'testapp2\nuser\npass\n') # Verify SQL file contents
		sqlFile2.close()

	# Clean up extracted files.
	os.remove('testfile1.txt')
	os.remove('testfile2.txt') # After extraction, this file will be in the root folder.
	os.remove('testfolder2/testfile3.txt')
	os.remove('testfolder2/testfile4.txt')
	os.rmdir('testfolder2')

	# Clean up output files.
	for sqlFile in [sqlFile for sqlFile in os.listdir('.') if '.sql' in sqlFile and 'testapp' in sqlFile]:
		os.remove(sqlFile)
	shutil.rmtree('testoutputdir')

	return res

#
# Entry point.
#

def runAllTests():
	testMethods = [
		(testValidateRequiredSection, "Test required sections helper"),
		(testValidateUniqueSection, "Test unique sections helper"),
		(testValidateRequiredAttribute, "Test rqeuired attribute helper"),
		(testValidateIntAttribute, "Test int attribute helper"),
		(testValidateUniqueAttribute, "Test unique attributes helper"),
		(testValidateAttributeReference, "Test attribute references helper"),
		(testValidateTopLevelXml, "Test validating top-level XML"),
		(testValidateInnerXml, "Test validating inner XML"),
		(testBackup, "Test end-to-end backup process")
	]

	# Run tests.
	res = True
	for testMethod in testMethods:
		res &= doTestMethod(testMethod[0], testMethod[1])
	
	if testVerbosity >= TestVerbosity.Summary:
		print "All tests passed." if res else "One or more tests failed."

runAllTests()
