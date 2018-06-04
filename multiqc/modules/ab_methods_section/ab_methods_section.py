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
        self._analysis_tool_versions = None


        # parse files
        self.publication_info = self.find_log_files('ab_methods_section/publication_info')
        self.analysis_tool_versions = self.find_log_files('ab_methods_section/analysis_tool_versions')

        self.pipelines = {}
        for ac in self.find_log_files('ab_methods_section/assembler_commands'):
            self.parse_assembler_command(ac)

        for lf in self.find_log_files('ab_methods_section/log_files'):
            self.parse_logfile(lf)

        if self.publication_info is None:
            raise UserWarning

        out_dict={}
        out_dict['authors'] = self.publication_info['authors']
        out_dict['abstract'] = ("The MinION is a portable DNA sequencer that generates long error-prone reads. "
                                "As both the hardware and analysis software are updated regularly, the most suitable "
                                "pipeline for subsequent analyses of a dataset generated with a given combination of "
                                "hardware and software for a given organism is not always clear. Here we present a "
                                "benchmark for a selection of <i>de novo</i> assemblers available to MinION users, on a"
                                " read set of <i>{organism}</i>. This benchmark is based on a "
                                "<a href=\\>benchmarking routine</a>, designed to facilitate easy replication on a "
                                "read set of choice and addition of other "
                                "<i>de novo</i> assembly pipelines.").format(organism=self.publication_info['organism'])
        out_dict['pipelines'] = ""
        for pl in self.pipelines:
            pipeline = self.pipelines[pl]
            htmltxt = ["<h4>"+ pl.replace("_", " ") +"</h4>" + pipeline['tool_description'], ""]
            version_list = ['<b>Included tools:</b><ul>']
            for tool in pipeline['version_info']:
                version_list.append("<li>" + tool + " (version: " + pipeline['version_info'][tool] + ") </li>")
            version_list.append("</ul>")
            htmltxt.append(''.join(version_list))
            htmltxt.append("<b>Used command:</b><pre><code>"+pipeline['command']+"</code></pre>")
            out_dict['pipelines'] += "<br>&zwnj;".join(htmltxt)
        out_dict['readset_quality'] = ("Reads in this dataset were generated on a Minion with {flowcell} flowcell with "
                                       "{kit} kit. The reads were basecalled using {basecaller}. Prior to assembly, "
                                       "the quality of the untreated readset was analysed using NanoPlot "
                                       "(version: {nanoplot}) and mapped using Minimap2 (version: "
                                       "{minimap2}).").format(flowcell=self.publication_info['flowcell'],
                                                              kit=self.publication_info['kit'],
                                                              basecaller=self.publication_info['basecaller'].replace('_', ' '),
                                                              nanoplot=self.analysis_tool_versions['Nanoplot'],
                                                              minimap2=self.analysis_tool_versions['Minimap2'])
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
            content=out_dict  # + self.methods
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
        fdict = list(f)
        if len(fdict) > 1:
            print(fdict)
            log.error('More than one publication info file found!')
            return
        if len(fdict) == 0:
            log.error('No publication info file found!')
            return
        fdict = fdict[0]
        self._publication_info = {}
        for kv in fdict['f'].split('\n'):
            if not len(kv):
                continue
            k, v = kv.split('=')
            self._publication_info[k] = v.strip('"')

    @analysis_tool_versions.setter
    def analysis_tool_versions(self, f):
        fdict = list(f)
        if len(fdict) > 1:
            print(fdict)
            log.error('More than one analysis tool versions file found!')
            return
        if len(fdict) == 0:
            log.error('No analysis tool versions file found!')
            return
        self._analysis_tool_versions = yaml.load(fdict[0]['f'])

    def parse_assembler_command(self, f):
        # TODO: Version info derived from commands added later! (which is ugly and hacky)
        # TODO: this entire parsing thing is in dire need of rewriting anyway

        tool_description = re.search("# TOOL DESCRIPTION.+(?=VERSIONS---)(?s)", f['f'])
        if tool_description:
            tool_description = tool_description.group(0)
            tool_description = tool_description.replace('#', '').split('\n')[1:]
            tool_description = ''.join(tool_description).strip()
        else:
            tool_description = "No description available"

        version_info = re.search("# VERSIONS.+(?=COMMANDS)(?s)", f['f'])
        if version_info:
            version_info = version_info.group(0)
            version_info = re.findall('(?<=#).+:.+', version_info)
            version_info = '\n'.join([vi.strip() for vi in version_info])
            version_info = yaml.load(version_info)
        else:
            version_info = {}

        command = re.search("# COMMANDS-------.+(?s)", f['f'])
        if command:
            command = command.group(0)
            command = '\n'.join(command.split('\n')[1:]).strip()
        else:
            command = 'No command in script or not parsed. Check files in assembler_scripts folder.'

        fn = splitext(f['fn'])[0]
        self.pipelines[fn] = {
            'tool_description': tool_description,
            'version_info': version_info,
            'command': command
        }

    def parse_logfile(self, f):
        """
        Parse the log files generated during assembler running. Only automatically found version info is
        retrieved here.
        """
        pipeline_name = splitext(f['fn'])[0]
        cur_pipeline = self.pipelines[pipeline_name]
        version_dict = cur_pipeline.get('version_info')

        ac_tool_list = list(version_dict) # previously composed list of tools

        version_text = re.search("(?<=START AUTO VERSION PRINTING\n).+(?=END AUTO VERSION PRINTING)(?s)", f['f'])
        if not version_text:
            log.warning('No version information found for pipeline {pl}. Skipping'.format(pl=pipeline_name))
            return
        version_text = version_text.group(0)
        version_text_list = version_text.strip('\n').split('\n')
        tool_list = []
        version_list = []
        for item in version_text_list:
            if item[0] == "#":
                tool_list.append(item[1:].strip())
            else:
                version_list.append(item)
        if len(tool_list) != len(version_list):
            log.error('The assembler log file does not seem to contain equal numbers of versions and tool names')
            raise UserWarning

        for t, v in zip(tool_list, version_list):
            if t in ac_tool_list:
                version_dict[t] = v
            else:
                log.warning('Tool {} is in assembler log file for pipeline {}, but not in command file. Skipping...'
                            .format(t, pipeline_name))
        self.pipelines[pipeline_name]['version_info'] = version_dict
