#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 27 15:41:12 2018

@author:
Maximilian N. Günther
MIT Kavli Institute for Astrophysics and Space Research, 
Massachusetts Institute of Technology,
77 Massachusetts Avenue,
Cambridge, MA 02109, 
USA
Email: maxgue@mit.edu
Web: www.mnguenther.com
"""

from __future__ import print_function, division, absolute_import

#::: plotting settings
import seaborn as sns
sns.set(context='paper', style='ticks', palette='deep', font='sans-serif', font_scale=1.5, color_codes=True)
sns.set_style({"xtick.direction": "in","ytick.direction": "in"})
sns.set_context(rc={'lines.markeredgewidth': 1})

#::: modules
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
from tqdm import tqdm
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable
from itertools import product

#::: my modules
import allesfitter
from allesfitter import config





###############################################################################
#::: plot publication ready spot plot
#::: flux
#::: model for 20 samples
#::: residuals for 1 sample
#::: 2D-spot map for 1 sample
###############################################################################

def plot_publication_spots_from_posteriors(datadir, Nsamples=20, command='save'):
    '''
    command : str
        'show', 'save', 'return', 'show and return', 'save and return'
    '''
    
    fig, ax1, ax2, ax3 = setup_grid()
        
    config.init(datadir)
    posterior_samples = allesfitter.get_ns_posterior_samples(datadir, Nsamples=Nsamples, as_type='2d_array')
    
    for inst in config.BASEMENT.settings['inst_all']:
        if config.BASEMENT.settings['host_N_spots_'+inst] > 0:
            
            xx = np.linspace(config.BASEMENT.data[inst]['time'][0], config.BASEMENT.data[inst]['time'][-1], 5000)
            
            for i_sample, sample in tqdm(enumerate(posterior_samples)):
            
                params = allesfitter.computer.update_params(sample)
                    
                spots = [ [params['host_spot_'+str(i)+'_long_'+inst] for i in range(1,config.BASEMENT.settings['host_N_spots_'+inst]+1) ],
                          [params['host_spot_'+str(i)+'_lat_'+inst] for i in range(1,config.BASEMENT.settings['host_N_spots_'+inst]+1) ],
                          [params['host_spot_'+str(i)+'_size_'+inst] for i in range(1,config.BASEMENT.settings['host_N_spots_'+inst]+1) ],
                          [params['host_spot_'+str(i)+'_brightness_'+inst] for i in range(1,config.BASEMENT.settings['host_N_spots_'+inst]+1) ] ]  
    
    
                model = allesfitter.computer.calculate_model(params, inst, 'flux')
                baseline = allesfitter.computer.calculate_baseline(params, inst, 'flux')

                model_xx = allesfitter.computer.calculate_model(params, inst, 'flux', xx=xx) #evaluated on xx (!)
                baseline_xx = allesfitter.computer.calculate_baseline(params, inst, 'flux', xx=xx) #evaluated on xx (!)
    
                if i_sample==0:
                    ax1 = axplot_data(ax1, config.BASEMENT.data[inst]['time'], config.BASEMENT.data[inst]['flux'], flux_err=np.exp(params['log_err_flux_'+inst]))
                    ax2 = axplot_residuals(ax2, config.BASEMENT.data[inst]['time'], config.BASEMENT.data[inst]['flux']-model-baseline, res_err=np.exp(params['log_err_flux_'+inst]))
                    ax3 = axplot_spots_2d(ax3, spots)      
                    
                ax1 = axplot_model(ax1, xx, model_xx+baseline_xx)  
                
            ax1.locator_params(axis='y', nbins=5)
        
            if 'save' in command:
                pubdir = os.path.join(config.BASEMENT.outdir, 'pub')
                if not os.path.exists(pubdir): os.makedirs(pubdir)
                fig.savefig( os.path.join(pubdir,'host_spots_'+inst+'.pdf'), bbox_inches='tight' )
                plt.close(fig)
    
            if 'show' in command:
                plt.show()
                
            if 'return' in command:
                return fig, ax1, ax2, ax3
                    
                    

def setup_grid():
    fig = plt.figure(figsize=(8,3.8))
    
    gs0 = gridspec.GridSpec(1, 2)
    
    gs00 = gridspec.GridSpecFromSubplotSpec(4, 1, subplot_spec=gs0[0], hspace=0)
    ax1 = plt.Subplot(fig, gs00[:-1, :])
    ax1.set(xlabel='', xticks=[], ylabel='Flux')
    fig.add_subplot(ax1)
    ax2 = plt.Subplot(fig, gs00[-1, :])
    ax2.set(xlabel='Phase', ylabel='Res.')
    fig.add_subplot(ax2)
    
    
    gs01 = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec=gs0[1])
    ax3 = plt.Subplot(fig, gs01[:, :])
    ax3.set(xlabel='Long. (deg)', ylabel='Lat. (deg.)')
    fig.add_subplot(ax3)
    
#    gs02 = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec=gs0[2])
#    cax = plt.Subplot(fig, gs02[:, :])
    
    plt.tight_layout()
    return fig, ax1, ax2, ax3
        
        

def axplot_data(ax, time, flux, flux_err=None):
    if flux_err is not None:
        ax.errorbar(time, flux,  yerr=flux_err, marker='.', linestyle='none', color='lightblue', zorder=9)
    ax.plot(time, flux, 'b.', zorder=10)
    return ax


def axplot_residuals(ax, time, res, res_err=None):
    if res_err is not None:
        ax.errorbar(time, res,  yerr=res_err, marker='.', linestyle='none', color='lightblue', zorder=9)
    ax.plot(time, res, 'b.', zorder=10)
    ax.axhline(0, color='r', linewidth=2, zorder=11)
    return ax
    

def axplot_model(ax, time, model):
    ax.plot(time, model, 'r-', zorder=11)
    return ax



        
def axplot_spots_2d(ax, spots):
    '''
    Inputs:
    -------
    spots : ...
    
    command : str
        'show' : show the figure (do not automatically save)
        'return' : return the figure object (do not display)
    
    e.g. for two spots:
    spots = [ [lon1, lon2],
              [lat1, lat2],
              [size1, size2],
              [brightness1, brightness2] ] 
    '''

    np.random.seed(42)

    spots = np.array(spots)
    N_spots = len(spots[0])
    
    for i in range(N_spots):
        lon, lat, size, brightness = spots[:,i]
        
        r = size
        theta = np.linspace(0, 2*np.pi, 100)
        lonv = lon + r * np.cos(theta)
        latv = lat + r * np.sin(theta)
        
#        lonv1 = lonv[ (lonv>0.) & (latv>-90.) ]
#        lonv1 = lonv[ (lonv>0.) & (latv>-90.) ]
#        
#        lonv2 = lonv[ (lonv<0.) & (latv>-90.) ] + 360.
#        lonv2 = lonv[ (lonv<0.) & (latv>-90.) ] + 360.
#        
#        lonv3 = lonv[ (lonv>0.) & (latv<-90.) ]
#        lonv3 = lonv[ (lonv>0.) & (latv<-90.) ]
#        
#        lonv4 = lonv[ (lonv>0.) & (latv>-90.) ]
#        lonv4 = lonv[ (lonv>0.) & (latv>-90.) ]
            
#            lonv = ( lon + r * np.cos(theta) ) % 360.
#            latv = ( lat + r * np.sin(theta) + 90. ) % 180. - 90.

        cm = plt.get_cmap('coolwarm')
        color = cm(brightness/2.)
        sc = ax.scatter(lon, lat, c=brightness, cmap='coolwarm', vmin=0, vmax=2)
        
        a = [-360.,0.,360.]
        b = [-180.,0.,180.]
        for r in product(a, b): 
            ax.fill(lonv+r[0], latv+r[1], color=color)
            ax.plot(lonv+r[0], latv+r[1], 'k-')
        
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    cbar = plt.colorbar(sc, cax=cax, ticks=[0,0.5,1,1.5,2])
    cbar.set_label('Brightness')
    ax.set(xlim=[0,360], ylim=[-90,90], xticks=[0,90,180,270,360], yticks=[-90,-45,0,45,90])
    
    return ax




        
        
        
        
                        
  

###############################################################################
#::: plot the spotmaps plots
#::: 3D-spot-map and 2D-spot-map, individually for 10 samples
###############################################################################                      

def plot_spots_from_posteriors(datadir, Nsamples=10, command='return'):
    
    if command=='show':
        Nsamples = 1 #overwrite user input and only show 1 sample if command=='show'
        
        
    config.init(datadir)
    posterior_samples_dic = allesfitter.get_ns_posterior_samples(datadir, Nsamples=Nsamples)
    
    for sample in tqdm(range(Nsamples)):
    
        params = {}
        for key in posterior_samples_dic:
            params[key] = posterior_samples_dic[key][sample]
        
        
        for inst in config.BASEMENT.settings['inst_all']:
            
            if config.BASEMENT.settings['host_N_spots_'+inst] > 0:
                spots = [
                                     [params['host_spot_'+str(i)+'_long_'+inst] for i in range(1,config.BASEMENT.settings['host_N_spots_'+inst]+1) ],
                                     [params['host_spot_'+str(i)+'_lat_'+inst] for i in range(1,config.BASEMENT.settings['host_N_spots_'+inst]+1) ],
                                     [params['host_spot_'+str(i)+'_size_'+inst] for i in range(1,config.BASEMENT.settings['host_N_spots_'+inst]+1) ],
                                     [params['host_spot_'+str(i)+'_brightness_'+inst] for i in range(1,config.BASEMENT.settings['host_N_spots_'+inst]+1) ]
                                    ]
        
                if command=='return':
                    fig, ax, ax2 = plot_spots(spots, command='return')
                    plt.suptitle('sample '+str(sample))
                    spotsdir = os.path.join(config.BASEMENT.outdir, 'spotmaps')
                    if not os.path.exists(spotsdir): os.makedirs(spotsdir)
                    fig.savefig( os.path.join(spotsdir,'host_spots_'+inst+'_posterior_sample_'+str(sample)) )
                    plt.close(fig)
                
                elif command=='show':
                    plot_spots(spots, command='show')
        
        for companion in config.BASEMENT.settings['companions_all']:
            for inst in config.BASEMENT.settings['inst_all']:
                if config.BASEMENT.settings[companion+'_N_spots_'+inst] > 0:
                    spots = [
                                         [params[companion+'_spot_'+str(i)+'_long_'+inst] for i in range(1,config.BASEMENT.settings[companion+'_N_spots_'+inst]+1) ],
                                         [params[companion+'_spot_'+str(i)+'_lat_'+inst] for i in range(1,config.BASEMENT.settings[companion+'_N_spots_'+inst]+1) ],
                                         [params[companion+'_spot_'+str(i)+'_size_'+inst] for i in range(1,config.BASEMENT.settings[companion+'_N_spots_'+inst]+1) ],
                                         [params[companion+'_spot_'+str(i)+'_brightness_'+inst] for i in range(1,config.BASEMENT.settings[companion+'_N_spots_'+inst]+1) ]
                                        ]
                    
                    if command=='return':
                        fig, ax, ax2 = plot_spots(spots, command='return')
                        plt.suptitle('sample '+str(sample))
                        spotsdir = os.path.join(config.BASEMENT.outdir, 'spotmaps')
                        if not os.path.exists(spotsdir): os.makedirs(spotsdir)
                        fig.savefig( os.path.join(spotsdir,companion+'_spots_'+inst+'_posterior_sample_'+str(sample)) )
                        plt.close(fig)
                    
                    elif command=='show':
                        plot_spots(spots, command='show')
                
                


def plot_spots(spots, command='show'):
    '''
    Inputs:
    -------
    spots : ...
    
    command : str
        'show' : show the figure (do not automatically save)
        'return' : return the figure object (do not display)
    
    e.g. for two spots:
    spots = [ [lon1, lon2],
              [lat1, lat2],
              [size1, size2],
              [brightness1, brightness2] ] 
    '''

    np.random.seed(42)

    spots = np.array(spots)
    N_spots = len(spots[0])
    radius = 1.
    N_rand = 3000
    
    fig = plt.figure(figsize=(10,4))
    ax = fig.add_subplot(121, projection='3d')
    ax2 = fig.add_subplot(122)
    
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    x = radius * np.outer(np.cos(u), np.sin(v))
    y = radius * np.outer(np.sin(u), np.sin(v))
    z = radius * np.outer(np.ones(np.size(u)), np.cos(v))
    ax.plot_surface(x, y, z, color='orange', linewidth=0, rstride=4, cstride=4, alpha=0.2, antialiased=False, shade=False)
    
    
    lon = np.linspace( 0./180.*np.pi, 360./180.*np.pi, 100 )
    lat = np.zeros_like(lon)
    x = radius * np.cos(lon) * np.cos(lat)
    y = radius * np.sin(lon) * np.cos(lat)
    z = radius * np.sin(lat)
    ax.plot(x,y,z,ls='-',c='grey',alpha=0.3)
    
    
    lat = np.linspace( 0./180.*np.pi, 360./180.*np.pi, 100 )
    lon = np.zeros_like(lat)
    x = radius * np.cos(lon) * np.cos(lat)
    y = radius * np.sin(lon) * np.cos(lat)
    z = radius * np.sin(lat)
    ax.plot(x,y,z,ls='-',c='grey',alpha=0.3)
    
    
    for i in range(N_spots):
        lon, lat, size, brightness = spots[:,i]
        
        r = size * np.sqrt(np.random.rand(N_rand))
        theta = np.random.rand(N_rand) * 2. * np.pi
        lonv = lon + r * np.cos(theta)
        latv = lat + r * np.sin(theta)
        
        lon = lonv/180.*np.pi
        lat = latv/180.*np.pi
        x = radius * np.cos(lon) * np.cos(lat)
        y = radius * np.sin(lon) * np.cos(lat)
        z = radius * np.sin(lat)
        c = brightness * np.ones_like(lon)
        sc = ax.scatter(x,y,z,c=c,marker='.', cmap='seismic', vmin=0, vmax=2, alpha=1, rasterized=True)
        ax2.scatter(lonv, latv, c=c, marker='.', cmap='seismic', vmin=0, vmax=2, alpha=1, rasterized=True)
        
        
        lon, lat, size, brightness = spots[:,i]
        
        r = size
        theta = np.linspace(0, 2*np.pi, 100)
        lonv = lon + r * np.cos(theta)
        latv = lat + r * np.sin(theta)
        
        lon = lonv/180.*np.pi
        lat = latv/180.*np.pi
        x = radius * np.cos(lon) * np.cos(lat)
        y = radius * np.sin(lon) * np.cos(lat)
        z = radius * np.sin(lat)
        ax.plot(x,y,z,'k-',zorder=20)
        ax2.plot(lonv, latv,'k-',zorder=20)
        
    plt.colorbar(sc)
        
    ax2.set(xlim=[0,360], ylim=[-90,90])
    
        
    
    if command=='return':
        return fig, ax, ax2

    elif command=='show':
        plt.show()
    
    
    
    
    
#if __name__ == '__main__':
#    plot_publication_spots_from_posteriors('/Users/mx/Dropbox (MIT)/Science/TESS_rapid_rotators/HS348/allesfit_2', command='save')
#    plot_publication_spots_from_posteriors('/Users/mx/Dropbox (MIT)/Science/TESS_rapid_rotators/TIC201789285_save/allesfit_8_spots', command='save')

    