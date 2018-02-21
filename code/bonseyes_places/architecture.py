#
# NVISO CONFIDENTIAL
#
# Copyright (c) 2017 nViso SA. All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") is the confidential and proprietary information
# owned by nViso or its suppliers or licensors.  Title to the  Material remains
# with nViso SA or its suppliers and licensors. The Material contains trade
# secrets and proprietary and confidential information of nViso or its
# suppliers and licensors. The Material is protected by worldwide copyright and trade
# secret laws and treaty provisions. You shall not disclose such Confidential
# Information and shall use it only in accordance with the terms of the license
# agreement you entered into with nViso.
#
# NVISO MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF
# THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE, OR NON-INFRINGEMENT. NVISO SHALL NOT BE LIABLE FOR
# ANY DAMAGES SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR
# DISTRIBUTING THIS SOFTWARE OR ITS DERIVATIVES.
#

import numpy as np
import lasagne
from lasagne.layers import InputLayer
from lasagne.layers import Conv2DLayer
from lasagne.layers import BatchNormLayer
from lasagne.layers import Pool2DLayer
from lasagne.layers import NonlinearityLayer
from lasagne.layers import ElemwiseSumLayer
from lasagne.layers import DenseLayer
from lasagne.layers import DropoutLayer
from lasagne.layers import FlattenLayer
from lasagne.layers import rrelu
from lasagne.nonlinearities import rectify, softmax, leaky_rectify
from lasagne.init import Glorot, GlorotUniform


def build_mlp(input_var=None):
    # This creates an MLP of two hidden layers of 800 units each, followed by
    # a softmax output layer of 10 units. It applies 20% dropout to the input
    # data and 50% dropout to the hidden layers.

    # Input layer, specifying the expected input shape of the network
    # (unspecified batchsize, 3 channel, 224 rows and 224 columns) and
    # linking it to the given Theano variable `input_var`, if any:
    l_in = lasagne.layers.InputLayer(shape=(None, 3, 224, 224),
                                     input_var=input_var)

    # Apply 20% dropout to the input data:
    l_in_drop = lasagne.layers.DropoutLayer(l_in, p=0.2)

    # Add a fully-connected layer of 800 units, using the linear rectifier, and
    # initializing weights with Glorot's scheme (which is the default anyway):
    l_hid1 = lasagne.layers.DenseLayer(
            l_in_drop, num_units=800,
            nonlinearity=lasagne.nonlinearities.rectify,
            W=lasagne.init.GlorotUniform())

    # We'll now add dropout of 50%:
    l_hid1_drop = lasagne.layers.DropoutLayer(l_hid1, p=0.5)

    # Another 800-unit layer:
    l_hid2 = lasagne.layers.DenseLayer(
            l_hid1_drop, num_units=800,
            nonlinearity=lasagne.nonlinearities.rectify)

    # 50% dropout again:
    l_hid2_drop = lasagne.layers.DropoutLayer(l_hid2, p=0.5)

    # Finally, we'll add the fully-connected output layer, of 10 softmax units:
    l_out = lasagne.layers.DenseLayer(
            l_hid2_drop, num_units=205,
            nonlinearity=lasagne.nonlinearities.softmax)

    # Each layer is linked to its incoming layer(s), so we only need to pass
    # the output layer to give access to a network in Lasagne:
    return l_out


def build_cnn(input_var=None):
    # As a third model, we'll create a CNN of two convolution + pooling stages
    # and a fully-connected hidden layer in front of the output layer.

    # Input layer, as usual:
    network = lasagne.layers.InputLayer(shape=(None, 3, 224, 224),
                                        input_var=input_var)
    # This time we do not apply input dropout, as it tends to work less well
    # for convolutional layers.

    # Convolutional layer with 32 kernels of size 5x5. Strided and padded
    # convolutions are supported as well; see the docstring.
    network = lasagne.layers.Conv2DLayer(
            network, num_filters=32, filter_size=(5, 5),
            nonlinearity=lasagne.nonlinearities.rectify,
            W=lasagne.init.GlorotUniform())
    # Expert note: Lasagne provides alternative convolutional layers that
    # override Theano's choice of which implementation to use; for details
    # please see http://lasagne.readthedocs.org/en/latest/user/tutorial.html.

    # Max-pooling layer of factor 2 in both dimensions:
    network = lasagne.layers.MaxPool2DLayer(network, pool_size=(2, 2))

    # Another convolution with 32 5x5 kernels, and another 2x2 pooling:
    network = lasagne.layers.Conv2DLayer(
            network, num_filters=32, filter_size=(5, 5),
            nonlinearity=lasagne.nonlinearities.rectify)
    network = lasagne.layers.MaxPool2DLayer(network, pool_size=(2, 2))

    # A fully-connected layer of 256 units with 50% dropout on its inputs:
    network = lasagne.layers.DenseLayer(
            lasagne.layers.dropout(network, p=.5),
            num_units=256,
            nonlinearity=lasagne.nonlinearities.rectify)

    # And, finally, the 10-unit output layer with 50% dropout on its inputs:
    network = lasagne.layers.DenseLayer(
            lasagne.layers.dropout(network, p=.5),
            num_units=10,
            nonlinearity=lasagne.nonlinearities.softmax)

    return network


