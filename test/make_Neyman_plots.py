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
#print debugging statements?
parser.add_option('-V','--verbose',  action='store_true', dest='verbose')
#Take the absolute value of mu and d?
parser.add_option('--unsigned',  action='store_true', dest='unsigned')
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
if options.unsigned :
	input_values_from_dirnames = [abs(float(dirname.split(dirnamestem)[1])) for dirname in dirlist if abs(float(dirname.split(dirnamestem)[1])) not in input_values]
else :
	input_values_from_dirnames = [float(dirname.split(dirnamestem)[1]) for dirname in dirlist]
input_values = array('d',input_values_from_dirnames)
#loop over the values and make the list of bin edges for the closure test histogram
input_bins_list = []
for i in range(len(input_values_from_dirnames)-1) :
	input_bins_list.append(input_values_from_dirnames[i]-0.5*(input_values_from_dirnames[i+1]-input_values_from_dirnames[i]))
input_bins_list.append(input_values_from_dirnames[-1]-0.5*(input_values_from_dirnames[-1]-input_values_from_dirnames[-2]))
input_bins_list.append(input_values_from_dirnames[-1]+0.5*(input_values_from_dirnames[-1]-input_values_from_dirnames[-2]))
input_bins = array('d',input_bins_list)
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
title = ''
#title = 'Fitting Closure Tests '
#if options.append.find('no_sys')!=-1 :
#	title += '(no systematics) '
#title+='for '
if options.par == 'Afb' :
	if options.unsigned :
		#title += '|A_{FB}|; True |A_{FB}|; Best Fit |A_{FB}|'
		title += '; True |A_{FB}|; Best Fit |A_{FB}|'
	else :
		#title += 'A_{FB}; True A_{FB}; Best Fit A_{FB}'
		title += '; True A_{FB}; Best Fit A_{FB}'
elif options.par == 'mu' :
	if options.unsigned :
		#title += '|#mu|; True |#mu|; Best Fit |#mu|'
		title += '; True |#mu|; Best Fit |#mu|'
	else :
		#title += '#mu; True #mu; Best Fit #mu'
		title += '; True #mu; Best Fit #mu'
elif options.par == 'd' :
	if options.unsigned :
		#title += '|d|; True |d|; Best Fit |d|'
		title += '; True |d|; Best Fit |d|'
	else :
		#title += 'd; True d; Best Fit d'
		title += '; True d; Best Fit d'
if options.par == 'Afb' :
	closure_test_histo = TH2D('closure_test_histo',title,n,input_bins,4*n+2,2*input_values[0]-0.025,2*input_values[n-1]+0.025)
else :
	closure_test_histo = TH2D('closure_test_histo',title,n,input_bins,4*n+2,input_values[0]-0.02,input_values[n-1]+0.02)
closure_test_histo.SetStats(0)

#Set graph attributes
onesigma_graph.SetFillColor(kGreen)
onesigma_graph.SetLineStyle(2)
onesigma_graph.SetLineWidth(3)
onesigma_graph.SetLineColor(kBlack)
onesigma_graph.SetMarkerStyle(20)
onesigma_graph.SetMarkerColor(kBlack)
twosigma_graph.SetFillColor(kYellow)
#tstitle='Neyman Construction for '
tstitle=''
formattedvar = ''
if options.par=='Afb' :
	formattedvar = 'A_{FB}'
elif options.par=='mu' :
	formattedvar = '#mu'
elif options.par=='d' :
	formattedvar = 'd'
#tstitle+=formattedvar
#if options.append.find('no_sys')!=-1 :
#	tstitle += ' (no systematics)'
tstitle+='; True %s; Best Fit %s'%(formattedvar,formattedvar)
twosigma_graph.SetTitle(tstitle)

#for each of the data points tested
for i in range(n) :
	realvalues=[]
	#build the path to the file holding the toy results
	filepath = ''; filepath_opp_sign = ''
	if options.par=='Afb' :
		filepath = '%s/toyGroup_%s=%.2f/higgsCombineToys%s%.3f.MultiDimFit.all.root'%(options.toygroupdir,options.par,input_values[i],options.par,input_values[i])
		filepath_opp_sign = '%s/toyGroup_%s=%.2f/higgsCombineToys%s%.3f.MultiDimFit.all.root'%(options.toygroupdir,options.par,-1*input_values[i],options.par,-1*input_values[i])
	else :
		filepath = '%s/toyGroup_%s=%.3f/higgsCombineToys%s%.3f.MultiDimFit.all.root'%(options.toygroupdir,options.par,input_values[i],options.par,input_values[i])
		filepath_opp_sign = '%s/toyGroup_%s=%.3f/higgsCombineToys%s%.3f.MultiDimFit.all.root'%(options.toygroupdir,options.par,-1*input_values[i],options.par,-1*input_values[i])
	files_to_read = [filepath]
	if options.unsigned :
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
			#add the value
			if options.unsigned :
				par_values_list.append(abs(readArray[0]))
			else :
				par_values_list.append(readArray[0])
	#sort the list
	par_values_list.sort()
	#read the values into the closure test histogram
	mean=0.
	for value in par_values_list :
		closure_test_histo.Fill(input_values[i],value,1./len(par_values_list))
		mean+=value
	if options.verbose : print '	Got '+str(len(par_values_list))+' values' #DEBUG
	#find the mean and median and +/- 1/2 sigma values
	mean=mean/len(par_values_list)
	median=par_values_list[int(round(len(par_values_list)*0.5))]
	#median = par_values_list[int(round(len(par_values_list)*(1.)/2.))]
	p1sigma = par_values_list[int(round(len(par_values_list)*(1.+0.683)/2.))]
	m1sigma = par_values_list[int(round(len(par_values_list)*(1-0.683)/2.))] 
	p2sigma = par_values_list[min(len(par_values_list)-1,int(round(len(par_values_list)*(1.+0.955)/2.)))] 
	m2sigma = par_values_list[min(len(par_values_list)-1,int(round(len(par_values_list)*(1.-0.955)/2.)))]
	#Set graphs' point values
	onesigma_graph.SetPoint(i,input_values[i],median)
	twosigma_graph.SetPoint(i,input_values[i],median)
	onesigma_graph.SetPointError(i,x_errs[i],x_errs[i],p1sigma-median,abs(m1sigma-median))
	twosigma_graph.SetPointError(i,x_errs[i],x_errs[i],p2sigma-median,abs(m2sigma-median))
	if options.verbose : print '	Bands: %.4f || %.4f | %.4f | %.4f || %.4f'%(m2sigma,m1sigma,median,p1sigma,p2sigma) #DEBUG

