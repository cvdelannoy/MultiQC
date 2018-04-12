#!/usr/bin/env python

""" MultiQC functions to plot a scatter plot """

import logging
import random
import os
import numpy as np
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from multiqc.utils import report, config
from math import ceil

logger = logging.getLogger(__name__)

letters = 'abcdefghijklmnopqrstuvwxyz'

def plot (data, pconfig=None):
    """ Plot a scatter plot with X,Y data.
    :param data: 2D dict, first keys as sample names, then x:y data pairs
    :param pconfig: optional dict with config key:value pairs. See CONTRIBUTING.md
    :return: HTML and JS, ready to be inserted into the page
    """
    if pconfig is None:
        pconfig = {}

    # Given one dataset - turn it into a list
    if type(data) is not list:
        data = [data]

    # Generate the data dict structure expected by HighCharts series
    plotdata = list()
    for ds in data:
        d = list()
        for s_name in ds:
            if type(ds[s_name]) is not list:
                ds[s_name] = [ ds[s_name] ]
            for k in ds[s_name]:
                if k['x'] is not None:
                    if 'xmax' in pconfig and float(k['x']) > float(pconfig['xmax']):
                        continue
                    if 'xmin' in pconfig and float(k['x']) < float(pconfig['xmin']):
                        continue
                if k['y'] is not None:
                    if 'ymax' in pconfig and float(k['y']) > float(pconfig['ymax']):
                        continue
                    if 'ymin' in pconfig and float(k['y']) < float(pconfig['ymin']):
                        continue
                this_series = { 'x': k['x'], 'y': k['y'] }
                try:
                    this_series['name'] = "{}: {}".format(s_name, k['name'])
                except KeyError:
                    this_series['name'] = s_name
                try:
                    this_series['color'] = k['color']
                except KeyError:
                    try:
                        this_series['color'] = pconfig['colors'][s_name]
                    except KeyError:
                        pass
                d.append(this_series)
        plotdata.append(d)

    # Add on annotation data series
    try:
        if pconfig.get('extra_series'):
            extra_series = pconfig['extra_series']
            if type(pconfig['extra_series']) == dict:
                extra_series = [[ pconfig['extra_series'] ]]
            elif type(pconfig['extra_series']) == list and type(pconfig['extra_series'][0]) == dict:
                extra_series = [ pconfig['extra_series'] ]
            for i, es in enumerate(extra_series):
                for s in es:
                    plotdata[i].append(s)
    except (KeyError, IndexError):
        pass

    # Make a plot
    if config.export_plots:
        export_scatter(plotdata, pconfig)
    return highcharts_scatter_plot(plotdata, pconfig)

def highcharts_scatter_plot (plotdata, pconfig=None):
    """
    Build the HTML needed for a HighCharts scatter plot. Should be
    called by scatter.plot(), which properly formats input data.
    """
    if pconfig is None:
        pconfig = {}

    # Get the plot ID
    if pconfig.get('id') is None:
        pconfig['id'] = 'mqc_hcplot_'+''.join(random.sample(letters, 10))

    # Sanitise plot ID and check for duplicates
    pconfig['id'] = report.save_htmlid(pconfig['id'])

    # Build the HTML for the page
    html = '<div class="mqc_hcplot_plotgroup">'

    # Buttons to cycle through different datasets
    if len(plotdata) > 1:
        html += '<div class="btn-group hc_switch_group">\n'
        for k, p in enumerate(plotdata):
            active = 'active' if k == 0 else ''
            try:
                name = pconfig['data_labels'][k]['name']
            except:
                name = k+1
            try:
                ylab = 'data-ylab="{}"'.format(pconfig['data_labels'][k]['ylab'])
            except:
                ylab = 'data-ylab="{}"'.format(name) if name != k+1 else ''
            try:
                ymax = 'data-ymax="{}"'.format(pconfig['data_labels'][k]['ymax'])
            except:
                ymax = ''
            html += '<button class="btn btn-default btn-sm {a}" data-action="set_data" {y} {ym} data-newdata="{k}" data-target="{id}">{n}</button>\n'.format(a=active, id=pconfig['id'], n=name, y=ylab, ym=ymax, k=k)
        html += '</div>\n\n'

    # The plot div
    html += '<div class="hc-plot-wrapper"><div id="{id}" class="hc-plot not_rendered hc-scatter-plot"><small>loading..</small></div></div></div> \n'.format(id=pconfig['id'])

    report.num_hc_plots += 1

    report.plot_data[pconfig['id']] = {
        'plot_type': "scatter",
        'datasets': plotdata,
        'config': pconfig
    }

    return html

def export_scatter(plotdata, pconfig):
    # for fformat in config.export_plot_formats: # Only need png for now
    nb_plots = len(plotdata)
    nb_rows = ceil((nb_plots * 1.0) / 2.0)
    vert_size = 7 * nb_rows
    plt.axis('equal')
    p = plt.figure(figsize=(14, vert_size), frameon=False)
    num_pat = re.compile('[0-9]+')
    for k, single_pd in enumerate(plotdata):
        x = [point['x'] for point in single_pd]
        y = [point['y'] for point in single_pd]
        color = [re.findall(num_pat, point.get('color', 'rgb(244, 91, 91, 1)')) for point in single_pd]
        color = np.array(color).astype(int)[:, 3]
        axes = p.add_subplot(nb_rows, 2, k+1)
        # _ = [axes.scatter(xc,yc,c=cc, s=2.5) for xc,yc,cc in zip(x,y,color)]
        axes.scatter(x, y, c=color / 255.0, s=2.5)
        axes.tick_params(labelsize=8, direction='out', left=False, right=False, top=False, bottom=False)
        axes.set_xlabel(pconfig['data_labels'][k].get('xlab', ''))
        axes.set_ylabel(pconfig['data_labels'][k].get('ylab', ''))
    # define plot id
    # name = pconfig['data_labels'][k].get('name','')
    # pid = 'mqc_{}_{}'.format(pconfig['id'], name)
    pid = 'mqc_{}'.format(pconfig['id'])
    pid = report.save_htmlid(pid, skiplint=True)
    # Make the directory if it doesn't already exist
    plot_dir = os.path.join(config.plots_dir, 'png')
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    # Make and save plot
    plot_fn = os.path.join(plot_dir, '{}.{}'.format(pid, 'png'))
    p.savefig(plot_fn, format='png')


def matplotlib_scatter(single_pd, k, pconfig=None):
    p = plt.figure(figsize=(14, 14), frameon=False)
    axes = p.add_subplot(111)
    axes.tick_params(labelsize=8, direction='out', left=False, right=False, top=False, bottom=False)
    axes.set_xlabel(pconfig.get('ylab', ''))
    axes.set_ylabel(pconfig.get('xlab', ''))
    x = [point['x'] for point in single_pd]
    y = [point['y'] for point in single_pd]
    axes.scatter(x, y)

    if 'title' in pconfig:
        top_gap = 1 + (0.5 / 14)
        plt.text(0.5, top_gap, pconfig['title'], horizontalalignment='center', fontsize=20, transform=axes.transAxes)
    axes.grid(True, zorder=0, which='both', axis='x', linestyle='-', color='#dedede', linewidth=1)
    axes.set_axisbelow(True)
    axes.spines['right'].set_visible(False)
    axes.spines['top'].set_visible(False)
    axes.spines['bottom'].set_visible(False)
    axes.spines['left'].set_visible(False)
    return p
