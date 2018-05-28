
class Generator():

    def __init__(self, train_path):
      self.first_prior = True
      self.anchors = create_ssd_anchors()
      self.last = "data"
      self.filepath = train_path
      self.bachground = 22
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
"""input: "data"
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
"""layer {
    name: "data"
    type: "Data"
    top: "data"
    top: "label"
    data_param{
        source: "%s"
        backend: LMDB
        batch_size: 64
    }
    transform_param {
        crop_size: %s
	mean_file: "imagenet.mean"
        mirror: true
    }
    include: { phase: TRAIN }
}
}
""")

    def data_train_ssd(self):
        with open(self.filepath, 'a') as f:
            f.write(
"""
layer {
  name: "data"
  type: "AnnotatedData"
  top: "data"
  top: "label"
  include {
    phase: TRAIN
  }
  transform_param {
    scale: 0.007843
    mirror: true
    mean_value: 127.5
    mean_value: 127.5
    mean_value: 127.5
    resize_param {
      prob: 1.0
      resize_mode: WARP
      height: %d
      width: %d
      interp_mode: LINEAR
      interp_mode: AREA
      interp_mode: NEAREST
      interp_mode: CUBIC
      interp_mode: LANCZOS4
    }
    emit_constraint {
      emit_type: CENTER
    }
    distort_param {
      brightness_prob: 0.5
      brightness_delta: 32.0
      contrast_prob: 0.5
      contrast_lower: 0.5
      contrast_upper: 1.5
      hue_prob: 0.5
      hue_delta: 18.0
      saturation_prob: 0.5
      saturation_lower: 0.5
      saturation_upper: 1.5
      random_order_prob: 0.0
    }
    expand_param {
      prob: 0.5
      max_expand_ratio: 4.0
    }
  }
  data_param {
    source: "%s"
    batch_size: %d
    backend: LMDB
  }
  annotated_data_param {
    batch_sampler {
      max_sample: 1
      max_trials: 1
    }
    batch_sampler {
      sampler {
        min_scale: 0.3
        max_scale: 1.0
        min_aspect_ratio: 0.5
        max_aspect_ratio: 2.0
      }
      sample_constraint {
        min_jaccard_overlap: 0.1
      }
      max_sample: 1
      max_trials: 50
    }
    batch_sampler {
      sampler {
        min_scale: 0.3
        max_scale: 1.0
        min_aspect_ratio: 0.5
        max_aspect_ratio: 2.0
      }
      sample_constraint {
        min_jaccard_overlap: 0.3
      }
      max_sample: 1
      max_trials: 50
    }
    batch_sampler {
      sampler {
        min_scale: 0.3
        max_scale: 1.0
        min_aspect_ratio: 0.5
        max_aspect_ratio: 2.0
      }
      sample_constraint {
        min_jaccard_overlap: 0.5
      }
      max_sample: 1
      max_trials: 50
    }
    batch_sampler {
      sampler {
        min_scale: 0.3
        max_scale: 1.0
        min_aspect_ratio: 0.5
        max_aspect_ratio: 2.0
      }
      sample_constraint {
        min_jaccard_overlap: 0.7
      }
      max_sample: 1
      max_trials: 50
    }
    batch_sampler {
      sampler {
        min_scale: 0.3
        max_scale: 1.0
        min_aspect_ratio: 0.5
        max_aspect_ratio: 2.0
      }
      sample_constraint {
        min_jaccard_overlap: 0.9
      }
      max_sample: 1
      max_trials: 50
    }
    batch_sampler {
      sampler {
        min_scale: 0.3
        max_scale: 1.0
        min_aspect_ratio: 0.5
        max_aspect_ratio: 2.0
      }
      sample_constraint {
        max_jaccard_overlap: 1.0
      }
      max_sample: 1
      max_trials: 50
    }
    label_map_file: "%s"
  }
}
"""  % (self.input_size, self.input_size, self.lmdb, self.batch, self.label_map))

    def data_test_ssd(self):
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
  name: "data"
  type: "AnnotatedData"
  top: "data"
  top: "label"
  include {
    phase: TEST
  }
  transform_param {
    scale: 0.007843
    mean_value: 127.5
    mean_value: 127.5
    mean_value: 127.5
    resize_param {
      prob: 1.0
      resize_mode: WARP
      height: %d
      width: %d
      interp_mode: LINEAR
    }
  }
  data_param {
    source: "%s"
    batch_size: %d
    backend: LMDB
  }
  annotated_data_param {
    batch_sampler {
    }
    label_map_file: "%s"
  }
}
""" %  (self.input_size, self.input_size, self.lmdb,  self.batch, self.label_map))


    def classifier_loss(self):
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
  name: "softmax"
  type: "Softmax"
  bottom: "%s"
  top: "prob"
}
layer {
  name: "accuracy"
  type: "Accuracy"
  bottom: "prob"
  bottom: "label"
  top: "accuracy"
}
layer{
  name: "loss"
  type: "SoftmaxWithLoss"
  bottom: "%s"
  bottom: "label"
  loss_weight: 1 
}
""" % (self.last, self.last))

    def ssd_predict(self):
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
  name: "mbox_conf_reshape"
  type: "Reshape"
  bottom: "mbox_conf"
  top: "mbox_conf_reshape"
  reshape_param {
    shape {
      dim: 0
      dim: -1
      dim: %d
    }
  }
}
layer {
  name: "mbox_conf_softmax"
  type: "Softmax"
  bottom: "mbox_conf_reshape"
  top: "mbox_conf_softmax"
  softmax_param {
    axis: 2
  }
}
layer {
  name: "mbox_conf_flatten"
  type: "Flatten"
  bottom: "mbox_conf_softmax"
  top: "mbox_conf_flatten"
  flatten_param {
    axis: 1
  }
}
layer {
  name: "detection_out"
  type: "DetectionOutput"
  bottom: "mbox_loc"
  bottom: "mbox_conf_flatten"
  bottom: "mbox_priorbox"
  top: "detection_out"
  include {
    phase: TEST
  }
  detection_output_param {
    num_classes: %d
    share_location: true
    background_label_id: %d
    nms_param {
      nms_threshold: 0.45
      top_k: 100
    }
    code_type: CENTER_SIZE
    keep_top_k: 100
    confidence_threshold: 0.25
  }
}
""" % (self.class_num, self.class_num, self.bachground))

    def ssd_test(self):
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
  name: "mbox_conf_reshape"
  type: "Reshape"
  bottom: "mbox_conf"
  top: "mbox_conf_reshape"
  reshape_param {
    shape {
      dim: 0
      dim: -1
      dim: %d
    }
  }
}
layer {
  name: "mbox_conf_softmax"
  type: "Softmax"
  bottom: "mbox_conf_reshape"
  top: "mbox_conf_softmax"
  softmax_param {
    axis: 2
  }
}
layer {
  name: "mbox_conf_flatten"
  type: "Flatten"
  bottom: "mbox_conf_softmax"
  top: "mbox_conf_flatten"
  flatten_param {
    axis: 1
  }
}
layer {
  name: "detection_out"
  type: "DetectionOutput"
  bottom: "mbox_loc"
  bottom: "mbox_conf_flatten"
  bottom: "mbox_priorbox"
  top: "detection_out"
  include {
    phase: TEST
  }
  detection_output_param {
    num_classes: %d
    share_location: true
    background_label_id: %d
    nms_param {
      nms_threshold: 0.45
      top_k: 400
    }
    code_type: CENTER_SIZE
    keep_top_k: 200
    confidence_threshold: 0.01
  }
}
layer {
  name: "detection_eval"
  type: "DetectionEvaluate"
  bottom: "detection_out"
  bottom: "label"
  top: "detection_eval"
  include {
    phase: TEST
  }
  detection_evaluate_param {
    num_classes: 24
    background_label_id: %d
    overlap_threshold: 0.5
    evaluate_difficult_gt: false
  }
}
""" % (self.class_num, self.class_num, self.bachground, self.bachground))

    def ssd_loss(self):
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
  name: "mbox_loss"
  type: "MultiBoxLoss"
  bottom: "mbox_loc"
  bottom: "mbox_conf"
  bottom: "mbox_priorbox"
  bottom: "label"
  top: "mbox_loss"
  include {
    phase: TRAIN
  }
  propagate_down: true
  propagate_down: true
  propagate_down: false
  propagate_down: false
  loss_param {
    normalization: VALID
  }
  multibox_loss_param {
    loc_loss_type: SMOOTH_L1
    conf_loss_type: SOFTMAX
    loc_weight: 1.0
    num_classes: %d
    share_location: true
    match_type: PER_PREDICTION
    overlap_threshold: 0.5
    use_prior_for_matching: true
    background_label_id: %d
    use_difficult_gt: true
    neg_pos_ratio: 3.0
    neg_overlap: 0.5
    code_type: CENTER_SIZE
    ignore_cross_boundary_bbox: false
    mining_type: MAX_NEGATIVE
  }
}
""" % (self.class_num, self.bachground))

    def concat_boxes(self, convs):
      for layer in ["loc", "conf"]:
        bottom =""
        for cnv in convs:
          bottom += "\n  bottom: \"%s_mbox_%s_flat\"" % (cnv, layer)
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
  name: "mbox_%s"
  type: "Concat"%s
  top: "mbox_%s"
  concat_param {
    axis: 1
  }
}
""" % (layer, bottom, layer))

      bottom =""
      for cnv in convs:
        bottom += "\n  bottom: \"%s_mbox_priorbox\"" % cnv
      with open(self.filepath, 'a') as f:
          f.write(
"""layer {
  name: "mbox_priorbox"
  type: "Concat"%s
  top: "mbox_priorbox"
  concat_param {
    axis: 2
  }
}
""" % bottom)

    def conv(self, name, out, kernel, stride=1, group=1, bias=False, bottom=None):

      if self.stage == "deploy": #for deploy, merge bn to bias, so bias must be true
          bias = True

      if bottom is None:
          bottom = self.last
      padstr = ""
      if kernel > 1:
          padstr = "\n    pad: %d" % (kernel / 2)
      groupstr = ""
      if group > 1:
          groupstr = "\n    group: %d\n    engine: CAFFE" % group
      stridestr = ""
      if stride > 1:
          stridestr = "\n    stride: %d" % stride
      bias_lr_mult = ""
      bias_filler = ""
      if bias == True:
          bias_filler = """
    bias_filler {
      type: "constant"
      value: 0.0
    }
