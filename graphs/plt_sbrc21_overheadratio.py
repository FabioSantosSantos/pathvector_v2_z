#!/usr/bin/python

import sys
import json
import numpy as np
from scipy.stats import sem, t
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser(description='Plot data')
parser.add_argument('--ndvr', metavar='FILE', required=True, nargs='+',
                    help='filename containing the logs')
parser.add_argument('--pathvector', metavar='FILE', required=True, nargs='+',
                    help='filename containing the logs')
parser.add_argument('--output', metavar='FILE', type=str, nargs='?',
                    help='filename to save the output (otherwise it will just show)')

args = parser.parse_args()


confidence = 0.95

data_ndvr = {}
for filename in args.ndvr:
    f = open(filename)
    result = json.load(f)
    for k in sorted(result.keys(), key=lambda k : int(k)):
        x = int(k)
        if x not in data_ndvr:
            data_ndvr[x] = []
        data_ndvr[x].append(result[k]['ticks'])

data_pathvector = {}
for filename in args.pathvector:
    f = open(filename)
    result = json.load(f)
    for k in sorted(result.keys(), key=lambda k : int(k)):
        x = int(k)
        if x not in data_pathvector:
            data_pathvector[x] = []
        data_pathvector[x].append(result[k]['ticks'])

result_data_ndvr = []
intv_data_ndvr = []
keys_ndvr = []
#for k in sorted(data_ndvr.keys(), key=lambda k : int(k)):
for k in sorted(data_ndvr):
    mydata = data_ndvr[k]
    mean = np.mean(mydata)
    intv = sem(mydata) * t.ppf((1 + confidence) / 2, len(mydata) - 1)
    result_data_ndvr.append(mean)
    intv_data_ndvr.append(intv)
    keys_ndvr.append(k)

result_data_pathvector = []
intv_data_pathvector = []
keys_pathvector = []
#for k in sorted(data_pathvector.keys(), key=lambda k : int(k)):
for k in sorted(data_pathvector):
    mydata = data_pathvector[k]
    mean = np.mean(mydata)
    intv = sem(mydata) * t.ppf((1 + confidence) / 2, len(mydata) - 1)
    keys_pathvector.append(k)
    result_data_pathvector.append(mean)
    intv_data_pathvector.append(intv)

width=2.0

fig = plt.figure()
fig.set_size_inches(8, 4)
plt.ylabel("CPU Clock Ticks")
plt.xlabel("Time (s)")
#plt.errorbar(sorted(data_ndvr.keys()), result_data_ndvr,  yerr=intv_data_ndvr, linestyle='-', label = 'ndvr', linewidth=width)
#plt.errorbar(sorted(data_nlsr.keys()), result_data_nlsr,  yerr=intv_data_nlsr, linestyle='-', label = 'nlsr', linewidth=width)
plt.errorbar(keys_ndvr, result_data_ndvr,  yerr=np.array(intv_data_ndvr), linestyle=':', label = 'ndvr', linewidth=width)
plt.errorbar(keys_pathvector, result_data_pathvector,  yerr=np.array(intv_data_pathvector), linestyle='-', label = 'pathvector', linewidth=width)
plt.legend(loc = 'upper right', fancybox=True)

if args.output:
    fig.savefig(args.output, format='pdf', dpi=100)
else:
    plt.show()
