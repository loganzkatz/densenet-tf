import tensorflow as tf 
from tensorflow.examples.tutorials.mnist import input_data

#Basic functions for initializing layers
def weights_init(shape):
    return tf.Variable(tf.truncated_normal(shape))

def bias_init(shape):
    return tf.Variable(tf.constant(0.1))

def conv2d(x, w):
    return tf.nn.conv2d(x, w, strides=[1,1,1,1], padding='SAME')

def maxpool(x):
    return tf.nn.max_pool(x, ksize=[1,2,2,1], strides=[1,2,2,1], padding="VALID")

def dropout(x, keep):
    return tf.nn.dropout(x, keep)

##The slightly more complicated blocks of layers

#Basic block of the model
#Takes in a convolution layer, adds batch norm, relu, and a new convolution with dropout
def bn_relu_conv(inputs, w_shape, b_shape, keep):
    w = weights_init(w_shape) 
    b = bias_init(b_shape) 
    batch = tf.contrib.layers.batch_norm(inputs)
    relu = tf.nn.relu(batch + b)
    conv = conv2d(relu, w)
    drop = dropout(conv, keep)
    return drop

#Adds a batch norm/relu/conv layer and concatenates it with the input layer
def add_layer(bottom, num_filter, keep):
    num_old = int(bottom.get_shape()[3])
    brc = bn_relu_conv(bottom, [3,3,num_old,num_filter], [num_filter], keep)
    concat = tf.concat(3, [bottom, brc])
    return concat

#The transition layer between blocks
#Performs a bn/relu/conv and then a 2x2 maxpool to reduce the image size
def transition(bottom, num_filter, keep):
    num_old = int(bottom.get_shape()[3])
    brc = bn_relu_conv(bottom, [3,3,num_old,num_filter], [num_filter], keep)
    pool = maxpool(brc)
    return pool

#The actual training step
def train_model(depth=7, first_output=16, growth_rate=12, drop_num=0.5):
    x = tf.placeholder(tf.float32, shape=[None, 784])
    y = tf.placeholder(tf.float32, shape=[None, 10])
    keep = tf.placeholder(tf.float32)
    mnist = input_data.read_data_sets('MNIST_data', one_hot=True)
    
    n_classes = 10

    n_channels = first_output
    #First conv layer
    with tf.variable_scope("input"):
        x_in = tf.reshape(x, [-1,28,28,1])
        w = weights_init([3,3,1,n_channels])
        layer = conv2d(x_in, w)

    N = (depth - 3)/2

    for i in range(1,N+1):
        name = "block1-{}".format(i)
        with tf.variable_scope(name): 
            layer = add_layer(layer, n_channels, keep)
        n_channels += growth_rate
    with tf.variable_scope("trans1"):
        layer = transition(layer, n_channels, keep)

    for i in range(1,3):
        name = "block2-{}".format(i)
        with tf.variable_scope(name): 
            layer = add_layer(layer, n_channels, keep)
        n_channels += growth_rate

    with tf.variable_scope("output"):
        batch = tf.contrib.layers.batch_norm(layer)
        relu = tf.nn.relu(batch)
        rs = relu.get_shape()
        n_flat = int(rs[1])*int(rs[2])*int(rs[3])
        flat = tf.reshape(relu, [-1, n_flat])
        w = weights_init([n_flat, n_classes])
        b = bias_init([n_classes])
        dense = tf.matmul(flat, w)
        output = tf.nn.softmax(dense + b)

    cross_entropy = tf.reduce_mean(-tf.reduce_sum(y * tf.log(output), reduction_indices=[1]))
    train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)

    correct_prediction = tf.equal(tf.argmax(output,1), tf.argmax(y,1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

    with tf.Session() as sess:
        sess.run(tf.initialize_all_variables())
        summary_writer = tf.train.SummaryWriter('../logs/', sess.graph)
        for i in range(1000):
            batch = mnist.train.next_batch(100)
            if i%100 == 0:
                train_accuracy = accuracy.eval(feed_dict={x:batch[0], y: batch[1], keep: 1})
                print "Accuracy: {}".format(train_accuracy)
            results = sess.run(train_step, feed_dict={x: batch[0], y: batch[1], keep: drop_num})

        

if __name__ == "__main__":
    train_model()
