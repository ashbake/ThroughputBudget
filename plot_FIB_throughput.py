# Loads throughput excel sheet and
# multiplies things out to get the total
# throughput

import matplotlib.pylab as plt
import numpy as np
from scipy import interpolate
from matplotlib.ticker import MultipleLocator

from utils import *

datapath   = './inputs/'
outpath    = './outputs/'

import matplotlib
font = {'size'   : 14}
matplotlib.rc('font', **font)

# Define yJHK band passes for plotting
x = np.arange(800, 2550, 0.05)
yJ = [980,1327]
HK = [1490,2460]
# define jhk

def get_fibred_throughput(length=10):
	"""
	length: new fiber length
	    rspec length is 74 m
	"""
	l0       = 65 #m , original length assumed in file

	x_zblan = [1.49,1.6,1.8,2.5]
	y_zblan = [0.83, 0.87, 0.9, 0.9] # data gary is assuming
	f_zblan = interpolate.interp1d(x_zblan,y_zblan,kind='linear')

	xnew    = np.arange(1.49,2.5,0.001)
	ynew    = f_zblan(xnew) ** (length/l0)
	lengths = np.ones_like(xnew) * length

	np.savetxt(datapath + 'fiber/zblan_throughput_%sm.csv'%length,np.vstack((xnew,ynew,lengths)).T,delimiter=',',header='wavelength_um,throughput')

	return xnew,ynew

def get_fibblue_throughput(length=10):
	"""
	length: new fiber length
	    bspec length is 76m
	"""
	l0          = 65 #m , original length assumed in file
	xl          = pd.ExcelFile('./inputs/fiber/raw/OFS_ClearLite_980_16_65m.xlsx')
	first_sheet = xl.sheet_names[0]
	df          = xl.parse(first_sheet)

	x_ofs = df['Wavelength'].values
	y_ofs = df['Fiber prop'].values
	lengths = np.ones_like(x_ofs) * length

	ynew    = y_ofs** (length/l0)

	np.savetxt(datapath + 'fiber/ofs_throughput_%sm.csv'%length,np.vstack((x_ofs,ynew,lengths)).T,delimiter=',',header='wavelength_um,throughput')
	
	return x_ofs,ynew


def load_subsection(x,key_name):
	"""
	load subsystem components labeled key
	
	inputs
	-----
	x - x array to interpolate data onto
	key_name - name of subsection to load

	returns 
	--------
	transmission  - dictionary
		contains data for each item in the subsection
	total - array
		the total throughput for this subsection
	"""
	includes, types, values, filenames, elements = load_file(excel_file)

	total = np.ones_like(x)
	transmission = {}

	# step through each item in excel file
	for i, include in enumerate(includes):
		# start a dictionary entry for new section
		if types[i] == 'Note':
			key = elements[i] # define key for loaded section
		if key==key_name: # if we're in the section we want, start loading data
			if include == 1: # only include if include is set to 1
				t = set_input(x, types[i], values[i], filenames[i])
				transmission[elements[i]] = t # save data in dic
				total*=t # runnign log of total

	return transmission, total


if __name__=='__main__':
	# load excel_file into transmission dictionary and return total throughupt t_all
	excel_file   = './HISPEC_allsubs.xlsx'

	# load the subsection specifically
	fib, fib_tot = load_subsection(x,'FIBER TRANSMISSION RED')
	coupling_NGS, ngs_tot = load_subsection(x,'COUPLING NGS')
	coupling_LGS,lgs_tot = load_subsection(x,'COUPLING LGS')

	##############
	# plot the total fib section
	fig, ax = plt.subplots(1, 1, figsize=(9,6))
	ax.fill_between(yJ,y1=0,y2=1,facecolor='blue',alpha=0.1,zorder=-100)
	ax.fill_between(HK,y1=0,y2=1,facecolor='red',alpha=0.1)
	ax.fill_between([1330,1490],y1=0,y2=1,facecolor='white',zorder=100)
	
	# plot fib items
	for key in fib.keys():
		print(key)
		if type(fib[key])!=np.array:
			ax.plot(x,np.ones_like(x)*fib[key],label=key)
		else:
			ax.plot(x,fib[key],label=key)

	# plot coupling
	#ax.plot(x,1.3*coupling_NGS['Fiber Coupling (NGS)']*coupling_NGS['HO WFE Strehl 120nm (NGS)'],label='NGS Coupling')
	#ax.plot(x,1.3*coupling_LGS['Fiber Coupling (LGS)']*coupling_LGS['HO WFE Strehl 230 nm (LGS)'],label='LGS Coupling')

	# TOTALs!
	ax.plot(x,fib_tot,'k',lw=2,ls='--')
	#ax.plot(x, fib_tot * ngs_tot,'k',lw=2,ls='--')

	ax.legend(fontsize=10)

	# grids!
	ax.yaxis.grid(True, which='both',alpha=0.5,zorder=1000)
	#ax.yaxis.set_minor_locator(MultipleLocator(0.01))
	ax.yaxis.set_major_locator(MultipleLocator(0.1))

	ax.set_xlabel('Wavelength (nm)',fontsize=12)
	ax.set_ylabel('Throughput',fontsize=12)
	ax.grid()
	ax.set_title('Fiber System Throughput')

	if not os.path.exists(outpath):
		os.makedirs(outpath)
	
	plt.savefig(outpath + '/fiber_subsystem.png',dpi=500)
	np.savetxt(outpath + './fiber_subsystem.csv', np.vstack((x/1000,fib_tot)).T,delimiter=',',header='wavelength (nm),transmission (I/F) ')
	
	







	