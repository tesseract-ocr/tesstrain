#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

maxticks=10
dataframe = pd.read_csv("plot_cer_validation.csv",sep='\t', encoding='utf-8')
t = dataframe['TrainingIteration']
x = dataframe['LearningIteration']
v = dataframe.ValidationCER
c = dataframe.CheckpointCER
cmax = c[np.argmax(c)]
vmax = v[np.argmax(v)]
if vmax > cmax:
    maxCERtoDisplay=vmax+2
else:
    maxCERtoDisplay=cmax+2

def annot_min(boxcolor, xpos, ypos, x,y):
    xmin = x[np.argmin(y)]
    ymin = y.min()
    boxtext= "{:.3f}% at Learning Iteration {:}" .format(ymin,xmin)
    ax1.annotate(boxtext, xy=(xmin, ymin), xytext=(xpos,ypos), textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.2', fc=boxcolor, alpha=0.3))

PlotTitle="Tesseract LSTM Training and Validation Character Error Rate %"
fig = plt.figure(figsize=(11,8.5)) #size is in inches
ax1 = fig.add_subplot()
ax1.set_ylim([-1,maxCERtoDisplay])
ax1.set_xlabel('Learning Iterations')
ax1.set_ylabel('Character Error Rate (%)')
ax1.set_xticks(x)
ax1.tick_params(axis='x', rotation=45, labelsize='small')
ax1.locator_params(axis='x', nbins=maxticks)  # limit ticks on x-axis
ax1.grid(True)

if not c.dropna().empty: # not NaN or empty
	ax1.scatter(x, c, c='gold', s=50, label='Best Model Checkpoints CER')
	ax1.plot(x, c, 'gold')
	annot_min('gold',-100,-30,x,c)

if not v.dropna().empty: # not NaN or empty
	ax1.plot(x, v, 'blue')
	ax1.scatter(x, v, c='blue', s=50, label='Validation CER')
	annot_min('blue',-100,-30,x,v)

# CER of START_MODEL using same eval list
dflang = pd.read_csv("plot_cer_lang.csv",sep='\t', encoding='utf-8')
ax1.text(x.min(),dflang.LangCER[0], 
               "{:.3f}% for START_MODEL {}" .format(dflang.LangCER[0],dflang.Name[0]), 
                color='red')

plt.title(label=PlotTitle)
plt.legend(loc='upper right')

ax2 = ax1.twiny() # ax1 and ax2 share y-axis
ax2.set_xlabel("Training Iterations")
ax2.set_xlim(ax1.get_xlim()) # ensure the independant x-axes now span the same range
ax2.set_xticks(x) # copy over the locations of the x-ticks from Learning Iterations
ax2.tick_params(axis='x', rotation=45, labelsize='small')
ax2.set_xticklabels(t) # But give value of Training Iterations
ax2.locator_params(axis='x', nbins=maxticks)  #  limit ticks on secondary x-axis

plt.savefig("plot_cer_validation.png")
