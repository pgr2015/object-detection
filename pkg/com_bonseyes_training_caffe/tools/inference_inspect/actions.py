from com_bonseyes_base.lib.impl.utils import execute_with_logs
from com_bonseyes_base.lib.api.tool import Context
from com_bonseyes_base.formats.data.data_tensors.api import DataTensorsViewer


def create(context : Context, architecture, weights, dataset: DataTensorsViewer):
    with dataset.view_content() as dataset_path:
        with context.data.edit_content() as output_file:
            # execute python2 inference script with the received data
            execute_with_logs('python2', '-u', 'inference.py', architecture, weights, dataset_path, output_file)
