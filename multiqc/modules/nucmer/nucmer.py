from multiqc.modules.base_module import BaseMultiqcModule
from multiqc.plots import linegraph
import logging
import re

# Initialise the logger
log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):
    def __init__(self):
        # Initialise the parent object
        super(MultiqcModule, self).__init__(
            name='Synteny plots', anchor='syntenyplot-module',
            href="",
            info="Synteny plots were based on an alignment made using Nucmer.")

        # find and load files
        self.plot_data = {}
        for f in self.find_log_files('nucmer'):
            plot_coords = self.plotfile_to_list(f['f'])
            if len(plot_coords):
                self.plot_data[f['s_name']] = plot_coords

        if not self.plot_data:
            raise UserWarning
        else:
            log.info("found nucmer coord files")

        self.make_plots()

    def plotfile_to_list(self, pf):
        pf_list = list(filter(None, pf.split('\n')[2:]))
        if not len(pf_list):
            return []
        lines_dict = {}
        lines_list = []
        for lc, lp in enumerate(pf_list):
            xc, yc = lp.split('|')[:2]
            x_start, x_stop = [int(x) for x in list(filter(None, xc.strip().split(' ')))]
            y_start, y_stop = [int(y) for y in list(filter(None, yc.strip().split(' ')))]
            dydx = float(y_start - y_stop) / float(x_start - x_stop)
            if dydx > 0:
                color = 'rgba(251, 128, 114, 1)'
                name = 'fwd'
            else:
                color = 'rgba(128, 177, 211, 1)'
                name = 'rev'
            lines_dict[str(lc)] = {x_start: y_start,
                                   x_stop: y_stop,
                                   'name': name,
                                   'color': color}
            lines_list.append({x_start: y_start,
                               x_stop: y_stop,
                               'name': name,
                               'color': color})
        return [lines_dict]

    @property
    def data_labels(self):
        return [{'name': list(l)[0], 'xlab': 'reference', 'ylab': list(l)[0]} for l in self.plot_data]


    def make_plots(self):
        pconfig = {
            'id': 'mummerplot',
            'title': 'nucmer: synteny plot',
            # 'marker_line_colour': 'rgba(0,0,0,0)',
            # 'marker_line_width': 0,
            # 'marker_size': 2,
            'enableMouseTracking': False,
            'square': True,
            'data_labels': self.data_labels
        }

        self.add_section(
            anchor='mummerplot',
            description='',
            plot=linegraph.plot(self.plot_data, pconfig)
            # plot=scatter.plot(self.plot_data, pconfig)
        )
