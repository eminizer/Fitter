from optparse import OptionParser
import os

#command-line options
parser = OptionParser()
parser.add_option('-D','--dirname',  type='string', action='store', dest='dirname', help='Name of top directory to create/put toys in')
parser.add_option('-P','--par', 	 type='choice', action='store', dest='par', choices=['Afb','mu','d'], help='Which parameter ("Afb", "mu", "d") is the parameter of interest? Required.')
(options, args) = parser.parse_args()

#stems for numerical values of parameters in toyGroups
stems = []
if options.par=='Afb' :
	stems = ['-0.50','-0.45','-0.40','-0.35','-0.30','-0.25','-0.20','-0.15','-0.10','-0.05','0.00','0.05','0.10','0.15','0.20','0.25','0.30','0.35','0.40','0.45','0.50']
else :
	stems = ['0.130','0.132','0.134','0.136','0.138','0.140','0.142','0.144','0.146','0.148','0.150','0.152','0.154','0.156','0.158','0.160','0.162','0.164','0.166','0.168','0.170']
dirnames = ['toyGroup_'+options.par+'='+stem for stem in stems]
#print dirnames #DEBUG

#get the current working directory so we can put new directories here
cwd = os.getcwd()

#create or cd to the inputted top directory
new_topdir_path = os.path.join(cwd,options.dirname)
if not os.path.isdir(new_topdir_path) :
	os.mkdir(new_topdir_path)
os.chdir(new_topdir_path)

#make the new directories within
for dirname in dirnames :
	os.mkdir(dirname)

#change back to where we started
os.chdir(cwd)
