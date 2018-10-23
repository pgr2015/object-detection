
class Generator():

    def __init__(self, train_path):
      self.first_prior = True
      self.filepath = train_path
      self.quantize = False

    def header(self, name):
        with open(self.filepath, 'w') as f:
            f.write("name: \"%s\"" % name)

    def quantizeNet(self):
        if self.quantize:
            with open(self.filepath, 'a') as f:
                f.write("quantize: true\n")

    def data_deploy(self):
        with open(self.filepath, 'a') as f:
            f.write(
"""
input: "data"
input_shape {
  dim: 1
  dim: 3
  dim: %d
  dim: %d
}
""" % (self.input_size, self.input_size))

    def data_train_classifier(self):
        with open(self.filepath, 'a') as f:
            f.write(
"""
layer {
    name: "data"
    type: "Data"
    top: "data"
    top: "label"
    include: { phase: TRAIN }
    data_param{
      source: "%s"
      backend: LMDB
      batch_size: %s
    }
    transform_param {
      crop_size: %s
	  mean_value: 127.5
      mirror: true
    }
}

"""%(self.lmdb,self.batch,self.input_size))


    def data_test_classifier(self):
        with open(self.filepath,'a') as f:
            f.write(
"""
layer {
    name: "data"
    type: "Data"
    top: "data"
    top: "label"
    include: { phase: TEST }
    data_param{
      source: "%s"
      backend: LMDB
      batch_size: %s
    }
    transform_param {
      crop_size: %s
      mean_file: 127.5
      mirror: true
    }
}
"""%(self.lmdb,self.batch,self.input_size))

    def conv(self, name, top, out, kernel, pad, stride, bottom=None):
        bias_lr_mult = ""
        weight_lr_mult = ""
        bias_filler = ""
        weight_filler = ""
        if self.stage == "test" or self.stage == "train":
            bias_filler = """
    bias_filler {
      type: "constant"
      value: 0.2
    }
"""
            bias_lr_mult = """
  param {
    lr_mult: 1.0
    decay_mult: 1.0
  }
"""
            weight_lr_mult = """
  param {
    lr_mult: 2.0
    decay_mult: 0.0
  }
"""
            weight_filler = """
  weight_filler {
    type: "xavier"
  }            
"""
        with open(self.filepath, 'a') as f:
            f.write(
"""layers {
  name: "%s"
  type: "Convolution"
  bottom: "%s"
  top: "%s"
  %s
  %s
  convolution_param {
    num_output: %d
    pad: %d
    kernel_size: %d
    stride: %d
    %s
    %s
  }
}
""" % (name, bottom, top, weight_lr_mult, bias_lr_mult, out, pad, kernel, stride, weight_filler,  bias_filler))

    def relu(self, bottom, top, name):
        with open(self.filepath, 'a') as f:
            f.write(
"""layers {
  name: "%s"
  type: "ReLU"
  bottom: "%s"
  top: "%s"
}
""" % (name, bottom, top))

    def max_pooling(self, bottom, top, name, kernel, stride):
        with open(self.filepath, 'a') as f:
            f.write(
'''layers {
  bottom: "%s"
  top: "%s"
  name: "%s"
  type: "Pooling"
  pooling_param {
    pool: MAX
    kernel_size: %d
    stride: %d
  }
}
'''%(bottom,top,name,kernel,stride))

    def fc(self, bottom, top, name, out):
        bias_lr_mult = ""
        bias_filler = ""
        weight_lr_mult = ""
        weight_filler = ""
        if self.stage == "train" or self.stage == "test":
            bias_filler ="""
bias_filler {
  type: "constant"
  value: 0.1
}
        """
            bias_lr_mult = """
param {
  lr_mult: 1.0
  decay_mult: 1.0
}
        """
            weight_lr_mult = """
param {
  lr_mult: 2.0
  decay_mult: 0.0
}
        """
            weight_filler = """
weight_filler {
  type: "gaussian"
  sdt: 0.005  }  
        """
        with open(self.filepath, 'a') as f:
            f.write(
"""
layers {
  bottom: "%s"
  top: "%s"
  name: "%s"
  type: "InnerProduct"
  %s
  %s
  inner_product_param {
    num_output: %d
    %s
    %s
    }
}
"""%(bottom, top,name, bias_lr_mult, weight_lr_mult, out, weight_filler, bias_filler)
            )

    def dropout(self, bottom, top, name, ratio):
        with open(self.filepath, 'a') as f:
            f. write(
"""
layers {
 bottom: "%s"
 top: "%s"
 name: "%s"
 type: "Dropout"
 dropout_param {
   dropout_ratio: %d
   }
}
"""%(bottom, top, name, ratio)
            )


    def acc_layer(self, bottom, top, name, topk):
        with open(self.filepath, 'a') as f:
            f.write(
"""
layers {
  name: "%s"
  bottom: "%s"
  top: "%s"
  type: "Accuracy"
  bottom:"label"
  accuracy_param {
    top_k: %d
   }
  include {
    phase: TEST
  } 
}
""" % (bottom, top, name, topk)         )


    def softmax_with_loss(self,bottom,top,name):
        with open(self.filepath, 'a') as f:
            f.write(
"""
layers {
  name: "%s"
  bottom: "%s"
  top: "%s"
  type: "SoftmaxWithLoss"
  bottom:"label"
}
""" % (bottom, top, name))

    def softmax(self, bottom, top, name):
        with open(self.filepath, 'a') as f:
            f.write(
"""
layers {
  bottom: "%s"
  top: "%s"
  name: "%s"
  type: "SOFTMAX"
}
"""%(bottom, top, name)
            )


    def generate(self, stage, lmdb,  class_num, batch, size, quantize=False):
        self.class_num = class_num
        self.lmdb = lmdb

        self.stage = stage
        self.batch = batch
        self.quantize = quantize
        self.input_size = 200
        self.size = size
        self.header("VGG-16")
        if self.quantize:
            self.quantizeNet()
        if stage == "train":
            assert (self.lmdb is not None)
            self.data_train_classifier()
        elif stage == "test":
            assert (self.lmdb is not None)
            self.data_test_classifier()
        else:
            self.data_deploy()

        self.conv(bottom="data", name="conv1", top="conv1", out=64, pad=3, kernel=7)
        # self.relu(bottom="conv1_1",top="conv1_1",name="relu1_1")
        # self.conv(bottom="conv1_1", name="conv1_2", top="conv1_2", out=64, pad=1, kernel=3)
        # self.relu(bottom="conv1_2", top="conv1_2", name="relu1_2")
        # self.max_pooling(bottom="conv1_2",top="pool1",name="pool1",kernel=2,stride=2)
        # self.conv(bottom="pool1", name="conv2_1", top="conv2_1", out=128, pad=1, kernel=3)
        # self.relu(bottom="conv2_1",top="conv2_1",name="relu2_1")
        # self.conv(bottom="conv2_1", name="conv2_2", top="conv2_2", out=128, pad=1, kernel=3)
        # self.relu(bottom="conv2_2",top="conv2_2",name="relu2_2")
        # self.max_pooling(bottom="conv2_2", top="pool2", name="pool2", kernel=2, stride=2)
        # self.conv(bottom="pool2", name="conv3_1", top="conv3_1", out=256, pad=1, kernel=3)
        # self.relu(bottom="conv3_1", top="conv3_1", name="relu3_1")
        # self.conv(bottom="conv3_1", name="conv3_2", top="conv3_2", out=256, pad=1, kernel=3)
        # self.relu(bottom="conv3_2", top="conv3_2", name="relu3_2")
        # self.conv(bottom="conv3_2", name="conv3_3", top="conv3_3", out=256, pad=1, kernel=3)
        # self.relu(bottom="conv3_3", top="conv3_3", name="relu3_3")
        # self.max_pooling(bottom="conv3_3", top="pool3", name="pool3", kernel=2, stride=2)
        # self.conv(bottom="pool3", name="conv4_1", top="conv4_1", out=512, pad=1, kernel=3)
        # self.relu(bottom="conv4_1", top="conv4_1", name="relu4_1")
        # self.conv(bottom="conv4_1", name="conv4_2", top="conv4_2", out=512, pad=1, kernel=3)
        # self.relu(bottom="conv4_2", top="conv4_2", name="relu4_2")
        # self.conv(bottom="conv4_2", name="conv4_3", top="conv4_3", out=512, pad=1, kernel=3)
        # self.relu(bottom="conv4_3", top="conv4_3", name="relu4_3")
        # self.max_pooling(bottom="conv4_3", top="pool4", name="pool4", kernel=2, stride=2)
        # self.conv(bottom="pool4", name="conv5_1", top="conv5_1", out=512, pad=1, kernel=3)
        # self.relu(bottom="conv5_1", top="conv5_1", name="relu5_1")
        # self.conv(bottom="conv5_1", name="conv5_2", top="conv5_2", out=512, pad=1, kernel=3)
        # self.relu(bottom="conv5_2", top="conv5_2", name="relu5_2")
        # self.conv(bottom="conv5_2", name="conv5_3", top="conv5_3", out=512, pad=1, kernel=3)
        # self.relu(bottom="conv5_3", top="conv5_3", name="relu5_3")
        # self.max_pooling(bottom="conv5_3", top="pool5", name="pool5", kernel=2, stride=2)
        # self.fc(top="fc6",name="fc6",bottom="pool5",out=4096)
        # self.relu(bottom="fc6",top="fc6",name="relu6")
        # self.dropout(bottom="fc6", top="fc6", name="drop6", ratio=0.5)
        # self.fc(top="fc7", name="fc7", bottom="fc6", out=4096)
        # self.relu(bottom="fc7", top="fc7", name="relu7")
        # self.dropout(bottom="fc7", top="fc7", name="drop7", ratio=0.5)
        # self.fc(top="fc8", bottom="fc7", name="fc8", out= class_num)
        # if self.stage == "train" or self.stage == "test":
        #     self.acc_layer(bottom="fc8", top="accuracy_at_1", name="accuracy_at_1", topk=1)
        #     self.softmax_with_loss(bottom="fc8",top="loss",name="loss")
        # else:
        #     self.softmax(bottom="fc8", top="prob", name="prob")


