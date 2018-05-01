#!/bin/bash

set -x
set -e

be-admin execution create train_mnist --workflow ./pkg/com.bonseyes.training.caffe/workflows/train.yml \
                        --model_architecture pkg/com.bonseyes.training.caffe/tests/assets/mnist/lenet_train_test.prototxt \
                        --test_dataset pkg/com.bonseyes.training.caffe/tests/assets/mnist/images.h5 \
                        --dataset pkg/com.bonseyes.training.caffe/tests/assets/mnist/images.h5 \
                        --solver_config pkg/com.bonseyes.training.caffe/tests/assets/mnist/lenet_solver.prototxt \
                        --log --force

be-admin execution artifact train_mnist save train caffe_model --output-file caffe_model.tar

echo "Press enter to finish...."
read

be-admin execution resume train_mnist