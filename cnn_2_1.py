from skimage import io
import numpy as np
import tensorflow as tf
import sys, os, scipy

def shuffle_in_unison(a, b):
	rng_state = np.random.get_state()
	np.random.shuffle(a)
	np.random.set_state(rng_state)
	np.random.shuffle(b)

def weight_variable(shape):
	initial = tf.truncated_normal(shape, stddev=0.1)
	return tf.Variable(initial)

def bias_variable(shape):
	initial = tf.constant(0.1, shape=shape)
	return tf.Variable(initial)

def conv2d(x, W):
	return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

def max_pool_2x2(x):
	return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
						strides=[1, 2, 2, 1], padding='SAME')


train_path = 'train/'
valid_path = 'valid/'
px = 64
n_train, n_valid = 17205, 1829
n_iters = 100000
n_labels = 104

#####################################
# initializing tensorflow variables #
#####################################

x = tf.placeholder(tf.float32, [None, px, px])
x_image = tf.reshape(x, [-1,px,px,1])

W_conv1 = weight_variable([5, 5, 1, 32])
b_conv1 = bias_variable([32])

h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)
h_pool1 = max_pool_2x2(h_conv1)


# takes in 32 features, spits out 64 features
W_conv2 = weight_variable([5, 5, 32, 64])
b_conv2 = bias_variable([64])

# h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)
h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)
h_pool2 = max_pool_2x2(h_conv2)


# takes in 64 features, spits out 128 features
W_fc1 = weight_variable([16 * 16 * 64, n_labels])
b_fc1 = bias_variable([n_labels])

h_pool2_flat = tf.reshape(h_pool2, [-1, 16*16*64])
y_conv = tf.matmul(h_pool2_flat, W_fc1) + b_fc1

keep_prob = tf.placeholder(tf.float32)

y_ = tf.placeholder(tf.int64, [None])

cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(y_conv, y_)

train_step = tf.train.AdamOptimizer(1e-3).minimize(cross_entropy)
correct_prediction = tf.equal(tf.argmax(y_conv, 1), y_)
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

init = tf.initialize_all_variables()

sess = tf.Session()
sess.run(init)

#############################################
# variables initialized, time to read files #
#############################################

train_labels = []
valid_labels = []

with open(train_path + 'labels.txt') as f:
	train_labels = f.readlines()

with open(valid_path + 'labels.txt') as f:
	valid_labels = f.readlines()

train_labels = np.array([int(i) for i in train_labels])
train_index = [i for i in range(len(train_labels)) if train_labels[i] < n_labels]
train_labels = np.array([train_labels[i] for i in train_index])

valid_labels = np.array([int(i) for i in valid_labels])
valid_index = [i for i in range(len(valid_labels)) if valid_labels[i] < n_labels]
valid_labels = np.array([valid_labels[i] for i in valid_index])

train = np.array([scipy.misc.imresize(io.imread(train_path+str(i)+'.png'), (px/320.0)) for i in train_index], dtype='float32')
# train = np.array([[item for sublist in l for item in sublist] for l in train])

valid = np.array([scipy.misc.imresize(io.imread(valid_path+str(i)+'.png'), px/320.0) for i in valid_index], dtype='float32')
# valid = np.array([[item for sublist in l for item in sublist] for l in valid])

#################################
# files read, time to train now #
#################################

for i in range(n_iters):
	batch_xs = train[100*(i%3) : 100*(i%3+1)]
	batch_ys = train_labels[100*(i%3) : 100*(i%3+1)]
	if i%100 == 0:
		shuffle_in_unison(train, train_labels)
	if i%100 == 0:
		train_accuracy = sess.run(accuracy, feed_dict={x: train[:n_train/100], y_: train_labels[:n_train/100], keep_prob: 0.5})
		valid_accuracy = sess.run(accuracy, feed_dict={x: valid[:n_valid/2], y_: valid_labels[:n_valid/2], keep_prob: 0.5})
		print("step %d, training accuracy %g validation accuracy %g"%(i, train_accuracy, valid_accuracy))	
	sess.run(train_step, feed_dict={x: batch_xs, y_: batch_ys, keep_prob: 0.5})

