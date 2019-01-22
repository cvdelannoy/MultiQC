from multiqc.modules.base_module import BaseMultiqcModule
from multiqc.plots import table
import logging
import csv
from collections import OrderedDict

# Initialise the logger
log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):
    def __init__(self):
        # Initialise the parent object
        super(MultiqcModule, self).__init__(name='CPU usage', anchor='ab-cpu-times',
        href="https://www.github.com/cvdelannoy/MinION_assembler_benchmark",
        info="was monitored during runs using the psutil package in Python3. Reported here are CPU time and memory usage"
             "(proportional and unique set size, PSS and USS respectively).")

        # find and load data
        self.cpu_usage = self.find_log_files('ab_cpu_times')

        # Plot table
        cpu_table = table.plot(data=self.cpu_usage)

        self.add_section(
            anchor='ab-cpu-times',
            description='',
            content=cpu_table
        )

        # Add to main table
        self.general_stats_addcols(self.cpu_usage_gs)

        # Write data to file
        self.write_data_file(self.cpu_usage, 'cpu_usage')

    @property
    def cpu_usage_gs(self):
        return self._cpu_usage_gs

    @property
    def cpu_usage(self):
        return self._cpu_usage

    @cpu_usage.setter
    def cpu_usage(self, f):
        # cur_cpu_times_dict = yaml.load(f['f'])
        list_f = list(f)
        if len(list_f) == 0:
            log.error('No CPU resources files!')
            raise UserWarning
        log.info('found CPU resource files')
        cpu_dict = dict()
        cpu_dict_gs = dict()
        for fc in list_f:
            cpu_list = list(csv.reader(fc['f'].split('\n'), delimiter='\t'))
            cpu_dict_cur = OrderedDict()
            cpu_dict_order = dict()
            cpu_dict_gs_cur = dict()
            for k, v in zip(cpu_list[0], cpu_list[1]):
                if k == 'h:m:s':
                    cpu_dict_cur['Wall time'] = v
                    cpu_dict_gs_cur['Wall time'] = v
                    cpu_dict_order[1] = 'Wall time'
                elif k == 'max_pss':
                    cpu_dict_cur['peak PSS (MB)'] = float(v)
                    cpu_dict_gs_cur['peak CPU usage (PSS) (MB)'] = float(v)
                    cpu_dict_order[2] = 'peak PSS (MB)'
                elif k == 'max_uss':
                    cpu_dict_cur['peak USS (MB)'] = float(v)
                    cpu_dict_order[3] = 'peak USS (MB)'
                elif k == 'mean_load':
                    cpu_dict_cur['mean CPU load (MB)'] = float(v)
                    cpu_dict_order[4] = 'mean CPU load (MB)'
                elif k == 'io_in':
                    cpu_dict_cur['I/O in (MB/s)'] = float(v)
                    cpu_dict_order[5] = 'I/O in (MB/s)'
                elif k == 'io_out':
                    cpu_dict_cur['I/O out (MB/s)'] = float(v)
                    cpu_dict_order[6] = 'I/O out (MB/s)'
            # enforce order in dict
            cpu_list_order = list(cpu_dict_order)
            cpu_list_order.sort()
            for n in cpu_list_order:
                cpu_dict_cur.move_to_end(cpu_dict_order[n])
            cpu_dict[fc['s_name']] = cpu_dict_cur
            cpu_dict_gs[fc['s_name']] = cpu_dict_gs_cur
        self._cpu_usage = cpu_dict
        self._cpu_usage_gs = cpu_dict_gs
