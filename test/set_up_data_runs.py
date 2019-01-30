from optparse import OptionParser
import os

#stems for the different types of toy groups
topdir_stems = ['nominal',
				'JESUp','JESDown',
				'JERUp','JERDown',
				'isrUp','isrDown',
				'fsrUp','fsrDown',
				'hdampUp','hdampDown',
				'tuneUp','tuneDown',
				'crUp','crDown',
				]
#topdir_stems = ['JESUp','JESDown','JERUp','JERDown']

#command-line options
parser = OptionParser()
parser.add_option('-P','--par',type='choice', action='store', dest='par', choices=['Afb','mu','d'], help='Which parameter ("Afb", "mu", "d") is the parameter of interest? Required.')
parser.add_option('-T', '--tfilename', type='string', action='store', dest='tfilename', default='templates_powheg_aggregated_all.root')
(options, args) = parser.parse_args()

topdirnames = ['DATA_'+options.par+'_'+tds for tds in topdir_stems]

#get the current working directory so we can put new directories here
cwd = os.getcwd()

#loop through the different a-posteriori systematic types and make directories
for tdn in topdirnames :
	new_topdir_path = os.path.join(cwd,tdn)
	if not os.path.isdir(new_topdir_path) :
		os.mkdir(new_topdir_path)

#write the commands to run the toy groups into text files
cmds = []
for tds,tdn in zip(topdir_stems,topdirnames) :
	#first command to get to the directory
	cmd1 = 'cd '+os.path.join(cwd,tdn)+'; cmsenv\n'
	#second command to run the fitter
	cmd2 = 'python '+os.path.join('~','fittertest','..','python','run_fits.py')+' -M data -P '+options.par+' --tfile '+os.path.join('~','templatetest','total_template_files',options.tfilename)
	if tds!='nominal' : #remove the simple systematics and rateParams if we don't want them
		cmd2+=' --noSS'# --noRateParams'
		cmd2+=' --postsys '+tds #add the systematic type
	#just a blank line to separate them
	cmd3='\n'
	cmds+=[cmd1,cmd2,cmd3]
	
#open the new file and write the commands
with open('int_cmds_'+options.par+'_DATA.txt','w') as fp :
	for cmd in cmds :
		fp.write(cmd)
