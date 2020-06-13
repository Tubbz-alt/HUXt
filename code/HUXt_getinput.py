# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 12:50:49 2020

@author: mathewjowens
"""
import httplib2
import urllib
import HUXt as H
import os
from pyhdf.SD import SD, SDC  
import matplotlib.pyplot as plt
from astropy.time import Time
import heliopy
import sunpy
import numpy as np
import astropy.units as u
import astropy
from heliopy.data import psp as psp_data, spice as spice_data

# <codecell> Get MAS data from MHDweb



def getMASboundaryconditions(cr=np.NaN, observatory='', runtype='', runnumber=''):
    """
    A function to grab the  Vr and Br boundary conditions from MHDweb. An order
    of preference for observatories is given in the function. Checks first if
    the data already exists in the HUXt boundary condition folder

    Parameters
    ----------
    cr : INT
        Carrington rotation number 
    observatory : STRING
        Name of preferred observatory (e.g., 'hmi','mdi','solis',
        'gong','mwo','wso','kpo'). Empty if no preference and automatically selected 
    runtype : STRING
        Name of preferred MAS run type (e.g., 'mas','mast','masp').
        Empty if no preference and automatically selected 
    runnumber : STRING
        Name of preferred MAS run number (e.g., '0101','0201').
        Empty if no preference and automatically selected    

    Returns
    -------
    flag : INT
        1 = successful download. 0 = files exist, -1 = no file found.

    """
    
    assert(np.isnan(cr)==False)
    
    #the order of preference for different MAS run results
    overwrite=False
    if not observatory:
        observatories_order=['hmi','mdi','solis','gong','mwo','wso','kpo']
    else:
        observatories_order=[str(observatory)]
        overwrite=True #if the user wants a specific observatory, overwrite what's already downloaded
        
    if not runtype:
        runtype_order=['mas','mast','masp']
    else:
        runtype_order=[str(runtype)]
        overwrite=True
    
    if not runnumber:
        runnumber_order=['0101','0201']
    else:
        runnumber_order=[str(runnumber)]
        overwrite=True
    
    #get the HUXt boundary condition directory
    dirs = H._setup_dirs_()
    _boundary_dir_ = dirs['boundary_conditions'] 
      
    #example URL: http://www.predsci.com/data/runs/cr2010-medium/mdi_mas_mas_std_0101/helio/br_r0.hdf 
    heliomas_url_front='http://www.predsci.com/data/runs/cr'
    heliomas_url_end='_r0.hdf'
    
    vrfilename = 'HelioMAS_CR'+str(int(cr)) + '_vr'+heliomas_url_end
    brfilename = 'HelioMAS_CR'+str(int(cr)) + '_br'+heliomas_url_end
    
    if (os.path.exists(os.path.join( _boundary_dir_, brfilename)) == False or 
        os.path.exists(os.path.join( _boundary_dir_, vrfilename)) == False or
        overwrite==True): #check if the files already exist
        #Search MHDweb for a HelioMAS run, in order of preference 
        h = httplib2.Http()
        foundfile=False
        for masob in observatories_order:
            for masrun in runtype_order:
                for masnum in runnumber_order:
                    urlbase=(heliomas_url_front + str(int(cr)) + '-medium/' + masob +'_' +
                         masrun + '_mas_std_' + masnum + '/helio/')
                    url=urlbase + 'br' + heliomas_url_end
                    #print(url)
                    
                    #see if this br file exists
                    resp = h.request(url, 'HEAD')
                    if int(resp[0]['status']) < 400:
                        foundfile=True
                        #print(url)
                    
                    #exit all the loops - clumsy, but works
                    if foundfile: 
                        break
                if foundfile:
                    break
            if foundfile:
                break
            
        if foundfile==False:
            print('No data available for given CR and observatory preferences')
            return -1
        
        #download teh vr and br files            
        print('Downloading from: ',urlbase)
        urllib.request.urlretrieve(urlbase+'br'+heliomas_url_end,
                           os.path.join(_boundary_dir_, brfilename) )    
        urllib.request.urlretrieve(urlbase+'vr'+heliomas_url_end,
                           os.path.join(_boundary_dir_, vrfilename) )  
        
        return 1
    else:
         print('Files already exist for CR' + str(int(cr)))   
         return 0


   
def readMASvrbr(cr):
    """
    A function to read in the MAS coundary conditions for a given CR

    Parameters
    ----------
    cr : INT
        Carrington rotation number

    Returns
    -------
    MAS_vr : NP ARRAY (NDIM = 2)
        Solar wind speed at 30rS, in km/s
    MAS_vr_Xa : NP ARRAY (NDIM = 1)
        Carrington longitude of Vr map, in rad
    MAS_vr_Xm : NP ARRAY (NDIM = 1)
        Latitude of Vr as angle down from N pole, in rad
    MAS_br : NP ARRAY (NDIM = 2)
        Radial magnetic field at 30rS, in model units
    MAS_br_Xa : NP ARRAY (NDIM = 1)
        Carrington longitude of Br map, in rad
    MAS_br_Xm : NP ARRAY (NDIM = 1)
       Latitude of Br as angle down from N pole, in rad

    """
    #get the boundary condition directory
    dirs = H._setup_dirs_()
    _boundary_dir_ = dirs['boundary_conditions'] 
    #create the filenames 
    heliomas_url_end='_r0.hdf'
    vrfilename = 'HelioMAS_CR'+str(int(cr)) + '_vr'+heliomas_url_end
    brfilename = 'HelioMAS_CR'+str(int(cr)) + '_br'+heliomas_url_end

    filepath=os.path.join(_boundary_dir_, vrfilename)
    assert os.path.exists(filepath)
    #print(os.path.exists(filepath))

    file = SD(filepath, SDC.READ)
    # print(file.info())
    # datasets_dic = file.datasets()
    # for idx,sds in enumerate(datasets_dic.keys()):
    #     print(idx,sds)
        
    sds_obj = file.select('fakeDim0') # select sds
    MAS_vr_Xa = sds_obj.get() # get sds data
    sds_obj = file.select('fakeDim1') # select sds
    MAS_vr_Xm = sds_obj.get() # get sds data
    sds_obj = file.select('Data-Set-2') # select sds
    MAS_vr = sds_obj.get() # get sds data
    
    #convert from model to physicsal units
    MAS_vr = MAS_vr*481.0 * u.km/u.s
    MAS_vr_Xa=MAS_vr_Xa * u.rad
    MAS_vr_Xm=MAS_vr_Xm * u.rad
    
    
    filepath=os.path.join(_boundary_dir_, brfilename)
    assert os.path.exists(filepath)
    file = SD(filepath, SDC.READ)
   
    sds_obj = file.select('fakeDim0') # select sds
    MAS_br_Xa = sds_obj.get() # get sds data
    sds_obj = file.select('fakeDim1') # select sds
    MAS_br_Xm = sds_obj.get() # get sds data
    sds_obj = file.select('Data-Set-2') # select sds
    MAS_br = sds_obj.get() # get sds data
    
    MAS_br_Xa=MAS_br_Xa * u.rad
    MAS_br_Xm=MAS_br_Xm * u.rad
    
    return MAS_vr, MAS_vr_Xa, MAS_vr_Xm, MAS_br, MAS_br_Xa, MAS_br_Xm


def get_MAS_equatorial_profiles(cr):
    """
    a function to download, read and process MAS output to provide HUXt boundary
    conditions at the helioequator

    Parameters
    ----------
    cr : INT
        Carrington rotation number

    Returns
    -------
    vr_in : NP ARRAY (NDIM = 1)
        Solar wind speed as a function of Carrington longitude at solar equator.
        Interpolated to HUXt longitudinal resolution. In km/s
    br_in : NP ARRAY(NDIM = 1)
        Radial magnetic field as a function of Carrington longitude at solar equator.
        Interpolated to HUXt longitudinal resolution. Dimensionless

    """
    
    assert(np.isnan(cr)==False and cr>0)
    
    #check the data exist, if not, download them
    getMASboundaryconditions(cr)    #getMASboundaryconditions(cr,observatory='mdi')
    
    #read the HelioMAS data
    MAS_vr, MAS_vr_Xa, MAS_vr_Xm, MAS_br, MAS_br_Xa, MAS_br_Xm = readMASvrbr(cr)
    
    #extract the value at the helioequator
    vr_eq=np.ones(len(MAS_vr_Xa))
    for i in range(0,len(MAS_vr_Xa)):
        vr_eq[i]=np.interp(np.pi/2,MAS_vr_Xm.value,MAS_vr[i][:].value)
    
    br_eq=np.ones(len(MAS_br_Xa))
    for i in range(0,len(MAS_br_Xa)):
        br_eq[i]=np.interp(np.pi/2,MAS_br_Xm.value,MAS_br[i][:])
        
    #now interpolate on to the HUXt longitudinal grid
    nlong=H.huxt_constants()['nlong']
    dphi=2*np.pi/nlong
    longs=np.linspace(dphi/2 , 2*np.pi -dphi/2,nlong)
    vr_in=np.interp(longs,MAS_vr_Xa.value,vr_eq)*u.km/u.s
    br_in=np.interp(longs,MAS_br_Xa.value,br_eq)

    #convert br into +/- 1
    #br_in[br_in>=0.0]=1.0*u.dimensionless_unscaled
    #br_in[br_in<0.0]=-1.0*u.dimensionless_unscaled
    
    return vr_in, br_in

# <codecell> Get the MAS equatorial profiles and run HUXt

#get the HUXt inputs
cr=2054
vr_in, br_in = get_MAS_equatorial_profiles(cr)
#now run HUXt
model = H.HUXt(v_boundary=vr_in, cr_num=cr, br_boundary=br_in,simtime=5*u.day, dt_scale=4)
model.solve([]) 

t_interest=0*u.day
model.plot(t_interest, field='ambient')
model.plot(t_interest, field='cme')
model.plot(t_interest, field='ptracer_cme')
model.plot(t_interest, field='ptracer_ambient')











# <codecell> Extract the properties at Earth latitude - not currently used

#create the time series
nlong=H.huxt_constants()['nlong']
tstart=sunpy.coordinates.sun.carrington_rotation_time(cr)
tstop=sunpy.coordinates.sun.carrington_rotation_time(cr+1)
dt=(tstop-tstart)/nlong
t=tstart + dt/2 + (tstop-tstart-dt) * np.linspace(0.,1.0,nlong)

### Now get Earth's Carrington Longitude vs time and visualize
earthSpiceKernel = spice_data.get_kernel("planet_trajectories")
heliopy.spice.furnish(earthSpiceKernel)
earthTrajectory = heliopy.spice.Trajectory("Earth")
earthTrajectory.generate_positions(t,'Sun','IAU_SUN')
earth = astropy.coordinates.SkyCoord(x=earthTrajectory.x,
                                     y=earthTrajectory.y,
                                     z=earthTrajectory.z,
                                     frame = sunpy.coordinates.frames.HeliographicCarrington,
                                     representation_type="cartesian"
                                     )
earth.representation_type="spherical"