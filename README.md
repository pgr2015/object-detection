
###How to clone repository

```
git clone git@bitbucket.org:bonseyes/wp3-project-objectdetection.git develop --recursive
```
###Configuration

Pack, training and benchmarking require access to a nVidia card, you need to map your card inside the container with a execution config.yml like the following:

```
application_config:
  run_opts:
    devices:
      - /dev/nvidiactl
      - /dev/nvidia-uvm-tools
      - /dev/nvidia-uvm
      - /dev/nvidia0
    volumes:  
      nvidia_driver_384.111:
        bind: /usr/local/nvidia
        mode: ro
```

You also has the option to have your raw datasets downloaded in your computer and connet them to the import container. To do that, you need to create a a docker volume that contains the raw datasets
To create this container you need to do the following:
1) Create a directory that will store the data 2) Copy the raw data in the directory 3) Modify the execution config.yml file adding a volume bound to the directory in each container:

```
     application_config:
       run_opts:             
         volumes:
           "/path/to/directory":
             bind: /volumes/data
             mode: ro
```

The exact name of the `nvidia_driver` volume can be found with the following command:

```
docker volumes ls | grep nvidia
```

###How to run the import for training

To import the youtube dataset for training you can use the following command:
```
pkg/com_bonseyes_base/bin/be-admin run --name import_data_training --config config.yml --force workflows/import_data.yml
```
In the `workflows/import_data.yml` file the user can establish the url where the dataset is uploaded (parameter `images` for image dataset and parameter labels for csv).

###How to run the import for benchmarking

To import the youtube dataset for benchmarking you can use the following command:
```
pkg/com_bonseyes_base/bin/be-admin run --name import_data_benchmark --config config.yml --force workflows/import_data.yml
```

In the `workflows/import_data.yml` file the user can establish the url where the dataset is uploaded (parameter `images` for image dataset and parameter labels for csv).

###Pack Training

To pack the imported images in the import for training step you can use the following command:

```
pkg/com_bonseyes_base/bin/be-admin run --name packTraining --config config.yml --force workflows/pack_data.yml --param raw_dataset execution-output local: import_data_training raw_dataset
```


###Export benchmark

To pack the imported images in the import for benchmarking step you can use the following command:
```
pkg/com_bonseyes_base/bin/be-admin run --name packBenchmark --config config.yml --force workflows/pack_data.yml --param raw_dataset execution-output local: import_data_benchmark raw_dataset
```


###Training Caffe SSD + MobileNet
To train a model with SSD + MobileNet you can use the following command:

```
pkg/com_bonseyes_base/bin/be-admin run workflows/train_data.yml --name training_v4 --force --config config.yml --param training_set execution-output local: packTraining training_set
```

In the `workflows/train_data.yml` file the user can establish the number of `epochs` (parameter epochs). By default, epochs = 28000

###Training CaffeBonseyes

To train a model with CaffeBonseyes you can use the following command:

```
pkg/com_bonseyes_base/bin/be-admin run workflows/train_data_CaffeBonseyes.yml --name training_CaffeBonseyes --force --config config.yml --param model execution-output local: training_v4 model --param training_set execution-output local: packTraining training_set
```

In the `workflows/train_data_CaffeBonseyes.yml` file the user can change the number of `epochs` (parameter epochs). By default, epochs = 28000.


###Benchmark
To benchmark a model with Caffe you can use the following command:

```
pkg/com_bonseyes_base/bin/be-admin run workflows/benchmark_data.yml --name benchmark_v4 --config config.yml --force --param model execution-output local: training_v4 model --param training_set execution-output local: packBenchmark training_set
```
In the `workflows/benchmark_data.yml` file, the user can change the number of `epochs` (parameter epochs). By default, epochs = 20000

###Benchmark CaffeBonseyes
To benchmark a model with CaffeBonseyes you can use the following command:

```
pkg/com_bonseyes_base/bin/be-admin run workflows/benchmark_data_CaffeBonseyes.yml --name benchmark_CaffeBonseyes --config config.yml --force --param model execution-output local: training_CaffeBonseyes model --param training_set execution-output local: packBenchmark training_set
```

In the `workflows/benchmark_data_CaffeBonseyes.yml` file, the user can change the number of ==epochs== (parameter epochs). By default, epochs = 20000

###Pipeline with Caffe SSD + MobileNet

To run a full pipeline with Caffe SSD + MobileNet you can use the following command:

```
pkg/com_bonseyes_base/bin/be-admin run --name pipeline_v4 --config config.yml --force workflows/pipeline.yml
```

In the `workflows/pipeline.yml` file the user can establish the following parameters:
- The image dataset and the labels file (csv) for training
- The image dataset and the labels file (csv) for benchmarking.
- Epochs for training with SSD + MobileNet
- Epochs for benchmark with SSD + MobileNet

###Pipeline with CaffeBonseyes
To run a full pipeline with Caffe SSD + MobileNet and CaffeBonseyes you can use the following command:

```
pkg/com_bonseyes_base/bin/be-admin run --name pipeline_CaffeBonseyes --config config.yml --force workflows/pipeline_CaffeBonseyes.yml
```

In the `workflows/pipeline.yml` file the user can establish the following parameters:
- The image dataset and the labels file (csv) for training
- The image dataset and the labels file (csv) for benchmarking.
- Epochs for training with SSD + MobileNet
- Epochs for training with CaffeBonseyes
- Epochs for benchmark with CaffeBonseyes


