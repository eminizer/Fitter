from ROOT import *
from array import array
import CMS_lumi, tdrstyle

onesided=True

gROOT.SetBatch()
#Set some TDR options
tdrstyle.setTDRStyle()
iPeriod = 4 #13TeV iPeriod = 1*(0/1 7 TeV) + 2*(0/1 8 TeV)  + 4*(0/1 13 TeV)
#CMS_lumi.writeExtraText = 1
CMS_lumi.writeExtraText = False
CMS_lumi.extraText = "Preliminary"

#name of the file holding the results of the "grid" run
input_filename = 'higgsCombineTest.MultiDimFit.mH120.root'
#name of the parameter in the tree whose values we're plotting against
parname = 'd'; parname_formatted = '#hat{d}_{t}'
#name of the deltaNLL branch in the tree
dnllname = 'deltaNLL'
#deltaNLL values  defining intervals
interval_points = {'68% CL':{'dnll_val':1.0,'par_vals':[],'linecolor':kBlue,'linestyle':2},
					'95% CL':{'dnll_val':3.84,'par_vals':[],'linecolor':kRed,'linestyle':1}
					}

#name of output file
output_filename = 'likelihood_profile.root'

#list of (par,deltaNLL) values to put in the graph
points = []

#open the input file
ifp = TFile.Open(input_filename)
#add the values to the list of points
limit_tree = ifp.Get('limit')
n_points = limit_tree.GetEntries()
par_arr = array('f',[0.]); limit_tree.SetBranchAddress(parname,par_arr)
dnll_arr = array('f',[0.]); limit_tree.SetBranchAddress(dnllname,dnll_arr)
for i in range(n_points) :
	limit_tree.GetEntry(i)
	if onesided and par_arr[0]<0 :
		continue
#	print 'appending par value %.8f'%(par_arr[0]) #DEBUG
	points.append((par_arr[0],dnll_arr[0]))
#sort the list from smallest to largest PoI value
points.sort(key=lambda x:x[0])
#print 'points = %s'%(points) #DEBUG
#find the intersection points by looping over the points in the graph
interval_d_values = []
for i in range(len(points)-1) :
	#get the info at this point
	thisdnll = points[i][1]; nextdnll = points[i+1][1]
	thisparval = points[i][0]; nextparval = points[i+1][0]
	#for each of the interval types
	for interval_type,interval in interval_points.iteritems() :
		#check if the curve is switching to above/below the value
		checkdnll = interval['dnll_val']
		if (thisdnll>checkdnll and nextdnll<checkdnll) or (thisdnll<checkdnll and nextdnll>checkdnll) :
			#interpolate the parameter value that intersects with the dnll value
			slope = (nextdnll-thisdnll)/(nextparval-thisparval)
			parval_at_int = ((checkdnll-thisdnll)/slope)+thisparval
			interval['par_vals'].append(parval_at_int)
			print 'interval %s %s value = %.8f'%(interval_type,parname,parval_at_int)
#close the input file
ifp.Close()

#open the output file
ofp = TFile(output_filename,'recreate')
#make the canvas
canv = TCanvas('dnll_scan','dnll_scan',900,900)
canv.SetTopMargin(0.07)
#make the graph and define attributes
gr = TGraph(len(points),array('f',[p[0] for p in points]),array('f',[p[1] for p in points]))
gr.Draw('ALP')
gr.SetTitle('')
gr.GetYaxis().SetTitle('-2 #Delta log(L)')
gr.GetYaxis().SetRangeUser(0.0,6.2)
if onesided :
	gr.GetXaxis().SetTitle('|%s|'%(parname_formatted))
else :	
	gr.GetXaxis().SetTitle(parname_formatted)
if onesided :
	gr.GetXaxis().SetRangeUser(0.,0.035)
gr.SetLineWidth(3)
#make lines to go on plot
lineparmin = gr.GetHistogram().GetXaxis().GetBinLowEdge(gr.GetHistogram().GetXaxis().GetFirst())
lineparmax = gr.GetHistogram().GetXaxis().GetBinUpEdge(gr.GetHistogram().GetXaxis().GetLast())
#print 'line xmin=%.8f / xmax=%.8f'%(lineparmin,lineparmax) #DEBUG
all_lines = {}
for interval_type,interval in interval_points.iteritems() :
	if not interval_type in all_lines.keys() :
		all_lines[interval_type] = []
	for pval in interval['par_vals'] :
		if onesided :
			all_lines[interval_type].append(TLine(lineparmin,interval['dnll_val'],pval,interval['dnll_val']))
			all_lines[interval_type].append(TLine(pval,0.,pval,interval['dnll_val']))
		else :
			all_lines[interval_type].append(TLine(lineparmin,interval['dnll_val'],lineparmax,interval['dnll_val']))
			all_lines[interval_type].append(TLine(pval,0.,pval,interval['dnll_val']))
	for l in all_lines[interval_type] :
		l.SetLineColor(interval['linecolor'])
		l.SetLineStyle(interval['linestyle'])
		l.SetLineWidth(3)
		l.Draw('SAME')
#make a legend
leg = TLegend(0.182,0.715,0.754,0.913)
leg.AddEntry(gr,'Likelihood scan','PL')
for interval_type,interval in interval_points.iteritems() :
	if len(all_lines[interval_type])>0 :
		leg.AddEntry(all_lines[interval_type][0],interval_type,'L')
leg.SetBorderSize(0)
leg.Draw('SAME')
#plot the CMS_Lumi lines on the canvas
iPeriod = 4 #13TeV iPeriod = 1*(0/1 7 TeV) + 2*(0/1 8 TeV)  + 4*(0/1 13 TeV)
iPos = 1#1 #iPos = 10*(alignment) + position (1/2/3 = left/center/right)
CMS_lumi.CMS_lumi(canv, iPeriod, iPos)
canv.Update()
#write canvas to file
canv.Write()
#close output file
ofp.Close()