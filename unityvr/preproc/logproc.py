### This module contains basic preprocessing functions for processing the unity VR log file

import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from os import mkdir, makedirs
from os.path import sep, isfile, exists
import json

#dataframe column defs
objDfCols = ['name','collider','px','py','pz','rx','ry','rz','sx','sy','sz']

posDfCols = ['frame','time','x','y','angle']
ftDfCols = ['frame','ficTracTReadMs','ficTracTWriteMs','dx','dy','dz']
dtDfCols = ['frame','time','dt']
nidDfCols = ['frame','time','dt','pdsig','imgfsig']

# Data class definition

@dataclass
class unityVRexperiment:

    # metadata as dict
    metadata: dict
        
    imaging: bool = False
    brainregion: str = None
    
    # timeseries data
    posDf: pd.DataFrame = pd.DataFrame(columns=posDfCols)
    ftDf: pd.DataFrame = pd.DataFrame(columns=ftDfCols)
    nidDf: pd.DataFrame = pd.DataFrame(columns=nidDfCols)
        
    # object locations
    objDf: pd.DataFrame = pd.DataFrame(columns=objDfCols)
    
    # methods
    def printMetadata(self):
        print('Metadata:\n')
        for key in self.metadata:
            print(key, ' : ', self.metadata[key])
    
    ## data wrangling
    def downsampleftDf(self):
        frameftDf = self.ftDf.groupby("frame").sum()
        frameftDf.reset_index(level=0, inplace=True)
        return frameftDf
    
    
    def saveData(self, saveDir, saveName):
        savepath = sep.join([saveDir,saveName, 'uvr'])
        # make directory
        if not exists(savepath):
            makedirs(savepath)
            
        # save metadata
        with open(sep.join([savepath,'metadata.json']), 'w') as outfile:
            json.dump(self.metadata, outfile,indent=4)
        
        # save dataframes
        self.objDf.to_csv(sep.join([savepath,'objDf.csv']))
        self.posDf.to_csv(sep.join([savepath,'posDf.csv']))
        self.ftDf.to_csv(sep.join([savepath,'ftDf.csv']))
        self.nidDf.to_csv(sep.join([savepath,'nidDf.csv']))
        
        return savepath

        
# constructor for unityVRexperiment
def constructUnityVRexperiment(dirName,fileName):
    
    dat = openUnityLog(dirName, fileName)
    
    metadat = makeMetaDict(dat, fileName)
    objDf = objDfFromLog(dat)
    posDf, ftDf, nidDf = timeseriesDfFromLog(dat)

    uvrexperiment = unityVRexperiment(metadata=metadat,posDf=posDf,ftDf=ftDf,nidDf=nidDf,objDf=objDf)
    
    return uvrexperiment


def loadUVRData(savepath):
    
    with open(sep.join([savepath,'metadata.json'])) as json_file:
        metadat = json.load(json_file)
    objDf = pd.read_csv(sep.join([savepath,'objDf.csv'])).drop(columns=['Unnamed: 0'])
    posDf = pd.read_csv(sep.join([savepath,'posDf.csv'])).drop(columns=['Unnamed: 0'])
    ftDf = pd.read_csv(sep.join([savepath,'ftDf.csv'])).drop(columns=['Unnamed: 0'])
    nidDf = pd.read_csv(sep.join([savepath,'nidDf.csv'])).drop(columns=['Unnamed: 0'])

    uvrexperiment = unityVRexperiment(metadata=metadat,posDf=posDf,ftDf=ftDf,nidDf=nidDf,objDf=objDf)
    
    return uvrexperiment


def parseHeader(notes, headerwords, metadat):
    
    for i, hw in enumerate(headerwords[:-1]):
        if hw in notes:
            metadat[i] = notes[notes.find(hw)+len(hw)+1:notes.find(headerwords[i+1])].split('~')[0].strip()
            
    return metadat

