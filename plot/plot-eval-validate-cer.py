#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
## from scipy.interpolate import UnivariateSpline

arg_parser = argparse.ArgumentParser(
    '''Creates plot from Training and Evaluation Character Error Rates''')
    
arg_parser.add_argument('-m', '--model', nargs='?',
                        metavar='MODEL_NAME', help='Model Name', required=True)
                        
arg_parser.add_argument('-v', '--validatelist', nargs='?', metavar='VALIDATELIST',
                        help='Validate List Suffix', required=True)
                        
arg_parser.add_argument('-y', '--ymaxcer', nargs='?', metavar='Y_MAX_CER',
                        help='Maximum CER % for y axis', required=True)

args = arg_parser.parse_args()

maxticks=5
maxCER=int(args.ymaxcer) #max y axis to display

ytsvfile = "tmp-" + args.model + "-" + args.validatelist + "-iteration.tsv"
ctsvfile = "tmp-" + args.model + "-" + args.validatelist + "-checkpoint.tsv"
etsvfile = "tmp-" + args.model + "-" + args.validatelist + "-eval.tsv"
vtsvfile = "tmp-" + args.model + "-" + args.validatelist + "-validate.tsv"
plotfile = "../data/" + args.model + "/plot/" + args.model + "-" + args.validatelist + "-cer.png"

ydf = pd.read_csv(ytsvfile,sep='\t', encoding='utf-8')
cdf = pd.read_csv(ctsvfile,sep='\t', encoding='utf-8')
edf = pd.read_csv(etsvfile,sep='\t', encoding='utf-8')
vdf = pd.read_csv(vtsvfile,sep='\t', encoding='utf-8')

ydf = ydf.sort_values('LearningIteration')
cdf = cdf.sort_values('LearningIteration')
edf = edf.sort_values('LearningIteration')
vdf = vdf.sort_values('LearningIteration')

y = ydf['IterationCER']
x = ydf['LearningIteration']
t = ydf['TrainingIteration']
c = cdf['CheckpointCER']
cx = cdf['LearningIteration']
ct = cdf['TrainingIteration']
e = edf['EvalCER']
ex = edf['LearningIteration']
et = edf['TrainingIteration'] # Not available in training log file
v = vdf['ValidationCER']
vx = vdf['LearningIteration']
vt = vdf['TrainingIteration']

trainlistfile = "../data/" + args.model + "/list.train"
evalistfile = "../data/" + args.model + "/list.eval"
validatelistfile = "../data/" + args.model + "/list." + args.validatelist

trainlistlinecount = len(open(trainlistfile).readlines(  ))
evallistlinecount = len(open(evalistfile).readlines(  ))
validatelistlinecount = len(open(validatelistfile).readlines(  ))

def annot_min(boxcolor, xpos, ypos, x, y, z):
    if z.isnull().values.any():
          xmin = x[np.argmin(y)]
          ymin = y.min()
          boxtext= "{:.3f}% CER\n  at {:.0f} iterations" .format(ymin,xmin)
    else:
          tmin = z[np.argmin(y)]
          xmin = x[np.argmin(y)]
          ymin = y.min()
          boxtext= "{:.3f}%  CER\n  at {:.0f} / {:.0f} iterations" .format(ymin,xmin,tmin)
    ax1.annotate(boxtext, xy=(xmin, ymin), xytext=(xpos,ypos), textcoords='offset points',
        arrowprops=dict(shrinkA=1, shrinkB=1, fc=boxcolor,alpha=0.7, ec='white', connectionstyle="arc3"),
        bbox=dict(boxstyle='round,pad=0.2', fc=boxcolor, alpha=0.3))

PlotTitle="Tesseract LSTM Training - Model Name = " + args.model + ", Validation List = list." + args.validatelist
fig = plt.figure(figsize=(11,8.5)) #size is in inches
ax1 = fig.add_subplot()

ax1.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax1.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.1f"))
ax1.set_ylabel('Character Error Rate %')

ax1.set_xlabel('Learning Iterations')
ax1.set_xticks(x)
ax1.tick_params(axis='x', rotation=45, labelsize='small')
ax1.locator_params(axis='x', nbins=maxticks)  # limit ticks on x-axis
ax1.grid(True)

ax1.scatter(x, y, c='teal', alpha=0.7, s=0.5, label='CER every 100 Training Iterations')
ax1.plot(x, y, 'teal', alpha=0.3, linewidth=0.5, label='Training CER')

if not v.dropna().empty: # not NaN or empty
	ax1.plot(vx, v, 'maroon', linewidth=0.7)
	ax1.scatter(vx, v, c='maroon', s=15,
    label='Validation CER from lstmeval (list.'  + args.validatelist +
    ' - ' + str(validatelistlinecount) +' lines)', alpha=0.5)
	annot_min('maroon',-100,60,vx,v,vt)

if not e.dropna().empty: # not NaN or empty
	ax1.plot(ex, e, 'magenta', linewidth=0.7)
	ax1.scatter(ex, e, c='magenta', s=15,
    label='Evaluation CER from lstmtraining (list.eval - ' +
    str(evallistlinecount) +' lines)', alpha=0.5)
	annot_min('magenta',-100,30,ex,e,et)

if not c.dropna().empty: # not NaN or empty
	ax1.scatter(cx, c, c='blue', s=12,
    label='Checkpoints CER  from lstmtraining (list.train - ' +
    str(trainlistlinecount) +' lines)', alpha=0.5)
	annot_min('blue',-100,-40,cx,c,ct)

ax1.set_xlim([0,None])
ax1.set_ylim([-0.5,maxCER])

## def fit_spline(splinex, spliney, splinedf, splines, splinecolor):
## 	if not spliney.dropna().empty: 
## 		uni = UnivariateSpline(splinex, spliney, s=splines)
## 		yxs = np.linspace(splinex.min(), splinex.max(), len(splinedf.index))
## 		ax1.plot(yxs, uni(yxs), splinecolor, alpha=0.5)
## 
## fit_spline(x, y, ydf, 500, 'teal')
## fit_spline(ex, e, edf, 0.1, 'magenta')
## fit_spline(vx, v, vdf, 1, 'maroon')

plt.title(label=PlotTitle)
plt.legend(loc='upper right')

# Secondary x axis on top to display Training Iterations
ax2 = ax1.twiny() # ax1 and ax2 share y-axis
ax2.set_xlabel("Training Iterations")
ax2.set_xlim(ax1.get_xlim()) # ensure the independant x-axes now span the same range
ax2.set_xticks(x) # copy over the locations of the x-ticks from Learning Iterations
ax2.tick_params(axis='x', rotation=45, labelsize='small')
ax2.set_xticklabels(t) # But give value of Training Iterations
ax2.locator_params(axis='x', nbins=maxticks)  # limit ticks to same as x-axis

plt.savefig(plotfile)
