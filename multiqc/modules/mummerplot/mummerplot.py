from multiqc.modules.base_module import BaseMultiqcModule
from multiqc.plots import scatter
import logging
import re

# Initialise the logger
log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):
    def __init__(self):
        # Initialise the parent object
        super(MultiqcModule, self).__init__(
            name='Synteny plots', anchor='syntenyplot-module',
            info=' were generated based on alignment by Nucmer, as included in Quast.')

        # find and load files
        self.plot_data_fwd = dict()
        self.plot_data_rev = dict()
        for f in self.find_log_files('mummerplot/fplot'):
            fn_clean = re.sub('\.fplot', '', f['fn'])
            self.plot_data_fwd[fn_clean] = self.plotfile_to_list(f['f'], 'fwd', 'rgba(251, 128, 114, 1)')
        for f in self.find_log_files('mummerplot/rplot'):
            fn_clean = re.sub('\.rplot', '', f['fn'])
            self.plot_data_rev[fn_clean] = self.plotfile_to_list(f['f'], 'ref', 'rgba(128, 177, 211, 1)')

        if not self.plot_data_fwd and not self.plot_data_rev:
            raise UserWarning
        else:
            log.info("found mummerplot images")

        all_file_names = list(self.plot_data_fwd)
        all_file_names.extend(list(self.plot_data_rev))
        unique_file_names = set(all_file_names)
        self.plot_data = [{un: []} for un in unique_file_names]
        for i, _ in enumerate(self.plot_data):
            un = list(self.plot_data[i])[0]
            un_fwd = self.plot_data_fwd.get(un)
            un_rev = self.plot_data_rev.get(un)
            if un_fwd:
                self.plot_data[i][un].extend(un_fwd)
            if un_rev:
                self.plot_data[i][un].extend(un_rev)
        self.make_plots()

    def plotfile_to_list(self, pf, name, color):
        step_size = 5000
        pf = re.sub('#.+\n+', '', pf)
        pf_list = pf.split('\n\n\n')  # 1 item per line
        points_list = []
        for line in pf_list:
            if not line:
                continue
            line_start, line_stop = line.split('\n')
            x_start, y_start, _ = line_start.split(' ')
            x_stop, y_stop, _ = line_stop.split(' ')
            x_start = int(x_start); y_start = int(y_start); x_stop = int(x_stop); y_stop = int(y_stop)
            if x_start == x_stop:
                continue
            dydx = float(y_start - y_stop) / float(x_start - x_stop)
            x_points = list(range(x_start, x_stop, step_size))
            if x_points[-1] != x_stop:  # ensure endpoint is always there
                x_points.append(x_stop)
            y_points = [0] * len(x_points)
            y_points[0] = y_start
            for i, xc in enumerate(x_points):
                y_points[i] = y_start + dydx * (xc - x_start)
            cur_points_list = [{'x': x, 'y': y, 'name': name, 'color': color} for x,y in zip(x_points, y_points)]
            points_list.extend(cur_points_list)
        return points_list

    @property
    def data_labels(self):
        return [{'name': list(l)[0], 'xlab': 'reference', 'ylab': list(l)[0]} for l in self.plot_data]


    def make_plots(self):
        pconfig = {
            'id': 'mummerplot',
            # 'marker_line_colour': 'rgba(0,0,0,0)',
            'marker_line_width': 0,
            'marker_size': 2,
            'enableMouseTracking': False,
            'square': True,
            'data_labels': self.data_labels
        }

        self.add_section(
            anchor='mummerplot',
            description='',
            plot=scatter.plot(self.plot_data, pconfig)
        )
