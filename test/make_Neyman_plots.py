from ROOT import *
from array import array
import CMS_lumi, tdrstyle
from math import *
import os, glob
from optparse import OptionParser

gROOT.SetBatch()

#Set some TDR options
tdrstyle.setTDRStyle()
iPeriod = 4 #13TeV iPeriod = 1*(0/1 7 TeV) + 2*(0/1 8 TeV)  + 4*(0/1 13 TeV)
CMS_lumi.writeExtraText = 1
CMS_lumi.extraText = "Preliminary"

##########								Parser Options								##########

parser = OptionParser()
#What to do?
parser.add_option('-P','--par', 	 type='choice', action='store', dest='par', choices=['Afb','mu','d'],
	help='Which parameter ("Afb", "mu", "d") is the parameter of interest? Required.')
#With which toyGroup directory?
parser.add_option('--toyGroupDir', type='string', action='store', dest='toygroupdir',	   	  
	help='Path to directory holding toyGroup runs to use for the plots')
#With which central value of the fit parameter (if Neyman plots rather than closure test plots)?
parser.add_option('--centralValue', type='float', action='store', default=10000000., dest='centralvalue',	   	  
	help='Central value of parameter of interest from fit to data')
#With what filename conventions?
parser.add_option('--append', type='string', action='store', default='', 		   dest='append',	   	  
	help='Append for end of parameter values filename')
#print debbugging statements?
parser.add_option('-V','--verbose',  action='store_true', dest='verbose')
(options, args) = parser.parse_args()

##########								Script								##########

#build output filename
output_filename = 'par_'+options.par+'_Neyman_plots'
if options.append!='' :
	output_filename+='_'+options.append
output_filename+='.root'

#open output file
outfile = TFile(output_filename,'recreate')

#build the list of input values by reading the toyGroup directory
cwd = os.getcwd()
os.chdir(options.toygroupdir)
dirnamestem = 'toyGroup_'+options.par+'='
dirlist = glob.glob(dirnamestem+'*')
if options.par=='Afb' :
	input_values = array('d',[float(dirname.split(dirnamestem)[1]) for dirname in dirlist])
else :
	input_values = array('d',[abs(float(dirname.split(dirnamestem)[1])) for dirname in dirlist if abs(float(dirname.split(dirnamestem)[1])) not in input_values])
os.chdir(cwd)
if options.verbose : print 'input_values = %s'%(input_values) #DEBUG

#TGraphErrors setup
n = len(input_values)
x_values = array('d',n*[1.0])
y_values = array('d',n*[1.0])
x_errs   = array('d',n*[0.1])
y_1_errs = array('d',n*[1.0])
y_2_errs = array('d',n*[1.0])
onesigma_graph = TGraphAsymmErrors(n,x_values,y_values,x_errs,x_errs,y_1_errs,y_1_errs)
twosigma_graph = TGraphAsymmErrors(n,x_values,y_values,x_errs,x_errs,y_2_errs,y_2_errs)

#closure test plot setup
title = 'Fitting Closure Tests '
if options.append.find('no_sys')!=-1 :
	title += '(no systematics) '
title+='for '
if options.par == 'Afb' :
	title += 'A_{FB}; Input A_{FB}; Fitted A_{FB}'
elif par_of_int == 'mu' :
	title += '#mu; Input |#mu|; Fitted |#mu|'
elif par_of_int == 'd' :
	title += 'd; Input |d|; Fitted |d|'
closure_test_histo = TH2D('closure_test_histo',title,(n-1),input_values,4*n,2*input_values[0],2*input_values[n-1])

#Set graph attributes
onesigma_graph.SetFillColor(kGreen)
onesigma_graph.SetLineStyle(2)
onesigma_graph.SetLineWidth(3)
onesigma_graph.SetLineColor(kBlack)
onesigma_graph.SetMarkerStyle(20)
onesigma_graph.SetMarkerColor(kBlack)
twosigma_graph.SetFillColor(kYellow)
tstitle='Neyman Construction for '
formattedvar = ''
if options.par=='Afb' :
	formattedvar = 'A_{FB}'
elif options.par=='mu' :
	formattedvar = '|#mu|'
elif options.par=='d' :
	formattedvar = '|d|'
tstitle+=formattedvar
if options.append.find('no_sys')!=-1 :
	tstitle += ' (no systematics)'
tstitle+='; Input %s; Fitted %s'%(formattedvar,formattedvar)
twosigma_graph.SetTitle(tstitle)

