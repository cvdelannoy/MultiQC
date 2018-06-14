from multiqc.modules.base_module import BaseMultiqcModule
from multiqc.plots import twocol_table
from collections import OrderedDict
import logging
import yaml

# Initialise the logger
log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):
    def __init__(self):
        # Initialise the parent object
        super(MultiqcModule, self).__init__(name='Raw read quality', anchor='read-quality',
        href="",
        info="was assessed assessed in two ways; Nanoplot was used to derive basic raw read set characteristics "
             "and quality messures. Then, sequencing error rates were estimated by aligning the reads to the "
             "reference genome using mappy (Minimap2).")

        self._alignment_summary = None



        # find and load alignment summary
        self.alignment_summary = self.find_log_files('ab_read_quality/alignment_summary')
            
        # find and load nanostats summary files
        self.nanostats_summary = OrderedDict()
        for f in self.find_log_files('ab_read_quality/nanostats'):
            self.parse_nanostats_summary(f)
        if len(self.nanostats_summary) == 0:
            raise UserWarning
        else:
            log.info("found nanostats file")

        # Fuse summary dicts
        self.ab_read_quality_measures = OrderedDict()
        self.fuse_summaries()


        # write parsed data to file
        self.write_data_file(dict(minimap2=self.alignment_summary, nanostats=self.nanostats_summary),
                             'multiqc_readqual_summary')

        # Table
        self.add_section(
            name="",
            anchor='read-quality',
            plot=self.ab_read_quality_table()
        )

    @property
    def alignment_summary(self):
        return self._alignment_summary

    @alignment_summary.setter
    def alignment_summary(self, f):
        f_list = list(f)
        if len(f_list) > 1:
            log.error('More than 1 alignment summary file found!')
            raise UserWarning
        elif len(f_list) == 0:
            log.error('No alignment summary file found!')
            raise UserWarning
        out_dict = dict()
        f_dict = yaml.load(f_list[0]['f'])
        basecount_cats = ['matches', 'mismatches', 'deletions', 'insertions']
        f_dict_basecounts = {bc: f_dict[bc] for bc in basecount_cats}
        block_len = sum(f_dict_basecounts.values()) * 1.0
        if block_len == 0:
            block_len = 0.000000001  # prevent breaking, but very ugly
        for k in basecount_cats:
            out_dict[k] = dict(absolute=f_dict_basecounts[k],
                               relative=f_dict_basecounts[k] * 1.0 / block_len * 100)
        self._alignment_summary = out_dict
        # # TODO
        # self._mapping_quality = f_dict['mapping_quality']
        # self._nb_mappings = f_dict['mapping_quality']

    #
    # def parse_minimap2_summary(self, f):
    #     f_dict = yaml.load(f['f'])
    #     block_len = sum(f_dict.values()) * 1.0
    #     if block_len == 0:
    #         block_len = 0.000000001  # prevent breaking, but very ugly
    #     for k in f_dict:
    #         self.minimap2_summary[k] = dict(absolute=f_dict[k],
    #                                           relative=f_dict[k] * 1.0 / block_len * 100)
            
    
    def parse_nanostats_summary(self, f):
        f_clean = f['f'].replace('\t', ' ').split('\n')[1:5]
        self.nanostats_summary = yaml.load('\n'.join(f_clean))


    def fuse_summaries(self):
        mm_keys = list(self.alignment_summary)
        mm_idx = 0
        for k in list(self.nanostats_summary):
            cur_dict = OrderedDict()
            cur_dict['ns_value'] = self.nanostats_summary[k]
            cur_dict['mm_name'] = '<h5><b>' + mm_keys[mm_idx]
            cur_dict['absolute'] = self.alignment_summary[mm_keys[mm_idx]]['absolute']
            cur_dict['relative'] = self.alignment_summary[mm_keys[mm_idx]]['relative']
            self.ab_read_quality_measures[k] = cur_dict
            mm_idx += 1

        # ns_keys = self.nanostats_summary.keys()
        # ns_idx = 0
        # for k in self.minimap2_summary.keys():
        #     cur_dict = self.minimap2_summary[k]
        #     cur_dict['ns_name'] = '<h5><b>' + ns_keys[ns_idx]
        #     cur_dict['ns_value'] = self.nanostats_summary[ns_keys[ns_idx]]
        #     self.ab_read_quality_measures[k] = cur_dict
        #     ns_idx += 1


    def ab_read_quality_table(self):
        headers = OrderedDict()
        headers['ns_value'] = {
            'title': 'Value',
            'description': 'metric value'
        }
        headers['mm_name'] = {
            'title': ' ',
            'description': 'metric name'
        }
        headers['absolute'] = {
            'title': 'N',
            'min': '0',
            'scale': 'RdYlGn',
            'format': '{:.2e}',
            'description': 'Base counts of each alignment category'
        }
        headers['relative'] = {
            'title': '%',
            'min': '0',
            'max': '100',
            # 'format': '{0:.0f}',
            'description': 'Fraction of total block alignment length'
        }
        config = {
            'id': 'ab_read_quality_table',
            'namespace': 'ab_read_quality_table'
        }

        return twocol_table.plot(self.ab_read_quality_measures, headers, config)