def makeMetaDict(dat, fileName):
    headerwords = ["expid", "experiment", "genotype","flyid","sex","notes","\n"]
    metadat = ['testExp', 'test experiment', 'testGenotype', 'NA', 'NA', "NA"]
    
    if 'headerNotes' in dat[0].keys():
        headerNotes = dat[0]['headerNotes']
        metadat = parseHeader(headerNotes, headerwords, metadat)

    [datestr, timestr] = fileName.split('.')[0].split('_')[1:3]
    
    metadata = {
        'expid': metadat[0],
        'experiment': metadat[1],
        'genotype': metadat[2],
        'sex': metadat[4],
        'flyid': metadat[3],
        'trial': 'trial'+fileName.split('.')[0].split('_')[-1][1:],
        'date': datestr,
        'time': timestr,
        'notes': metadat[5]
    } 
    
    return metadata
    
    
def openUnityLog(dirName, fileName):
    '''load json log file'''
    import json
    from os.path import sep
    
    # Opening JSON file 
    f = open(sep.join([dirName, fileName])) 

    # returns JSON object as  
    # a dictionary 
    data = json.load(f)
    
    return data


# Functions for extracting data from log file and converting it to pandas dataframe

def objDfFromLog(dat):
    # get dataframe with info about objects in vr
    matching = [s for s in dat if "meshGameObjectPath" in s]
    entries = [None]*len(matching)
    for entry, match in enumerate(matching):
        framedat = {'name': match['meshGameObjectPath'], 
                    'collider': match['colliderType'], 
                    'px': match['worldPosition']['x'], 
                    'py': match['worldPosition']['z'],
                    'pz': match['worldPosition']['y'],
                    'rx': match['worldRotationDegs']['x'], 
                    'ry': match['worldRotationDegs']['z'],
                    'rz': match['worldRotationDegs']['y'],
                    'sx': match['worldScale']['x'], 
                    'sy': match['worldScale']['z'],
                    'sz': match['worldScale']['y']}
        entries[entry] = pd.Series(framedat).to_frame().T
    objDf = pd.concat(entries,ignore_index = True)
    
    return objDf


def posDfFromLog(dat):
    # get info about camera position in vr
    matching = [s for s in dat if "attemptedTranslation" in s]    
    entries = [None]*len(matching)
    for entry, match in enumerate(matching):
        framedat = {'frame': match['frame'], 
                        'time': match['timeSecs'], 
                        'x': match['worldPosition']['x'], 
                        'y': match['worldPosition']['z'],
                        'angle': match['worldRotationDegs']['y'],
                        'dx':match['actualTranslation']['x'],
                        'dy':match['actualTranslation']['z'],
                        'dxattempt': match['attemptedTranslation']['x'],
                        'dyattempt': match['attemptedTranslation']['z']
                       }
        entries[entry] = pd.Series(framedat).to_frame().T
    posDf = pd.concat(entries,ignore_index = True)

    return posDf


def ftDfFromLog(dat):
    # get fictrac data
    matching = [s for s in dat if "ficTracDeltaRotationVectorLab" in s]
    entries = [None]*len(matching)
    for entry, match in enumerate(matching):
        framedat = {'frame': match['frame'], 
                        'ficTracTReadMs': match['ficTracTimestampReadMs'], 
                        'ficTracTWriteMs': match['ficTracTimestampWriteMs'], 
                        'dx': match['ficTracDeltaRotationVectorLab']['x'], 
                        'dy': match['ficTracDeltaRotationVectorLab']['y'],
                        'dz': match['ficTracDeltaRotationVectorLab']['z']}
        entries[entry] = pd.Series(framedat).to_frame().T

    if len(entries) > 0:
        ftDf = pd.concat(entries, ignore_index = True)
    else:
        ftDf = pd.DataFrame()
        
    return ftDf

def dtDfFromLog(dat):
    # get delta time info
    matching = [s for s in dat if "deltaTime" in s]
    entries = [None]*len(matching)
    for entry, match in enumerate(matching):
        framedat = {'frame': match['frame'], 
                    'time': match['timeSecs'], 
                    'dt': match['deltaTime']}
        entries[entry] = pd.Series(framedat).to_frame().T
    dtDf = pd.concat(entries,ignore_index = True)
            
    return dtDf


