### This module contains functions for plotting VR data, including functions to vizualize trajectories, frame rate, ...

import matplotlib.patches as mpatches
from matplotlib import patches
import matplotlib.pyplot as plt
import numpy as np
from os.path import sep, isfile, exists


## General
# axis beautification
def myAxisTheme(myax):
    myax.get_xaxis().tick_bottom()
    myax.get_yaxis().tick_left()
    myax.spines['top'].set_visible(False)
    myax.spines['right'].set_visible(False)

def plotScaleBar(ax,xlen,pos,labeltext):
    ax.plot([pos[0],pos[0]+xlen],[pos[1],pos[1]],'k')
    ax.text(pos[0],pos[1],labeltext)
    
def minimalAxisTheme(myax, xlen,pos,labeltext):
    plotScaleBar(myax,xlen,pos,labeltext)
    myax.axis('off')
    myax.set_aspect('equal')

def pathPlotAxisTheme(myax, units):
    myax.spines['top'].set_visible(False)
    myax.spines['right'].set_visible(False)
    myax.spines['bottom'].set_visible(False)
    myax.spines['left'].set_visible(False)
    myax.get_xaxis().set_ticks([])
    myax.get_yaxis().set_ticks([])
    myax.set_aspect('equal')
    myax.set_xlabel('x [{}]'.format(units))
    myax.set_ylabel('y [{}]'.format(units))
    
    
    
def plotVRpathWithObjects(uvrExperiment,limx,limy, myfigsize):

    fig, ax = plt.subplots(1,1, figsize=myfigsize)
    
    ax = plotAllObjects(uvrExperiment, ax)

    ax.plot(uvrExperiment.posDf['x'], uvrExperiment.posDf['y'],color='grey',alpha=0.5)
    ax.scatter(uvrExperiment.posDf['x'], uvrExperiment.posDf['y'],s=7,c=uvrExperiment.posDf['time'],cmap='viridis')
    
    if np.isfinite(limx[0]):
        ax.set_xlim(limx[0], limx[1])
        ax.set_ylim(limy[0], limy[1])
    ax.set_aspect('equal')
    
    return fig

def plotAllObjects(uvrExperiment, ax):
    
    for obj in range(uvrExperiment.objDf.shape[0]):
        if("Plane" in uvrExperiment.objDf.name[obj]): continue
            
        if("FlyCamera" not in uvrExperiment.objDf.name[obj]):
            ax = plotObjectEllipse(ax, 
                                   [uvrExperiment.objDf['sx'][obj], uvrExperiment.objDf['sy'][obj]], 
                                   [uvrExperiment.objDf['px'][obj], uvrExperiment.objDf['py'][obj]])
            ax.annotate(uvrExperiment.objDf['name'][obj], (uvrExperiment.objDf['px'][obj]+5, uvrExperiment.objDf['py'][obj]-10))
    return ax


def plotObjectEllipse(ax, rad, pos):
    ellipse = mpatches.Ellipse((pos[0],pos[1]), rad[0], rad[1], color='grey', alpha=0.5)
    ax.add_patch(ellipse)
    
    return ax

