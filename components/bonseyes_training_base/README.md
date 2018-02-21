Bonseyes base training containers
=====================================

This components contains code that is useful to setup a training
 pipeline.

This component provides some APIs implementation to manage data and
  training:
  
  - import_container.py : an API to import data from an external source 
    to the pipeline in a standardized way
    
  - export_container.py : an API to export standardized data to a HDF5 file
    containing input/output tensors for the neural network trained by the 
    pipeline
    
  - processing_container.py: an API to create a processed view of samples
    imported in the pipeline
    
  - sampling_container.py: an API to create a subset of data create of the
    data imported in the pipeline
    
  - train_validation_split.py: an API to split an exported HDF5 tensor two
    subsets. One for training and one for validation
    
The component also provide a container fully implements the train_validation_split API
for a classification task and creates a validation set that is uniformely distributed 
according.
 
Creating an import container
------------------------------

An import container is responsible extracting data and annotations (labels) from a ZIP file
and store the data in a standardized format. To build a new import container you need
to do the following:

  1. Create a new directory `containers/my_import`
  2. Create a `Dockerfile` in `containers/my_import` with the following contents:

         # derive from the bonseyes-base
         FROM bonseyes-base

         # add framework files to create an import container 
         ADD components/bonseyes_training_base/code /app
         
         # add the custom import code
         ADD containers/my_import /app

  3. Create a `app.py` in `containers/my_import` with the following content and adapt the contents to match your input
     format:
    
         import os
         from zipfile import ZipFile
         
         from bonseyes_training_base.import_container import create_import_app      
         
         # this function must yield one after the other all the samples present in the zip being imported
         # and the corresponding data. The data is the raw version of data that is given as input to the model.
         def data(input_zip):
        
            with ZipFile(input_zip) as z:                                   
                                
                for sample in << list of all samples in the zip >>:                                    
                                        
                    # sample data is an associative array for different pieces of data associated with
                    # the sample and a file-like object from where the data can be read
                    sample_data = {'com.example.data1': z.open(<< get path to data1 for sample >>, 'r'),
                                   'com.example.data2': z.open(<< get path to data2 for sample >>, 'r'),
                                   ... }

                    # sample annotations is an associative array for different labels that are applied
                    # to the sample
                    sample_annotations = {'com.example.medatata1': << get metadata1 for sample >>, 
                                         'com.example.medatata2': << get metadata2 for sample >>,
                                          ... }
        
                    yield sample, sample_data


         DESCRIPTION = "<< description of the container >>"
         
         app = create_import_app(data, DESCRIPTION)     

  4. Add the following to your `docker-compose-build.yml` in the section `services` :
  
         my-project-my-import:
           build:
                context: .
                dockerfile: containers/my_import/Dockerfile
           image: my-project-my-import
           depends_on:
                - bonseyes-base                
                
  5. Add the following to your `docker-compose.yml` in the section `services`:

         my_import:
            image: my-project-my-import
            volumes:
              - my_import:/data
            depends_on:
              - dashboard
              
  6. Add the following to your `docker-compose.yml` in the section `volumes`:
  
         volumes:
            - my-project-my-import
  
  7. Finally you need to edit your pipeline container to include the new container. Find the `app.py` of your pipeline
     and look for the containers parameter of the `create_app` function. Then add the following:
     
         containers = { ... , 'my_import': {'type': CONTAINER_CATEGORY_DATA}}
                        
 
Dataset artifact format
---------------------------

The dataset artifact format has the type 'com.bonseyes.dataset'. Each dataset is a collection of samples, each sample is
composed by a possible input(s) to a model and associated metadata. Each sample has a name, some data (raw input data), 
some views (pre-processed data) and some annotations (metadata).
  
A dataset artifact contains a json file stored under /artifacts/{name}/dataset.json with the following structure:
  
{ 'sample1' : { 'data' : { 'data_type1' : <<value>>, 'data_type2' : <<value>> , ...}
                'views' : { 'view_type1' : <<value>>, 'view_type2' : <<value>> , ... }
                'annotations': {'annotation_type1': <<value>>, 'annotation_type2': <<value>>, ... },
  'sample2' : ... 
}

Views and data values may be relative or absolute urls to the actual payload. Data can for instance be 'sample1/image' 
and can be retrieved at url /artifacts/{name}/sample1/image.