def pdDfFromLog(dat):
    # get NiDaq signal
    matching = [s for s in dat if "tracePD" in s]
    entries = [None]*len(matching)
    for entry, match in enumerate(matching):
        framedat = {'frame': match['frame'], 
                    'time': match['timeSecs'], 
                    'pdsig': match['tracePD'],
                    'imgfsig': match['imgFrameTrigger']}
        
        entries[entry] = pd.Series(framedat).to_frame().T
    pdDf = pd.concat(entries,ignore_index = True)
            
    return pdDf


def timeseriesDfFromLog(dat):
    from scipy.signal import medfilt

    posDf = pd.DataFrame(columns=posDfCols)
    ftDf = pd.DataFrame(columns=ftDfCols)
    dtDf = pd.DataFrame(columns=dtDfCols)
    pdDf = pd.DataFrame(columns = ['frame','time','pdsig', 'imgfsig'])

    posDf = posDfFromLog(dat)
    ftDf = ftDfFromLog(dat)
    dtDf = dtDfFromLog(dat)
    pdDf = pdDfFromLog(dat)
    
            
    posDf.time = posDf.time-posDf.time[0]
    dtDf.time = dtDf.time-dtDf.time[0]
    pdDf.time = pdDf.time-pdDf.time[0]
    
    if len(ftDf) > 0:
        ftDf.ficTracTReadMs = ftDf.ficTracTReadMs-ftDf.ficTracTReadMs[0]
        ftDf.ficTracTWriteMs = ftDf.ficTracTWriteMs-ftDf.ficTracTWriteMs[0]
    
    posDf = pd.merge(dtDf, posDf, on="frame", how='outer').rename(columns={'time_x':'time'}).drop(['time_y'],axis=1)
    nidDf = pd.merge(dtDf, pdDf, on="frame", how='outer').rename(columns={'time_x':'time'}).drop(['time_y'],axis=1)
    
    nidDf["pdFilt"]  = nidDf.pdsig.values
    nidDf.pdFilt[np.isfinite(nidDf.pdsig)] = medfilt(nidDf.pdsig[np.isfinite(nidDf.pdsig)])
    nidDf["pdThresh"]  = 1*(np.asarray(nidDf.pdFilt>=np.nanmedian(nidDf.pdFilt.values)))
    
    nidDf["imgfFilt"]  = nidDf.imgfsig.values
    nidDf.imgfFilt[np.isfinite(nidDf.imgfsig)] = medfilt(nidDf.imgfsig[np.isfinite(nidDf.imgfsig)])
    # replace with .loc[:, ...]
    nidDf["imgfThresh"]  = 1*(np.asarray(nidDf.imgfFilt>=np.nanmedian(nidDf.imgfFilt.values)))
    
    nidDf = generateInterTime(nidDf)
    
    return posDf, ftDf, nidDf


def generateInterTime(tsDf):
    from scipy import interpolate
    
    tsDf['framestart'] = np.hstack([0,1*np.diff(tsDf.time)>0])

    tsDf['counts'] = 1
    sampperframe = tsDf.groupby('frame').sum()[['time','dt','counts']].reset_index(level=0)
    sampperframe['fs'] = sampperframe.counts/sampperframe.dt

    frameStartIndx = np.hstack((0,np.where(tsDf.framestart)[0]))
    frameStartIndx = np.hstack((frameStartIndx, frameStartIndx[-1]+sampperframe.counts.values[-1]-1))
    frameIndx = tsDf.index.values

    frameNums = tsDf.frame[frameStartIndx].values.astype('int')
    frameNumsInterp = np.hstack((frameNums, frameNums[-1]+1))

    timeAtFramestart = tsDf.time[frameStartIndx].values

    #generate interpolated frames
    frameinterp_f = interpolate.interp1d(frameStartIndx,frameNums)
    tsDf['frameinterp'] = frameinterp_f(frameIndx)

    timeinterp_f = interpolate.interp1d(frameStartIndx,timeAtFramestart)
    tsDf['timeinterp'] = timeinterp_f(frameIndx)
    
    return tsDf