def build_ImageNet(input_var=None):
    
    net = {}
    
    net['input'] = lasagne.layers.InputLayer(shape=(None, 3, 224, 224), input_var=input_var)
    net['conv1'] = lasagne.layers.Conv2DLayer(net['input'], num_filters=96, filter_size=(7, 7), stride=(2,2), flip_filters=False)
    net['norm1'] = lasagne.layers.BatchNormLayer(net['conv1'], alpha=0.0001) # caffe has alpha = alpha * pool_size
    net['pool1'] = lasagne.layers.Pool2DLayer(net['norm1'], pool_size=3, stride=3, ignore_border=False)
    net['conv2'] = lasagne.layers.Conv2DLayer(net['pool1'], num_filters=256, filter_size=(5,5), flip_filters=False)
    net['pool2'] = lasagne.layers.Pool2DLayer(net['conv2'], pool_size=2, stride=2, ignore_border=False)
    net['conv3'] = lasagne.layers.Conv2DLayer(net['pool2'], num_filters=512, filter_size=(3,3), pad=1, flip_filters=False)
    net['conv4'] = lasagne.layers.Conv2DLayer(net['conv3'], num_filters=512, filter_size=(3,3), pad=1, flip_filters=False)
    net['conv5'] = lasagne.layers.Conv2DLayer(net['conv4'], num_filters=512, filter_size=(3,3), pad=1, flip_filters=False)
    net['pool5'] = lasagne.layers.Pool2DLayer(net['conv5'], pool_size=3, stride=3, ignore_border=False)
    net['fc6'] = lasagne.layers.DenseLayer(net['pool5'], num_units=4096)
    net['drop6'] = lasagne.layers.DropoutLayer(net['fc6'], p=0.25)
    net['fc7'] = lasagne.layers.DenseLayer(net['drop6'], num_units=4096)
    net['drop7'] = lasagne.layers.DropoutLayer(net['fc7'], p=0.25)
    net['fc8'] = lasagne.layers.DenseLayer(net['drop7'], num_units=10, nonlinearity=lasagne.nonlinearities.softmax)
        
    return net['fc8']


def fire_expand_block(input_layer, name, nr_filter_squeeze, nr_filter_expand):
    
    net = {}
    # squeeze
    net[name+'squeeze1x1'] = BatchNormLayer(ConvLayer(input_layer, 
                                            nr_filter_squeeze, 1, pad='same',nonlinearity=None, W=GlorotUniform('relu')))
    net[name+'relu_squeeze1x1'] = rrelu(net[name+'squeeze1x1'])
    
    # expand left
    net[name+'expand1x1'] = BatchNormLayer(ConvLayer(net[name+'relu_squeeze1x1'], 
                                            nr_filter_expand, 1, pad='same', nonlinearity=None, W=GlorotUniform('relu')))
    net[name+'relu_expand1x1'] = rrelu(net[name+'expand1x1'])
    
    # expand right    
    net[name+'expand3x3'] = BatchNormLayer(ConvLayer(net[name+'relu_squeeze1x1'], 
                                            nr_filter_expand, 3, pad='same', nonlinearity=None,  W=GlorotUniform('relu')))
    net[name+'relu_expand3x3'] = rrelu(net[name+'expand3x3'])

    return net
    
