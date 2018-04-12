"""
=============
 assembler_benchmark
=============

Custom template for assembler benchmark reports

"""
import os
from multiqc.utils import config

template_parent = 'default'

# base64_plots = False

template_dir = os.path.dirname(__file__)
base_fn = 'base.html'

output_subdir = 'multiqc_report'
# copy_files = ['assets']

# This has already been done in the main script, do now if it was false
# if not config.export_plots:
#     tmp_dir = config.data_tmp_dir.rstrip('multiqc_data')
#     config.plots_tmp_dir = os.path.join(tmp_dir, 'multiqc_plots')
#     config.plots_dir = config.plots_tmp_dir
#     if not os.path.exists(config.plots_dir):
#         os.makedirs(config.plots_dir)
# config.export_plots = True