"""
          bias_lr_mult = """
  param {
    lr_mult: 2.0
    decay_mult: 0.0
  }
"""
      biasstr = ""
      if bias == False:
          biasstr = "\n    bias_term: true"
      with open(self.filepath, 'a') as f:
          f.write(
"""layer {
  name: "%s"
  type: "Convolution"
  bottom: "%s"
  top: "%s"
  param {
    lr_mult: 1.0
    decay_mult: 1.0
  }%s
  convolution_param {
    num_output: %d%s%s
    kernel_size: %d%s%s
    weight_filler {
      type: "msra"
    }%s
  }
}
""" % (name, bottom, name, bias_lr_mult, out, biasstr, padstr, kernel, stridestr, groupstr, bias_filler))
      self.last = name

    def bn(self, name):
      if self.stage == "deploy":  #deploy does not need bn, you can use merge_bn.py to generate a new caffemodel
         return
      with open(self.filepath, 'a') as f:
          f.write(
"""layer {
  name: "%s/bn"
  type: "BatchNorm"
  bottom: "%s"
  top: "%s"
  param {
    lr_mult: 0
    decay_mult: 0
  }
  param {
    lr_mult: 0
    decay_mult: 0
  }
  param {
    lr_mult: 0
    decay_mult: 0
  }
}
layer {
  name: "%s/scale"
  type: "Scale"
  bottom: "%s"
  top: "%s"
  param {
    lr_mult: 1.0
    decay_mult: 0.0
  }
  param {
    lr_mult: 2.0
    decay_mult: 0.0
  }
  scale_param {
    filler {
      value: 1
    }
    bias_term: true
    bias_filler {
      value: 0
    }
  }
}
""" % (name,name,name,name,name,name))
      self.last = name

    def relu(self, name):
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
  name: "%s/relu"
  type: "ReLU"
  bottom: "%s"
  top: "%s"
}
""" % (name, name, name))
        self.last
        self.last = name

    def conv2(self, name, name2, out, kernel, stride=1, group=1, bias=False, bottom=None):

      if self.stage == "deploy": #for deploy, merge bn to bias, so bias must be true
          bias = True

      if bottom is None:
          bottom = self.last
      padstr = ""
      if kernel > 1:
          padstr = "\n    pad: %d" % (kernel / 2)
      groupstr = ""
      if group > 1:
          groupstr = "\n    group: %d\n    engine: CAFFE" % group
      stridestr = ""
      if stride > 1:
          stridestr = "\n    stride: %d" % stride
      bias_lr_mult = ""
      bias_filler = ""
      if bias == True:
          bias_filler = """
    bias_filler {
      type: "constant"
      value: 0.0
    }
"""
          bias_lr_mult = """
  param {
    lr_mult: 2.0
    decay_mult: 0.0
  }
"""
      biasstr = ""
      if bias == False:
          biasstr = "\n    bias_term: true"
      with open(self.filepath, 'a') as f:
          f.write(
"""layer {
  name: "%s"
  type: "Convolution"
  bottom: "%s"
  top: "%s"
  param {
    lr_mult: 1.0
    decay_mult: 1.0
  }%s
  convolution_param {
    num_output: %d%s%s
    kernel_size: %d%s%s
    weight_filler {
      type: "msra"
    }%s
  }
}
""" % (name, bottom, name2, bias_lr_mult, out, biasstr, padstr, kernel, stridestr, groupstr, bias_filler))
      self.last = name2

    def bn(self, name):
      if self.stage == "deploy":  #deploy does not need bn, you can use merge_bn.py to generate a new caffemodel
         return
      with open(self.filepath, 'a') as f:
          f.write(
"""layer {
  name: "%s/bn"
  type: "BatchNorm"
  bottom: "%s"
  top: "%s"
  param {
    lr_mult: 0
    decay_mult: 0
  }
  param {
    lr_mult: 0
    decay_mult: 0
  }
  param {
    lr_mult: 0
    decay_mult: 0
  }
}
layer {
  name: "%s/scale"
  type: "Scale"
  bottom: "%s"
  top: "%s"
  param {
    lr_mult: 1.0
    decay_mult: 0.0
  }
  param {
    lr_mult: 2.0
    decay_mult: 0.0
  }
  scale_param {
    filler {
      value: 1
    }
    bias_term: true
    bias_filler {
      value: 0
    }
  }
}
""" % (name,name,name,name,name,name))
      self.last = name

    def relu(self, name):
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
  name: "%s/relu"
  type: "ReLU"
  bottom: "%s"
  top: "%s"
}
""" % (name, name, name))
        self.last
        self.last = name


    def conv_bn_relu(self, name, num, kernel, stride):
      self.conv(name, num, kernel, stride)
      self.bn(name)
      self.relu(name)

    def conv_bn_relu_with_factor(self, name, num, kernel, stride):
      num = int(num * self.size)
      self.conv(name, num, kernel, stride)
      self.bn(name)
      self.relu(name)

    def conv_dw_pw(self, name, inp, outp, stride):
      inp = int(inp * self.size)
      outp = int(outp * self.size)
      name1 = name + "/dw"
      self.conv(name1, inp, 3, stride, inp)
      self.bn(name1)
      self.relu(name1)
      name2 = name
      self.conv(name2, outp, 1)
      self.bn(name2)
      self.relu(name2)

    def ave_pool(self, name):
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
  name: "%s"
  type: "Pooling"
  bottom: "%s"
  top: "%s"
  pooling_param {
    pool: AVE
    global_pooling: true
  }
}
""" % (name, self.last, name))
        self.last = name

    def permute(self, name):
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
  name: "%s_perm"
  type: "Permute"
  bottom: "%s"
  top: "%s_perm"
  permute_param {
    order: 0
    order: 2
    order: 3
    order: 1
  }
}
""" % (name, name, name))
        self.last = name + "_perm"

    def flatten(self, name):
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
  name: "%s_flat"
  type: "Flatten"
  bottom: "%s_perm"
  top: "%s_flat"
  flatten_param {
    axis: 1
  }
}
""" % (name, name, name))
        self.last = name + "_flat"

    def mbox_prior(self, name, min_size, max_size, aspect_ratio):
      min_box = self.input_size * min_size
      max_box_str = ""
      aspect_ratio_str = ""
      if max_size is not None:
          max_box = self.input_size * max_size
          max_box_str = "\n    max_size: %.1f" % max_box
      for ar in aspect_ratio:
          aspect_ratio_str += "\n    aspect_ratio: %.1f" % ar

      with open(self.filepath, 'a') as f:
          f.write(
"""layer {
  name: "%s_mbox_priorbox"
  type: "PriorBox"
  bottom: "%s"
  bottom: "data"
  top: "%s_mbox_priorbox"
  prior_box_param {
    min_size: %.1f%s%s
    flip: true
    clip: false
    variance: 0.1
    variance: 0.1
    variance: 0.2
    variance: 0.2
    offset: 0.5
  }
}
""" % (name, name, name, float(min_box), max_box_str, aspect_ratio_str))

    def mbox_conf(self, bottom, num):
       name = bottom + "_mbox_conf"
       self.conv2(name+"_new", name ,num, 1, bias=True, bottom=bottom)
       self.permute(name)
       self.flatten(name)
    def mbox_loc(self, bottom, num):
       name = bottom + "_mbox_loc"
       self.conv(name, num, 1, bias=True, bottom=bottom)
       self.permute(name)
       self.flatten(name)

    def mbox(self, bottom, num):
       self.mbox_loc(bottom, num * 4)
       self.mbox_conf(bottom, num * self.class_num)
       min_size, max_size = self.anchors[0]
       if self.first_prior:
           self.mbox_prior(bottom, min_size, None, [2.0])
           self.first_prior = False
       else:
           self.mbox_prior(bottom, min_size, max_size,[2.0,3.0])
       self.anchors.pop(0)

    def fc(self, name, output):
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
  name: "%s"
  type: "InnerProduct"
  bottom: "%s"
  top: "%s"
  param { lr_mult: 1  decay_mult: 1 }
  param { lr_mult: 2  decay_mult: 0 }
  inner_product_param {
    num_output: %d
    weight_filler { type: "msra" }
    bias_filler { type: "constant"  value: 0 }
  }
}
""" % (name, self.last, name, output))
        self.last = name

    def reshape(self, name, output):
        with open(self.filepath, 'a') as f:
            f.write(
"""layer {
    name: "%s"
    type: "Reshape"
    bottom: "%s"
    top: "%s"
    reshape_param { shape { dim: -1 dim: %s dim: 1 dim: 1 } }
}
""" % ( name, self.last, name, output))
        self.last = name

    def generate(self, stage, lmdb, label_map, class_num, batch, gen_ssd, size, quantize=False):
      self.class_num = class_num
      self.lmdb = lmdb
      self.label_map = label_map
      self.stage = stage
      self.batch = batch
      self.quantize = quantize
      if gen_ssd:
          self.input_size = 300
      else:
          self.input_size = 224
      self.size = size
      self.class_num = class_num

      if gen_ssd:
          self.header("MobileNet-SSD")
      else:
          self.header("MobileNet")
      if self.quantize:
          self.quantizeNet()
      if stage == "train":
          if gen_ssd:
              assert(self.lmdb is not None)
              assert(self.label_map is not None)
              self.data_train_ssd()
          else:
              assert(self.lmdb is not None)
              self.data_train_classifier()
      elif stage == "test":
          self.data_test_ssd()
      else:
          self.data_deploy()
      self.conv_bn_relu_with_factor("conv0", 32, 3, 2)
      self.conv_dw_pw("conv1", 32,  64, 1)
      self.conv_dw_pw("conv2", 64, 128, 2)
      self.conv_dw_pw("conv3", 128, 128, 1)
      self.conv_dw_pw("conv4", 128, 256, 2)
      self.conv_dw_pw("conv5", 256, 256, 1)
      self.conv_dw_pw("conv6", 256, 512, 2)
      self.conv_dw_pw("conv7", 512, 512, 1)
      self.conv_dw_pw("conv8", 512, 512, 1)
      self.conv_dw_pw("conv9", 512, 512, 1)
      self.conv_dw_pw("conv10",512, 512, 1)
      self.conv_dw_pw("conv11",512, 512, 1)
      self.conv_dw_pw("conv12",512, 1024, 2)
      self.conv_dw_pw("conv13",1024, 1024, 1)
      if gen_ssd is True:
          self.conv_bn_relu("conv14_1", 256, 1, 1)
          self.conv_bn_relu("conv14_2", 512, 3, 2)
          self.conv_bn_relu("conv15_1", 128, 1, 1)
          self.conv_bn_relu("conv15_2", 256, 3, 2)
          self.conv_bn_relu("conv16_1", 128, 1, 1)
          self.conv_bn_relu("conv16_2", 256, 3, 2)
          self.conv_bn_relu("conv17_1", 64,  1, 1)
          self.conv_bn_relu("conv17_2", 128, 3, 2)
          self.mbox("conv11", 3)
          self.mbox("conv13", 6)
          self.mbox("conv14_2", 6)
          self.mbox("conv15_2", 6)
          self.mbox("conv16_2", 6)
          self.mbox("conv17_2", 6)
          self.concat_boxes(['conv11', 'conv13', 'conv14_2', 'conv15_2', 'conv16_2', 'conv17_2'])
          if stage == "train":
             self.ssd_loss()
          elif stage == "deploy":
             self.ssd_predict()
          else:
             self.ssd_test()
      else:
          self.ave_pool("pool")
          self.conv("fc", class_num, 1, 1, 1, True)
          if stage == "train":
             self.classifier_loss()


def create_ssd_anchors(num_layers=6,
                       min_scale=0.2,
                       max_scale=0.95):
  box_specs_list = []
  scales = [min_scale + (max_scale - min_scale) * i / (num_layers - 1)
            for i in range(num_layers)] + [1.0]
  return list(zip(scales[:-1], scales[1:]))

def proto_generator(train_path,stage,lmdb,labelmap,classes,batch, background=0, gen_ssd=True, size=1.0):
  gen = Generator(train_path)
  gen.generate(stage,lmdb,labelmap,classes,batch,gen_ssd, size)


def proto_generator_BonseyesCaffe(train_path,stage,lmdb,labelmap,classes,batch, quantize=False, background=0, gen_ssd=True, size=1.0):
  gen = Generator(train_path)
  gen.generate(stage,lmdb,labelmap,classes,batch,gen_ssd, size, quantize)


def solver_generator(filepath,net,max_it,output_path,eval_type):
  with open(filepath, 'w') as f:
    f.write( """net: "%s"
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
    f.write( """train_net: "%s"
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

def solver_generator_BonseyesCaffe(filepath, net, max_it, output_path, eval_type):
        with open(filepath, 'w') as f:
            f.write(
"""net: "%s"
# test_net: "./examples/MobileNet/proto/MobileNetSSD_test.prototxt"
# test_iter: 673
# test_interval: 10000
base_lr: 0.000005
display: 10
max_iter: % d
lr_policy: "multistep"
gamma: 0.5
weight_decay: 0.00005
snapshot: 1000
snapshot_prefix: "%ssnapshot"
solver_mode: GPU
debug_info: false
snapshot_after_train: true
# test_initialization: false
average_loss: 10
stepvalue: 20000
stepvalue: 40000
iter_size: 1
type: "RMSProp"
eval_type: "%s"
ap_version: "11point"


display_sparsity: 2000
sparse_mode: SPARSE_UPDATE
sparsity_target: 0.7
sparsity_step_factor: 0.02
sparsity_step_iter: 2000
sparsity_start_iter: 0
sparsity_start_factor: 0.0
# sparsity_threshold_maxratio: 0.2
# sparsity_itr_increment_bfr_applying: true
# sparsity_threshold_value_max: 0.2
show_per_class_result: true

""" % (net, max_it, output_path, eval_type))


def solver_generator_test_BonseyesCaffe(filepath,net_train, net_test,iter,output_path,eval_type):
  with open(filepath, 'w') as f:
    f.write( """train_net: "%s"
test_net: "%s"
test_iter: %d
test_interval: 10000
base_lr: 0.000005
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
# display_sparsity: 2000
# sparse_mode: SPARSE_UPDATE
# sparsity_target: 0.7
# sparsity_step_factor: 0.05
# sparsity_step_iter: 2000
# sparsity_start_iter: 0
# sparsity_start_factor: 0.25
# sparsity_threshold_maxratio: 0.2
# sparsity_itr_increment_bfr_applying: true
# sparsity_threshold_value_max: 0.2
show_per_class_result: true
""" % (net_train, net_test, iter, output_path, eval_type))