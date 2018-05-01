Bonseyes base training containers
=====================================

This components contains code that is useful to setup a training pipeline.

This component provides some APIs implementation to manage data and training:

  - dataset_parallelize_process.py : an API to parallelize read and process of samples in datasets

  - import_helper.py : an API to import data from an external source to the 
    pipeline in a standardized way

  - export_helper.py : an API to export standardized data to a HDF5 file
    containing input/output tensors for the neural network trained by the 
    pipeline

  - processing_helper.py: an API to create a processed view of samples
    imported in the pipeline

  - sampling_helper.py: an API to create a subset of data create of the
    data imported in the pipeline


Dataset artifact format
---------------------------

The dataset artifact format has the type 'com.bonseyes.dataset'. Each dataset is a collection of samples, each sample is
composed by a possible input(s) to a model and associated metadata. Each sample has a name, some data (raw input data), 
some views (pre-processed data) and some annotations (metadata).
  
A dataset artifact contains a json file stored the at the url

/artifacts/{artifact_name}/v/{version_name}/data/dataset.json

with the following structure:
  
{ 'sample1' : { 'data' : { 'data_type1' : <<value>>, 'data_type2' : <<value>> , ...}
                'views' : { 'view_type1' : <<value>>, 'view_type2' : <<value>> , ... }
                'annotations': {'annotation_type1': <<value>>, 'annotation_type2': <<value>>, ... },
  'sample2' : ... 
}

Views and data values may be relative or absolute urls to the actual payload. Data can for instance be 'sample1/image' 
and can be retrieved at url /artifacts/{artifact_name}/v/{version_name}/data/sample1/image.
