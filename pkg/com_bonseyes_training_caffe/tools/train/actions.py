import os
from bonseyes.tool.utils import execute_with_logs
import google.protobuf.text_format as txtf
import h5py
import caffe_pb2


def convert_to_caffe_format(data_file, output_file):
    data = h5py.File(data_file, 'r')
    data_caffe = h5py.File(output_file, 'w')
    data_caffe.create_dataset("data", data['input'].shape)
    data_caffe.create_dataset("label", data['output'].shape)
    data_caffe["data"][:] = data['input']
    data_caffe["label"][:] = data['output']
    data.close()


def create_proto(input_file, output_file, hdf5_path, test_hdf5_path):
    net = caffe_pb2.NetParameter()

    with open(input_file) as f:
        s = f.read()
        txtf.Merge(s, net)
    # TODO Remove the change in the type and provide an input proto already in H5_caffe_format
    # Here the input proto should not contain any data_param or image_data_param field either in train or test
    for layer in net.layer:
        if layer.type == "Data" or layer.type == "ImageData":
            layer.type = "HDF5Data"
            if not layer.include[0].phase:
                layer.hdf5_data_param.source = output_file + "_train.txt"
                layer.hdf5_data_param.batch_size = 2
            else:
                layer.hdf5_data_param.source = output_file + "_test.txt"
                layer.hdf5_data_param.batch_size = 2
    # Write files where the paths of the hdf5 data will be
    with open(output_file + "_test.txt", 'w') as f:
        f.write(test_hdf5_path)
    with open(output_file + "_train.txt", 'w') as f:
        f.write(hdf5_path)
    # Write the changed proto
    with open(output_file, 'w') as f:
        f.write(str(net))


def create_solver(input_proto, solver_config, output_file, output_dir):
    with open(output_file, 'w') as f:
        for line in open(solver_config):
            # Change the snapshot_prefix to dump the files in the appropriate path
            if 'snapshot_prefix:' in line:
                f.write("snapshot_prefix: \"" + output_dir + "/\"" + "\n")
            elif 'net:' in line:
                f.write("net: \"" + input_proto + "\"" + "\n")
            else:
                f.write(line)


def create(version, model_architecture, test_dataset, dataset, solver_config):
    data_directory = version.create_data_directory()

    with version.internal_data.edit() as tmp_dir, \
            data_directory.edit() as output_dir:
        # Train dataset
        caffe_h5_path = os.path.join(tmp_dir, 'caffe.h5')
        convert_to_caffe_format(dataset, caffe_h5_path)

        # Test dataset
        caffe_h5_path_test = os.path.join(tmp_dir, 'test_caffe.h5')
        convert_to_caffe_format(test_dataset, caffe_h5_path_test)

        train_prototxt = os.path.join(tmp_dir, 'model_h5.prototxt')
        create_proto(model_architecture, train_prototxt, caffe_h5_path, caffe_h5_path_test)

        real_solver_config_path = os.path.join(tmp_dir, 'solver.prototxt')
        create_solver(train_prototxt, solver_config, real_solver_config_path, output_dir)
        # TODO add support of multi_gpu use
        execute_with_logs('/opt/caffe/build/tools/caffe', 'train', '--solver=' + real_solver_config_path, '--gpu', '0')
