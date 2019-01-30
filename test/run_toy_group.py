from optparse import OptionParser
import os

#command-line options
parser = OptionParser()
parser.add_option('-G','--group',type='string', action='store', dest='groupname', help='Name of toy group to run')
(options, args) = parser.parse_args()

#get the current working directory so we can cd back here at the end
cwd = os.getcwd()

#look for and open the file of commands
int_cmd_filename = 'int_cmds_'+options.groupname+'.txt'
if not os.path.isfile(int_cmd_filename) :
	print 'ERROR: cannot find interactive command file %s in current path %s'%(int_cmd_filename,cwd)
	exit()
with open(int_cmd_filename,'r') as icfp :
	raw_int_cmds = [line.rstrip('\n') for line in icfp.readlines()]

#look for and change to the toyGroup directory
toygroupdirname = 'toyGroups_'+options.groupname
if not os.path.isdir(toygroupdirname) :
	print 'ERROR: cannot find toy group directory %s in current path %s'%(toygroupdirname,cwd)
	exit()
os.chdir(toygroupdirname)

#run the commands
for rawcmd in raw_int_cmds :
	if rawcmd.startswith('cd') : #if it's the command to get to ther specific directory and cmsenv, just cd to that directory
		newdir=rawcmd[len('cd '+cwd+'/'+toygroupdirname+'/'):-1*len('; cmsenv')]
		print 'CD-ing to directory %s'%(newdir)
		os.chdir(newdir)
	elif rawcmd.startswith('python') : #if it's the command to run the fitter, just run the command verbatim
		print 'running %s'%(rawcmd)
		os.system(rawcmd)
	elif rawcmd=='' : #otherwise it's done with on of the toy group runs, CD back to the upper directory
		newdir=os.path.join(cwd,toygroupdirname)
		print 'CD-ing back to group directory %s'%(newdir)
		os.chdir(newdir)

os.chdir(cwd)
print 'All done running toy groups for %s :)'%(options.groupname)