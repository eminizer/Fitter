from ROOT import *
from array import array
from math import *

#settings
#data_fit_central_value =  #AFB WITH SYS
data_fit_central_value = 0.1 #AFB NO SYS
#data_fit_central_value = 0.0910471482453 #MU WITH SYS
#data_fit_central_value = 0.0364291482813 #MU NO SYS
#data_fit_central_value =  #D WITH SYS 
#data_fit_central_value =  #D NO SYS

#append = '_everything'
append = '_fix_mu_and_d'; par_of_int = 'AFB'
#append = '_fix_AFB_and_d'; par_of_int = 'mu'
#append = '_fix_AFB_and_mu'; par_of_int = 'd'
append = '_only_'+par_of_int

input_values = array('d',[-0.5,-0.45,-0.4,-0.35,-0.3,-0.25,-0.2,-0.15,-0.1,-0.05,0.0,0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55])
if par_of_int!='AFB' :
	input_values = array('d',[0.0,0.025,0.05,0.075,0.1,0.125,0.15,0.175,0.2,0.225,0.25,0.275,0.3,0.325])
	#input_values = array('d',[-0.3,-0.275,-0.25,-0.225,-0.2,-0.175,-0.15,-0.125,-0.1,-0.075,-0.05,-0.025,0.0,0.025,0.05,0.075,0.1,0.125,0.15,0.175,0.2,0.225,0.25,0.275,0.3,0.325])

output_filename = 'par_'+par_of_int+'_closure_test_plots'+append+'.root'

#output file
outfile = TFile(output_filename,'recreate')

#TGraphErrors setup
n = len(input_values)-1
x_values = array('d',n*[1.0])
y_values = array('d',n*[1.0])
x_errs   = array('d',n*[0.1])
y_1_errs = array('d',n*[1.0])
y_2_errs = array('d',n*[1.0])
onesigma_graph = TGraphAsymmErrors(n,x_values,y_values,x_errs,x_errs,y_1_errs,y_1_errs)
twosigma_graph = TGraphAsymmErrors(n,x_values,y_values,x_errs,x_errs,y_2_errs,y_2_errs)

#closure test plot setup
title = 'Fitting Closure Tests'
if append.find('_only_')!=-1 :
	title += ' (no systematics)'
if par_of_int == 'AFB' :
	title += '; Input A_{FB}; Fitted A_{FB}'
elif par_of_int == 'mu' :
	title += '; Input |#mu|; Fitted |#mu|'
elif par_of_int == 'd' :
	title += '; Input |d|; Fitted |d|'
closure_test_histo = TH2D('closure_test_histo',title,n,input_values,4*n,2*input_values[0],2*input_values[n-1])

#Set graph attributes
onesigma_graph.SetFillColor(kGreen)
onesigma_graph.SetLineStyle(2)
onesigma_graph.SetLineWidth(3)
onesigma_graph.SetLineColor(kBlack)
onesigma_graph.SetMarkerStyle(20)
onesigma_graph.SetMarkerColor(kBlack)
twosigma_graph.SetFillColor(kYellow)
if par_of_int=='AFB' :
	twosigma_graph.SetTitle('Neyman Construction for A_{FB}')
	twosigma_graph.GetXaxis().SetTitle('Input A_{FB}')
	twosigma_graph.GetYaxis().SetTitle('Fitted A_{FB}')
elif par_of_int=='mu' :
	twosigma_graph.SetTitle('Neyman Construction for #mu')
	twosigma_graph.GetXaxis().SetTitle('Input |#mu|')
	twosigma_graph.GetYaxis().SetTitle('Fitted |#mu|')
elif par_of_int=='d' :
	twosigma_graph.SetTitle('Neyman Construction for d')
	twosigma_graph.GetXaxis().SetTitle('Input |d|')
	twosigma_graph.GetYaxis().SetTitle('Fitted |d|')

