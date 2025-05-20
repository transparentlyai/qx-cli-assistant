# src/qx/tools/file_operations_base.py
# This file previously contained the `is_path_allowed` function.
# This function has been duplicated into the relevant plugins:
# - src/qx/plugins/read_file_plugin.py
# - src/qx/plugins/write_file_plugin.py
# to make them more standalone.
#
# This file is now obsolete and can be deleted.

import logging

logger = logging.getLogger(__name__)
logger.info("file_operations_base.py is obsolete. 'is_path_allowed' is now part of individual file operation plugins.")