if options.centralvalue!=10000000. :
	#Interpolate given the central value
	if options.par=='Afb' :
		data_fit_one_sigma_down = 2*input_values[0]
		data_fit_one_sigma_up   = 2*input_values[n-1]
		data_fit_two_sigma_down = 2*input_values[0]
		data_fit_two_sigma_up   = 2*input_values[n-1]
	else :
		data_fit_one_sigma_down = input_values[0]-0.02
		data_fit_one_sigma_up   = input_values[n-1]+0.02
		data_fit_two_sigma_down = input_values[0]-0.02
		data_fit_two_sigma_up   = input_values[n-1]+0.02
	dfosd_changed = False; dftsd_changed = False
	data_fit_mean = options.centralvalue
	for i in range(n-1) :
		thisymedian = array('d',[0.0]); thisx = array('d',[0.0])
		nextymedian = array('d',[0.0]); nextx = array('d',[0.0])
		onesigma_graph.GetPoint(i,thisx,thisymedian); onesigma_graph.GetPoint(i+1,nextx,nextymedian)
		thisyhi  = thisymedian[0]+onesigma_graph.GetErrorYhigh(i)
		thisylow = thisymedian[0]-onesigma_graph.GetErrorYlow(i)
		nextyhi  = nextymedian[0]+onesigma_graph.GetErrorYhigh(i+1)
		nextylow = nextymedian[0]-onesigma_graph.GetErrorYlow(i+1)
		if thisyhi <= options.centralvalue and nextyhi > options.centralvalue and not dfosd_changed :
			slope = (nextyhi-thisyhi)/(input_values[i+1]-input_values[i])
			data_fit_one_sigma_down = (options.centralvalue-thisyhi)/slope+input_values[i]
			dfosd_changed=True
		if thisylow <= options.centralvalue and nextylow > options.centralvalue :
			slope = (nextylow-thisylow)/(input_values[i+1]-input_values[i])
			data_fit_one_sigma_up = (options.centralvalue-thisylow)/slope+input_values[i]
		if thisymedian[0] <= options.centralvalue and nextymedian[0] > options.centralvalue :
			slope = (nextymedian[0]-thisymedian[0])/(input_values[i+1]-input_values[i])
			data_fit_mean = (options.centralvalue-thisymedian[0])/slope+input_values[i]
	for i in range(n-1) :
		thisymedian = array('d',[0.0]); thisx = array('d',[0.0])
		nextymedian = array('d',[0.0]); nextx = array('d',[0.0])
		twosigma_graph.GetPoint(i,thisx,thisymedian); twosigma_graph.GetPoint(i+1,nextx,nextymedian)
		thisyhi  = thisymedian[0]+twosigma_graph.GetErrorYhigh(i)
		thisylow = thisymedian[0]-twosigma_graph.GetErrorYlow(i)
		nextyhi  = nextymedian[0]+twosigma_graph.GetErrorYhigh(i+1)
		nextylow = nextymedian[0]-twosigma_graph.GetErrorYlow(i+1)
		if thisyhi <= options.centralvalue and nextyhi > options.centralvalue and not dftsd_changed :
			slope = (nextyhi-thisyhi)/(input_values[i+1]-input_values[i])
			data_fit_two_sigma_down = (options.centralvalue-thisyhi)/slope+input_values[i]
			dftsd_changed=True
		if thisylow <= options.centralvalue and nextylow > options.centralvalue :
			slope = (nextylow-thisylow)/(input_values[i+1]-input_values[i])
			data_fit_two_sigma_up = (options.centralvalue-thisylow)/slope+input_values[i]

	if options.verbose : print 'Central value = %.6f, plus one sigma = %.6f, minus one sigma = %.6f'%(data_fit_mean,data_fit_one_sigma_up,data_fit_one_sigma_down) #DEBUG
	if options.verbose : print '	plus two sigma = %.6f, minus two sigma = %.6f'%(data_fit_two_sigma_up,data_fit_two_sigma_down) #DEBUG
	print 'FINAL RESULT: Parameter %s = %.6f + %.6f - %.6f (95%% CL ~= +/-%.6f)'%(options.par,data_fit_mean,data_fit_one_sigma_up-data_fit_mean,abs(data_fit_one_sigma_down-data_fit_mean),data_fit_two_sigma_up)

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