def proto_generator(train_path, stage, lmdb, labelmap, classes, batch, background=0, gen_ssd=True, size=1.0):
  gen = Generator(train_path)
  gen.generate(stage, lmdb,  classes, batch, size)

def solver_generator(filepath,net,max_it,output_path,eval_type):
  with open(filepath, 'w') as f:
    f.write("""net: "%s"
#test_net: "./examples/MobileNet/proto/MobileNetSSD_test.prototxt"
#test_iter: 673
#test_interval: 10000
base_lr: 0.0005
display: 10
max_iter: %d
lr_policy: "multistep"
gamma: 0.5
weight_decay: 0.00005
snapshot: 1000
snapshot_prefix: "%ssnapshot"
solver_mode: GPU
debug_info: false
snapshot_after_train: true
#test_initialization: false
average_loss: 10
stepvalue: 20000
stepvalue: 40000
iter_size: 1
type: "RMSProp"
eval_type: "%s"
ap_version: "11point"
""" % (net, max_it, output_path, eval_type))


def solver_generator_test(filepath,net_train, net_test,iter,output_path,eval_type):
  with open(filepath, 'w') as f:
    f.write("""train_net: "%s"
test_net: "%s"
test_iter: %d
test_interval: 10000
base_lr: 0.0005
display: 10
max_iter: 0
lr_policy: "multistep"
gamma: 0.5
weight_decay: 0.00005
snapshot: 0
snapshot_prefix: "%ssnapshot"
solver_mode: GPU
debug_info: false
snapshot_after_train: false
test_initialization: true
average_loss: 10
stepvalue: 20000
stepvalue: 40000
iter_size: 1
type: "RMSProp"
eval_type: "%s"
ap_version: "11point"
show_per_class_result: true
""" % (net_train, net_test, iter, output_path, eval_type))