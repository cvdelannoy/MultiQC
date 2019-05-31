from multiqc.modules.base_module import BaseMultiqcModule
from os.path import splitext
import logging
import yaml
import re


# Initialise the logger
log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):
    def __init__(self):
        # Initialise the parent object
        super(MultiqcModule, self).__init__(anchor='ab_methods_section',
        info="")

        self._publication_info = None
        self._analysis_tool_versions = dict()
        self.pipelines = dict()
        self.commands = dict()

        # --- parse files ---
        self.publication_info = self.find_log_files('ab_methods_section/publication_info')
        self.analysis_tool_versions = self.find_log_files('ab_methods_section/analysis_tool_versions')
        for lf in self.find_log_files('ab_methods_section/log_files'):
            self.parse_logfile(lf)
        for lf in self.find_log_files('ab_methods_section/cmd_files'):
            self.parse_cmdfile(lf)

        # --- construct HTML text ---
        out_dict = dict()
        out_dict['authors'] = self.publication_info['authors']
        out_dict['abstract'] = ("The MinION is a portable DNA sequencer that generates long error-prone reads. "
                                "As both the hardware and analysis software are updated regularly, the most suitable "
                                "pipeline for subsequent analyses of a dataset generated with a given combination of "
                                "hardware and software for a given organism is not always clear. Here we present a "
                                "benchmark for a selection of <i>de novo</i> assemblers available to MinION users, on a"
                                " read set of <i>{spec_name}</i> (NCBI taxID: {taxid}). This benchmark is based on a "
                                "<a href=\\>benchmarking routine</a>, designed to facilitate easy replication on a "
                                "read set of choice and addition of other <i>de novo</i> assembly pipelines."
                                ).format(spec_name=self.publication_info['species_name'],
                                         taxid=self.publication_info['taxid'])

        out_dict['pipelines'] = ""
        for pl in self.pipelines:
            pipeline = self.pipelines[pl]
            htmltxt = ["<h4>"+ pl.replace("_", " ") +"</h4>" + pipeline['description'], ""]
            version_list = ['<b>Included tools:</b><ul>']
            for tool in pipeline['versions']:
                version_list.append("<li>" + tool + " (version: " + str(pipeline['versions'][tool]) + ") </li>")
            version_list.append("</ul>")
            htmltxt.append(''.join(version_list))
            command = self.commands.get(pl)
            if not command:
                command = 'COMMAND NOT FOUND!'
            htmltxt.append("<b>Used command:</b><pre><code>" + command + "</code></pre>")
            out_dict['pipelines'] += "<br>&zwnj;".join(htmltxt)

        out_dict['readset_quality'] = ("Reads in this dataset were generated on a Minion with {flowcell} flowcell with "
                                       "{kit} kit. The reads were basecalled using {basecaller}. Prior to assembly, "
                                       "the quality of the untreated readset was analysed using NanoPlot "
                                       "(version: {nanoplot}) and mapped using the mappy module (version: "
                                       "{mappy}) in Python3.").format(flowcell=self.publication_info['flowcell'],
                                                              kit=self.publication_info['kit'],
                                                              basecaller=self.publication_info['basecaller'].replace('_', ' '),
                                                              nanoplot=self.analysis_tool_versions.get('Nanoplot', 'Not performed; requires fastq reads'),
                                                              mappy=self.analysis_tool_versions['Mappy'])
        out_dict['assembly_quality'] = ("Produced assemblies were analyzed and compared on continuity and agreement "
                                        "with the reference genome. Quast (version: {quast}) was used to determine a "
                                        "wide array of quality metrics in both quality categories and produce synteny "
                                        "plots. To elucidate any bias in the occurence of certain sequences, 5-mers in "
                                        "the assemblies and the reference genomes were compared using Jellyfish "
                                        "(version: {jellyfish}). Finally, results were summarized "
                                        "using MultiQC.").format(quast=self.analysis_tool_versions['Quast'],
                                                                 jellyfish=self.analysis_tool_versions['Jellyfish'])

        self.add_section(
            anchor='methods',
            description='',
            content=out_dict
        )
        self.write_data_file(out_dict, 'ab_methods')

    @property
    def publication_info(self):
        return self._publication_info

    @property
    def analysis_tool_versions(self):
        return self._analysis_tool_versions

    @publication_info.setter
    def publication_info(self, f):
        flist = list(f)
        if len(flist) > 1:
            print(flist)
            log.error('More than one publication info file found!')
            return
        elif len(flist) == 0:
            log.error('No publication info file found!')
            return
        self._publication_info = yaml.load(flist[0]['f'])

    @analysis_tool_versions.setter
    def analysis_tool_versions(self, f):
        flist = list(f)
        if len(flist) > 1:
            print(flist)
            log.error('More than one analysis tool versions file found!')
            return
        if len(flist) == 0:
            log.error('No analysis tool versions file found!')
            return
        self._analysis_tool_versions = yaml.load(flist[0]['f'])

    def parse_logfile(self, f):
        """
        Parse the log files generated during assembler running.
        """
        info_match = re.search("(?<=START METHODS PRINTING\n).+(?=END METHODS PRINTING)(?s)", f['f'])
        if info_match is None:
            log.warning('no methods information found in {}, skipping').format(f['fn'])
        else:
            self.pipelines[f['s_name']] = yaml.load(info_match.group(0))

    def parse_cmdfile(self, f):
        """
        Parse the cmd files generated during assembler running, containing the commands used per assembler.
        """
        self.commands[f['s_name']] = f['f']
