from multiqc.modules.base_module import BaseMultiqcModule
from collections import OrderedDict
import logging
import yaml
import datetime

# Initialise the logger
log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):
    def __init__(self):
        # Initialise the parent object
        super(MultiqcModule, self).__init__(name='assembler benchmark CPU times', anchor='ab-cpu-times',
        href="https://www.github.com/cvdelannoy/MinION_assembler_benchmark",
        info="is a tiny custom module to parse a yaml file containing CPU running times of several toosl included in"
             "a de novo assembler benchmarking tool")

        # find and load data
        self.cpu_times_dict = OrderedDict()
        for f in self.find_log_files('ab_cpu_times'):
            self.parse_files(f)
        if len(self.cpu_times_dict ) == 0:
            raise UserWarning
        else:
            log.info("found {} CPU time entries".format(len(self.cpu_times_dict)))

        # Add to main table (anything else not necessary)
        self.general_stats_addcols(self.cpu_times_dict)


    def parse_files(self, f):
        cur_cpu_times_dict = yaml.load(f['f'])
        for k in cur_cpu_times_dict.keys():
            if k in self.cpu_times_dict:
                log.debug('Found a second entry of CPU times for {}. Overwriting...'.format(k))
            cpu_time = str(datetime.timedelta(seconds=cur_cpu_times_dict[k]))
            self.cpu_times_dict[k] = {'CPU time': cpu_time}
