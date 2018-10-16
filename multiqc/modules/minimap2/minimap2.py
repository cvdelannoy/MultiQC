from multiqc.modules.base_module import BaseMultiqcModule
from multiqc.plots import scatter
import logging
import csv

# Initialise the logger
log = logging.getLogger(__name__)

class MultiqcModule(BaseMultiqcModule):
    def __init__(self):
        # Initialise the parent object
        super(MultiqcModule, self).__init__(
            name='Alignment plots', anchor='alignmentplot-module',
            href="",
            info="were based on an alignment made using minimap2.")

        # find and load files
        self.plot_data = []
        self.data_labels = []
        self.max_coord = 0
        for f in self.find_log_files('minimap2', filehandles=True):
            plot_coords, max_coord = self.plotfile_to_list(f['f'])
            if len(plot_coords):
                self.plot_data.append({f['s_name']: plot_coords})
                self.data_labels.append({'name': f['s_name'][15:],
                                         'xlab': 'reference',
                                         'ylab': f['s_name'][15:]})
                self.max_coord = max(self.max_coord, max_coord)

        if not self.plot_data:
            raise UserWarning
        else:
            log.info("found minimap2 coord files")
        self.make_plots()

    def plotfile_to_list(self, pf):
        step_size = 10000
        lines_dict = {}
        lines_list = []
        points_list = []
        max_val = 0
        reader = csv.reader(pf, dialect='excel-tab')
        next(reader)
        for row in reader:
            if len(row) < 5:
                continue
            x_start, x_stop, y_start, y_stop = [int(r) for r in row[:4]]
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
                y_points[i] = y_start + dydx * (xc - x_start) + x_start
            cur_points_list = [{'x': x, 'y': y, 'color': color} for x, y in
                               zip(x_points, y_points)]
            points_list.extend(cur_points_list)
            lines_dict[x_start] = y_start
            lines_dict[x_stop] = y_stop
            max_val = max(max_val, y_start, y_stop, x_start, x_stop)
            lines_list.append({x_start: y_start,
                               x_stop: y_stop})
        return points_list, max_val

    def make_plots(self):
        pconfig = {
            'id': 'contig_alignment_plot',
            'title': 'Contig alignment plot',
            # 'marker_line_colour': 'rgba(0,0,0,0)',
            'marker_line_width': 0,
            'marker_size': 2,
            'enableMouseTracking': False,
            'square': True,
            'data_labels': self.data_labels,
            'xmin': 0,
            'ymin': 0,
            'xmax': self.max_coord,
            'ymax': self.max_coord
        }

        self.add_section(
            anchor='contig_alignment_plots',
            description='',
            plot=scatter.plot(data=self.plot_data, pconfig=pconfig)
        )
