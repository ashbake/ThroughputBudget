# Loads throughput excel sheet and
# multiplies things out to get the total
# throughput

#########################################################
# NOTES ON EXCEL INPUT FORMAT
#
# - automatically imports the first sheet
# - First column should have 1s in rows for what 
#   one wants to include
# - Section labels start with "FALSE, Note, NAME_OF_SECTION"
# - Throughput will be computed for sections as well 
#   as the total
# - Under 'Type' options are 'Coating', 'Constant', or 
#   'Internal Transmission'
#   - 'Coating' loads a file as is
#   - 'Constant' assumes the constant value in the 'value'
#      column
#   - 'Internal Transmission' uses value entry as optic 
#      thickness in mm and loads a file that has wavelength,
#      transmission, and thickness in mm as the columns.
#      The code then scales the values to the thickness value
#########################################################
import matplotlib.pylab as plt
import numpy as np
import pandas as pd
import csv,os
from scipy import interpolate
from matplotlib.ticker import MultipleLocator

from astropy import units as u
from astropy.modeling.models import BlackBody

import matplotlib
font = {'size'   : 14}
matplotlib.rc('font', **font)

yJ = [980,1327]
HK = [1490,2460]

###### NEW CLASS WHO DIS
class CalcThroughput():
    """
    Uses Excel throughput tracker for loading throughput for hispec and modhis options

    """
    def __init__(self, wave, excel_file, data_path='./data/throughput/hispec_subsystems/'):  
        """    
        inputs
        ------
        wave - array [nm]
            wavelength array to interpolate everything on
        excel_file - str
            name of the excel file. Assumes location is data_path
        data_path - str
            path to excel_file and the throughput coatings data that are pointed to in the excel_file
            
        outputs
        -------
        s - array
            base throughput (no coupling) sampled at wave
        data - dictionary
            contains individual surface data
        """
        self.wave = wave
        self.excel_file = excel_file
        self.data_path = data_path
        
        # load dictionary of transmission data for each subsection then combine
        self.includes, self.types, self.values, self.filenames, self.emissivities, self.temperatures, self.elements = self._loadThroughputFile(excel_file)
        
    def run(self, keys, save_path=None, label='test', include_ind=1, R=100000, npix=3):
        """Combine various sections into the throughputs we want 
        that are already loaded in __init__ into transmission_dic
        
        input
        ------
        keys - list
            list of keys that to include in the tranmission calculation
            e.g. for atc throughput you would do 
            		keys = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI ATC']
        save_path - str (default: None)
			path to where to save data, if none will not save data
        label - str (default: test)
			label to add to the saved data name
        include_ind - int
            value in the 'Include?' column of the excel file that indicates to include the row in the transmission calculation. 
            Will always include '1' , never include '0', and will also include include_ind values (for selecting dichroic options)
            TODO: make include_ind a list to allow for more options in the future   

        output
        ------
        final_throughput - array
	        final throughput array sampled on wave grid. 
            Also stored as self.total_throughput
        """
        self.save_path = save_path
        self.label = label

        # loads every section for include_ind and 1 then parses (TODO combine this into one to mimic calcBackground)
        self.transmission_dic = self._loadTransmissionData(include_ind) 
        self.total_throughput = self._combineTransmission(self.wave, 
                                                           self.transmission_dic, 
                                                           keys)
        # load background - only loads specified sections in 'keys'
        self.path_background, self.path_background_dic = self._calcBackground(keys, 
                                                                              include_ind, 
                                                                              R=R, npix=npix)
        # save throughput and path background as files in save_path
        if save_path != None:   
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            np.savetxt(save_path + './transmission_total_%s.txt'%label, np.vstack((self.wave,self.total_throughput)).T,delimiter=',',header='wavelength (nm),transmission (I/F) ')
            if type(self.path_background.value) != np.float64: 
                np.savetxt(save_path + './instbkg_%s.txt'%label, np.vstack((self.wave, self.path_background.value)).T,delimiter=',',header='wavelength (nm),inst_bkg (ph/s) ')
            else:
                np.savetxt(save_path + './instbkg_%s.txt'%label, [self.path_background.value], delimiter=',',header=f'include_ind={include_ind}\n {keys}\ninst_bkg (ph/s)')
                 

    
    def _loadTransmissionData(self, include_ind=1):
        """ Load transmission data into dictionary

        Assumes that the excel file has been loaded in __init__ and that the includes, types, values, filenames, and elements arrays are available

        outputs
        -------
        transmission : dictionary
            dictionary with keys as section headers and values as 
            transmission arrays
        """
        transmission = {}
        for i, include in enumerate(self.includes):
            # start a dictionary entry for new section
            if self.types[i] == 'Note':
                key = self.elements[i]
                transmission[key] = np.ones_like(self.wave)
            # if include (first column) is 1, include it
            if (include == 1) or (include == include_ind):
                # process input based on entry type and mulitply all together
                print(key, self.elements[i])
                transmission[key] *= self._setInput(self.wave,self.types[i], self.values[i], 
                                                   self.filenames[i],self.data_path)

        return transmission

    def _calcBackground(self, keys_to_include, include_ind=1, R=100000, npix=3):
        """ Compute emissivity. See excel sheet for which surfaces have emissivity data.
        Should double check all files are defined out to 2.5um. 
        If FEI ATC is in the path, integrates instead of using R & npix. Otherwise does a per reduced pixel calculation.

        inputs
        ------
        keys_to_include: list
            list of subsections heading keys to include e.g. ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI ATC']

        include_ind: int
            which to include in addition to 1 (for selecting dichroics)

        R: float
            resolving power of spectrograph (default 100,000)
        
        npix: float
            pixel sampling of spectrograph per resolution element (default 100,000)

        save_path: str
            path to save wave, path_background to file prefixed 'inst_bkg'

        outputs
        -------
        path_background - array or float
            if FEI ATC is in keys_to_include, it will be float otherwise will be an array sampled on self.wave assuming R and npix for spectral dispersion and SMF coupling

        path_background_flux - dictionary
            has the independent emission of each subsystem

        references:
        https://caltech.sharepoint.com/:p:/r/sites/coo/hispec/_layouts/15/Doc.aspx?sourcedoc=%7BDB5077D7-912D-4B5F-83DC-2A38FBC6150D%7D&file=Thermal%20Background%20Analytical%20Calculations.pptx&action=edit&mobileredirect=true
        """ 
        if 'FEI ATC' in keys_to_include: # if FEI ATC is included, need to assume ATC metrics
            Aomega = 28.3 * u.radian**2 * u.micron ** 2 # Area times omega assuming f/6 cold snout, 1.132 π2 p2 / (4F#2)
        else:
            # These are only valid for the spectrograph
            dlambda  = u.nm * self.wave / R / npix # pixel width in nanometers considering pixel sampling
            #fwhm = ((self.wave * u.nm / telescope_diameter) * u.radian).to(u.arcsec)
            #Aomega   = 1.13 * 2 * fwhm **2 * np.pi * (telescope_diameter/2)**2 # this reduces 1.775 * lambda^2
            Aomega   = 1.775 * u.radian**2 * (u.nm * self.wave) ** 2 # area of telescope times solid angle of fiber on sky, approx what couples into the SMF

        path_background_flux = {}                        # for storing snapshots of each subsystem where only considers that subsystem
        path_background_total = np.zeros_like(self.wave) # for combining full path to include full throughput of path

        for i, include in enumerate(self.includes):
            # start a dictionary entry for new section
            if self.types[i] == 'Note':
                key = self.elements[i]
                if key in keys_to_include: path_background_flux[key] = np.zeros_like(self.wave) # refresh this for each subsystem
            if key in keys_to_include:
                print(f'Compute Emissivity - including {key} components')
                # if include (first column) is 1, include it
                if (include == 1) or (include==include_ind):
                    # Load the transmission for this surface
                    transmission_surface = self._setInput(self.wave,self.types[i], self.values[i], 
                        self.filenames[i],self.data_path)

                    # Parse Emissivity entry
                    if (self.emissivities[i] == '1-R') or (self.emissivities[i] == '1-T'):
                        emissivity_surface = 1 - transmission_surface
                        flux_out_surface   = emissivity_surface * self._get_bb_radiation(self.temperatures[i] * u.K, Aomega) 
                    elif not np.isnan(self.emissivities[i]): # should be a number if not 1-R or 1-T or nan
                        emissivity_surface = self.emissivities[i] * np.ones_like(self.wave)
                        flux_out_surface   = emissivity_surface * self._get_bb_radiation(self.temperatures[i]*u.K, Aomega) 
                    else:
                        flux_out_surface = np.zeros_like(self.wave) # add 0 for line if doesnt have emissivity, but still must consider throughput effect

                    # New flux emissivity of surface gets added to the old emissivity, which is lowered by transmission of this surface
                    path_background_flux[key] = path_background_flux[key] * transmission_surface + flux_out_surface 
                    path_background_total     = path_background_total * transmission_surface + flux_out_surface 

        if 'FEI ATC' in keys_to_include:
            self.path_background = np.trapezoid(path_background_total, x=u.nm * self.wave).decompose()
        else:
            self.path_background = (path_background_total * dlambda).decompose()

        return self.path_background, path_background_flux

    def _get_bb_radiation(self, temperature, Aomega):
        """
        Compute blackbody radiation flux density for a surface with temperature

        inputs
        ------
        temperature - [u.K] 
            temperature of blackbody
        
        Aomega - [u.m^2 * u.arcsec^2]
            Solid angle times area or etendue of fiber
        """
        bb_fxn  = BlackBody(temperature, scale=1.0 * u.erg / (u.micron * u.s * u.cm**2 * u.arcsec**2)) 
        bb_density      = Aomega * bb_fxn(self.wave * u.nm)
        bb_flux         = bb_density.to(u.photon/u.s/u.micron, equivalencies=u.spectral_density(u.nm * self.wave)) 

        return bb_flux

    def _combineTransmission(self, x, transmission_dic, keys):
        """for key in keys, multiply all transmission entries together."""
        t_all = np.ones_like(x)
        for key in keys:
            t_all *= transmission_dic[key]
        
        return t_all
    
    def _loadThroughputFile(self,excel_file):
        """
        read excel file and return contents 

        inputs
        ------
        excel_file : str
            path to and name of excel file to load

        outputs
        -------
        includes : array
            1 if include, 0 if not
        types : array
            'Coating', 'Constant', or 'Internal Transmission'
        values : array
            value of input
        filenames : array
            file name of input
        elements : array
            section header
        """
        # read in the efficiency excel file into a dataframe ('df')
        xl = pd.ExcelFile(excel_file)
        #xl.sheet_names
        first_sheet = xl.sheet_names[0]
        df = xl.parse(first_sheet)
        #df.head()

        # get the number of active surfaces in the excel file
        #num_active_sfcs = df['Include?'].value_counts()[1]

        includes  = df['Include?'] # 0 to exclude, 1 to include, 2-5 selecting which ATC dichroic to assume
        types     = df['Type']     # coating, constant, or internal transmission
        values    = df['Value']
        filenames = df['Datafile']
        emissivities = df['Emissivity']  # populated for coatings that have emissivity data, otherwise NaN
        temperatures = df['Temperature'] # "
        elements  = df['Element']  # maybe for plotting/grouping

        return includes, types, values, filenames, emissivities, temperatures, elements

    def _setInput(self,wave, tt, value, file_name, data_path):
        """
        Processes a config input as either txt or float, interpolates it to x array, text file wavelengths assumes microns or nm

        inputs
        ------
        x : array
            wavelengths in nm
        tt : str
            'Coating', 'Constant', or 'Internal Transmission'
        value : float
            value of input
        filename : str
            file name of input

        outputs
        -------
        f_interp : array
            transmission values interpolated onto x array
        """
        if tt == 'Constant' or tt=='constant':
            return value
        else:
            with open(data_path + file_name.replace('\\','/'),'r') as test:
                lines = test.readlines()
                delimiter= csv.Sniffer().sniff(lines[2]).delimiter
            
            f = pd.read_csv(data_path + file_name.replace('\\','/'),sep=delimiter,engine='python').values

            if f[:,0][0] < 100:
                f[:,0] *=1000 # convert micron to nm

            # define thickness ratio if internal transmission
            thickness_ratio = value / f[:,2][0]\
                    if tt == 'Internal Transmission'\
                    else 1.0

            if np.nanmax(f[:,1]) > 1.05:
                f_interp =  interpolate.interp1d(f[:,0], f[:,1]/100,bounds_error=False,fill_value='extrapolate')
                return f_interp(wave) ** thickness_ratio
            else:    
                f_interp =  interpolate.interp1d(f[:,0], f[:,1],bounds_error=False,fill_value='extrapolate')
                return f_interp(wave) ** thickness_ratio

    def plotTotalThroughput(self,ax=None):
        """Plot self.total_throughput
        inputs
        -----
        label - str
			name to label the plot
        save_path - str (default None)
			path to save the plot image and the total throughput arrays 
        """
        if ax==None:    fig, ax = plt.subplots(1, 1, figsize=(9,4))
        ax.fill_between(yJ,y1=0,y2=1,facecolor='blue',alpha=0.1,zorder=-100)
        ax.fill_between(HK,y1=0,y2=1,facecolor='red',alpha=0.1)

        #ax.text(385.1,0.041,'Requirement',fontsize=9)

        ax.plot(self.wave,self.total_throughput,'k',label='Total Throughput')
        ax.legend()
        #ax.set_ylim(0,np.max(self.total_throughput) * 1.1)

        # grids!
        ax.yaxis.grid(True, which='both',alpha=0.5)
        ax.yaxis.set_minor_locator(MultipleLocator(0.01))
        ax.yaxis.set_major_locator(MultipleLocator(0.1))

        ax.set_xlabel('Wavelength (nm)',fontsize=12)
        ax.set_ylabel('Throughput',fontsize=12)
        ax.grid()
        
        plt.title(self.label)
        if self.save_path != None: plt.savefig(self.save_path + '/transmission_total_%s.png'%self.label,dpi=500)

    def plotBackground(self,ax=None):
        """Plot self.total_throughput
        inputs
        -----
        label - str
			name to label the plot
        save_path - str (default None)
			path to save the plot image and the total throughput arrays 
        """
        if len(self.path_background)==1: print('Path Background is a single number (ATC probably)'); return

        if ax==None:    fig, ax = plt.subplots(1, 1, figsize=(9,4))
        ax.fill_between(yJ,y1=0,y2=1,facecolor='blue',alpha=0.1,zorder=-100)
        ax.fill_between(HK,y1=0,y2=1,facecolor='red',alpha=0.1)

        #ax.text(385.1,0.041,'Requirement',fontsize=9)

        ax.plot(self.wave, self.path_background,'k',label=self.label)
        ax.legend()
        ax.set_ylim(0,np.max(self.path_background.value) * 1.5)

        # grids!
        ax.yaxis.grid(True, which='both',alpha=0.5)

        ax.set_xlabel('Wavelength (nm)',fontsize=12)
        ax.set_ylabel('Instrument Background (ph/s)',fontsize=12)
        
        plt.title(self.label)
        if self.save_path != None: plt.savefig(self.save_path + '/instbkg_%s.png'%self.label,dpi=500)

    def plotSubsectionComponents(self,key_name):
        """
        plot subsystem components labeled by key
        
        Could be rewritten to avoid duplicate loading of excel file..
        """

        total = np.ones_like(self.wave)

        fig, ax = plt.subplots(1, 1, figsize=(8,5))
        for i, include in enumerate(self.includes):
            # start a dictionary entry for new section
            if self.types[i] == 'Note':
                key = self.elements[i]
            if key==key_name:
                if include == 1:
                    t = self._setInput(self.wave,self.types[i], self.values[i], self.filenames[i],self.data_path)
                    if self.types[i]=='Coating' or self.types[i]=='coating':
                        ax.plot(self.wave,t,label=self.elements[i])
                    if self.types[i]=='Constant' or self.types[i]=='constant':
                        ax.plot(self.wave,self.wave*0+t,label=self.elements[i])
                    total*=t

        ax.fill_between(yJ,y1=0,y2=1,facecolor='blue',alpha=0.1,zorder=-100)
        ax.fill_between(HK,y1=0,y2=1,facecolor='red',alpha=0.1)
        ax.set_xlabel('Wavelength [nm]')
        ax.set_ylabel('Transmission')
        
        ax.plot(self.wave,total,'k',lw=2)
        plt.legend(fontsize=8)
        plt.title(key_name)
        plt.grid()

        if self.save_path != None: plt.savefig(self.save_path + '/subsection_components_%s.png'%key_name,dpi=500)

    def plotSubsections(self,keys,ax=None,):
        """ plot transmission for each subsystem
        
        inputs
        -----
        keys - list
            list of subsystem keywords to include in the plot e.g. 'AO' or 'FEI COMMON'
         """
        # define specific things
        if ax==None: fig, ax = plt.subplots(1, 1, figsize=(9,4))

        for k in keys: 
            # only plot if not ones
            if np.any(self.transmission_dic[k]!=1): 
                ax.plot(self.wave,self.transmission_dic[k],label=k) 

        ax.plot(self.wave,self.total_throughput,'k',lw=2, label='Total Throughput')
        ax.fill_between(yJ,y1=0,y2=1,facecolor='blue',alpha=0.3)
        ax.fill_between(HK,y1=0,y2=1,facecolor='red',alpha=0.3)
        ax.set_ylim(0,1.1)

        ax.set_xlabel('Wavelength (nm)',fontsize=12)
        ax.set_ylabel('Throughput',fontsize=12)
        plt.title(self.label)
        
        ax.legend(fontsize=7)
        ax.grid()

        if self.save_path != None: plt.savefig(self.save_path + '/transmission_components_%s.png'%self.label,dpi=500)

        return ax


