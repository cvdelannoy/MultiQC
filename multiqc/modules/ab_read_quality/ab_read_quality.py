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
        super(MultiqcModule, self).__init__(name='Raw read qaulity', anchor='read-quality',
        href="",
        info=". Nanoplot was used to derive basic raw read set characteristics and quality messures."
             "Sequencing error rates were estimated by aligning the reads to the reference genome using minimap2.")

        # find and load minimap2 summary files
        self.minimap2_summary = OrderedDict()
        for f in self.find_log_files('ab_read_quality/minimap2'):
            self.parse_minimap2_summary(f)
        if len(self.minimap2_summary ) == 0:
            raise UserWarning
        else:
            log.info("found Minimap2 alignment summary")
            
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
        self.write_data_file(dict(minimap2=self.minimap2_summary, nanostats=self.nanostats_summary),
                             'multiqc_readqual_summary')

        # Table
        self.add_section(
            name="",
            anchor='read-quality',
            description="""Read length and general quality meaures were calculated using NanoStat. 
            Matches, substitutions, deletions and insertions with respect to a given reference, 
            after alignment with Minimap2.""",
            plot=self.ab_read_quality_table()
        )

    def parse_minimap2_summary(self, f):
        f_dict = yaml.load(f['f'])
        block_len = sum(f_dict.values()) * 1.0
        if block_len == 0:
            block_len = 0.000000001  # prevent breaking, but very ugly
        for k in f_dict:
            self.minimap2_summary[k] = dict(absolute=f_dict[k],
                                              relative=f_dict[k] * 1.0 / block_len * 100)
            
    
    def parse_nanostats_summary(self, f):
        f_clean = f['f'].replace('\t', ' ').split('\n')[1:5]
        self.nanostats_summary = yaml.load('\n'.join(f_clean))


    def fuse_summaries(self):
        mm_keys = list(self.minimap2_summary)
        mm_idx = 0
        for k in list(self.nanostats_summary):
            cur_dict = OrderedDict()
            cur_dict['ns_value'] = self.nanostats_summary[k]
            cur_dict['mm_name'] = '<h5><b>' + mm_keys[mm_idx]
            cur_dict['absolute'] = self.minimap2_summary[mm_keys[mm_idx]]['absolute']
            cur_dict['relative'] = self.minimap2_summary[mm_keys[mm_idx]]['relative']
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
