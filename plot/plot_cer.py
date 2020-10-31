#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

csvlinesstep=100 # ticks after this many rows from csv file
maxCERtoDisplay=110 # max value for y axis, use -1 as min value
PlotTitle="Tesseract LSTM training and Evaluation Character Error Rates -1% to " + str(maxCERtoDisplay) + "%"

dataframe = pd.read_csv("plot_cer.csv",sep='\t', encoding='utf-8')
# TrainingIteration is being read as float followed by decimal and zero
# and Is null for EvalCER - following fixes the tick labels on secondary x axis
dataframe['TrainingIteration'] = dataframe['TrainingIteration'].fillna(-1)
dataframe['TrainingIteration'] = dataframe['TrainingIteration'].astype(int)
dataframe['TrainingIteration'] = dataframe['TrainingIteration'].astype(str)
dataframe['TrainingIteration'] = dataframe['TrainingIteration'].replace('-1', np.nan)
t = dataframe['TrainingIteration']
tticks = dataframe['TrainingIteration'][::csvlinesstep]
x = dataframe['LearningIteration']
xticks = dataframe['LearningIteration'][::csvlinesstep]
y = dataframe.IterationCER
c = dataframe.CheckpointCER
e = dataframe.EvalCER

def annot_min(boxcolor, x,y):
    xmin = x[np.argmin(y)]
    ymin = y.min()
    boxtext= "Minimum CER = {:.3f}".format(ymin)
    ax1.annotate(boxtext, xy=(xmin, ymin), xytext=(-10,10),
            textcoords='offset points', ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', fc=boxcolor, alpha=0.3))

fig = plt.figure(figsize=(11,8.5)) #size is in inches
ax1 = fig.add_subplot()
ax1.set_ylim([-1,maxCERtoDisplay])
ax1.set_xlabel('Learning Iterations')
ax1.set_ylabel('Character Error Rate (%)')
ax1.set_xticks(xticks)
ax1.tick_params(axis='x', rotation=90, labelsize='small')
ax1.grid(True)
ax1.scatter(x, y, s=1, c='blue', label='Training CER at every 100 iterations')
ax1.plot(x, c, 'teal')
ax1.scatter(x, c, c='teal', s=11, label='Best model checkpoint CER')
annot_min('teal',x,c)
ax1.plot(x, e, 'magenta')
ax1.scatter(x, e, c='magenta', s=11, label='Evaluation CER')
annot_min('magenta',x,e)

plt.title(label=PlotTitle)
plt.legend(loc='upper right')

ax2 = ax1.twiny() # ax1 and ax2 share y-axis
ax2.set_xlabel("Training Iterations")
ax2.tick_params(axis='x', rotation=90, labelsize='small')
ax2.set_xlim(ax1.get_xlim()) # ensure the independant x-axes now span the same range
ax2.set_xticks(xticks) # copy over the locations of the x-ticks from ax1 - Learning Iterations
ax2.set_xticklabels(tticks) # But display value of corresponding Training Iterations

plt.savefig("plot_cer.png")
