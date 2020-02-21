from optparse import OptionParser
import os

#stems for the different types of toy groups
topdir_stems = ['with_sys','no_sys',
				#'JESUp','JESDown',
				#'JERUp','JERDown',
				#'isrUp','isrDown',
				#'fsrUp','fsrDown',
				#'hdampUp','hdampDown',
				#'tuneUp','tuneDown',
				#'crUp','crDown',
				]

#command-line options
parser = OptionParser()
parser.add_option('-P','--par',type='choice', action='store', dest='par', choices=['Afb','mu','d'], help='Which parameter ("Afb", "mu", "d") is the parameter of interest? Required.')
parser.add_option('-T', '--tfilename', type='string', action='store', dest='tfilename', default='templates_powheg_dynamic_binning_smoothed_with_JEC.root')
(options, args) = parser.parse_args()

#stems for numerical values of parameters in toyGroups
stems = []
if options.par=='Afb' :
	centralval = 0.05352; errfromdatafit = 0.10326
elif options.par=='d' :
	centralval = 1.44771e-07; errfromdatafit = 0.01054
elif options.par=='mu' :
	centralval = -0.02280; errfromdatafit = 0.00748
stems = ['{0:.{1}f}'.format(centralval+(i-10)*(errfromdatafit/2.), 5) for i in range(21)]
topdirnames = ['toyGroups_'+options.par+'_'+tds for tds in topdir_stems]
dirnames = ['toyGroup_'+options.par+'='+stem for stem in stems]
#print dirnames #DEBUG

#get the current working directory so we can put new directories here
cwd = os.getcwd()

#loop through the different types of toy groups
for tdn in topdirnames :
	#create or cd to the inputted top directory
	new_topdir_path = os.path.join(cwd,tdn)
	if not os.path.isdir(new_topdir_path) :
		os.mkdir(new_topdir_path)
	os.chdir(new_topdir_path)
	#make the new directories within, deleting the old if they already exist
	for dirname in dirnames :
		if os.path.isdir(dirname) :
			os.system('rm -rf '+dirname)
		os.mkdir(dirname)
	#change back to where we started
	os.chdir(cwd)

#write the commands to run the toy groups into text files
for tds,tdn in zip(topdir_stems,topdirnames) :
	cmds = []
	for s,dn in zip(stems,dirnames) :
		#first command to get to the directory
		cmd1 = 'cd '+os.path.join(cwd,tdn,dn)+'; cmsenv\n'
		#second command to run the fitter
		cmd2 = 'python '+os.path.join('~','fittertest','..','python','run_fits.py')+' -M toyGroup -P '+options.par+' --tfile '+os.path.join('~','templatetest','total_template_files',options.tfilename)
		if tds!='with_sys' : #remove the simple systematics and rateParams if we don't want them
			cmd2+=' --noSS --noRateParams'
			if tds!='no_sys' : #add the systematic type if applicable
				cmd2+=' --postsys '+tds
		cmd2+=' --toy-'+options.par+' '+s+'\n'
		#just a blank line to separate them
		cmd3='\n'
		cmds+=[cmd1,cmd2,cmd3]
	#open the new file and write the commands
	with open('int_cmds_'+options.par+'_'+tds+'.txt','w') as fp :
		for cmd in cmds :
			fp.write(cmd)
