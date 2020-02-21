from ROOT import *
from array import array
import CMS_lumi, tdrstyle
from math import *
import os, glob

gROOT.SetBatch()

#name of output file
ofn = 'gof_plots.root'

#some options for the fit parameters and algorithms to plot
#fitdapp = '_measurements/GoF_runs'
fitdapp = '_measurements/saturated_GoF_runs'
filesdapp = fitdapp #'_algo_files'
datafn='higgsCombineTest.GoodnessOfFit.mH120.root'
toyfnpatt='higgsCombineTest.GoodnessOfFit.mH120.*.root'
cnames = ['t1_muplus_SR','t1_muminus_SR','t1_elplus_SR','t1_elminus_SR',
		  't2_muplus_SR','t2_muminus_SR','t2_elplus_SR','t2_elminus_SR',
		  't3_muplus_SR','t3_muminus_SR','t3_elplus_SR','t3_elminus_SR',]
pois = ['Afb','d','mu']
#algos = ['KS']#,'AD']#,'saturated']
algos = ['saturated']
fndict = {}
for poi in pois :
	fndict[poi] = {}
	for algo in algos :
		fndict[poi][algo]={}
		fndict[poi][algo]['data']='../{}{}/{}'.format(poi,fitdapp,datafn)
		fndict[poi][algo]['toys']=glob.glob('../{}{}/{}'.format(poi,fitdapp,toyfnpatt))

#dictionary of histogram limits/bins per poi and algorithm
hdetails ={
	't1_muplus_SR':{
		'Afb':{'KS':{'nBins':100,'low':0.,'hi':0.045},'AD':{'nBins':100,'low':0.,'hi':10.},},
		'd':{'KS':{'nBins':100,'low':0.,'hi':0.2},'AD':{'nBins':100,'low':0.,'hi':65.},},
		'mu':{'KS':{'nBins':100,'low':0.,'hi':0.2},'AD':{'nBins':100,'low':0.,'hi':60.},},},
	't1_muminus_SR':{
		'Afb':{'KS':{'nBins':100,'low':0.,'hi':0.035},'AD':{'nBins':100,'low':0.,'hi':10.},},
		'd':{'KS':{'nBins':100,'low':0.,'hi':0.15},'AD':{'nBins':100,'low':0.,'hi':15.},},
		'mu':{'KS':{'nBins':100,'low':0.,'hi':0.15},'AD':{'nBins':100,'low':0.,'hi':15.},},},
	't1_elplus_SR':{
		'Afb':{'KS':{'nBins':100,'low':0.,'hi':0.07},'AD':{'nBins':100,'low':0.,'hi':15.},},
		'd':{'KS':{'nBins':100,'low':0.,'hi':0.22},'AD':{'nBins':100,'low':0.,'hi':25.},},
		'mu':{'KS':{'nBins':100,'low':0.,'hi':0.22},'AD':{'nBins':100,'low':0.,'hi':25.},},},
	't1_elminus_SR':{
		'Afb':{'KS':{'nBins':100,'low':0.,'hi':0.06},'AD':{'nBins':100,'low':0.,'hi':10.},},
		'd':{'KS':{'nBins':100,'low':0.,'hi':0.18},'AD':{'nBins':100,'low':0.,'hi':12.},},
		'mu':{'KS':{'nBins':100,'low':0.,'hi':0.18},'AD':{'nBins':100,'low':0.,'hi':12.},},},
	't2_muplus_SR':{
		'Afb':{'KS':{'nBins':100,'low':0.,'hi':0.08},'AD':{'nBins':100,'low':0.,'hi':10.},},
		'd':{'KS':{'nBins':100,'low':0.,'hi':0.12},'AD':{'nBins':100,'low':0.,'hi':100.},},
		'mu':{'KS':{'nBins':100,'low':0.,'hi':0.12},'AD':{'nBins':100,'low':0.,'hi':110.},},},
	't2_muminus_SR':{
		'Afb':{'KS':{'nBins':100,'low':0.,'hi':0.015},'AD':{'nBins':100,'low':0.,'hi':10.},},
		'd':{'KS':{'nBins':100,'low':0.,'hi':0.06},'AD':{'nBins':100,'low':0.,'hi':15.},},
		'mu':{'KS':{'nBins':100,'low':0.,'hi':0.06},'AD':{'nBins':100,'low':0.,'hi':20.},},},
	't2_elplus_SR':{
		'Afb':{'KS':{'nBins':100,'low':0.,'hi':0.05},'AD':{'nBins':100,'low':0.,'hi':12.},},
		'd':{'KS':{'nBins':100,'low':0.,'hi':0.15},'AD':{'nBins':100,'low':0.,'hi':25.},},
		'mu':{'KS':{'nBins':100,'low':0.,'hi':0.15},'AD':{'nBins':100,'low':0.,'hi':35.},},},
	't2_elminus_SR':{
		'Afb':{'KS':{'nBins':100,'low':0.,'hi':0.05},'AD':{'nBins':100,'low':0.,'hi':6.},},
		'd':{'KS':{'nBins':100,'low':0.,'hi':0.17},'AD':{'nBins':100,'low':0.,'hi':25.},},
		'mu':{'KS':{'nBins':100,'low':0.,'hi':0.14},'AD':{'nBins':100,'low':0.,'hi':28.},},},
	't3_muplus_SR':{
		'Afb':{'KS':{'nBins':100,'low':0.,'hi':0.0065},'AD':{'nBins':100,'low':0.,'hi':5.},},
		'd':{'KS':{'nBins':100,'low':0.,'hi':0.045},'AD':{'nBins':100,'low':0.,'hi':105.},},
		'mu':{'KS':{'nBins':100,'low':0.,'hi':0.047},'AD':{'nBins':100,'low':0.,'hi':135.},},},
	't3_muminus_SR':{
		'Afb':{'KS':{'nBins':100,'low':0.,'hi':0.0065},'AD':{'nBins':100,'low':0.,'hi':10.},},
		'd':{'KS':{'nBins':100,'low':0.,'hi':0.03},'AD':{'nBins':100,'low':0.,'hi':60.},},
		'mu':{'KS':{'nBins':100,'low':0.,'hi':0.032},'AD':{'nBins':100,'low':0.,'hi':70.},},},
	't3_elplus_SR':{
		'Afb':{'KS':{'nBins':100,'low':0.,'hi':0.006},'AD':{'nBins':100,'low':0.,'hi':7.},},
		'd':{'KS':{'nBins':100,'low':0.,'hi':0.025},'AD':{'nBins':100,'low':0.,'hi':60.},},
		'mu':{'KS':{'nBins':100,'low':0.,'hi':0.025},'AD':{'nBins':100,'low':0.,'hi':60.},},},
	't3_elminus_SR':{
		'Afb':{'KS':{'nBins':100,'low':0.,'hi':0.007},'AD':{'nBins':100,'low':0.,'hi':9.},},
		'd':{'KS':{'nBins':100,'low':0.,'hi':0.025},'AD':{'nBins':100,'low':0.,'hi':85.},},
		'mu':{'KS':{'nBins':100,'low':0.,'hi':0.025},'AD':{'nBins':100,'low':0.,'hi':115.},},},
	'all_channels':{
		'Afb':{'saturated':{'nBins':80,'low':800.,'hi':1200.},},
		'd':{'saturated':{'nBins':80,'low':800.,'hi':1200.},},
		'mu':{'saturated':{'nBins':80,'low':800.,'hi':1200.},},
	}
}