#for each of the data points tested
for i in range(n) :
	realvalues=[]
	#build the path to the file holding the toy results
	filepath = '%s/toyGroup_%s=%.2f/higgsCombineToys%s%.3f.MultiDimFit.all.root'%(options.toygroupdir,options.par,input_values[i],options.par,input_values[i])
	filepath_opp_sign = '%s/toyGroup_%s=%.2f/higgsCombineToys%s%.3f.MultiDimFit.all.root'%(options.toygroupdir,options.par,-1*input_values[i],options.par,-1*input_values[i])
	files_to_read = [filepath]
	if options.par!='Afb' :
		files_to_read.append(filepath_opp_sign)
	#make a list of all the fitted parameter values
	par_values_list = []
	for fp in files_to_read :
		if options.verbose : print 'Getting '+options.par+' values from file at path '+fp #DEBUG
		#open the root file
		par_values_file = TFile.Open(fp)
		#put the values in the list
		treename='limit'
		readArray = array('f',[0.])
		tree=par_values_file.Get(treename)
		n_tree_entries = tree.GetEntries()
		tree.SetBranchAddress(options.par,readArray)
		for j in range(n_tree_entries) :
			tree.GetEntry(j)
			#if the POI is Afb, add the value, otherwise add its absolute value
			if options.par=='Afb' :
				par_values_list.append(readArray[0])
			else :
				par_values_list.append(abs(readArray[0]))
	#sort the list
	par_values_list.sort()
	#read the values into the closure test histogram
	mean=0.
	for value in par_values_list :
		closure_test_histo.Fill(input_values[i],value,1./len(par_values_list))
		mean+=value
	if options.verbose : print '	Got '+str(len(par_values_list))+' values' #DEBUG
	#find the mean and +/- 1/2 sigma values
	mean=mean/len(par_values_list)
	#median = par_values_list[int(round(len(par_values_list)*(1.)/2.))]
	p1sigma = par_values_list[int(round(len(par_values_list)*(1.+0.683)/2.))]
	m1sigma = par_values_list[int(round(len(par_values_list)*(1-0.683)/2.))] 
	p2sigma = par_values_list[min(len(par_values_list)-1,int(round(len(par_values_list)*(1.+0.955)/2.)))] 
	m2sigma = par_values_list[min(len(par_values_list)-1,int(round(len(par_values_list)*(1.-0.955)/2.)))]
	#Set graphs' point values
	onesigma_graph.SetPoint(i,input_values[i],mean)
	twosigma_graph.SetPoint(i,input_values[i],mean)
	onesigma_graph.SetPointError(i,x_errs[i],x_errs[i],p1sigma-mean,abs(m1sigma-mean))
	twosigma_graph.SetPointError(i,x_errs[i],x_errs[i],p2sigma-mean,abs(m2sigma-mean))
	if options.verbose : print '	Bands: %.4f || %.4f | %.4f | %.4f || %.4f'%(m2sigma,m1sigma,mean,p1sigma,p2sigma) #DEBUG

