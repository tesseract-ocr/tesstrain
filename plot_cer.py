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
etsvfile =  arg_list[4] # modelname + "-eval.tsv" - Not used as no training iterations number
stsvfile =  arg_list[5] # modelname + "-sub.tsv"
ltsvfile =  arg_list[6] # modelname + "-lstmeval.tsv"
otsvfile =  arg_list[7] # modelname + "-ocreval.tsv"
itsvfile =  arg_list[8] # modelname + "-isrieval.tsv"

maxticks=10
maxCER=int(ymaxcer) #max y axis to display

ydf = pd.read_csv(ytsvfile,sep='\t', encoding='utf-8')
cdf = pd.read_csv(ctsvfile,sep='\t', encoding='utf-8')
#edf = pd.read_csv(etsvfile,sep='\t', encoding='utf-8')
sdf = pd.read_csv(stsvfile,sep='\t', encoding='utf-8')
ldf = pd.read_csv(ltsvfile,sep='\t', encoding='utf-8')
odf = pd.read_csv(otsvfile,sep='\t', encoding='utf-8')
idf = pd.read_csv(itsvfile,sep='\t', encoding='utf-8')

ydf = ydf.sort_values('TrainingIteration')
cdf = cdf.sort_values('TrainingIteration')
#edf = edf.sort_values('LearningIteration') # TrainingIteration not available in training log file
sdf = sdf.sort_values('TrainingIteration')
ldf = ldf.sort_values('TrainingIteration')
odf = odf.sort_values('TrainingIteration')
idf = idf.sort_values('TrainingIteration')

y = ydf['IterationCER']
x = ydf['LearningIteration']
t = ydf['TrainingIteration']

c = cdf['CheckpointCER']
cx = cdf['LearningIteration']
ct = cdf['TrainingIteration']

#e = edf['EvalCER']
#ex = edf['LearningIteration']
#et = edf['TrainingIteration'] # Not available in training log file

s = sdf['SubtrainerCER']
sx = sdf['LearningIteration']
st = sdf['TrainingIteration']

l = ldf['EvalCER']
lx = ldf['LearningIteration']
lt = ldf['TrainingIteration']

o = odf['EvalCER']
ox = odf['LearningIteration']
ot = odf['TrainingIteration']

i = 100-idf['EvalCER'] # 100 - Accuracy %
ix = idf['LearningIteration']
it = idf['TrainingIteration']

plotfile = "data/" + modelname + "/plots/" + modelname + "-" + ymaxcer + ".png"

def annot_min(boxcolor, xpos, ypos, x, y, z):
    tmin = z[np.argmin(y)]
    xmin = x[np.argmin(y)]
    ymin = y.min()
    boxtext= " {:.3f}% at {:,} / {:,} " .format(ymin,xmin,tmin)
    ax1.annotate(boxtext, xy=(tmin, ymin), xytext=(xpos,ypos), textcoords='offset points', color='black', fontsize=9,
        arrowprops=dict(shrinkA=1, shrinkB=1, fc=boxcolor,alpha=0.7, ec='white', connectionstyle="arc3"),
        bbox=dict(boxstyle='round,pad=0.2', fc=boxcolor, alpha=0.3))

PlotTitle="Tesseract LSTM Training - Model Name = " + modelname
fig = plt.figure(figsize=(11,8.5)) #size is in inches
ax1 = fig.add_subplot()

ax1.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax1.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.1f"))
ax1.set_ylabel('Error Rate %')

ax1.set_xlabel('Training Iterations')
ax1.set_xticks(t)
ax1.tick_params(axis='x', labelsize='small')
ax1.locator_params(axis='x', nbins=maxticks)  # limit ticks on x-axis
ax1.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax1.xaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))

ax1.scatter(t, y, c='teal', alpha=0.7, s=0.5, label='BCER every 100 Training Iterations')
ax1.plot(t, y, 'teal', alpha=0.3, linewidth=0.5, label='Training BCER')
ax1.grid(True)

if not c.dropna().empty: # not NaN or empty
    ax1.scatter(ct, c, c='blue', s=15,
       label='BCER at Checkpoints during training', alpha=0.5)
    annot_min('blue',-50,-50,cx,c,ct)

if not l.dropna().empty: # not NaN or empty
    ax1.plot(lt, l, 'indigo', linewidth=0.5, label='lstmeval BCER')
    ax1.scatter(lt, l, c='indigo', s=10, label='BCER from lstmeval after training', alpha=0.5)
    annot_min('indigo',40,-40,lx,l,lt)

if not o.dropna().empty: # not NaN or empty
    ax1.plot(ot, o, 'red', linewidth=0.5, label='impactcentre/ocrevalUAtion CER')
    ax1.scatter(ot, o, c='red', s=10, label='CER from ocrevalUAtion', alpha=0.5)
    annot_min('red',40,40,ox,o,ot)

if not i.dropna().empty: # not NaN or empty
    ax1.plot(it, i, 'green', linewidth=0.5, label='ISRI ocreval CER')
    ax1.scatter(it, i, c='green', s=10, label='CER from ISRI ocreval', alpha=0.5)
    annot_min('green',80,80,ix,i,it)

if not s.dropna().empty: # not NaN or empty
    ax1.plot(st, s, 'orange', linewidth=0.5, label='SubTrainer BCER')
    ax1.scatter(st, s, c='orange', s=0.5,
       label='BCER for UpdateSubtrainer every 100 iterations', alpha=0.5)
    annot_min('orange',-100,-100,sx,s,st)

tmax = t[np.argmax(x)]
ymax = y[np.argmax(x)]
xmax = x.max()
boxtext= " {:.3f}% at \n  {:,} \n {:,} " .format(ymax,xmax,tmax)
ax1.annotate(boxtext, xy=(tmax, ymax), xytext=(20,-10), textcoords='offset points', color='black',
            bbox=dict(boxstyle='round,pad=0.2', fc='teal', alpha=0.3))

plt.title('CER by Training Iterations - from various OCR evaluation tools',fontsize=10)
plt.suptitle(PlotTitle, y=0.95, fontsize = 14, fontweight = 'bold')
plt.legend(loc='upper right')

ax1.set_ylim([-0.5,maxCER])

# Secondary x axis on top to display Learning Iterations
ax2 = ax1.twiny() # ax1 and ax2 share y-axis
ax2.set_xlabel("Learning Iterations")
ax2.set_xlim(ax1.get_xlim()) # ensure the independant x-axes now span the same range
ax2.set_xticks(t) # copy over the locations of the x-ticks from Training Iterations
ax2.tick_params(axis='x', labelsize='small')
ax2.set_xticklabels(matplotlib.ticker.StrMethodFormatter('{x:,.0f}').format_ticks(x)) # But give value of Learning Iterations
ax2.locator_params(axis='x', nbins=maxticks)  # limit ticks to same as x-axis
ax2.xaxis.set_ticks_position('bottom') # set the position of ticks of the second x-axis to bottom
ax2.xaxis.set_label_position('bottom') # set the position of labels of the second x-axis to bottom
ax2.spines['bottom'].set_position(('outward', 36)) # positions the second x-axis below the first x-axis



plt.savefig(plotfile)
