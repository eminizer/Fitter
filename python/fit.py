from ROOT import TFile
import multiprocessing
from datetime import date
from array import array
import copy
import os, glob

#Fit Class

class Fit(object) :

	def __init__(self,topologies,leptypes,parameter,nojec,noss,norateparams,nocontrolregions,sumcharges,fnparts,toyAfb,toymu,toyd) :
		self._topologies=topologies
		self._ltypes=leptypes
		self._fitpar=parameter
		toyparsdict={'Afb':toyAfb,'mu':toymu,'d':toyd}
		self._toypar=toyparsdict[self._fitpar]
		self._nojec=nojec
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
		for i in range(len(dc_tuples)) :
			os.system('rm -f %s'%(dc_tuples[i][0]))
		print 'Done.'
		#if desired, add in the rateParams at the end of the card
		if not self._noRateParams :
			self._addRateParamsToTotalCard_(templatefilepath)

	def refinePhysicsModel(self) :
		print 'Building physics model for fit %s'%(self._name)
		#first build the filename for the new custom model
		fn = self._name+'_PhysicsModel.py'
		#make the dictionary of variables to replace in the template file
		rep_data = {'fitname':self._name,
					}
		#open the new file to write into
		newfile = open(fn,'w')
		#open the template file to use
		template_file = open(os.environ['CMSSW_BASE']+'/src/Analysis/Fitter/python/AFB_PhysicsModel_template.txt','r')
		#for each line in the template file
		for line in template_file.readlines() :
			newfile.write(line%rep_data)
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
		cmd+=' --PO verbose'
		cmd+=' -o '+self._workspace_filename
		cmd+=' -P '+self._physics_model_filename.split('.')[0]+':'+self._physics_model_filename.split('.')[0]
		print cmd
		os.system(cmd)
		#reset the pythonpath
		os.environ['PYTHONPATH']=orig_pythonpath
		print 'Done'

	def runCombine(self,mode,ntoys,nthreads,savetoys,tfilepath) :
		print 'Running Combine for fit %s'%(self._name)
		if mode=='data' : 
			#run a single fit to the observed data
			self._runSingleDataFit_()
		elif mode=='toyGroup' : 
			#run a group of toys and produce a fit with all the bestfit parameter values for use in the Neyman construction
			self._runToyGroup_(ntoys,nthreads,savetoys)
		elif mode=='singleToy' : 
			#run a single toy with the given input value of the POI and make fit comparison plots
			fit_diagnostics_filename = self._runSingleToyFit_(savetoys)
			self._makePostfitCompPlots_(fit_diagnostics_filename,tfilepath)

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
		if topology=='t1' or (topology=='t2' and region=='SR') :
			template_filename+='wo_QCD_'
		elif topology=='t3' or (topology=='t2' and region=='WJets_CR') :
			template_filename+='w_QCD_'
		if self._sumcharges :
			template_filename+='sum'
		else :
			template_filename+='sep'
		template_filename+='_datacard_template.txt'
		#make the dictionary of variables to replace in the template file
		rep_data = {'fitname':self._name,
					'lt':leptype,
					'r':region,
					'templatefilename':tfilepath,
					'topology':topology,
					'tr':'b' if topology in ['t1','t2'] else 'r'}
		#open the new file to write into
		newfile = open(fn,'w')
		#open the template file to use
		template_file = open(template_filename,'r')
		#for each line in the template file
		for line in template_file.readlines() :
			#exclude/skip a couple lines specifically
			sys_to_skip = []
			#if we're running without systematics
			if self._nojec :
				sys_to_skip += ['JES','JER']
			if self._noss :
				sys_to_skip += ['pileup_weight',rep_data['lt']+'_trig_eff_weight_'+rep_data['tr'],rep_data['lt']+'_ID_weight',rep_data['lt']+'_iso_weight','btag_eff_weight','ren_scale_weight','fact_scale_weight','comb_scale_weight','pdfas_weight']
			if line.split()[0]%rep_data in sys_to_skip :
				continue
			#if we're running with rateParams
			if self._noRateParams and line.find('rateParam')!=-1 :
				continue
			#boosted topologies and resolved electrons don't have lepton isolation uncertainty
			if topology in ['t1','t2'] or (topology=='t3' and leptype=='el') :
				if line.split()[0]%rep_data==rep_data['lt']+'_iso_weight' :
					continue
			#otherwise write the substituted line
			newfile.write(line%rep_data)
		#close the files
		template_file.close(); newfile.close()
		#return the tuple of (filename,channel_prepend)
		return (fn,pp)

	def _addRateParamsToTotalCard_(self,tfilepath) :
		outfile = open(self._total_datacard_filename,'a')
		outfile.write('# Rateparams for individual processes\n')
		#make the dictionary of all the rateParam lines by topology
		rate_params_lines = {}
		rate_params_lines['t1']=[]
		rate_params_lines['t1'].append('Rwjets_t1 rateParam t1_* fwjets 1')
		rate_params_lines['t1'].append('Rbck_t1 rateParam t1_* fbck 1')
		rate_params_lines['t1'].append('qq_scale_t1 rateParam t1_* fq* ((%(NTOT)s-@0*%(NWJETS)s-@1*%(NBCK)s)/(%(NTT)s)) Rwjets_t1,Rbck_t1')
		rate_params_lines['t1'].append('Rqqbar_t1 rateParam t1_* fq* 1')
		rate_params_lines['t1'].append('gg_scale_t1 rateParam t1_* fg0 @0*((%(NTT)s-@1*%(NQQ)s)/(%(NGG)s)) qq_scale_t1,Rqqbar_t1')
		rate_params_lines['t2']=[]
		rate_params_lines['t2'].append('Rwjets_t2 rateParam t2_* fwjets 1')
		rate_params_lines['t2'].append('Rbck_t2 rateParam t2_* fbck 1')
		rate_params_lines['t2'].append('Rqqbar_t2 rateParam t2_* fq* 1')
		if not self._nocontrolregions :
			rate_params_lines['t2'].append('Rqcd_t2 rateParam t2_* fqcd 1')
			rate_params_lines['t2'].append('qq_scale_t2 rateParam t2_* fq* ((%(NTOT)s-@0*%(NWJETS)s-@1*%(NBCK)s-@2*%(NQCD)s)/(%(NTT)s)) Rwjets_t2,Rbck_t2,Rqcd_t2')
			rate_params_lines['t2'].append('gg_scale_t2 rateParam t2_* fg0 @0*((%(NTT)s-@1*%(NQQ)s)/(%(NGG)s)) qq_scale_t2,Rqqbar_t2')
		else :
			rate_params_lines['t2'].append('qq_scale_t2 rateParam t2_* fq* ((%(NTOT)s-@0*%(NWJETS)s-@1*%(NBCK)s)/(%(NTT)s)) Rwjets_t2,Rbck_t2')
			rate_params_lines['t2'].append('gg_scale_t2 rateParam t2_* fg0 @0*((%(NTT)s-@1*%(NQQ)s)/(%(NGG)s)) qq_scale_t2,Rqqbar_t2')
		rate_params_lines['t3']=[]
		rate_params_lines['t3'].append('Rwjets_t3 rateParam t3_* fwjets 1')
		rate_params_lines['t3'].append('Rbck_t3 rateParam t3_* fbck 1')
		rate_params_lines['t3'].append('Rqcd_t3 rateParam t3_* fqcd 1')
		rate_params_lines['t3'].append('qq_scale_t3 rateParam t3_* fq* ((%(NTOT)s-@0*%(NWJETS)s-@1*%(NBCK)s-@2*%(NQCD)s)/(%(NTT)s)) Rwjets_t3,Rbck_t3,Rqcd_t3')
		rate_params_lines['t3'].append('Rqqbar_t3 rateParam t3_* fq* 1')
		rate_params_lines['t3'].append('gg_scale_t3 rateParam t3_* fg0 @0*((%(NTT)s-@1*%(NQQ)s)/(%(NGG)s)) qq_scale_t3,Rqqbar_t3')
		for topology in self._topologies :
			#which regions should we sum over?
			regions = ['SR']
			if topology!='t3' and not self._nocontrolregions :
				regions.append('WJets_CR')
			#make this topology's replacement dictionary
			aux_temp_file = TFile.Open(tfilepath.split('.root')[0]+'_aux.root')
			nwjets=0.; nbck=0.; nqq=0.; ngg=0.; nqcd=0.
			for region in regions :
				nwjets+=aux_temp_file.Get(topology+'_'+region+'_NWJETS').GetBinContent(1)
				nbck+=aux_temp_file.Get(topology+'_'+region+'_NBCK').GetBinContent(1)
				nqq+=aux_temp_file.Get(topology+'_'+region+'_NQQBAR').GetBinContent(1)
				ngg+=aux_temp_file.Get(topology+'_'+region+'_NGG').GetBinContent(1)
				if topology=='t3' or (topology=='t2' and region=='WJets_CR') :
					nqcd+=aux_temp_file.Get(topology+'_'+region+'_NQCD').GetBinContent(1)
			aux_temp_file.Close()
			rep_data = {'NWJETS':nwjets,
						'NBCK':nbck,
						'NQCD':nqcd,
						'NQQ':nqq,
						'NGG':ngg,
						'NTT':nqq+ngg,
						'NTOT':nwjets+nbck+nqcd+nqq+ngg}
			for line in rate_params_lines[topology] :
				outfile.write((line%rep_data)+'\n')
		outfile.close()

	def _runSingleDataFit_(self) :
		#still blinded
		print 'ERROR: Not ready to run on data yet; rerun with -M toyGroup/singleToy '

	def _runToyGroup_(self,ntoys,nthreads,savetoys) :
		#multithread running the fits
		procs = []
		for i in range(nthreads) :
			#start the command to run Combine
			print 'PARALLEL TOYS: each multiprocessing job will run %d toys (%d total)'%(ntoys/nthreads,nthreads*(ntoys/nthreads))
			cmd = 'combine -M MultiDimFit '+self._workspace_filename
			if self._noss and self._nojec : #fix nuisance parameters
				cmd+=' --toysNoSystematics'
			#set observable value for toys
			cmd+=' --setParameters %s=%.3f'%(self._fitpar,self._toypar)
			#set the number of toys
			cmd+=' --toys %d'%(ntoys/nthreads)
			#set a random seed for the RNG
			cmd+=' -s -1'
			if savetoys : #save the toys
				cmd+=' --saveToys'
			#save the fit results to multidimfitNAME.root
			cmd+=' --saveFitResult'
			#make it print out progress, etc.
			cmd+=' --verbose 0'
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

	def _runSingleToyFit_(self,savetoys) :
		#start the command to run Combine
		cmd = 'combine -M FitDiagnostics '+self._workspace_filename
		if self._noss and self._nojec : #fix nuisance parameters
			cmd+=' --toysNoSystematics'
		#set observable value for toys
		cmd+=' --setParameters %s=%.3f'%(self._fitpar,self._toypar)
		#run on only one toy
		cmd+=' --toys 1'
		#set a random seed for the RNG
		cmd+=' -s -1'
		if savetoys : #save the toys
			cmd+=' --saveToys'
		#save shapes with uncertainty
		cmd+=' --saveShapes --saveWithUncertainties'
		#make it print out progress, etc.
		cmd+=' --verbose 0'
		#set the fit name 
		cmd+=' --name Toys%s%.3f'%(self._fitpar,self._toypar)
		print cmd
		os.system(cmd)
		#return the filename of the output
		outputfilename = 'fitDiagnosticsToys%s%.3f.root'%(self._fitpar,self._toypar)
		return outputfilename

	def _makePostfitCompPlots_(self,fdfn,tfp) :
		print 'Making postfit comparison plots with input filename=%s'%(fdfn)
		#run the script that makes the postfit comparison plots
		cmd = 'python /uscms_data/d3/eminizer/ttbar_13TeV/CMSSW_8_1_0/src/Analysis/TemplateMaker/python/make_postfit_comp_plots.py '
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