if options.centralvalue!=10000000. :
	#Interpolate given the central value
	data_fit_one_sigma_down = 2*input_values[0]
	data_fit_one_sigma_up   = 2*input_values[n-1]
	data_fit_two_sigma_down = 2*input_values[0]
	data_fit_two_sigma_up   = 2*input_values[n-1]
	data_fit_mean = options.centralvalue
	for i in range(n-1) :
		thisx = array('d',[0.0]); thisymean = array('d',[0.0])
		nextx = array('d',[0.0]); nextymean = array('d',[0.0])
		onesigma_graph.GetPoint(i,thisx,thisymean); onesigma_graph.GetPoint(i+1,nextx,nextymean)
		thisyhi  = thisymean[0]+onesigma_graph.GetErrorYhigh(i)
		thisylow = thisymean[0]-onesigma_graph.GetErrorYlow(i)
		nextyhi  = nextymean[0]+onesigma_graph.GetErrorYhigh(i+1)
		nextylow = nextymean[0]-onesigma_graph.GetErrorYlow(i+1)
		if thisyhi <= options.centralvalue and nextyhi > options.centralvalue and data_fit_one_sigma_down == 2*input_values[0] :
			slope = (nextyhi-thisyhi)/(input_values[i+1]-input_values[i])
			data_fit_one_sigma_down = (options.centralvalue-thisyhi)/slope+input_values[i]
		if thisylow <= options.centralvalue and nextylow > options.centralvalue :
			slope = (nextylow-thisylow)/(input_values[i+1]-input_values[i])
			data_fit_one_sigma_up = (options.centralvalue-thisylow)/slope+input_values[i]
		if thisymean[0] <= options.centralvalue and nextymean[0] > options.centralvalue :
			slope = (nextymean[0]-thisymean[0])/(input_values[i+1]-input_values[i])
			data_fit_mean = (options.centralvalue-thisymean[0])/slope+input_values[i]
	for i in range(n-1) :
		thisx = array('d',[0.0]); thisymean = array('d',[0.0])
		nextx = array('d',[0.0]); nextymean = array('d',[0.0])
		twosigma_graph.GetPoint(i,thisx,thisymean); twosigma_graph.GetPoint(i+1,nextx,nextymean)
		thisyhi  = thisymean[0]+twosigma_graph.GetErrorYhigh(i)
		thisylow = thisymean[0]-twosigma_graph.GetErrorYlow(i)
		nextyhi  = nextymean[0]+twosigma_graph.GetErrorYhigh(i+1)
		nextylow = nextymean[0]-twosigma_graph.GetErrorYlow(i+1)
		if thisyhi <= options.centralvalue and nextyhi > options.centralvalue and data_fit_one_sigma_down == 2*input_values[0] :
			slope = (nextyhi-thisyhi)/(input_values[i+1]-input_values[i])
			data_fit_two_sigma_down = (options.centralvalue-thisyhi)/slope+input_values[i]
		if thisylow <= options.centralvalue and nextylow > options.centralvalue :
			slope = (nextylow-thisylow)/(input_values[i+1]-input_values[i])
			data_fit_two_sigma_up = (options.centralvalue-thisylow)/slope+input_values[i]

	if options.verbose : print 'Central value = %.5f, plus one sigma = %.5f, minus one sigma = %.5f'%(data_fit_mean,data_fit_one_sigma_up,data_fit_one_sigma_down) #DEBUG
	if options.verbose : print '	plus two sigma = %.5f, minus two sigma = %.5f'%(data_fit_two_sigma_up,data_fit_two_sigma_down) #DEBUG
	print 'FINAL RESULT: Parameter %s = %.5f + %.5f - %.5f (95%% CL ~= +/-%.5f)'%(options.par,data_fit_mean,data_fit_one_sigma_up-data_fit_mean,abs(data_fit_one_sigma_down-data_fit_mean),data_fit_two_sigma_up)

	#Build the lines to indicate based on the data fit value
	lines = []
	x_low = twosigma_graph.GetXaxis().GetBinLowEdge(twosigma_graph.GetXaxis().GetFirst())
	x_high = twosigma_graph.GetXaxis().GetBinUpEdge(twosigma_graph.GetXaxis().GetLast())
	y_low = twosigma_graph.GetYaxis().GetBinLowEdge(twosigma_graph.GetYaxis().GetFirst())
	lines.append(TLine(x_low,options.centralvalue,data_fit_one_sigma_up,options.centralvalue))
	lines.append(TLine(data_fit_one_sigma_down,options.centralvalue,data_fit_one_sigma_down,y_low))
	lines.append(TLine(data_fit_one_sigma_up,options.centralvalue,data_fit_one_sigma_up,y_low))
	lines.append(TLine(data_fit_mean,options.centralvalue,data_fit_mean,y_low))
	for line in lines :
		line.SetLineWidth(3); line.SetLineColor(kRed); line.SetLineStyle(2)

	#Build a legend
	leg = TLegend(0.62,0.67,0.9,0.9)
	leg.AddEntry(onesigma_graph,'toy mean values','PL')
	leg.AddEntry(onesigma_graph,'#pm 1 #sigma','F')
	leg.AddEntry(twosigma_graph,'#pm 2 #sigma','F')
	leg.AddEntry(lines[0],'data fit','L')

	#Plot the neyman construction histogram
	neyman_canv = TCanvas('neyman_canv','neyman_canv',900,900)
	neyman_canv.cd()
	twosigma_graph.Draw('A E3')
	onesigma_graph.Draw('SAME E3')
	onesigma_graph.Draw('SAME PLX')
	for line in lines :
		line.Draw()
	leg.Draw()
	outfile.cd()
	neyman_canv.Write()

#The line to go on the closure test plots
otherline = TLine(input_values[0],input_values[0],input_values[n-1],input_values[n-1])
otherline.SetLineColor(kBlack)
otherline.SetLineWidth(4)

#plot the closure test histogram
closure_test_canv = TCanvas('closure_test_canv','closure_test_canv',900,900)
closure_test_canv.cd()
closure_test_histo.Draw('COL')
otherline.Draw()

outfile.cd()
closure_test_canv.Write()
outfile.Close()