#for each of the data points tested
for i in range(n) :
	realvalues=[]
	#build the filepath
	filepath = '../CLOSURE_TESTS'+append
	par_values_filename = 'par_'
	if par_of_int=='AFB' :
		par_values_filename+='Afb'
	else :
		par_values_filename+=par_of_int
	par_values_opp_sign_filename = par_values_filename
	par_values_filename+='='+str(input_values[i]).split('.')[0]+'_'+str(input_values[i]).split('.')[1]+'_fit_values'+append+'.txt'
	par_values_opp_sign_filename+='=-'+str(input_values[i]).split('.')[0]+'_'+str(input_values[i]).split('.')[1]+'_fit_values'+append+'.txt'
	filepath_opp_sign = filepath
	filepath+='/'+par_values_filename
	filepath_opp_sign+='/'+par_values_opp_sign_filename
	print 'Getting '+par_of_int+' values from file at path '+filepath
	#open the fit values file
	par_values_file = open(filepath)
	#put the values in a list
	lines = par_values_file.readlines()
	if par_of_int!='AFB' and input_values[i]!=0.0 :
		print '	Getting additional '+par_of_int+' values from file at path '+filepath_opp_sign
		par_values_opp_sign_file = open(filepath_opp_sign)
		lines+=par_values_opp_sign_file.readlines()
	#read the values into the closure test histogram
	for value in lines :
		realvalue = eval(value)
		if par_of_int != 'AFB' :
			realvalue = abs(realvalue)
		realvalues.append(realvalue)
		closure_test_histo.Fill(input_values[i],realvalue,1./len(lines))
	print '	Got '+str(len(realvalues))+' values'
	#find the mean and std. dev.
	mean = 0
	sqmean = 0
	for value in realvalues :
		mean+=value; sqmean+=value**2
	mean = mean/len(realvalues); sqmean = sqmean/len(realvalues)
	std_dev = sqrt(abs(sqmean-mean**2))
	#Set graphs' point values
	onesigma_graph.SetPoint(i,input_values[i],mean)
	twosigma_graph.SetPoint(i,input_values[i],mean)
	onesigma_graph.SetPointError(i,x_errs[i],x_errs[i],std_dev,std_dev)
	twosigma_graph.SetPointError(i,x_errs[i],x_errs[i],std_dev*2,std_dev*2)

#Interpolate given the central value
data_fit_one_sigma_down = 2*input_values[0]
data_fit_one_sigma_up   = 2*input_values[n-1]
data_fit_two_sigma_down = 2*input_values[0]
data_fit_two_sigma_up   = 2*input_values[n-1]
data_fit_mean = data_fit_central_value
for i in range(n-1) :
	thisx = array('d',[0.0]); thisymean = array('d',[0.0])
	nextx = array('d',[0.0]); nextymean = array('d',[0.0])
	onesigma_graph.GetPoint(i,thisx,thisymean); onesigma_graph.GetPoint(i+1,nextx,nextymean)
	thisyhi  = thisymean[0]+onesigma_graph.GetErrorYhigh(i)
	thisylow = thisymean[0]-onesigma_graph.GetErrorYlow(i)
	nextyhi  = nextymean[0]+onesigma_graph.GetErrorYhigh(i+1)
	nextylow = nextymean[0]-onesigma_graph.GetErrorYlow(i+1)
	if thisyhi <= data_fit_central_value and nextyhi > data_fit_central_value and data_fit_one_sigma_down == 2*input_values[0] :
		slope = (nextyhi-thisyhi)/(input_values[i+1]-input_values[i])
		data_fit_one_sigma_down = (data_fit_central_value-thisyhi)/slope+input_values[i]
	if thisylow <= data_fit_central_value and nextylow > data_fit_central_value :
		slope = (nextylow-thisylow)/(input_values[i+1]-input_values[i])
		data_fit_one_sigma_up = (data_fit_central_value-thisylow)/slope+input_values[i]
	if thisymean[0] <= data_fit_central_value and nextymean[0] > data_fit_central_value :
		slope = (nextymean[0]-thisymean[0])/(input_values[i+1]-input_values[i])
		data_fit_mean = (data_fit_central_value-thisymean[0])/slope+input_values[i]
