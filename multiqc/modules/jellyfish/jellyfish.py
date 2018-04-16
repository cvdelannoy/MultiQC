#!/usr/bin/env python

""" MultiQC module to parse results from jellyfish  """

from __future__ import print_function

import logging
from os.path import splitext
from multiqc.utils import config
from multiqc.plots import linegraph, scatter
from multiqc.modules.base_module import BaseMultiqcModule
import itertools

# Initialise the logger
log = logging.getLogger(__name__)

class MultiqcModule(BaseMultiqcModule):
    def __init__(self):
        # Initialise the parent object
        super(MultiqcModule, self).__init__(name='Jellyfish', anchor='jellyfish',
        href="http://www.cbcb.umd.edu/software/jellyfish/",
        info="is a tool for fast, memory-efficient counting of k-mers in DNA.")

        self.jellyfish_data = dict()
        self.kmer_distance_dict = dict()
        self.jellyfish_max_x = 0
        for f in self.find_log_files('jellyfish', filehandles=True):
            self.parse_jellyfish_data(f)

        if self.jellyfish_max_x < 100:
            self.jellyfish_max_x = 200 # the maximum is below 100, we display anyway up to 200
        else:
            self.jellyfish_max_x = 2*self.max_key #in this case the area plotted is a function of the maximum x

        self.jellyfish_count_data = dict()
        for f in self.find_log_files('jellyfish/count', filehandles=True):
            self.parse_jellyfish_count_data(f)

        if len(self.jellyfish_data) == 0 and len(self.jellyfish_count_data) < 2:
            raise UserWarning

        log.info("Found {} histogram files".format(len(self.jellyfish_data)))
        log.info("Found {} count (dump) files".format(len(self.jellyfish_count_data)))

        if len(self.jellyfish_data):
            self.frequencies_plot(xmax=self.jellyfish_max_x)
        if len(self.jellyfish_count_data) >= 2:
            self.kmer_comparison_plot()

    def parse_jellyfish_data(self, f):
        """ Go through the hist file and memorise it """
        histogram = {}
        occurence = 0
        for line in f['f']:
            line = line.rstrip('\n')
            occurence = int(line.split(" ")[0])
            count = int(line.split(" ")[1])
            histogram[occurence] = occurence*count
        #delete last occurnece as it is the sum of all kmer occuring more often than it.
        del histogram[occurence]
        #sanity check
        self.max_key = max(histogram, key=histogram.get)
        self.jellyfish_max_x = max(self.jellyfish_max_x, self.max_key)
        if len(histogram) > 0:
            if f['s_name'] in self.jellyfish_data:
                log.debug("Duplicate sample name found! Overwriting: {}".format(f['s_name']))
            self.add_data_source(f)
            self.jellyfish_data[f['s_name']] = histogram

    def parse_jellyfish_count_data(self, f):
        """memorise every jf count(dump) file """
        initial_dict = {}
        full_dict = {}
        for line in f['f']:
            line = line.rstrip('\n')
            kmer, count = line.split(' ')
            initial_dict[str(kmer)] = int(count)
        unique_symbols = set(''.join(initial_dict.keys()))
        kmer_length = set([len(k) for k in initial_dict.keys()])
        if len(kmer_length) > 1:
            log.error('Not all kmers in {} of same size!'.format(f['fn'])) # This should never happen if jellyfish works correctly
        # all_kmers = itertools.combinations_with_replacement(unique_symbols, kmer_length.pop())
        all_kmers = itertools.product(unique_symbols, repeat=kmer_length.pop())
        all_kmers = [''.join(km) for km in all_kmers]
        for ak in all_kmers:
            full_dict[ak] = initial_dict.get(ak, 0)
        full_dict['unique_symbols'] = unique_symbols
        if f['fn'] in self.jellyfish_count_data:
            log.debug("Duplicate sample name found! Overwriting: {}".format(f['s_name']))
        self.add_data_source(f)
        self.jellyfish_count_data[f['fn']] = full_dict

    def kmer_comparison_plot(self):
        """Generate comparison scatter plots between each pair of count files """
        plot_data = []
        data_labels = []
        name_pairs = itertools.combinations(self.jellyfish_count_data.keys(), 2)
        max_value = 0
        for n in name_pairs:
            cur_name = ' vs '.join(n)
            cur_plot_data = {cur_name: [
                {'x': self.jellyfish_count_data[n[0]][kmer],
                 'y': self.jellyfish_count_data[n[1]][kmer],
                 'name': kmer} for kmer in self.all_kmers]}
            # TODO: finishing addition of kmer distance to general stats table as soon as I find out how to easily define which file the reference file is...
            # self.kmer_distance_dict[n] = sum([abs(km['x'] - km['y']) for km in cur_plot_data[cur_name]])
            plot_data.append(cur_plot_data)
            data_labels.append({'name': cur_name,
                                'xlab': splitext(n[0])[0].replace('_', ' '),
                                'ylab': splitext(n[1])[0].replace('_', ' ')})
            cur_max_value = max([pd['x'] for pd in cur_plot_data[cur_name]])
            max_value = max(max_value, cur_max_value)

            pconfig = {
                'id': 'jellyfish_kmer_scatterplot',
                'title': 'Jellyfish: K-mer plot',
                'xmin': 0,
                'xmax': max_value,
                'ymin': 0,
                'ymax': max_value,
                'marker_size': 2,
                'marker_line_color': '#FFF',
                'marker_colour': 'rgba(251, 128, 114, 1)',
                'square': True,
                # 'extra_series': {
                #     'name': 'x = y',
                #     'data': [[0, 0], [max_value, max_value]],
                #     'dashStyle': 'Dash',
                #     'lineWidth': 1,
                #     'color': '#000000',
                #     'marker': {'enabled': False},
                #     'enableMouseTracking': False,
                #     'showInLegend': False
                # }
            }

        pconfig['data_labels'] = data_labels

        # if config.plots_force_flat:
        #     for pd in plot_data:
        #         pd_key = list(pd)[0]
        #         pd_key_ns = pd_key.replace(' ', '_')
        #         pd_data = {point['name']: point for point in pd[pd_key]}
        #         pd_pconfig = pconfig
        #         pd_pconfig['xlab'], _, pd_pconfig['ylab'] = pd_key.split(' ')
        #         self.add_section(
        #             anchor='jellyfish_kmer_comparison_plot_{}'.format(pd_key_ns),
        #             description='k-mer occurance in {} and {}'.format(pd_pconfig['xlab'], pd_pconfig['ylab']),
        #             plot=scatter.plot(pd_data, pd_pconfig)
        #         )
        # else:

        self.add_section(
            anchor='jellyfish_kmer_comparison_plot',
            description='Compare how often k-mers occur in different assemblies and the reference genome.',
            plot=scatter.plot(plot_data, pconfig)
        )

    def frequencies_plot(self, xmin=0, xmax=200):
        """ Generate the qualities plot """

        helptext = '''
            A possible way to assess the complexity of a library even in
            absence of a reference sequence is to look at the kmer profile of the reads.
            The idea is to count all the kmers (_i.e._, sequence of length `k`) that occur
            in the reads. In this way it is possible to know how many kmers occur
            `1,2,.., N` times and represent this as a plot.
            This plot tell us for each x, how many k-mers (y-axis) are present in the
            dataset in exactly x-copies.

            In an ideal world (no errors in sequencing, no bias, no  repeated regions)
            this plot should be as close as  possible to a gaussian distribution.
            In reality we will always see a peak for `x=1` (_i.e._, the errors)
            and another peak close to the expected coverage. If the genome is highly
            heterozygous a second peak at half of the coverage can be expected.'''

        pconfig = {
            'id': 'Jellyfish_kmer_plot',
            'title': 'Jellyfish: K-mer plot',
            'ylab': 'Counts',
            'xlab': 'k-mer frequency',
            'xDecimals': False,
            'xmin': xmin,
            'xmax': xmax
        }

        self.add_section(
            anchor='jellyfish_kmer_plot',
            description='The K-mer plot lets you estimate library complexity and coverage from k-mer content.',
            helptext=helptext,
            plot=linegraph.plot(self.jellyfish_data, pconfig)
        )

    @property
    def unique_symbols(self):
        symbols_per_file = [self.jellyfish_count_data[k]['unique_symbols'] for k in self.jellyfish_count_data]
        unique_symbols = set(itertools.chain.from_iterable(symbols_per_file))
        if any(unique_symbols != cur_symbols for cur_symbols in symbols_per_file):
            log.error("Not all count files deal with the same symbols")
            raise UserWarning
        return unique_symbols

    @property
    def kmer_length(self):
        all_keys = [self.jellyfish_count_data[dk].keys() for dk in self.jellyfish_count_data]
        all_keys = set(itertools.chain.from_iterable(all_keys))
        all_keys.remove('unique_symbols')
        kmer_lengths = set([len(k) for k in all_keys])
        if len(kmer_lengths) != 1:
            log.error("Found varying k-mer lengths in jellyfish files: {}".format(set(kmer_lengths)))
            raise UserWarning
        return kmer_lengths.pop()

    @property
    def all_kmers(self):
        kmers_separate_symbols = itertools.product(self.unique_symbols, repeat=self.kmer_length)
        kmers = [''.join(km) for km in kmers_separate_symbols]
        return kmers
