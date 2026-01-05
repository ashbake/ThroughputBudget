# uses cThroughput to load throughput of various paths and plot

import matplotlib.pylab as plt
import numpy as np
import pandas as pd
import csv, os
from scipy.interpolate import interp1d
from matplotlib.ticker import MultipleLocator

from cThroughput import CalcThroughput

import matplotlib
font = {'size'   : 14}
matplotlib.rc('font', **font)

data_path   = './inputs/'
save_path    = './outputs/'
excel_file = '../HISPEC_allsubs.xlsx'
#excel_file   = './HISPEC_gary_version.xlsx'

# Define yJHK band passes for plotting
x = np.arange(800, 2550, 0.05)
yJ = [980,1327]
HK = [1490,2460]

ct = CalcThroughput(x, '../HISPEC_allsubs.xlsx',data_path='./inputs/')

if __name__=='__main__':	
	#'TELESCOPE', 'AO', 'FEI  COMMON', 'FEI ATC', 'FEI BLUE', 'FEI RED', 'COUPLING', 'FIBER TRANSMISSION BLUE', 'FIBER TRANSMISSION RED', 'BSPEC ', 'RSPEC '
	configs = {}
	configs['bspec'] = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI BLUE', 'COUPLING NGS', 'FIBER TRANSMISSION BLUE', 'BSPEC']
	configs['rspec'] = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI RED', 'COUPLING NGS', 'FIBER TRANSMISSION RED', 'RSPEC']
	configs['ATC']   = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI ATC']

	# CAL paths -
	configs['FEI_Rinject'] = ['FEI COMMON', 'FEI RED', 'COUPLING PERFECT', 'FIBER TRANSMISSION RED', 'RSPEC']
	configs['FEI_Binject'] = ['FEI COMMON', 'FEI BLUE', 'COUPLING PERFECT', 'FIBER TRANSMISSION BLUE', 'BSPEC']
	configs['AO_Rinject']  = ['AO','FEI COMMON', 'FEI RED', 'COUPLING NGS', 'FIBER TRANSMISSION RED', 'RSPEC']
	configs['AO_Binject']  = ['AO','FEI COMMON', 'FEI BLUE', 'COUPLING NGS', 'FIBER TRANSMISSION BLUE', 'BSPEC']
	# TODO add back injection option

	
	# combine subsystems to get full transmission and plot
	for path in configs.keys(): #['bspec']:
		throughput = ct.run(configs[path],save_path=save_path,label=path)
		ax = ct.plotSubsections(configs[path],save_path=None,label=path)
		ct.plotTotalThroughput(label=path,ax=ax,save_path=save_path)

	# can also plot the components of a subsection like this:
	#ct.plotSubsectionComponents('FEI COMMON')

    # calc throughputs WITHOUT THE BLAZE - need to go to excel sheet and put a 0 under include column for blaze file
    save_path = './outputs/foraidan/'
    gbt = CalcThroughput(x, '../HISPEC_allsubs.xlsx',data_path='./inputs/')
    
    # define sections of instrument to include
    atc_keys = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI BLUE', 
                'COUPLING NGS', 'FIBER TRANSMISSION BLUE', 'BSPEC']
    label    = 'BSPEC_endTOend_NGS'
    throughput = gbt.run(atc_keys,save_path=save_path,label=label)
    gbt.plotTotalThroughput(label=label,save_path=save_path)
    gbt.plotSubsections(keys=atc_keys,label=label + ' Subsections',save_path=save_path)
    gbt.plotSubsectionComponents('BSPEC',save_path=save_path)

    # calc total hispec  rspec
    atc_keys = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI RED', 
                'COUPLING NGS', 'FIBER TRANSMISSION RED', 'RSPEC']
    label    = 'RSPEC_endTOend_NGS'
    throughput = gbt.run(atc_keys,save_path=save_path,label=label)
    gbt.plotTotalThroughput(label=label,save_path=save_path)
    gbt.plotSubsections(keys=atc_keys,label=label + ' Subsections',save_path=save_path)
    gbt.plotSubsectionComponents('RSPEC',save_path=save_path)


	







	