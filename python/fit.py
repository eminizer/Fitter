from ROOT import TFile
import multiprocessing
from datetime import date
from array import array
import copy
import os, glob

#Fit Class

class Fit(object) :

	def __init__(self,topologies,leptypes,parameter,postsys,noss,norateparams,nocontrolregions,sumcharges,fnparts,toyAfb,toymu,toyd,toySeed,vb,ppo) :
		self._topologies=topologies
		self._ltypes=leptypes
		self._fitpar=parameter
		toyparsdict={'Afb':toyAfb,'mu':toymu,'d':toyd}
		self._toypar=toyparsdict[self._fitpar]
		self._toyAfb=toyAfb
		self._toySeed=toySeed
		self._postsys=postsys
		self._noss=noss
		self._noRateParams=norateparams
		self._nocontrolregions=nocontrolregions
		self._sumcharges=sumcharges
		self._name = self._fitpar
		for topology in self._topologies :
			self._name+='_'+topology
		for ltype in self._ltypes :
			self._name+='_'+ltype
		print 'initializing fit with name '+self._name
		self._verbose = vb
		self._post_plots_only = ppo

	########		PUBLIC FUNCTIONS 			########

	def buildDatacards(self,templatefilepath) :
		print 'Building data cards for fit %s'%(self._name)
		dc_tuples = [] #list of datacard tuples with (datacard_filename,bin_prepend)
		for topology in self._topologies :
			#build the signal region datacards
			for ltype in self._ltypes :
				dc_tuples.append(self._buildDatacard_('SR',topology,ltype,templatefilepath))
			#build the W+Jets CR datacards if necessary
			if topology!='t3' and not self._nocontrolregions :
				for ltype in self._ltypes :
					dc_tuples.append(self._buildDatacard_('WJets_CR',topology,ltype,templatefilepath))
		#combine the datacards
		print 'Combining cards for fit %s'%(self._name)
		cmd = 'combineCards.py '
		for i in range(len(dc_tuples)) :
			cmd+='%s=%s '%(dc_tuples[i][1],dc_tuples[i][0])
		self._total_datacard_filename = self._name+'_total_datacard.txt'
		cmd+='> %s'%(self._total_datacard_filename)
		print cmd
		os.system(cmd)
		#delete the individual channel cards (housekeeping)
		#for i in range(len(dc_tuples)) : #DEBUG
		#	os.system('rm -f %s'%(dc_tuples[i][0])) #DEBUG
		print 'Done.'
		#if desired, add in the rateParams at the end of the card
		if not self._noRateParams :
			self._addRateParamsToTotalCard_(templatefilepath)

	def refinePhysicsModel(self,tfilepath) :
		print 'Building physics model for fit %s'%(self._name)
		#first build the filename for the new custom model
		fn = self._name+'_PhysicsModel.py'
		#make the dictionary of variables to replace in the template file, and the list of function lines to write into it
		rep_data = {'fitname':self._name}
		flines = []
		#if this is a mu or d fit we need some renormalization factors
		if not self._fitpar=='Afb' :
			nq1={}; nq2={}; nqq={}; ng1={}; ng2={}; ng3={}; ng4={}; ngg={}
			#make the list of channel names for which to pull template yields
			channames = []
			for topology in self._topologies :
				for ltype in self._ltypes :
					if self._sumcharges :
						channames.append(topology+'_'+ltype)
					else :
						channames.append(topology+'_'+ltype+'plus')
						channames.append(topology+'_'+ltype+'minus')
			#get the process yields in each channel
			temp_file = TFile.Open(tfilepath)
			for cname in channames :
				nq1[cname]=0.; nq2[cname]=0.; nqq[cname]=0.; ng1[cname]=0.; ng2[cname]=0.; ng3[cname]=0.; ng4[cname]=0.; ngg[cname]=0.
				#for qqbar
				nqq[cname]+=temp_file.Get(cname+'_SR__fq0').Integral()
				nq1[cname]+=temp_file.Get(cname+'_SR__fq1').Integral()
				nq2[cname]+=temp_file.Get(cname+'_SR__fq2').Integral()
				#for gg
				ngg[cname]+=temp_file.Get(cname+'_SR__fg0').Integral()
				ng1[cname]+=temp_file.Get(cname+'_SR__fg1').Integral()
				ng2[cname]+=temp_file.Get(cname+'_SR__fg2').Integral()
				ng3[cname]+=temp_file.Get(cname+'_SR__fg3').Integral()
				ng4[cname]+=temp_file.Get(cname+'_SR__fg4').Integral()
			temp_file.Close()
			#make the list of function lines to add to the template physicsModel file
			for cname in channames :
				#for d fits
				if self._fitpar=='d' :
					#for qqbar
					FQQ='(1.-@0*@0*((%f)/(%f))+@0*@0*((%f)/(%f)))'%(nq1[cname],nqq[cname],nq2[cname],nqq[cname])
					flines.append('self.modelBuilder.factory_(\'expr::%s_fqd0("((1.)/(%s))",d)\')'%(cname,FQQ))
					flines.append('self.modelBuilder.factory_(\'expr::%s_fqd1("((-1.*@0*@0)/(%s))",d)\')'%(cname,FQQ))
					flines.append('self.modelBuilder.factory_(\'expr::%s_fqd2("((@0*@0)/(%s))",d)\')'%(cname,FQQ))
					#flines.append('self.modelBuilder.factory_(\'expr::%s_fqd0("1.+@0-@0",d)\')'%(cname))
					#flines.append('self.modelBuilder.factory_(\'expr::%s_fqd1("1.+@0-@0",d)\')'%(cname))
					#flines.append('self.modelBuilder.factory_(\'expr::%s_fqd2("1.+@0-@0",d)\')'%(cname))
					#for gg
					FGG='(1.+@0*@0*((%f)/(%f))+@0*@0*((%f)/(%f))+@0*@0*@0*@0*((%f)/(%f)))'%(ng2[cname],ngg[cname],ng3[cname],ngg[cname],ng4[cname],ngg[cname])
					flines.append('self.modelBuilder.factory_(\'expr::%s_fgd0("((1.)/(%s))",d)\')'%(cname,FGG))
					flines.append('self.modelBuilder.factory_(\'expr::%s_fgd2("((@0*@0)/(%s))",d)\')'%(cname,FGG))
					flines.append('self.modelBuilder.factory_(\'expr::%s_fgd3("((@0*@0)/(%s))",d)\')'%(cname,FGG))
					flines.append('self.modelBuilder.factory_(\'expr::%s_fgd4("((@0*@0*@0*@0)/(%s))",d)\')'%(cname,FGG))
				elif self._fitpar=='mu' :
					#for qqbar
					FQQ='(1.+(2.*@0+@0*@0)*((%f)/(%f))+(@0*@0)*((%f)/(%f)))'%(nq1[cname],nqq[cname],nq2[cname],nqq[cname])
					flines.append('self.modelBuilder.factory_(\'expr::%s_fqmu0("((1.)/(%s))",mu)\')'%(cname,FQQ))
					flines.append('self.modelBuilder.factory_(\'expr::%s_fqmu1("((2*@0+@0*@0)/(%s))",mu)\')'%(cname,FQQ))
					flines.append('self.modelBuilder.factory_(\'expr::%s_fqmu2("((@0*@0)/(%s))",mu)\')'%(cname,FQQ))
					#for gg
					FGG='(1.+@0*(1.+@0)*((%f)/(%f))+@0*@0*(1.+@0)*((%f)/(%f))+@0*@0*(1.-5.*@0)*((%f)/(%f))+@0*@0*@0*@0*((%f)/(%f)))'%(ng1[cname],ngg[cname],ng2[cname],ngg[cname],ng3[cname],ngg[cname],ng4[cname],ngg[cname])
					flines.append('self.modelBuilder.factory_(\'expr::%s_fgmu0("((1.)/(%s))",mu)\')'%(cname,FGG))
					flines.append('self.modelBuilder.factory_(\'expr::%s_fgmu1("((@0+@0*@0)/(%s))",mu)\')'%(cname,FGG))
					flines.append('self.modelBuilder.factory_(\'expr::%s_fgmu2("((@0*@0+@0*@0*@0)/(%s))",mu)\')'%(cname,FGG))
					flines.append('self.modelBuilder.factory_(\'expr::%s_fgmu3("((@0*@0-5.*@0*@0*@0)/(%s))",mu)\')'%(cname,FGG))
					flines.append('self.modelBuilder.factory_(\'expr::%s_fgmu4("((@0*@0*@0*@0)/(%s))",mu)\')'%(cname,FGG))
				else :
					print 'ERROR: fitpar %s not recognized, cannot find template physicsModel file!'
					return
		#open the new file to write into
		newfile = open(fn,'w')
		#open the template file to use
		template_file = open(os.environ['CMSSW_BASE']+'/src/Analysis/Fitter/python/'+self._fitpar+'_PhysicsModel_template.txt','r')
		#for each line in the template file
		for line in template_file.readlines() :
			#if it's not the line that indicates where the function lines go just sub in and write it out
			if line.find('###FUNCTIONS BELOW')==-1 :
				newfile.write(line%rep_data)
			#if it is that line, though, write all of the function lines instead
			else :
				for fline in flines :
					newfile.write('        %s\n'%fline)
		#close the files
		template_file.close(); newfile.close()
		#set this fit's model filename
		self._physics_model_filename = fn
		print 'Done.'

	def createWorkspace(self) :
		print 'Creating workspace for fit %s'%(self._name)
		#set the name for the workspace
		self._workspace_filename = self._name+'_workspace.root'
		#append this directory to the pythonpath so it can find the physicsmodel module
		orig_pythonpath = os.environ['PYTHONPATH']
		os.environ['PYTHONPATH']=orig_pythonpath+':'+os.getcwd()
		#run text2workspace.py
		cmd = 'text2workspace.py '+self._total_datacard_filename
		cmd+=' --X-no-optimize-bins'
		#add option to multiply the top pt reweighting uncertainty by five
		#cmd+=" --X-rescale-nuisance 'top_pt_re_weight' 5.0 "
		cmd+=' --PO verbose'
		if self._verbose :
			cmd+=' --verbose 5'
		cmd+=' -o '+self._workspace_filename
		cmd+=' -P '+self._physics_model_filename.split('.')[0]+':'+self._physics_model_filename.split('.')[0]
		print cmd
		os.system(cmd)
		#reset the pythonpath
		os.environ['PYTHONPATH']=orig_pythonpath
		print 'Done'

	def runCombine(self,mode,ntoys,nthreads,savetoys,tfilepath,toysfilename) :
		print 'Running Combine for fit %s'%(self._name)
		if mode=='data' : 
			#run a single fit to the observed data
			fit_diagnostics_filename = self._runSingleDataFit_()
			if not self._post_plots_only :
				self._makeNuisanceImpactPlots_()
			self._makePostfitCompPlots_(fit_diagnostics_filename,tfilepath)
		elif mode=='toyGroup' : 
			if self._post_plots_only :
				print 'ERROR: run with --postfit_plots_only but this is a toyGroup where no postfit plots are made... try again with different options'
				return
			#run a group of toys and produce a fit with all the bestfit parameter values for use in the Neyman construction
			self._runToyGroup_(ntoys,nthreads,savetoys)
		elif mode=='singleToy' : 
			fit_diagnostics_filename = self._runSingleToyFit_(savetoys,toysfilename)
			self._makePostfitCompPlots_(fit_diagnostics_filename,tfilepath)
		elif mode=='genSingleToy' :
			#generate one toy with all the current settings and quit
			self._generateSingleToy_()

	########		GETTERS/SETTERS 			########

	def getName(self) :
		return self._name

	########		INTERNAL FUNCTIONS 			########

	def _buildDatacard_(self,region,topology,leptype,tfilepath) :
		#first build the filename and channel prepend for the new datacard
		fn = self._name+'_'+topology+'_'+region+'_'+leptype+'_datacard.txt'
		pp = topology #general prepend
		if self._sumcharges : #if charges are summed then each card has only one channel, so name them topology_leptype
			pp+='_'+leptype
		#figure out which template datacard to open
		template_filename = os.environ['CMSSW_BASE']+'/src/Analysis/Fitter/python/'
		template_filename+=self._fitpar+'_'
		if self._sumcharges :
			template_filename+='sum'
		else :
			template_filename+='sep'
		template_filename+='_datacard_template.txt'
		#make the dictionary of variables to replace in the template file
		signalsysID='' if self._postsys=='nominal' else '__'+self._postsys
		backgroundsysID='__'+self._postsys if (self._postsys.startswith('JES') or self._postsys.startswith('JER')) else ''
		rqcdvals = {'t1_muplus_SR':0.166,
					't1_muminus_SR':-0.283,
					't1_elplus_SR':0.082,
					't1_elminus_SR':0.452,
					't1_muplus_WJets_CR':0.629,
					't1_muminus_WJets_CR':0.704,
					't1_elplus_WJets_CR':0.704,
					't1_elminus_WJets_CR':0.704,
					't2_muplus_SR':-0.180,
					't2_muminus_SR':0.192,
					't2_elplus_SR':0.192,
					't2_elminus_SR':0.021,
					't2_muplus_WJets_CR':-0.704,
					't2_muminus_WJets_CR':-0.301,
					't2_elplus_WJets_CR':0.198,
					't2_elminus_WJets_CR':0.208,
					't3_muplus_SR':-0.025,
					't3_muminus_SR':-0.039,
					't3_elplus_SR':-0.411,
					't3_elminus_SR':-0.471,
					}
		rqcderrs = {'t1_muplus_SR':0.555,
					't1_muminus_SR':0.387,
					't1_elplus_SR':0.3,
					't1_elminus_SR':0.3,
					't1_muplus_WJets_CR':0.3,
					't1_muminus_WJets_CR':0.3,
					't1_elplus_WJets_CR':0.3,
					't1_elminus_WJets_CR':0.3,
					't2_muplus_SR':0.3,
					't2_muminus_SR':0.3,
					't2_elplus_SR':0.3,
					't2_elminus_SR':0.3,
					't2_muplus_WJets_CR':0.3,
					't2_muminus_WJets_CR':0.3,
					't2_elplus_WJets_CR':0.3,
					't2_elminus_WJets_CR':0.3,
					't3_muplus_SR':0.3,
					't3_muminus_SR':0.3,
					't3_elplus_SR':0.3,
					't3_elminus_SR':0.3,
					}
		rep_data = {'fitname':self._name,
					'lt':leptype,
					'r':region,
					#'templatefilename':tfilepath,
					'templatefilename':tfilepath.rstrip('.root')+'_aux.root' if region=='WJets_CR' else tfilepath,
					'topology':topology,
					'tr':'b' if topology in ['t1','t2'] else 'r',
					'signalsysID':signalsysID,
					'backgroundsysID':backgroundsysID,
					'crapp':'_z' if region=='WJets_CR' else '',
					'rwjetsval':-0.1689,
					'rwjetserr':0.1,
					'rqcdplusval':rqcdvals[topology+'_'+leptype+'plus_'+region],
					'rqcdpluserr':rqcderrs[topology+'_'+leptype+'plus_'+region],
					'rqcdminusval':rqcdvals[topology+'_'+leptype+'minus_'+region],
					'rqcdminuserr':rqcderrs[topology+'_'+leptype+'minus_'+region],
					}
		#open the new file to write into
		newfile = open(fn,'w')
		#open the template file to use
		template_file = open(template_filename,'r')
		#for each line in the template file
		#print '---------------------------------------------' #DEBUG
		for line in template_file.readlines() :
			#print line #DEBUG
			#exclude/skip a couple lines specifically (namely top tagging efficiency if there are no top tags)
			sys_to_skip = ['ttag_eff_weight_merged','ttag_eff_weight_semimerged','ttag_eff_weight_notmerged'] if topology!='t1' else []
			#if we're running without systematics
			if self._noss :
				sys_to_skip += ['pileup_weight',
								rep_data['lt']+'_trig_eff_weight_'+rep_data['tr'],
								rep_data['lt']+'_ID_weight',
								rep_data['lt']+'_iso_weight',
								'btag_eff_weight_flavb_'+rep_data['tr'],
								'btag_eff_weight_flavc_'+rep_data['tr'],
								'btag_eff_weight_light_'+rep_data['tr'],
								'ttag_eff_weight_merged',
								'ttag_eff_weight_semimerged',
								'ttag_eff_weight_notmerged',
								'ren_scale_weight',
								'fact_scale_weight',
								'comb_scale_weight',
								'pdfas_weight',
								'B_frag_weight',
								'B_br_weight',
								'top_pt_re_weight',
								]
			#add the systematics to skip
			#sys_to_skip.append('B_br_weight')
			#sys_to_skip.append('btag_eff_weight_light_r')
			#sys_to_skip.append('el_ID_weight')
			#sys_to_skip.append('top_pt_re_weight')
			#sys_to_skip.append('pdfas_weight')
			#print 'line split = %s'%(line.split()) #DEBUG
			if line.split()[0]%rep_data in sys_to_skip :
				continue
			#if we're running with rateParams
			if self._noRateParams and len(line.split())>1 and (line.split()[1].find('rateParam')!=-1 or line.split()[1].find('param')!=-1) :
				continue
			#boosted topologies and resolved electrons don't have lepton isolation uncertainty
			if topology in ['t1','t2'] or (topology=='t3' and leptype=='el') :
				if line.split()[0]%rep_data==rep_data['lt']+'_iso_weight' :
					continue
			#otherwise write the substituted line
			#if line.startswith('process') : #DEBUG
			#	print 'old: %s \nnew: %s \n------------------------------------'%(line, line%rep_data) #DEBUG
			newfile.write(line%rep_data)
		#close the files
		template_file.close(); newfile.close()
		#return the tuple of (filename,channel_prepend)
		return (fn,pp)

	def _addRateParamsToTotalCard_(self,tfilepath) :
		outfile = open(self._total_datacard_filename,'a')
		outfile.write('# Rateparams for individual processes\n')
		#fwjets/fbck scaled agnostic of channel
		outfile.write('fwjets_scale rateParam * fwjets (1.+@0) Rwjets\n')
		#outfile.write('fbck_scale rateParam * fbck (1.+@0) Rbck\n')
		#build list of channel identifiers for fqcd/fqp/fqm/fgg rateParams which need individual scales (fqcd) or normalizations (others)
		cids=[]
		for t in self._topologies :
			regions = ['SR']
			if t!='t3' and not self._nocontrolregions :
				regions.append('WJets_CR')
			for l in self._ltypes :
				for r in regions :
					if self._sumcharges :
						cids.append(t+'_'+l+'_'+r)
					else :
						cids.append(t+'_'+l+'plus_'+r)
						cids.append(t+'_'+l+'minus_'+r)
		#print 'cids = %s'%(cids) #DEBUG
		#make the lists of all the other rateParam lines by channel
		temp_file = TFile.Open(tfilepath)
		for cid in cids :
			rate_params_lines = []
			rate_params_lines.append('fqcd_scale_'+cid+' rateParam '+cid+' fqcd (1.+@0) Rqcd_'+cid+'')
			#rate_params_lines.append('fqp_scale_'+cid+' rateParam '+cid+' fqp0 (1.+@0)*((%(NTOT_'+cid+')s-(1.+@1)*%(NWJETS_'+cid+')s-(1.+@2)*%(NBCK_'+cid+')s)/(%(NTT_'+cid+')s)) Rqqbar,Rwjets,Rbck')
			#rate_params_lines.append('fqm_scale_'+cid+' rateParam '+cid+' fqm0 (1.+@0)*((%(NTOT_'+cid+')s-(1.+@1)*%(NWJETS_'+cid+')s-(1.+@2)*%(NBCK_'+cid+')s)/(%(NTT_'+cid+')s)) Rqqbar,Rwjets,Rbck')
			#rate_params_lines.append('fgg_scale_'+cid+' rateParam '+cid+' fg0 ((%(NTT_'+cid+')s-(1.+@0)*%(NQQ_'+cid+')s)/(%(NGG_'+cid+')s))*((%(NTOT_'+cid+')s-(1.+@1)*%(NWJETS_'+cid+')s-(1.+@2)*%(NBCK_'+cid+')s)/(%(NTT_'+cid+')s)) Rqqbar,Rwjets,Rbck')
			rate_params_lines.append('fqp_scale_'+cid+' rateParam '+cid+' fqp* (1.+@0)*((%(NTOT_'+cid+')s-(1.+@1)*%(NWJETS_'+cid+')s-(1.)*%(NBCK_'+cid+')s)/(%(NTT_'+cid+')s)) Rqqbar,Rwjets')
			rate_params_lines.append('fqm_scale_'+cid+' rateParam '+cid+' fqm* (1.+@0)*((%(NTOT_'+cid+')s-(1.+@1)*%(NWJETS_'+cid+')s-(1.)*%(NBCK_'+cid+')s)/(%(NTT_'+cid+')s)) Rqqbar,Rwjets')
			rate_params_lines.append('fgg_scale_'+cid+' rateParam '+cid+' fg* ((%(NTT_'+cid+')s-(1.+@0)*%(NQQ_'+cid+')s)/(%(NGG_'+cid+')s))*((%(NTOT_'+cid+')s-(1.+@1)*%(NWJETS_'+cid+')s-(1.)*%(NBCK_'+cid+')s)/(%(NTT_'+cid+')s)) Rqqbar,Rwjets')
			#make this channel's replacement dictionary
			nwjets=temp_file.Get(cid+'__fwjets').Integral()
			nbck=temp_file.Get(cid+'__fbck').Integral()
			nqq=temp_file.Get(cid+'__fqp0').Integral()+temp_file.Get(cid+'__fqm0').Integral()
			ngg=temp_file.Get(cid+'__fg0').Integral()
			nqcd=temp_file.Get(cid+'__fqcd').Integral()
			rep_data = {'NWJETS_'+cid:nwjets,
						'NBCK_'+cid:nbck,
						'NQCD_'+cid:nqcd,
						'NQQ_'+cid:nqq,
						'NGG_'+cid:ngg,
						'NTT_'+cid:nqq+ngg,
						'NTOT_'+cid:nwjets+nbck+nqq+ngg}
			#print 'cid = %s, rep_data = %s'%(cid, rep_data) #DEBUG
			for line in rate_params_lines :
				#print 'new line: %s \n'%(line%rep_data) #DEBUG
				outfile.write((line%rep_data)+'\n')
		#add the line for autoMCstats
		#outfile.write('* autoMCStats 1. 1')
		temp_file.Close()
		outfile.close()

	def _runSingleDataFit_(self) :
		#start the command to run Combine
		cmd = 'combine -M FitDiagnostics '+self._workspace_filename
		#save shapes with uncertainty
		cmd+=' --saveShapes --saveWithUncertainties'
		#don't fit only to the background because that doesn't make sense for our analysis
		cmd+=' --skipBOnlyFit'
		#make it print out progress, etc.
		cmd+=' --verbose 5' if self._verbose else ' --verbose 0'
		#set the fit name 
		cmd+=' --name Data%s'%(self._fitpar)
		if not self._post_plots_only :
			print cmd
			os.system(cmd)
		#return the filename of the output
		outputfilename = 'fitDiagnosticsData%s.root'%(self._fitpar)
		return outputfilename

	def _runToyGroup_(self,ntoys,nthreads,savetoys) :
		#multithread running the fits
		procs = []
		for i in range(nthreads) :
			#start the command to run Combine
			print 'PARALLEL TOYS: each multiprocessing job will run %d toys (%d total)'%(ntoys/nthreads,nthreads*(ntoys/nthreads))
			cmd = 'combine -M MultiDimFit '+self._workspace_filename
			#fix nuisance parameters
			if self._noss :
				cmd+=' --toysNoSystematics'
			#set observable value for toys
			cmd+=' --setParameters %s=%.3f'%(self._fitpar,self._toypar)
			#set the number of toys
			cmd+=' --toys %d'%(ntoys/nthreads)
			#set the seed for the RNG
			cmd+=' -s '+self._toySeed
			if savetoys : #save the toys
				cmd+=' --saveToys'
			#save the fit results to multidimfitNAME.root
			cmd+=' --saveFitResult'
			#make it print out progress, etc.
			cmd+=' --verbose 5' if self._verbose else ' --verbose 0'
			#set the fit name 
			cmd+=' --name Toys%s%.3f_%d'%(self._fitpar,self._toypar,i)
			p = multiprocessing.Process(target=runFitCommand,args=(cmd,))
			p.start()
			procs.append(p)
		for proc in procs :
			proc.join()
		#aggregate the outputted files
		print 'Aggregating separate results'
		files_to_delete = []
		haddcmd = 'hadd -f higgsCombineToys%s%.3f.MultiDimFit.all.root '%(self._fitpar,self._toypar)
		for i in range(nthreads) :
			fit_result_filename_pattern = 'higgsCombineToys%s%.3f_%d.MultiDimFit.m*.*.root'%(self._fitpar,self._toypar,i)
			fit_result_files = glob.glob(fit_result_filename_pattern)
			if len(fit_result_files)>1 :
				print 'WARNING: more than one file found matching pattern higgsCombineToys%s%.3f_%d.MultiDimFit.m*.*.root'%(self._fitpar,self._toypar,i)
			print '	Adding file from fit with seed %s (Make sure none of these match)'%(fit_result_files[0].split('.')[-2])
			haddcmd+=fit_result_files[0]+' '
			files_to_delete.append(fit_result_files[0])
		os.system(haddcmd)
		for f in files_to_delete :
			os.system('rm -rf %s'%(f))
		#os.system('rm -rf multidimfitToys%s%.3f_*.root'%(self._fitpar,self._toypar))
		#open the output file 
		fit_result_file = TFile.Open('higgsCombineToys%s%.3f.MultiDimFit.all.root'%(self._fitpar,self._toypar))
		#get back the parameter values from the toys
		limit_tree = fit_result_file.Get('limit')
		parloc = array('f',[0.])
		limit_tree.SetBranchAddress(self._fitpar,parloc)
		parvals = []
		for ientry in range(limit_tree.GetEntries()) :
			limit_tree.GetEntry(ientry)
			parvals.append(parloc[0])
		#sort the list and grab the 1- and 2-sigma confidence intervals
		parvals.sort()
		print 'Sorted list of all bestfit POI values (%d total): '%(len(parvals))
		print parvals
		minustwo = parvals[int(round(len(parvals)*(1-0.955)/2.))]
		minusone = parvals[int(round(len(parvals)*(1-0.683)/2.))]
		median 	 = parvals[int(round(len(parvals)*(1.)/2.))]
		plusone  = parvals[int(round(len(parvals)*(1.+0.683)/2.))]
		plustwo  = parvals[min(len(parvals)-1,int(round(len(parvals)*(1.+0.955)/2.)))]
		#print them out : )
		print '-----------------------------------------------------'
		print 'FINAL PARAMETER VALUE INTERVALS:'
		print '%.4f || %.4f | %.4f | %.4f || %.4f'%(minustwo,minusone,median,plusone,plustwo)
		print '-----------------------------------------------------'
		fit_result_file.Close()

	def _runSingleToyFit_(self,savetoys,toysfilename) :
		#start the command to run Combine
		cmd = 'combine -M FitDiagnostics '+self._workspace_filename
		#pull toys from file if desired
		if toysfilename!='' :
			cmd+=' --toysFile=%s'%(toysfilename)
		#fix nuisance parameters
		if self._noss :
			cmd+=' --toysNoSystematics'
		#set observable value for toys
		cmd+=' --setParameters %s=%.3f'%(self._fitpar,self._toypar)
		#run on only one toy
		cmd+=' --toys 1'
		#set the seed for the RNG
		cmd+=' -s '+self._toySeed
		if savetoys : #save the toys
			cmd+=' --saveToys'
		#save shapes with uncertainty
		cmd+=' --saveShapes --saveWithUncertainties'
		#don't fit only to the background because that doesn't make sense for our analysis
		cmd+=' --skipBOnlyFit'
		#use the custom starting point for the POI
		cmd+=' --customStartingPoint'
		#make it print out progress, etc.
		cmd+=' --verbose 5' if self._verbose else ' --verbose 0'
		#set the fit name 
		cmd+=' --name Toys%s%.3f'%(self._fitpar,self._toypar)
		if not self._post_plots_only :
			print cmd
			os.system(cmd)
			#run the nuisance impacts plots
			print 'Plotting nuisance impacts for fit %s'%(self._name)
			#make the first command to run the initial fit through combineTool.py
			cmd = 'combineTool.py -M Impacts -d %s -t -1 --setParameters %s=%.3f -m 125 --doInitialFit  --robustFit 1'%(self._workspace_filename,self._fitpar,self._toypar)
			print cmd
			os.system(cmd)
			#make the second command to do scans for each nuisance parameter
			cmd = 'combineTool.py -M Impacts -d %s -t -1 --setParameters %s=%.3f --robustFit 1 -m 125 --doFits --parallel %d'%(self._workspace_filename,self._fitpar,self._toypar,4)
			print cmd
			os.system(cmd)
			#make the third command to collect the results and put them in a json file
			cmd = 'combineTool.py -M Impacts -d %s -t -1 --setParameters %s=%.3f -m 125 -o impacts_%s.json'%(self._workspace_filename,self._fitpar,self._toypar,self._name)
			print cmd
			os.system(cmd)
			#make the final command to plot the impacts
			cmd = 'plotImpacts.py -i impacts_%s.json -o impacts_%s'%(self._name,self._name)
			print cmd
			os.system(cmd)
		#return the filename of the output
		outputfilename = 'fitDiagnosticsToys%s%.3f.root'%(self._fitpar,self._toypar)
		return outputfilename

	def _generateSingleToy_(self) :
		#start the command to run combine
		cmd = 'combine -M GenerateOnly '+self._workspace_filename
		#fix nuisance parameters
		if self._noss :
			cmd+=' --toysNoSystematics'
		#set observable value for toys
		cmd+=' --setParameters %s=%.3f'%(self._fitpar,self._toypar)
		#run on only one toy
		cmd+=' --toys 1'
		#set the seed for the RNG
		cmd+=' -s '+self._toySeed
		#save the toy
		cmd+=' --saveToys'
		#make it print out progress, etc.
		cmd+=' --verbose 5' if self._verbose else ' --verbose 0'
		#set the fit name 
		cmd+=' --name GeneratedToy%s%.3f'%(self._fitpar,self._toypar)
		print cmd
		os.system(cmd)
		toyfilename=glob.glob('higgsCombineGeneratedToy%s%.3f.GenerateOnly.mH120.*.root'%(self._fitpar,self._toypar))
		if len(toyfilename)>1 :
			print 'WARNING: more than one toy file with these settings has been generated in this directory! Only one will be printed!'
		print 'single generated toy will be in file '+toyfilename[0]


	def _makeNuisanceImpactPlots_(self) :
		print 'Plotting nuisance impacts for fit %s'%(self._name)
		#make the first command to run the initial fit through combineTool.py
		cmd = 'combineTool.py -M Impacts -d %s -m 125 --doInitialFit'%(self._workspace_filename)
		print cmd
		os.system(cmd)
		#make the second command to do scans for each nuisance parameter
		cmd = 'combineTool.py -M Impacts -d %s -m 125 --doFits --parallel %d'%(self._workspace_filename,4)
		print cmd
		os.system(cmd)
		#make the third command to collect the results and put them in a json file
		cmd = 'combineTool.py -M Impacts -d %s -m 125 -o impacts_%s.json'%(self._workspace_filename,self._name)
		print cmd
		os.system(cmd)
		#make the final command to plot the impacts
		cmd = 'plotImpacts.py -i impacts_%s.json -o impacts_%s'%(self._name,self._name)
		print cmd
		os.system(cmd)

	def _makePostfitCompPlots_(self,fdfn,tfp) :
		print 'Making postfit comparison plots with input filename=%s'%(fdfn)
		#run the script that makes the postfit comparison plots
		cmd = 'python /uscms_data/d3/eminizer/ttbar_13TeV/CMSSW_8_1_0/src/Analysis/TemplateMaker/python/make_mc_data_comp_plots.py '
		#in postfit mode
		cmd+='-M postfit '
		#add the template filename
		cmd+='--tfilename %s '%(tfp)
		#add the combine FitDiagnostics output filename
		cmd+='--cfilename %s '%(os.path.join(os.getcwd(),fdfn))
		#set the name for the file with the plots
		cmd+='--outfilename %s_postfit_comparison_plots.root'%(self._name)
		print cmd
		os.system(cmd)

def runFitCommand(cmd) :
	print cmd 
	os.system(cmd)