for i in range(n-1) :
	thisx = array('d',[0.0]); thisymean = array('d',[0.0])
	nextx = array('d',[0.0]); nextymean = array('d',[0.0])
	twosigma_graph.GetPoint(i,thisx,thisymean); twosigma_graph.GetPoint(i+1,nextx,nextymean)
	thisyhi  = thisymean[0]+twosigma_graph.GetErrorYhigh(i)
	thisylow = thisymean[0]-twosigma_graph.GetErrorYlow(i)
	nextyhi  = nextymean[0]+twosigma_graph.GetErrorYhigh(i+1)
	nextylow = nextymean[0]-twosigma_graph.GetErrorYlow(i+1)
	if thisyhi <= data_fit_central_value and nextyhi > data_fit_central_value and data_fit_one_sigma_down == 2*input_values[0] :
		slope = (nextyhi-thisyhi)/(input_values[i+1]-input_values[i])
		data_fit_two_sigma_down = (data_fit_central_value-thisyhi)/slope+input_values[i]
	if thisylow <= data_fit_central_value and nextylow > data_fit_central_value :
		slope = (nextylow-thisylow)/(input_values[i+1]-input_values[i])
		data_fit_two_sigma_up = (data_fit_central_value-thisylow)/slope+input_values[i]

print 'Central value = %.5f, plus one sigma = %.5f, minus one sigma = %.5f'%(data_fit_mean,data_fit_one_sigma_up,data_fit_one_sigma_down)
print '	plus two sigma = %.5f, minus two sigma = %.5f'%(data_fit_two_sigma_up,data_fit_two_sigma_down)
print 'FINAL RESULT: Parameter %s = %.5f + %.5f - %.5f (95%% CL = %.5f)'%(par_of_int,data_fit_mean,data_fit_one_sigma_up-data_fit_mean,abs(data_fit_one_sigma_down-data_fit_mean),data_fit_two_sigma_up)

#Build the lines to indicate based on the data fit value
lines = []
x_low = twosigma_graph.GetXaxis().GetBinLowEdge(twosigma_graph.GetXaxis().GetFirst())
x_high = twosigma_graph.GetXaxis().GetBinUpEdge(twosigma_graph.GetXaxis().GetLast())
y_low = twosigma_graph.GetYaxis().GetBinLowEdge(twosigma_graph.GetYaxis().GetFirst())
lines.append(TLine(x_low,data_fit_central_value,data_fit_one_sigma_up,data_fit_central_value))
lines.append(TLine(data_fit_one_sigma_down,data_fit_central_value,data_fit_one_sigma_down,y_low))
lines.append(TLine(data_fit_one_sigma_up,data_fit_central_value,data_fit_one_sigma_up,y_low))
lines.append(TLine(data_fit_mean,data_fit_central_value,data_fit_mean,y_low))
for line in lines :
	line.SetLineWidth(3); line.SetLineColor(kRed); line.SetLineStyle(2)

#Build a legend
leg = TLegend(0.62,0.67,0.9,0.9)
leg.AddEntry(onesigma_graph,'Mean values','PL')
leg.AddEntry(onesigma_graph,'#pm 1 #sigma','F')
leg.AddEntry(twosigma_graph,'#pm 2 #sigma','F')
leg.AddEntry(lines[0],'data fit','L')

#The line to go on the closure test plots
otherline = TLine(input_values[0],input_values[0],input_values[n-1],input_values[n-1])
otherline.SetLineColor(kBlack)
otherline.SetLineWidth(4)

#Plot the neyman construction histogram
neyman_canv = TCanvas('neyman_canv','neyman_canv',900,900)
neyman_canv.cd()
twosigma_graph.Draw('A E3')
onesigma_graph.Draw('SAME E3')
onesigma_graph.Draw('SAME PLX')
for line in lines :
	line.Draw()
leg.Draw()

#plot the closure test histogram
closure_test_canv = TCanvas('closure_test_canv','closure_test_canv',900,900)
closure_test_canv.cd()
closure_test_histo.Draw('COL')
otherline.Draw()

neyman_canv.Write()
closure_test_canv.Write()
outfile.Close()
