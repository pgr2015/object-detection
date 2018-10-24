
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
  convolution_param {
    num_output: %d
    pad: %d
    kernel_size: %d
    stride: %d
    bias_term: false
    %s
    %s
  }
}
""" % (name, bottom, top, out, pad, kernel, stride, weight_filler,  bias_filler))

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

    def bn(self,bottom, top, name):
        with open(self.filepath, 'a') as f:
            f.write(
"""
layers {
  bottom: "%s"
  top: "%s"
  name: "%s"
  type: "BatchNorm"
  batch_norm_param{
  }
}
"""%(bottom, top, name)
            )

    def scale(self, bottom, top, name):
        with open(self.filepath, 'a') as f:
            f.write(
"""
layers {
  bottom: "%s"
  top: "%s"
  name: "%s"
  type: "Scale"
  scale_param {
    bias_term: true
  }
}
"""%(bottom, top, name)
            )

    def eltwise(self, bottom1, bottom2, top, name):
        with open(self.filepath, 'a') as f:
            f.write(
"""
layers {
  bottom: "%s"
  bottom: "%s"
  top: "%s"
  name: "%s"
  type: "Eltwise"
  eltwise_param {
  
  }
}
""" % (bottom1, bottom2, top, name)
            )

    def avg_pool(self,bottom, top, name, kernel, stride):
        with open(self.filepath, 'a') as f:
            f.write(
"""
layers {
  bottom: "%s"
  top: "%s"
  name: "%s"
  type: "Pooling"
  pooling_param {
    kernel_size: %d
    stride: %d
    pool: AVE
  }
}
"""%(bottom, top, name, kernel, stride))

    def generate(self, stage, lmdb,  class_num, batch, size, quantize=False):
        self.class_num = class_num
        self.lmdb = lmdb

        self.stage = stage
        self.batch = batch
        self.quantize = quantize
        self.input_size = 200
        self.size = size
        self.header("Resnet-50")
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

        self.conv(bottom="data", name="conv1", top="conv1", out=64, pad=3, kernel=7,stride=2)
        self.bn(bottom="conv1", top="conv1", name="bn_conv1")
        self.scale(bottom="conv1", top="conv1", name="scale_conv1")
        self.relu(bottom="conv1",top="conv1", name="conv1_relu")
        self.max_pooling(bottom="conv1", top="pool1", name="pool1", kernel=3, stride=2)

        self.conv(bottom="pool1", top="res2a_branch1", name="res2a_branch1", out=256, kernel=1, pad=0, stride=1)
        self.bn(bottom="res2a_branch1", top="res2a_branch1", name="bn2a_branch1")
        self.scale(bottom="res2a_branch1", top="res2a_branch1", name="scale2a_branch1")

        self.conv(bottom="pool1", top="res2a_branch2a", name="res2a_branch2a", out=64, kernel=1, pad=0, stride=1)
        self.bn(bottom="res2a_branch2a", top="res2a_branch2a", name="bn2a_branch2a")
        self.scale(bottom="res2a_branch2a", top="res2a_branch2a", name="scale2a_branch2a")
        self.relu(bottom="res2a_branch2a", top="res2a_branch2a", name="res2a_branch2a_relu")

        self.conv(bottom="res2a_branch2a", top="res2a_branch2b", name="res2a_branch2b", out=64, kernel=3, pad=1, stride=1)
        self.bn(bottom="res2a_branch2b", top="res2a_branch2b", name="bn2a_branch2b")
        self.scale(bottom="res2a_branch2b", top="res2a_branch2b", name="scale2a_branch2b")
        self.relu(bottom="res2a_branch2b", top="res2a_branch2b", name="res2a_branch2b_relu")

        self.conv(bottom="res2a_branch2b", top="res2a_branch2c", name="res2a_branch2c", out=256, kernel=1, pad=0, stride=1)
        self.bn(bottom="res2a_branch2c", top="res2a_branch2c", name="bn2a_branch2c")
        self.scale(bottom="res2a_branch2c", top="res2a_branch2c", name="scale2a_branch2b")
        self.eltwise(bottom1="res2a_branch1", bottom2="res2a_branch2c", top="res2a", name="res2a")
        self.relu(bottom="res2a", top="res2a", name="res2a_relu")

        self.conv(bottom="res2a", top="res2b_branch2a", name="res2b_branch2a", out=64, kernel=1, pad=0, stride=1)
        self.bn(bottom="res2b_branch2a", top="res2b_branch2a", name="bn2b_branch2a")
        self.scale(bottom="res2b_branch2a", top="res2b_branch2a", name="scale2b_branch2a")
        self.relu(bottom="res2b_branch2a", top="res2b_branch2a", name="res2b_branch2a_relu")

        self.conv(bottom="res2b_branch2a", top="res2b_branch2b", name="res2b_branch2b", out=64, kernel=3, pad=1, stride=1)
        self.bn(bottom="res2b_branch2b", top="res2b_branch2b", name="bn2b_branch2b")
        self.scale(bottom="res2b_branch2b", top="res2b_branch2b", name="scale2b_branch2b")
        self.relu(bottom="res2b_branch2b", top="res2b_branch2b", name="res2b_branch2b_relu")

        self.conv(bottom="res2b_branch2b", top="res2b_branch2c", name="res2b_branch2c", out=256, kernel=1, pad=0, stride=1)
        self.bn(bottom="res2b_branch2c", top="res2b_branch2c", name="bn2b_branch2c")
        self.scale(bottom="res2b_branch2c", top="res2b_branch2c", name="scale2b_branch2b")
        self.eltwise(bottom1="res2a", bottom2="res2b_branch2c", top="res2b", name="res2b")
        self.relu(bottom="res2b", top="res2b", name="res2b_relu")

        self.conv(bottom="res2b", top="res2c_branch2a", name="res2c_branch2a", out=64, kernel=1, pad=0, stride=1)
        self.bn(bottom="res2c_branch2a", top="res2c_branch2a", name="bn2c_branch2a")
        self.scale(bottom="res2c_branch2a", top="res2c_branch2a", name="scale2c_branch2a")
        self.relu(bottom="res2c_branch2a", top="res2c_branch2a", name="res2c_branch2a_relu")

        self.conv(bottom="res2c_branch2a", top="res2c_branch2b", name="res2c_branch2b", out=64, kernel=3, pad=1, stride=1)
        self.bn(bottom="res2c_branch2b", top="res2c_branch2b", name="bn2c_branch2b")
        self.scale(bottom="res2c_branch2b", top="res2c_branch2b", name="scale2c_branch2b")
        self.relu(bottom="res2c_branch2b", top="res2c_branch2b", name="res2c_branch2b_relu")

        self.conv(bottom="res2c_branch2b", top="res2c_branch2c", name="res2c_branch2c", out=256, kernel=1, pad=0, stride=1)
        self.bn(bottom="res2c_branch2c", top="res2c_branch2c", name="bn2c_branch2c")
        self.scale(bottom="res2c_branch2c", top="res2c_branch2c", name="scale2c_branch2b")
        self.eltwise(bottom1="res2b", bottom2="res2c_branch2c", top="res2c", name="res2c")
        self.relu(bottom="res2c", top="res2c", name="res2c_relu")

        self.conv(bottom="res2c", top="res3a_branch1", name="res3a_branch1", out=512, kernel=1, pad=0, stride=2)
        self.bn(bottom="res3a_branch1", top="res3a_branch1", name="bn3a_branch1")
        self.scale(bottom="res3a_branch1", top="res3a_branch1", name="scale3a_branch1")

        self.conv(bottom="res2c", top="res3a_branch2a", name="res3a_branch2a", out=128, kernel=1, pad=0, stride=2)
        self.bn(bottom="res3a_branch2a", top="res3a_branch2a", name="bn3a_branch2a")
        self.scale(bottom="res3a_branch2a", top="res3a_branch2a", name="scale3a_branch2a")
        self.relu(bottom="res3a_branch2a", top="res3a_branch2a", name="res3a_branch2a_relu")

        self.conv(bottom="res3a_branch2a", top="res3a_branch2b", name="res3a_branch2b", out=128, kernel=3, pad=1, stride=1)
        self.bn(bottom="res3a_branch2b", top="res3a_branch2b", name="bn3a_branch2b")
        self.scale(bottom="res3a_branch2b", top="res3a_branch2b", name="scale3a_branch2b")
        self.relu(bottom="res3a_branch2b", top="res3a_branch2b", name="res3a_branch2b_relu")

        self.conv(bottom="res3a_branch2b", top="res3a_branch2c", name="res3a_branch2c", out=512, kernel=1, pad=0,
                  stride=1)
        self.bn(bottom="res3a_branch2c", top="res3a_branch2c", name="bn3a_branch2c")
        self.scale(bottom="res3a_branch2c", top="res3a_branch2c", name="scale3a_branch2b")
        self.eltwise(bottom1="res3a_branch1", bottom2="res3a_branch2c", top="res3a", name="res3a")
        self.relu(bottom="res3a", top="res3a", name="res3a_relu")

        self.conv(bottom="res3a", top="res3b_branch2a", name="res3b_branch2a", out=128, kernel=1, pad=0, stride=1)
        self.bn(bottom="res3b_branch2a", top="res3b_branch2a", name="bn3b_branch2a")
        self.scale(bottom="res3b_branch2a", top="res3b_branch2a", name="scale3b_branch2a")
        self.relu(bottom="res3b_branch2a", top="res3b_branch2a", name="res3b_branch2a_relu")

        self.conv(bottom="res3b_branch2a", top="res3b_branch2b", name="res3b_branch2b", out=128, kernel=3, pad=1, stride=1)
        self.bn(bottom="res3b_branch2b", top="res3b_branch2b", name="bn3b_branch2b")
        self.scale(bottom="res3b_branch2b", top="res3b_branch2b", name="scale3b_branch2b")
        self.relu(bottom="res3b_branch2b", top="res3b_branch2b", name="res3b_branch2b_relu")

        self.conv(bottom="res3b_branch2b", top="res3b_branch2c", name="res3b_branch2c", out=512, kernel=1, pad=0,
                  stride=1)
        self.bn(bottom="res3b_branch2c", top="res3b_branch2c", name="bn3b_branch2c")
        self.scale(bottom="res3b_branch2c", top="res3b_branch2c", name="scale3b_branch2c")
        self.eltwise(bottom1="res3a", bottom2="res3b_branch2c", top="res3b", name="res3b")
        self.relu(bottom="res3b", top="res3b", name="res3b_relu")

        self.conv(bottom="res3b", top="res3c_branch2a", name="res3c_branch2a", out=128, kernel=1, pad=0, stride=1)
        self.bn(bottom="res3c_branch2a", top="res3c_branch2a", name="bn3c_branch2a")
        self.scale(bottom="res3c_branch2a", top="res3c_branch2a", name="scale3c_branch2a")
        self.relu(bottom="res3c_branch2a", top="res3c_branch2a", name="res3c_branch2a_relu")

        self.conv(bottom="res3c_branch2a", top="res3c_branch2b", name="res3c_branch2b", out=128, kernel=3, pad=1,
                  stride=1)
        self.bn(bottom="res3c_branch2b", top="res3c_branch2b", name="bn3c_branch2b")
        self.scale(bottom="res3c_branch2b", top="res3c_branch2b", name="scale3c_branch2b")
        self.relu(bottom="res3c_branch2b", top="res3c_branch2b", name="res3c_branch2b_relu")

        self.conv(bottom="res3c_branch2b", top="res3c_branch2c", name="res3c_branch2c", out=512, kernel=1, pad=0,
                  stride=1)
        self.bn(bottom="res3c_branch2c", top="res3c_branch2c", name="bn3c_branch2c")
        self.scale(bottom="res3c_branch2c", top="res3c_branch2c", name="scale3c_branch2c")
        self.eltwise(bottom1="res3b", bottom2="res3c_branch2c", top="res3c", name="res3c")
        self.relu(bottom="res3c", top="res3c", name="res3c_relu")

        self.conv(bottom="res3c", top="res3d_branch2a", name="res3d_branch2a", out=128, kernel=1, pad=0, stride=1)
        self.bn(bottom="res3d_branch2a", top="res3d_branch2a", name="bn3d_branch2a")
        self.scale(bottom="res3d_branch2a", top="res3d_branch2a", name="scale3d_branch2a")
        self.relu(bottom="res3d_branch2a", top="res3d_branch2a", name="res3d_branch2a_relu")

        self.conv(bottom="res3d_branch2a", top="res3d_branch2b", name="res3d_branch2b", out=128, kernel=3, pad=1, stride=1)
        self.bn(bottom="res3d_branch2b", top="res3d_branch2b", name="bn3d_branch2b")
        self.scale(bottom="res3d_branch2b", top="res3d_branch2b", name="scale3d_branch2b")
        self.relu(bottom="res3d_branch2b", top="res3d_branch2b", name="res3d_branch2b_relu")

        self.conv(bottom="res3d_branch2b", top="res3d_branch2c", name="res3d_branch2c", out=512, kernel=1, pad=0, stride=1)
        self.bn(bottom="res3d_branch2c", top="res3d_branch2c", name="bn3d_branch2c")
        self.scale(bottom="res3d_branch2c", top="res3d_branch2c", name="scale3d_branch2c")
        self.eltwise(bottom1="res3c", bottom2="res3d_branch2c", top="res3d", name="res3d")
        self.relu(bottom="res3d", top="res3d", name="res3d_relu")

        self.conv(bottom="res3d", top="res4a_branch1", name="res4a_branch1", out=1024, kernel=1, pad=0, stride=2)
        self.bn(bottom="res4a_branch1", top="res4a_branch1", name="bn4a_branch1")
        self.scale(bottom="res4a_branch1", top="res4a_branch1", name="scale4a_branch1")

        self.conv(bottom="res3d", top="res4a_branch2a", name="res4a_branch2a", out=256, kernel=1, pad=0, stride=2)
        self.bn(bottom="res4a_branch2a", top="res4a_branch2a", name="bn4a_branch2a")
        self.scale(bottom="res4a_branch2a", top="res4a_branch2a", name="scale4a_branch2a")
        self.relu(bottom="res4a_branch2a", top="res4a_branch2a", name="res4a_branch2a_relu")

        self.conv(bottom="res4a_branch2a", top="res4a_branch2b", name="res4a_branch2b", out=256, kernel=3, pad=1, stride=1)
        self.bn(bottom="res4a_branch2b", top="res4a_branch2b", name="bn4a_branch2b")
        self.scale(bottom="res4a_branch2b", top="res4a_branch2b", name="scale4a_branch2b")
        self.relu(bottom="res4a_branch2b", top="res4a_branch2b", name="res4a_branch2b_relu")

        self.conv(bottom="res4a_branch2b", top="res4a_branch2c", name="res4a_branch2c", out=1024, kernel=1, pad=0, stride=1)
        self.bn(bottom="res4a_branch2c", top="res4a_branch2c", name="bn4a_branch2c")
        self.scale(bottom="res4a_branch2c", top="res4a_branch2c", name="scale4a_branch2b")
        self.eltwise(bottom1="res4a_branch1", bottom2="res4a_branch2c", top="res4a", name="res4a")
        self.relu(bottom="res4a", top="res4a", name="res4a_relu")

        self.conv(bottom="res4a", top="res4b_branch2a", name="res4b_branch2a", out=256, kernel=1, pad=0, stride=1)
        self.bn(bottom="res4b_branch2a", top="res4b_branch2a", name="bn4b_branch2a")
        self.scale(bottom="res4b_branch2a", top="res4b_branch2a", name="scale4b_branch2a")
        self.relu(bottom="res4b_branch2a", top="res4b_branch2a", name="res4b_branch2a_relu")

        self.conv(bottom="res4b_branch2a", top="res4b_branch2b", name="res4b_branch2b", out=256, kernel=3, pad=1, stride=1)
        self.bn(bottom="res4b_branch2b", top="res4b_branch2b", name="bn4b_branch2b")
        self.scale(bottom="res4b_branch2b", top="res4b_branch2b", name="scale4b_branch2b")
        self.relu(bottom="res4b_branch2b", top="res4b_branch2b", name="res4b_branch2b_relu")

        self.conv(bottom="res4b_branch2b", top="res4b_branch2c", name="res4b_branch2c", out=1024, kernel=1, pad=0, stride=1)
        self.bn(bottom="res4b_branch2c", top="res4b_branch2c", name="bn4b_branch2c")
        self.scale(bottom="res4b_branch2c", top="res4b_branch2c", name="scale4b_branch2c")
        self.eltwise(bottom1="res4a", bottom2="res4b_branch2c", top="res4b", name="res4b")
        self.relu(bottom="res4b", top="res4b", name="res4b_relu")

        self.conv(bottom="res4b", top="res4c_branch2a", name="res4c_branch2a", out=256, kernel=1, pad=0, stride=1)
        self.bn(bottom="res4c_branch2a", top="res4c_branch2a", name="bn4c_branch2a")
        self.scale(bottom="res4c_branch2a", top="res4c_branch2a", name="scale4c_branch2a")
        self.relu(bottom="res4c_branch2a", top="res4c_branch2a", name="res4c_branch2a_relu")

        self.conv(bottom="res4c_branch2a", top="res4c_branch2b", name="res4c_branch2b", out=256, kernel=3, pad=1, stride=1)
        self.bn(bottom="res4c_branch2b", top="res4c_branch2b", name="bn4c_branch2b")
        self.scale(bottom="res4c_branch2b", top="res4c_branch2b", name="scale4c_branch2b")
        self.relu(bottom="res4c_branch2b", top="res4c_branch2b", name="res4c_branch2b_relu")

        self.conv(bottom="res4c_branch2b", top="res4c_branch2c", name="res4c_branch2c", out=1024, kernel=1, pad=0,
                  stride=1)
        self.bn(bottom="res4c_branch2c", top="res4c_branch2c", name="bn4c_branch2c")
        self.scale(bottom="res4c_branch2c", top="res4c_branch2c", name="scale4c_branch2c")
        self.eltwise(bottom1="res4b", bottom2="res4c_branch2c", top="res4c", name="res4c")
        self.relu(bottom="res4c", top="res4c", name="res4c_relu")

        self.conv(bottom="res4c", top="res4d_branch2a", name="res4d_branch2a", out=256, kernel=1, pad=0, stride=1)
        self.bn(bottom="res4d_branch2a", top="res4d_branch2a", name="bn4d_branch2a")
        self.scale(bottom="res4d_branch2a", top="res4d_branch2a", name="scale4d_branch2a")
        self.relu(bottom="res4d_branch2a", top="res4d_branch2a", name="res4d_branch2a_relu")

        self.conv(bottom="res4d_branch2a", top="res4d_branch2b", name="res4d_branch2b", out=256, kernel=3, pad=1,
                  stride=1)
        self.bn(bottom="res4d_branch2b", top="res4d_branch2b", name="bn4d_branch2b")
        self.scale(bottom="res4d_branch2b", top="res4d_branch2b", name="scale4d_branch2b")
        self.relu(bottom="res4d_branch2b", top="res4d_branch2b", name="res4d_branch2b_relu")

        self.conv(bottom="res4d_branch2b", top="res4d_branch2c", name="res4d_branch2c", out=1024, kernel=1, pad=0,
                  stride=1)
        self.bn(bottom="res4d_branch2c", top="res4d_branch2c", name="bn4d_branch2c")
        self.scale(bottom="res4d_branch2c", top="res4d_branch2c", name="scale4d_branch2c")
        self.eltwise(bottom1="res4c", bottom2="res4d_branch2c", top="res4d", name="res4d")
        self.relu(bottom="res4d", top="res4d", name="res4d_relu")

        self.conv(bottom="res4d", top="res4e_branch2a", name="res4e_branch2a", out=256, kernel=1, pad=0, stride=1)
        self.bn(bottom="res4e_branch2a", top="res4e_branch2a", name="bn4e_branch2a")
        self.scale(bottom="res4e_branch2a", top="res4e_branch2a", name="scale4e_branch2a")
        self.relu(bottom="res4e_branch2a", top="res4e_branch2a", name="res4e_branch2a_relu")

        self.conv(bottom="res4e_branch2a", top="res4e_branch2b", name="res4e_branch2b", out=256, kernel=3, pad=1,
                  stride=1)
        self.bn(bottom="res4e_branch2b", top="res4e_branch2b", name="bn4e_branch2b")
        self.scale(bottom="res4e_branch2b", top="res4e_branch2b", name="scale4e_branch2b")
        self.relu(bottom="res4e_branch2b", top="res4e_branch2b", name="res4e_branch2b_relu")

        self.conv(bottom="res4e_branch2b", top="res4e_branch2c", name="res4e_branch2c", out=1024, kernel=1, pad=0,
                  stride=1)
        self.bn(bottom="res4e_branch2c", top="res4e_branch2c", name="bn4e_branch2c")
        self.scale(bottom="res4e_branch2c", top="res4e_branch2c", name="scale4e_branch2c")
        self.eltwise(bottom1="res4d", bottom2="res4e_branch2c", top="res4e", name="res4e")
        self.relu(bottom="res4e", top="res4e", name="res4e_relu")

        self.conv(bottom="res4e", top="res4f_branch2a", name="res4f_branch2a", out=256, kernel=1, pad=0, stride=1)
        self.bn(bottom="res4f_branch2a", top="res4f_branch2a", name="bn4f_branch2a")
        self.scale(bottom="res4f_branch2a", top="res4f_branch2a", name="scale4f_branch2a")
        self.relu(bottom="res4f_branch2a", top="res4f_branch2a", name="res4f_branch2a_relu")

        self.conv(bottom="res4f_branch2a", top="res4f_branch2b", name="res4f_branch2b", out=256, kernel=3, pad=1,
                  stride=1)
        self.bn(bottom="res4f_branch2b", top="res4f_branch2b", name="bn4f_branch2b")
        self.scale(bottom="res4f_branch2b", top="res4f_branch2b", name="scale4f_branch2b")
        self.relu(bottom="res4f_branch2b", top="res4f_branch2b", name="res4f_branch2b_relu")

        self.conv(bottom="res4f_branch2b", top="res4f_branch2c", name="res4f_branch2c", out=1024, kernel=1, pad=0,
                  stride=1)
        self.bn(bottom="res4f_branch2c", top="res4f_branch2c", name="bn4f_branch2c")
        self.scale(bottom="res4f_branch2c", top="res4f_branch2c", name="scale4f_branch2c")
        self.eltwise(bottom1="res4e", bottom2="res4f_branch2c", top="res4f", name="res4f")
        self.relu(bottom="res4f", top="res4f", name="res4f_relu")

        self.conv(bottom="res4f", top="res5a_branch1", name="res5a_branch1", out=2048, kernel=1, pad=0, stride=2)
        self.bn(bottom="res5a_branch1", top="res5a_branch1", name="bn5a_branch1")
        self.scale(bottom="res5a_branch1", top="res5a_branch1", name="scale5a_branch1")

        self.conv(bottom="res4f", top="res5a_branch2a", name="res5a_branch2a", out=512, kernel=1, pad=0, stride=2)
        self.bn(bottom="res5a_branch2a", top="res5a_branch2a", name="bn5a_branch2a")
        self.scale(bottom="res5a_branch2a", top="res5a_branch2a", name="scale5a_branch2a")
        self.relu(bottom="res5a_branch2a", top="res5a_branch2a", name="res5a_branch2a_relu")

        self.conv(bottom="res5a_branch2a", top="res5a_branch2b", name="res5a_branch2b", out=512, kernel=3, pad=1, stride=1)
        self.bn(bottom="res5a_branch2b", top="res5a_branch2b", name="bn5a_branch2b")
        self.scale(bottom="res5a_branch2b", top="res5a_branch2b", name="scale5a_branch2b")
        self.relu(bottom="res5a_branch2b", top="res5a_branch2b", name="res5a_branch2b_relu")

        self.conv(bottom="res5a_branch2b", top="res5a_branch2c", name="res5a_branch2c", out=2048, kernel=1, pad=0, stride=1)
        self.bn(bottom="res5a_branch2c", top="res5a_branch2c", name="bn5a_branch2c")
        self.scale(bottom="res5a_branch2c", top="res5a_branch2c", name="scale5a_branch2c")
        self.eltwise(bottom1="res5a_branch1", bottom2="res5a_branch2c", top="res5a", name="res5a")
        self.relu(bottom="res5a", top="res5a", name="res5a_relu")

        self.conv(bottom="res5a", top="res5b_branch2a", name="res5b_branch2a", out=512, kernel=1, pad=0, stride=1)
        self.bn(bottom="res5b_branch2a", top="res5b_branch2a", name="bn5b_branch2a")
        self.scale(bottom="res5b_branch2a", top="res5b_branch2a", name="scale5b_branch2a")
        self.relu(bottom="res5b_branch2a", top="res5b_branch2a", name="res5b_branch2a_relu")

        self.conv(bottom="res5b_branch2a", top="res5b_branch2b", name="res5b_branch2b", out=512, kernel=3, pad=1,
                  stride=1)
        self.bn(bottom="res5b_branch2b", top="res5b_branch2b", name="bn5b_branch2b")
        self.scale(bottom="res5b_branch2b", top="res5b_branch2b", name="scale5b_branch2b")
        self.relu(bottom="res5b_branch2b", top="res5b_branch2b", name="res5b_branch2b_relu")

        self.conv(bottom="res5b_branch2b", top="res5b_branch2c", name="res5b_branch2c", out=2048, kernel=1, pad=0, stride=1)
        self.bn(bottom="res5b_branch2c", top="res5b_branch2c", name="bn5b_branch2c")
        self.scale(bottom="res5b_branch2c", top="res5b_branch2c", name="scale5b_branch2c")
        self.eltwise(bottom1="res5a", bottom2="res5b_branch2c", top="res5b", name="res5b")
        self.relu(bottom="res5b", top="res5b", name="res5b_relu")

        self.conv(bottom="res5b", top="res5c_branch2a", name="res5c_branch2a", out=512, kernel=1, pad=0, stride=1)
        self.bn(bottom="res5c_branch2a", top="res5c_branch2a", name="bn5c_branch2a")
        self.scale(bottom="res5c_branch2a", top="res5c_branch2a", name="scale5c_branch2a")
        self.relu(bottom="res5c_branch2a", top="res5c_branch2a", name="res5c_branch2a_relu")

        self.conv(bottom="res5c_branch2a", top="res5c_branch2b", name="res5c_branch2b", out=512, kernel=3, pad=1, stride=1)
        self.bn(bottom="res5c_branch2b", top="res5c_branch2b", name="bn5c_branch2b")
        self.scale(bottom="res5c_branch2b", top="res5c_branch2b", name="scale5c_branch2b")
        self.relu(bottom="res5c_branch2b", top="res5c_branch2b", name="res5c_branch2b_relu")

        self.conv(bottom="res5c_branch2b", top="res5c_branch2c", name="res5c_branch2c", out=2048, kernel=1, pad=0, stride=1)
        self.bn(bottom="res5b_branch2c", top="res5b_branch2c", name="bn5b_branch2c")
        self.scale(bottom="res5c_branch2c", top="res5c_branch2c", name="scale5c_branch2c")
        self.eltwise(bottom1="res5b", bottom2="res5c_branch2c", top="res5c", name="res5c")
        self.relu(bottom="res5c", top="res5c", name="res5c_relu")

        self.avg_pool(bottom="res5c", top="pool5", name="pool5", kernel=7, stride=1)
        self.fc(bottom="pool5", top="fc1000", name="fc1000", out=class_num)
        if self.stage=="train" or self.stage=="test":
            self.softmax_with_loss(bottom="fc1000",top="prob", name="prob")
            self.acc_layer(bottom="fc1000", top="accuracy/top-1", name="accuracy/top-1", topk=1)
        else:
            self.softmax(bottom="fc1000", top="prob", name="prob")

        # if self.stage == "train" or self.stage == "test":
        #     self.acc_layer(bottom="fc8", top="accuracy_at_1", name="accuracy_at_1", topk=1)
        #     self.softmax_with_loss(bottom="fc8",top="loss",name="loss")
        # else:
        #     self.softmax(bottom="fc8", top="prob", name="prob")

def proto_generator(train_path, stage, lmdb,  classes, batch, gen_ssd=True, size=1.0):
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

if __name__=="__main__":
    proto_generator("resnet.prototxt","train","123.lmdb",classes=2, batch=32)