def build_squeeznetv2(block_names, input_var=None, output_dim=205):
    net = {}
    
    net['input'] = InputLayer(shape=(None, 3, 224, 224),input_var=input_var)
    net['conv1'] = BatchNormLayer(ConvLayer(net['input'], 64, 3, stride=(2,2), pad='same', nonlinearity=None, W=GlorotUniform('relu')))
    net['relu_conv1'] = rrelu(net['conv1'])
    net['pool1'] = PoolLayer(net['relu_conv1'], 3, stride=(2,2), mode='max')
    
    sub_net = fire_expand_block(net['pool1'], block_names[0], nr_filter_squeeze=16, nr_filter_expand=64)
    net.update(sub_net)
    #fire2/concat
    net[block_names[0]+'concat'] = ConcatLayer([sub_net[block_names[0]+'relu_expand1x1'],sub_net[block_names[0]+'relu_expand3x3']], axis = 1)
     
    sub_net= fire_expand_block(net[block_names[0]+'concat'], block_names[1], nr_filter_squeeze=16, nr_filter_expand=64)
    net.update(sub_net)
    #fire3/concat
    net[block_names[1]+'concat'] = ConcatLayer([sub_net[block_names[1]+'relu_expand1x1'],sub_net[block_names[1]+'relu_expand3x3']], axis = 1)
    
    net['pool3'] = PoolLayer(net[block_names[1]+'concat'], 3, stride=(2,2), mode='max')
    
    sub_net = fire_expand_block(net['pool3'], block_names[2], nr_filter_squeeze=32, nr_filter_expand=128)
    net.update(sub_net)
    #fire4/concat
    net[block_names[2]+'concat'] = ConcatLayer([sub_net[block_names[2]+'relu_expand1x1'],sub_net[block_names[2]+'relu_expand3x3']], axis = 1) 
    
    sub_net = fire_expand_block(net[block_names[2]+'concat'], block_names[3], nr_filter_squeeze=32, nr_filter_expand=128)
    net.update(sub_net)
    #fire5/concat
    net[block_names[3]+'concat'] = ConcatLayer([sub_net[block_names[3]+'relu_expand1x1'],sub_net[block_names[3]+'relu_expand3x3']], axis = 1)
    
    net['pool5'] = PoolLayer(net[block_names[3]+'concat'], 3, stride=(2,2), mode='max')
    
    sub_net = fire_expand_block(net['pool5'], block_names[4], nr_filter_squeeze=48, nr_filter_expand=192)
    net.update(sub_net)
    #fire6/concat
    net[block_names[4]+'concat'] = ConcatLayer([sub_net[block_names[4]+'relu_expand1x1'],sub_net[block_names[4]+'relu_expand3x3']], axis = 1)
     
    sub_net = fire_expand_block(net[block_names[4]+'concat'], block_names[5], nr_filter_squeeze=48, nr_filter_expand=192)
    net.update(sub_net)
    #fire7/concat
    net[block_names[5]+'concat'] = ConcatLayer([sub_net[block_names[5]+'relu_expand1x1'],sub_net[block_names[5]+'relu_expand3x3']], axis = 1)
    
    sub_net = fire_expand_block(net[block_names[5]+'concat'], block_names[6], nr_filter_squeeze=64, nr_filter_expand=256)
    net.update(sub_net)
    #fire8/concat
    net[block_names[6]+'concat'] = ConcatLayer([sub_net[block_names[6]+'relu_expand1x1'],sub_net[block_names[6]+'relu_expand3x3']], axis = 1)
    
    sub_net = fire_expand_block(net[block_names[6]+'concat'], block_names[7], nr_filter_squeeze=64, nr_filter_expand=256)
    net.update(sub_net)
    #fire9/concat
    net[block_names[7]+'concat'] = ConcatLayer([sub_net[block_names[7]+'relu_expand1x1'],sub_net[block_names[7]+'relu_expand3x3']], axis = 1)
    
    net['drop9'] = DropoutLayer(net[block_names[7]+'concat'], p = 0.5)
    
    net['conv10'] = ConvLayer(net['drop9'], output_dim, 1, pad='same', nonlinearity=None, W=GlorotUniform('relu'))
    net['relu_conv10'] = rrelu(net['conv10'])
    
    net['pool10'] = PoolLayer(net['relu_conv10'], 13, pad=0, mode='average_exc_pad', ignore_border=False, stride=1)
    
    net['prob'] = NonlinearityLayer(FlattenLayer(net['pool10']), nonlinearity=softmax)
    
    return net['prob']


def iterate_minibatches(inputs, targets, batchsize, shuffle=False):
    assert len(inputs) == len(targets)
    if shuffle:
        indices = np.arange(len(inputs))
        np.random.shuffle(indices)
    for start_idx in range(0, len(inputs) - batchsize + 1, batchsize):
        if shuffle:
            excerpt = indices[start_idx:start_idx + batchsize]
        else:
            excerpt = slice(start_idx, start_idx + batchsize)
        yield inputs[excerpt], targets[excerpt]
