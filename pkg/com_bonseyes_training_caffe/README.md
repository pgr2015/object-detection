Bonseyes Training Caffe Tools
==========================================

This package contains the following tool:

  - train: performs training with BVLC/caffe


# Example of use for Mnist data:

- First put the required files for the training in pkg/com.bonseyes.training.caffe/tests/assets/mnist :
    - The images in h5 lpdnn format
    - the train/test prototxt (without data_param field, SEE CODE pkg/com.bonseyes.training.caffe/tools/action.py)
    - solver.prototxt
- Then fix the paths in `./pkg/com.bonseyes.training.caffe/scripts/train.sh` and run the following :

- First build images using : `./pkg/com.bonseyes.training.caffe/scripts/build.sh`
- Then run training `./pkg/com.bonseyes.training.caffe/scripts/train.sh`

The final caffemodel snapshots will be dumped as a tar file in pkg/

