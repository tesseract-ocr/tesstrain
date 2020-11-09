#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

csvlinesstep=50
maxCERtoDisplay=11
PlotTitle="Tesseract LSTM training and Evaluation Character Error Rates (-1 to " + str(maxCERtoDisplay) + "%)"

dataframe = pd.read_csv("plot_cer.csv",sep='\t', encoding='utf-8')
dataframe['TrainingIteration'] = dataframe['TrainingIteration'].fillna(-2)
dataframe['TrainingIteration'] = dataframe['TrainingIteration'].astype(int)
dataframe['TrainingIteration'] = dataframe['TrainingIteration'].astype(str)
dataframe['TrainingIteration'] = dataframe['TrainingIteration'].replace('-2', np.nan)
t = dataframe['TrainingIteration']
tticks = dataframe['TrainingIteration'][::csvlinesstep]
x = dataframe['LearningIteration']
xticks = dataframe['LearningIteration'][::csvlinesstep]
y = dataframe.IterationCER
c = dataframe.CheckpointCER
e = dataframe.EvalCER

def annot_min(boxcolor, xpos, ypos, x,y):
    xmin = x[np.argmin(y)]
    ymin = y.min()
    boxtext= "{:.3f}% at Learning Iteration {:}" .format(ymin,xmin)
    ax1.annotate(boxtext, xy=(xmin, ymin), xytext=(xpos,ypos), textcoords='offset points',
            arrowprops=dict(shrinkA=0.05, shrinkB=1, fc=boxcolor, ec='white', connectionstyle="arc3"),
            bbox=dict(boxstyle='round,pad=0.2', fc=boxcolor, alpha=0.3))

fig = plt.figure(figsize=(11,8.5)) #size is in inches
ax1 = fig.add_subplot()
ax1.set_ylim([-1,maxCERtoDisplay])
ax1.set_xlabel('Learning Iterations')
ax1.set_ylabel('Character Error Rate (%)')
ax1.set_xticks(xticks)
ax1.tick_params(axis='x', rotation=45, labelsize='small')
ax1.grid(True)
ax1.scatter(x, c, c='gold', s=50, label='Best Model Checkpoints CER')
ax1.plot(x, c, 'gold')
annot_min('gold',-150,-30,x,c)

ax1.scatter(x, y, s=5, c='teal', label='CER every 100 Training Iterations')
ax1.plot(x, y, 'teal')

ax1.plot(x, e, 'magenta')
ax1.scatter(x, e, c='magenta', s=50, label='Evaluation CER')
annot_min('magenta',-150,60,x,e) #uncomment only when eval data exists

plt.title(label=PlotTitle)
plt.legend(loc='upper right')

ax2 = ax1.twiny() # ax1 and ax2 share y-axis
ax2.set_xlabel("Training Iterations")
ax2.set_xlim(ax1.get_xlim()) # ensure the independant x-axes now span the same range
ax2.set_xticks(xticks) # copy over the locations of the x-ticks from Learning Iterations
ax2.tick_params(axis='x', rotation=45, labelsize='small')
ax2.set_xticklabels(tticks) # But give value of Training Iterations

plt.savefig("plot_cer_zoomin.png")