#Set some TDR options
tdrstyle.setTDRStyle()
iPeriod = 4 #13TeV iPeriod = 1*(0/1 7 TeV) + 2*(0/1 8 TeV)  + 4*(0/1 13 TeV)
CMS_lumi.writeExtraText = 1
CMS_lumi.extraText = "Preliminary"

#array to hold values from trees
la=array('d',[0.])

#list of all objects so they don't get deleted
allobjs = []

#open the output file
ofp = TFile(ofn,'recreate')

##loop over all the channels
#for cn in cnames :
#	print('In channel {}...'.format(cn))
##loop over the different pois and algorithms
for poi in pois :
	print('  Getting values for fits for {}...'.format(poi))
	for algo in algos :
		print('    Getting {} algorithm results...'.format(algo))
		#open the data file to get the single value
		dfp = TFile.Open(fndict[poi][algo]['data'])
		dt=dfp.Get('limit')
		#dt.SetBranchAddress(cn,la)
		dt.SetBranchAddress('limit',la)
		dt.GetEntry(0)
		datavalue=la[0]
		print('      data value: {}'.format(datavalue))
		dfp.Close()
		#get values from each of the toy dataset files
		toyvalues = []
		#toyvaluehist = TH1D('{}_{}_{}_h'.format(cn,poi,algo),'; {} test statistic; # toys'.format(algo),hdetails[cn][poi][algo]['nBins'],
		#					hdetails[cn][poi][algo]['low'],hdetails[cn][poi][algo]['hi'])
		toyvaluehist = TH1D('{}_{}_h'.format(poi,algo),'; {} test statistic; # toys'.format(algo),hdetails['all_channels'][poi][algo]['nBins'],
							hdetails['all_channels'][poi][algo]['low'],hdetails['all_channels'][poi][algo]['hi'])
		allobjs.append(toyvaluehist)
		for tfn in fndict[poi][algo]['toys'] :
			tfp=TFile.Open(tfn)
			tt=tfp.Get('limit')
			#tt.SetBranchAddress(cn,la)
			tt.SetBranchAddress('limit',la)
			for entry in range(tt.GetEntries()) :
				tt.GetEntry(entry)
				toyvalues.append(la[0])
				toyvaluehist.Fill(la[0])
			tfp.Close()
		#calculate the p-value from the data value and the list of toy values
		toyvalues.sort()
		ntvs=len(toyvalues)
		print('      lowest/median/highest of {} toy values: {} / {} / {}'.format(ntvs,toyvalues[0],toyvalues[ntvs/2],toyvalues[ntvs-1]))
		firsthighervalueindex=ntvs
		for index,tv in enumerate(toyvalues) :
			if tv>datavalue :
				firsthighervalueindex=index
				break
		pvalue = 1.*len(toyvalues[firsthighervalueindex:])/ntvs
		print('      p value = {}'.format(pvalue))
		#Declare the canvas, set histogram/line/etc. properties, and make/save plots
		ofp.cd()
		#canv = TCanvas('{}_{}_{}_c'.format(cn,poi,algo),'{}_{}_{}_c'.format(cn,poi,algo),1100,900)
		canv = TCanvas('{}_{}_c'.format(poi,algo),'{}_{}_c'.format(poi,algo),1100,900)
		allobjs.append(canv)
		toyvaluehist.SetStats(0); toyvaluehist.SetMinimum(0)
		toyvaluehist.SetLineWidth(3); toyvaluehist.SetLineColor(kBlack)
		datavalueline = TLine(datavalue,0,datavalue,toyvaluehist.GetMaximum())
		allobjs.append(datavalueline)
		datavalueline.SetLineWidth(3); datavalueline.SetLineColor(kRed+2)
		toyvaluehist.Draw("HIST") 
		datavalueline.Draw("SAME")
		allobjs.append(CMS_lumi.CMS_lumi(canv, iPeriod, 33))
		canv.Write()

print('Done!')
ofp.Close()

