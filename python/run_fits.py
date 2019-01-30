#imports
from fit import Fit
from optparse import OptionParser

##########								Parser Options								##########

parser = OptionParser()
#What to do?
parser.add_option('-M','--mode',  type='choice', action='store', dest='mode', choices=['data','toyGroup','singleToy','genWorkspace','genSingleToy'],
	help='Run on real data ("data") or toys ("toys")? Required.')
parser.add_option('-P','--par', 	 type='choice', action='store', dest='par', choices=['Afb','mu','d'],
	help='Which parameter ("Afb", "mu", "d") is the parameter of interest? Required.')
#With which template file?
parser.add_option('--tfile', type='string', action='store', dest='tfilepath',	   	  
	help='Which template file is holding the fit histograms? Required.')
#Over which subsets of the total run?
parser.add_option('--topologies', type='string', action='store', default='t1__t2__t3', dest='topologies',	   	  
	help='Which topologies do you want to do fits for? Separated by double underscores. ("t1","t2","t3")')
parser.add_option('--leptypes',   type='string', action='store', default='mu__el', 	   dest='leptypes',	   	  
	help='Which lepton types do you want to do simultaneous fits for? Separated by double underscores. ("mu","el")')
#With what a-posteriori systematic settings?
parser.add_option('--postsys',  type='choice', action='store', dest='postsys', default='nominal',
	choices=['nominal',
			 'JESUp','JESDown',
			 'JERUp','JERDown',
			 'isrUp','isrDown',
			 'fsrUp','fsrDown',
			 'hdampUp','hdampDown',
			 'tuneUp','tuneDown',
			 'crUp','crDown',
			 ], 
	help='What a-posteriori systematic settings do you want to use?')
#With what level of involvement?
parser.add_option('--noSS',  action='store_true', dest='noss')  #leave out other "simple" systematics
parser.add_option('--noRateParams',  action='store_true', dest='norateparams')  #leave out 'rateParam' nuisances
parser.add_option('--noCRs',  action='store_true', dest='nocontrolregions')  #fit in signal region only
parser.add_option('--sumCharges',  action='store_true', dest='sumcharges')  #are lepton charges summed in the template file?
parser.add_option('--verbose', action='store_true', dest='vb') #print debugging combine output?
parser.add_option('--postfit_plots_only', action='store_true', dest='postplotsonly') #just make postfit comparison plots?
#In what filename conventions?
parser.add_option('--out', 	  type='string', action='store', default='parameters', dest='out',	   	  
	help='Name stem for parameter values files made by this script')
parser.add_option('--append', type='string', action='store', default='', 		   dest='append',	   	  
	help='Append for end of parameter values filename')
#Configurations for toy runs
parser.add_option('--ntoys', type='int', action='store', default=1000, dest='ntoys',	   	  
	help='How many toys to run for each fit?')
parser.add_option('--nthreads', type='int', action='store', default=2, dest='nthreads',	   	  
	help='How many parallel processes should we use in running the fits to toys?')
parser.add_option('--toy-Afb', type='float', action='store', default=0.0, dest='toyAfb',	   	  
	help='Toy Afb value')
parser.add_option('--toy-mu',  type='float', action='store', default=0.0, dest='toymu',	   	  
	help='Toy mu value')
parser.add_option('--toy-d',   type='float', action='store', default=0.0, dest='toyd',	   	  
	help='Toy d value')
parser.add_option('--toySeed', type='string', action='store', default='-1', dest='toySeed',	   	  
	help='Seed for toy generation')
parser.add_option('--saveToys',  action='store_true', dest='savetoys')
parser.add_option('--toysFile', type='string', action='store', default='', dest='toysFile',	help='Name of file to pull pre-generated toys from')

(options, args) = parser.parse_args()

#process some options into lists
topologies = [t.lower() for t in options.topologies.split('__')]
leptypes = [lt.lower() for lt in options.leptypes.split('__')]
fnamepieces = (options.out,options.append)

##########								Main Script								##########

#start a new fit object (also initializes the parameter file)
fit = Fit(topologies,leptypes,options.par,options.postsys,options.noss,options.norateparams,options.nocontrolregions,options.sumcharges,fnamepieces,options.toyAfb,options.toymu,options.toyd,options.toySeed,options.vb,options.postplotsonly)

#build datacards
fit.buildDatacards(options.tfilepath)

#add PoIs and refine the model with a PhysicsModel class
fit.refinePhysicsModel(options.tfilepath)

#combine all of it into a workspace file using text2workspace.py
fit.createWorkspace()

if options.mode!='genWorkspace' :
	#run the fits using Combine
	fit.runCombine(options.mode,options.ntoys,options.nthreads,options.savetoys,options.tfilepath,options.toysFile)
