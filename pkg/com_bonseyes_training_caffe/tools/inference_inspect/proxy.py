from com_bonseyes_base.lib.api.proxy import Proxy
from com_bonseyes_base.lib.api.tool import Artifact
from com_bonseyes_base.lib.impl.values.memory_values import ResourceValue


class CaffeInferenceInspect(Proxy):

    @staticmethod
    def _get_manifest_name() -> str:
        return 'pkg/com_bonseyes_training_caffe/tools/inference_inspect/manifest.yml'

    def create(self, architecture: ResourceValue, weights: ResourceValue, dataset: ResourceValue) -> Artifact:
        return self._create_artifact({
            "architecture": architecture,
            "weights" : weights,
            "dataset": dataset
        })
