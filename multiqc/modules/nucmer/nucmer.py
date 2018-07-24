from multiqc.modules.base_module import BaseMultiqcModule
from multiqc.plots import linegraph, scatter
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
        # self.plot_data = {}
        self.plot_data = []
        self.data_labels = []
        plots_html = ''
        for f in self.find_log_files('nucmer'):
            plot_coords, val_range = self.plotfile_to_list(f['f'], f['s_name'])
        #     if len(plot_coords):
        #         data_labels = {'name': f['s_name'],
        #                        'xlab': 'reference',
        #                        'ylab': f['s_name']}
        #         plots_html += self.write_plot_html(plot_coords, data_labels, val_range)
        #
        # self.draw_plots(plots_hmtl=plots_html)
            if len(plot_coords):
                # self.plot_data[f['s_name']] = plot_coords
                self.plot_data.append({f['s_name']: plot_coords})
                self.data_labels.append({'name': f['s_name'],
                                         'xlab': 'reference',
                                         'ylab': f['s_name']})

        if not self.plot_data:
            raise UserWarning
        else:
            log.info("found nucmer coord files")
        print(self.data_labels)
        self.make_plots()

    def plotfile_to_list(self, pf, name):
        pf_list = list(filter(None, pf.split('\n')[2:]))
        step_size = 5000
        if not len(pf_list):
            return []
        lines_dict = {}
        lines_list = []
        points_list = []
        val_range = [9999999999,0]
        for lc, lp in enumerate(pf_list):
            xc, yc = lp.split('|')[:2]
            x_start, x_stop = [int(x) for x in list(filter(None, xc.strip().split(' ')))]
            y_start, y_stop = [int(y) for y in list(filter(None, yc.strip().split(' ')))]
            dydx = float(y_start - y_stop) / float(x_start - x_stop)
            if dydx > 0:
                color = 'rgba(251, 128, 114, 1)'
            else:
                color = 'rgba(128, 177, 211, 1)'

            x_points = list(range(x_start, x_stop, step_size))
            if x_points[-1] != x_stop:  # ensure endpoint is always there
                x_points.append(x_stop)
            y_points = [0] * len(x_points)
            y_points[0] = y_start
            for i, xc in enumerate(x_points):
                y_points[i] = y_start + dydx * (xc - x_start)
            cur_points_list = [{'x': x, 'y': y, 'color': color} for x, y in
                                            zip(x_points, y_points)]
            points_list.extend(cur_points_list)
            lines_dict[x_start] = y_start
            lines_dict[x_stop] = y_stop
            # lines_dict[str(lc)] = {x_start: y_start,
            #                        x_stop: y_stop,
            #                        'name': name,
            #                        'color': color}
            val_range = [min(val_range[0], x_start, x_stop, y_start, y_stop),
                         max(val_range[1], x_start, x_stop, y_start, y_stop)]
            lines_list.append({x_start: y_start,
                               x_stop: y_stop})
        return points_list, val_range


    def make_plots(self):
        pconfig = {
            'id': 'mummerplot',
            'title': 'nucmer: synteny plot',
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
            # plot=linegraph.plot(self.plot_data, pconfig)
            plot=scatter.plot(data=self.plot_data, pconfig=pconfig)
        )

    def write_plot_html(self, plot_data, data_labels, vr):
        pconfig = {
            'id': 'mummerplot',
            'title': 'nucmer: synteny plot',
            # 'marker_line_colour': 'rgba(0,0,0,0)',
            # 'marker_line_width': 0,
            # 'marker_size': 2,
            'enableMouseTracking': False,
            'square': True,
            'extra_series': {
                'name': 'real_data',
                'dashStyle': 'Dash',
                'data': plot_data,
                'lineWidth': 1,
                'color': '#000000',
                'marker': {'enabled': False},
                'enableMouseTracking': False,
                'showInLegend': False,
            }
        }
        return linegraph.plot(data={'diag':{vr[0]:vr[0], vr[1]:vr[1]}}, pconfig=pconfig)

    def draw_plots(self, plots_hmtl):
        self.add_section(
            anchor='Nucmer',
            description='',
            plot=plots_hmtl
        )