def calc_strehl(wfe,wavelength):
    """
    Extended extended Marechal equation - used function by code
    as of No 20th. See KOAN doc for info

    inputs
    ------
    wfe: nm
    wavelength: nm, grid or single number

    outputs
    -------
    strehl at wavelength
    """
    marechal = 2*np.pi*wfe/wavelength
    strehl = np.exp(-(0.75 * (marechal + 0.2615))**2 + 0.05)

    return strehl



if __name__=='__main__':
    # define wavelength array
    x = np.arange(900,2600,0.1)
    # example save strehl
    wfe = 120 # nm

    strehl = calc_strehl(wfe,x)
    np.savetxt('inputs/fiber/strehl_howfe_%snm.csv'%wfe, np.vstack((x,strehl)).T,delimiter=',',header='wavelength(nm), strehl')

    # ATC Throughput Example
    gbt = CalcThroughput(x, './HISPEC_allsubs.xlsx',data_path='./inputs/')
    atc_keys = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI ATC']
    label    = 'ATC Throughput'
    gbt.run(atc_keys)
    gbt.plotTotalThroughput(label=label)
    gbt.plotSubsections(keys=atc_keys,label=label + ' Subsections')
    gbt.plotSubsectionComponents('AO')

    # BSPEC Throughput Example (minus coupling)
    atc_keys = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI ATC']


