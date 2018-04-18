from multiqc.modules.base_module import BaseMultiqcModule
from multiqc.plots import scatter
import logging

# Initialise the logger
log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):
    def __init__(self):
        # Initialise the parent object
        super(MultiqcModule, self).__init__(
            name='Synteny plots', anchor='mummerplot-module',
            href="http://mummer.sourceforge.net/",
            info="Synteny plots were based on an alignment made using Nucmer (included in Quast).")

        # find and load files
        self.plot_data = dict()
        for f in self.find_log_files('quast_synteny'):
            self.plot_data[f['s_name'].replace('_', ' ')] = [self.plotfile_to_list(f['f'])]

        if not self.plot_data:
            raise UserWarning
        else:
            log.info("found mummerplot images")
        self.make_plots()

    def plotfile_to_list(self, pf):
        step_size = 5000
        pf_list = pf.split('\n')  # 1 item per line
        points_list = []
        for line in pf_list:
            if not line:
                continue
            x_coords, y_coords = line.split('|')[:2]
            x_start, x_stop = x_coords.split(' ')[:2]
            y_start, y_stop = y_coords.split(' ')[:2]
            x_start = int(x_start); y_start = int(y_start); x_stop = int(x_stop); y_stop = int(y_stop)
            if x_start == x_stop:
                continue
            dydx = float(y_start - y_stop) / float(x_start - x_stop)
            if dydx > 0: # fwd
                color='rgba(251, 128, 114, 1)'
            else:
                color='rgba(128, 177, 211, 1)'
            x_points = list(range(x_start, x_stop, step_size))
            if x_points[-1] != x_stop:  # ensure endpoint is always there
                x_points.append(x_stop)
            y_points = [0] * len(x_points)
            y_points[0] = y_start
            for i, xc in enumerate(x_points):
                y_points[i] = y_start + dydx * (xc - x_start)
            cur_points_list = [{'x': x, 'y': y, 'color': color} for x,y in zip(x_points, y_points)]
            points_list.extend(cur_points_list)
        return points_list

    @property
    def data_labels(self):
        return [{'name': l, 'xlab': 'reference', 'ylab': l} for l in self.plot_data]


    def make_plots(self):
        pconfig = {
            'id': 'syntenyplot',
            'title': 'Synteny plot',
            'marker_line_width': 0,
            'marker_size': 2,
            'enableMouseTracking': False,
            'square': True,
            'data_labels': self.data_labels
        }

        self.add_section(
            anchor='syntenyplot',
            description='',
            plot=scatter.plot(self.plot_data, pconfig)
        )
