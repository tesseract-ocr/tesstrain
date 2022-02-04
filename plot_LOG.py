#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys

arg_list = sys.argv[1].split(',') 
modelname = arg_list[0]
ymaxcer = arg_list[1]

ytsvfile =  arg_list[2] # modelname + "-iteration.tsv"
ctsvfile =  arg_list[3] # modelname + "-checkpoint.tsv"
etsvfile =  arg_list[4] # modelname + "-eval.tsv"
stsvfile =  arg_list[5] # modelname + "-sub.tsv"

maxticks=4
maxCER=int(ymaxcer) #max y axis to display

ydf = pd.read_csv(ytsvfile,sep='\t', encoding='utf-8')
cdf = pd.read_csv(ctsvfile,sep='\t', encoding='utf-8')
edf = pd.read_csv(etsvfile,sep='\t', encoding='utf-8')
sdf = pd.read_csv(stsvfile,sep='\t', encoding='utf-8')

ydf = ydf.sort_values('LearningIteration')
cdf = cdf.sort_values('LearningIteration')
edf = edf.sort_values('LearningIteration')
sdf = sdf.sort_values('LearningIteration')

y = ydf['IterationCER']
x = ydf['LearningIteration']
t = ydf['TrainingIteration']

c = cdf['CheckpointCER']
cx = cdf['LearningIteration']
ct = cdf['TrainingIteration']

e = edf['EvalCER']
ex = edf['LearningIteration']
et = edf['TrainingIteration'] # Not available in training log file

s = sdf['SubtrainerCER']
sx = sdf['LearningIteration']
st = sdf['TrainingIteration']

plotfile = "data/" + modelname + "/plots/" + modelname + "-LOG-" + ymaxcer + ".png"

def annot_min(boxcolor, xpos, ypos, x, y, z):
    if z.isnull().values.any():
          xmin = x[np.argmin(y)]
          ymin = y.min()
          boxtext= " {:.3f}% at {:,} learning iterations " .format(ymin,xmin)
    else:
          tmin = z[np.argmin(y)]
          xmin = x[np.argmin(y)]
          ymin = y.min()
          boxtext= " {:.3f}% at {:,} / {:,} " .format(ymin,xmin,tmin)
    ax1.annotate(boxtext, xy=(xmin, ymin), xytext=(xpos,ypos), textcoords='offset points', color='black', fontsize=9,
        arrowprops=dict(shrinkA=1, shrinkB=1, fc=boxcolor,alpha=0.7, ec='white', connectionstyle="arc3"),
        bbox=dict(boxstyle='round,pad=0.2', fc=boxcolor, alpha=0.3))

PlotTitle="Tesseract LSTM Training - Model Name = " + modelname
fig = plt.figure(figsize=(11,8.5)) #size is in inches
ax1 = fig.add_subplot()

ax1.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax1.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.1f"))
ax1.set_ylabel('Error Rate %')

ax1.set_xlabel('Learning Iterations')
ax1.set_xticks(x)
ax1.tick_params(axis='x', labelsize='small')
ax1.locator_params(axis='x', nbins=maxticks)  # limit ticks on x-axis
ax1.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax1.xaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))

ax1.scatter(x, y, c='teal', alpha=0.7, s=0.5, label='BCER every 100 Training Iterations')
ax1.plot(x, y, 'teal', alpha=0.3, linewidth=0.5, label='Training BCER')
ax1.grid(True)

if not c.dropna().empty: # not NaN or empty
    ax1.scatter(cx, c, c='blue', s=15,
       label='BCER at Checkpoints during training)', alpha=0.5)
    annot_min('blue',-50,-50,cx,c,ct)

if not e.dropna().empty: # not NaN or empty
    ax1.plot(ex, e, 'magenta', linewidth=1.0)
    ax1.scatter(ex, e, c='magenta', s=30,
       label='BCER from evaluation during training', alpha=0.5)
    annot_min('magenta',-50,50,ex,e,et)

if not s.dropna().empty: # not NaN or empty
    ax1.plot(sx, s, 'orange', linewidth=0.5, label='SubTrainer BCER')
    ax1.scatter(sx, s, c='orange', s=0.5,
       label='BCER for UpdateSubtrainer every 100 iterations', alpha=0.5)
    annot_min('orange',-100,-100,sx,s,st)

plt.title('CER by Learning Iterations - from training log',fontsize=10)
plt.suptitle(PlotTitle, y=0.95, fontsize = 14, fontweight = 'bold')
plt.legend(loc='upper right')

ax1.set_ylim([-0.5,maxCER])

# Secondary x axis on top to display Training Iterations
ax2 = ax1.twiny() # ax1 and ax2 share y-axis
ax2.set_xlabel("Training Iterations")
ax2.set_xlim(ax1.get_xlim()) # ensure the independant x-axes now span the same range
ax2.set_xticks(x) # copy over the locations of the x-ticks from Learning Iterations
ax2.tick_params(axis='x', labelsize='small')
ax2.set_xticklabels(matplotlib.ticker.StrMethodFormatter('{x:,.0f}').format_ticks(t)) # But give value of Training Iterations
ax2.locator_params(axis='x', nbins=maxticks)  # limit ticks to same as x-axis
ax2.xaxis.set_ticks_position('bottom') # set the position of ticks of the second x-axis to bottom
ax2.xaxis.set_label_position('bottom') # set the position of labels of the second x-axis to bottom
ax2.spines['bottom'].set_position(('outward', 36)) # positions the second x-axis below the first x-axis

plt.savefig(plotfile)
