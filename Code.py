#Import libraries

import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
import cv2
from os import listdir
from os.path import join, isfile
import keras

from PIL import Image
from sklearn.preprocessing import LabelBinarizer
from keras.models import Sequential, Model
from tensorflow.keras.layers import BatchNormalization
from keras.layers.convolutional import Conv2D
from keras.layers.convolutional import MaxPooling2D
from keras.layers import Dense, Conv2D, MaxPool2D , Flatten
from keras.layers import Input, GlobalAveragePooling2D, concatenate, AveragePooling2D
from keras.layers.core import Activation, Flatten, Dropout
from keras import backend as K
from keras.preprocessing.image import ImageDataGenerator
from keras.optimizers import Adam
from keras.preprocessing import image
from tensorflow.keras.utils import img_to_array
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix,accuracy_score
from sklearn.decomposition import PCA

"""#Data Augmentation"""

default_image_size = tuple((224, 224))
directory_root = '/content/drive/MyDrive/Dataset'

# horizontal flip
def hflip(image_dir):
  image = cv2.imread(image_dir)
  image = cv2.flip(image, 0) 
  return convert_image_to_array(image)

# vertical flip
def vflip(image_dir):
  image = cv2.imread(image_dir)
  image = cv2.flip(image, 1)   
  return convert_image_to_array(image)

# histogram equalization function
def hist(img):
  img_to_yuv = cv2.cvtColor(img,cv2.COLOR_BGR2YUV)
  img_to_yuv[:,:,0] = cv2.equalizeHist(img_to_yuv[:,:,0])
  hist_equalization_result = cv2.cvtColor(img_to_yuv, cv2.COLOR_YUV2BGR)
  return hist_equalization_result

#gaussian blurring
from scipy import ndimage
def gaussian(img):
  img = ndimage.gaussian_filter(img, sigma= 5.11)
  return img

# function for rotation
import random
def rotation(img):
  img = cv2.imread(img)
  rows,cols = img.shape[0],img.shape[1]
  randDeg = random.randint(-180, 180)
  matrix = cv2.getRotationMatrix2D((cols/2, rows/2), randDeg, 0.70)
  rotated = cv2.warpAffine(img, matrix, (rows, cols), borderMode=cv2.BORDER_CONSTANT)
  return convert_image_to_array(rotated)  

def convert_image_to_array(image_dir):
    try:
        if type(image_dir) is str :
            image = cv2.imread(image_dir)
        else :
            image = image_dir
        if image is not None :
            image = gaussian(image)
            image = hist(image)
            image=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
            image = cv2.resize(image, default_image_size)   
            return img_to_array(image)
        else :
            return np.array([])
    except Exception as e:
        print(f"Error : {e}")
        return None

"""#Load Dataset"""

image_list, label_list = [], []

try:
    print("[INFO] Loading images ...")
    root_dir = listdir(directory_root)

    for plant_folder in root_dir :
        plant_disease_image_list = listdir(f"{directory_root}/{plant_folder}")
                
        for image in plant_disease_image_list:
            image_directory = f"{directory_root}/{plant_folder}/{image}"
            image_list.append(convert_image_to_array(image_directory))
            label_list.append(plant_folder)
            image_list.append(hflip(image_directory))
            label_list.append(plant_folder)
            image_list.append(vflip(image_directory))
            label_list.append(plant_folder)
            image_list.append(rotation(image_directory))
            label_list.append(plant_folder)
    print("[INFO] Image loading completed")  
except Exception as e:
    print(f"Error : {e}")

"""#Pre-processing"""

label_binarizer = LabelBinarizer()
image_labels = label_binarizer.fit_transform(label_list)
n_classes = len(label_binarizer.classes_)

len(image_list)

np_image_list = np.array(image_list, dtype=np.float16) / 225.0

from sklearn.model_selection import train_test_split
print("[INFO] Spliting data to train, test")
x_train, x_test, y_train, y_test = train_test_split(np_image_list, image_labels, test_size=0.33, random_state = 42)

from keras.utils import np_utils
y_test = np_utils.to_categorical(y_test)
y_train=np_utils.to_categorical(y_train)

print("X_train shape : ",x_train.shape)
print("y_train shape : ",y_train.shape)
print("X_test shape : ",x_test.shape)
print("y_test shape : ",y_test.shape)

#Define Deep Learning models

**DenseNet**

def conv_layer(conv_x, filters):
    conv_x = BatchNormalization()(conv_x)
    conv_x = Activation('relu')(conv_x)
    conv_x = Conv2D(filters, (3, 3), kernel_initializer='he_uniform', padding='same', use_bias=False)(conv_x)
    conv_x = Dropout(0.2)(conv_x)
    return conv_x


def dense_block(block_x, filters, growth_rate, layers_in_block):
    for i in range(layers_in_block):
        each_layer = conv_layer(block_x, growth_rate)
        block_x = concatenate([block_x, each_layer], axis=-1)
        filters += growth_rate

    return block_x, filters


def transition_block(trans_x, tran_filters):
    trans_x = BatchNormalization()(trans_x)
    trans_x = Activation('relu')(trans_x)
    trans_x = Conv2D(tran_filters, (1, 1), kernel_initializer='he_uniform', padding='same', use_bias=False)(trans_x)
    trans_x = AveragePooling2D((2, 2), strides=(2, 2))(trans_x)

    return trans_x, tran_filters


def dense_net(filters, growth_rate, classes, dense_block_size, layers_in_block):
    input_img = Input(shape=(224, 224, 1))
    x = Conv2D(24, (3, 3), kernel_initializer='he_uniform', padding='same', use_bias=False)(input_img)

    dense_x = BatchNormalization()(x)
    dense_x = Activation('relu')(x)

    dense_x = MaxPooling2D((3, 3), strides=(2, 2), padding='same', name='feature_layer')(dense_x)
    for block in range(dense_block_size - 1):
        dense_x, filters = dense_block(dense_x, filters, growth_rate, layers_in_block)
        dense_x, filters = transition_block(dense_x, filters)

    dense_x, filters = dense_block(dense_x, filters, growth_rate, layers_in_block)
    dense_x = BatchNormalization()(dense_x)
    dense_x = Activation('relu')(dense_x)
    dense_x = GlobalAveragePooling2D()(dense_x)

    output = Dense(classes, activation='softmax')(dense_x)

    return Model(input_img, output)

def densenet():
  dense_block_size = 1
  layers_in_block = 4

  growth_rate = 12
  classes = 2
  model = dense_net(growth_rate * 2, growth_rate, classes, dense_block_size, layers_in_block)
  return model

"""**Convolution Neural Network**"""

def cnn():
  model = Sequential()
  depth=1
  height=224
  width=224
  inputShape = (height, width, depth)
  chanDim = -1
  if K.image_data_format() == "channels_first":
      inputShape = (depth, height, width)
      chanDim = 1
  print(inputShape)
  model.add(Conv2D(32, (3, 3), padding="same",input_shape=inputShape))
  model.add(Activation("relu"))
  model.add(BatchNormalization(axis=chanDim))
  model.add(MaxPooling2D(pool_size=(3, 3)))
  model.add(Dropout(0.25))
  model.add(Conv2D(64, (3, 3), padding="same"))
  model.add(Activation("relu"))
  model.add(BatchNormalization(axis=chanDim))
  model.add(Conv2D(64, (3, 3), padding="same"))
  model.add(Activation("relu"))
  model.add(BatchNormalization(axis=chanDim))
  model.add(MaxPooling2D(pool_size=(2, 2)))
  model.add(Dropout(0.25))
  model.add(Conv2D(128, (3, 3), padding="same"))
  model.add(Activation("relu"))
  model.add(BatchNormalization(axis=chanDim))
  model.add(Conv2D(128, (3, 3), padding="same"))
  model.add(Activation("relu"))
  model.add(BatchNormalization(axis=chanDim))
  model.add(MaxPooling2D(pool_size=(2, 2),name='feature_layer'))
  model.add(Dropout(0.25))
  model.add(Flatten())
  model.add(Dense(1024))
  model.add(Activation("relu"))
  model.add(BatchNormalization())
  model.add(Dropout(0.5))
  model.add(Dense(n_classes))
  model.add(Activation("softmax"))
  return model

"""**ResNet**"""

# initializer =  keras.initializers.glorot_uniform(seed=0)
initializer = initializers.glorot_normal()

"""
Creates Residual Network with 50 layers
"""
def resnet(input_shape=(224, 224, 1), classes=2):
    # Define the input as a tensor with shape input_shape
    X_input = layers.Input(input_shape)

    # Zero-Padding
    X = layers.ZeroPadding2D((3, 3))(X_input)
    
    # Stage 1
    X = layers.Conv2D(64, (7, 7), strides=(2, 2), name='conv1', 
                            kernel_initializer=initializer)(X)
    X = layers.BatchNormalization(axis=3, name='bn_conv1')(X)
    X = layers.Activation('relu')(X)
    X = layers.MaxPooling2D((3, 3), strides=(2, 2))(X)

    # Stage 2
    X = convolutional_block(X, f = 3, filters=[64, 64, 256], stage=2, block='a', s=1)
    X = identity_block(X, 3, [64, 64, 256], stage=2, block='b')
    X = identity_block(X, 3, [64, 64, 256], stage=2, block='c')

    # Stage 3
    X = convolutional_block(X, f = 3, filters=[128, 128, 512], stage=3, block='a', s=2)
    X = identity_block(X, 3, [128, 128, 512], stage=3, block='b')
    X = identity_block(X, 3, [128, 128, 512], stage=3, block='c')
    X = identity_block(X, 3, [128, 128, 512], stage=3, block='d')

    # Stage 4
    X = convolutional_block(X, f = 3, filters=[256, 256, 1024], stage=4, block='a', s=2)
    X = identity_block(X, 3, [256, 256, 1024], stage=4, block='b')
    X = identity_block(X, 3, [256, 256, 1024], stage=4, block='c')
    X = identity_block(X, 3, [256, 256, 1024], stage=4, block='d')
    X = identity_block(X, 3, [256, 256, 1024], stage=4, block='e')
    X = identity_block(X, 3, [256, 256, 1024], stage=4, block='f')
    
    # Stage 5
    X = convolutional_block(X, f = 3, filters=[512, 512, 2048], stage=5, block='a', s=2)
    X = identity_block(X, 3, [512, 512, 2048], stage=5, block='b')
    X = identity_block(X, 3, [512, 512, 2048], stage=5, block='c')

    # AVGPOOL
    X = layers.AveragePooling2D(pool_size=(2, 2),name='feature_layer')(X)
    
    # output layer
    X = layers.Flatten()(X)
    X = layers.Dense(classes, activation='softmax', name='fc{}'
                            .format(classes), kernel_initializer=initializer)(X)
    
    # Create model
    model = keras.models.Model(inputs=X_input, outputs=X, name='resnet50')

    return model

"""
Identity Block of ResNet
"""
def identity_block(X, f, filters, stage, block):
    # defining name basis
    conv_name_base = 'res' + str(stage) + block + '_branch'
    bn_name_base = 'bn' + str(stage) + block + '_branch'

    # Retrieve Filters
    F1, F2, F3 = filters
    
    # Save the input value. You'll need this later to add back to the main path. 
    X_shortcut = X
    
    # First component of main path
    X = layers.Conv2D(filters=F1, kernel_size=(1, 1), strides=(1,1), padding='same', 
                            name=conv_name_base + '2a', kernel_initializer=initializer)(X)
    X = layers.BatchNormalization(axis=3, name=bn_name_base + '2a')(X)
    X = layers.Activation('relu')(X)
    X = layers.Dropout(0.5)(X)
    
    # Second component of main path
    X = layers.Conv2D(filters=F2, kernel_size=(f, f), strides=(1,1), padding='same', 
                            name=conv_name_base + '2b', kernel_initializer=initializer)(X)
    X = layers.BatchNormalization(axis=3, name=bn_name_base + '2b')(X)
    X = layers.Activation('relu')(X)
    X = layers.Dropout(0.5)(X)

    # Third component of main path
    X = layers.Conv2D(filters=F3, kernel_size=(1, 1), strides=(1,1), padding='same', 
                            name=conv_name_base + '2c', kernel_initializer=initializer)(X)
    X = layers.BatchNormalization(axis=3, name=bn_name_base + '2c')(X)

    # Add shortcut value to main path, and pass it through a RELU activation
    X = layers.Add()([X, X_shortcut])
    X = layers.Activation('relu')(X)
    
    return X

"""
Convolutional Block of ResNet
"""
def convolutional_block(X, f, filters, stage, block, s=2):
    # defining name basis
    conv_name_base = 'res' + str(stage) + block + '_branch'
    bn_name_base = 'bn' + str(stage) + block + '_branch'

    # Retrieve Filters
    F1, F2, F3 = filters
    
    # Save the input value
    X_shortcut = X

    # First component of main path 
    X = layers.Conv2D(F1, (1, 1), strides=(s, s), name=conv_name_base + '2a', 
                            padding='same', kernel_initializer=initializer)(X)
    X = layers.BatchNormalization(axis=3, name=bn_name_base + '2a')(X)
    X = layers.Activation('relu')(X)
    X = layers.Dropout(0.5)(X)
    
    # Second component of main path
    X = layers.Conv2D(F2, (f, f), strides=(1, 1), name=conv_name_base + '2b', 
                            padding='same', kernel_initializer=initializer)(X)
    X = layers.BatchNormalization(axis=3, name=bn_name_base + '2b')(X)
    X = layers.Activation('relu')(X)
    X = layers.Dropout(0.5)(X)

    # Third component of main path
    X = layers.Conv2D(F3, (1, 1), strides=(1, 1), name=conv_name_base + '2c', 
                            padding='same', kernel_initializer=initializer)(X)
    X = layers.BatchNormalization(axis=3, name=bn_name_base + '2c')(X)

    X_shortcut = layers.Conv2D(F3, (1, 1), strides=(s,s), name=conv_name_base + '1', 
                                    padding='same', kernel_initializer=initializer)(X_shortcut)
    X_shortcut = layers.BatchNormalization(axis=3, name=bn_name_base + '1')(X_shortcut)

    # Add shortcut value to main path, and pass it through a RELU activation
    X = layers.Add()([X, X_shortcut])
    X = layers.Activation('relu')(X)
    
    return X

"""#Define DL model functions"""

def sum(model):
  model.summary()

def comp(model):
  from keras.optimizers import Adam
  opt = Adam(lr=0.001)
  model.compile(optimizer=opt, loss=keras.losses.categorical_crossentropy, metrics=['accuracy'])

def fitmodel(model):
  hist=model.fit(x_train,y_train, epochs=16, batch_size=32, shuffle=True,
                    validation_data=(x_test, y_test), validation_steps=16)
  return hist

"""#Define Performance Metrics for DL models"""

def performance(model):
  print("[INFO] Calculating model accuracy")
  scores = model.evaluate(x_test, y_test)
  print(f"Test Accuracy: {scores[1]*100}")
  scores = model.evaluate(x_test, y_test)
  print(f"Train Accuracy: {model.evaluate(x_train,y_train)[1]*100}")

def graph(hist):
  acc = hist.history['accuracy']
  val_acc = hist.history['val_accuracy']
  loss = hist.history['loss']
  val_loss = hist.history['val_loss']
  epochs = range(1, len(acc) + 1)
  #Train and validation accuracy
  plt.plot(epochs, acc, 'b', label='Training accurarcy')
  plt.plot(epochs, val_acc, 'r', label='Validation accurarcy')
  plt.title('Training and Validation accurarcy')
  plt.legend()
  plt.figure()
  #Train and validation loss
  plt.plot(epochs, loss, 'b', label='Training loss')
  plt.plot(epochs, val_loss, 'r', label='Validation loss')
  plt.title('Training and Validation loss')
  plt.legend()
  plt.show()

"""#Execute DL models

**DenseNet**
"""

model_densenet=densenet()
sum(model_densenet)
comp(model_densenet)
hist_densenet=fitmodel(model_densenet)
performance(model_densenet)
graph(hist_densenet)

"""**CNN**"""

model_cnn=cnn()
sum(model_cnn)
comp(model_cnn)
hist_cnn=fitmodel(model_cnn)
performance(model_cnn)
graph(hist_cnn)

"""**ResNet**"""

model_resnet=resnet()
sum(model_resnet)
comp(model_resnet)
hist_resnet=fitmodel(model_resnet)
performance(model_resnet)
graph(hist_resnet)

"""#Define Feature Extraction"""

def extract(model,x_train,x_test,y_train,y_test):
  new_model=Model(inputs=model.input,outputs=model.get_layer('concatenate_11').output)

  #Let's obtain the Input Representations
  x_train_n=new_model.predict(x_train)
  x_test_n=new_model.predict(x_test)
  
  #Convert back the labels
  y_train_n=[ np.where(r==1)[0][0] for r in y_train ]
  y_test_n=[ np.where(r==1)[0][0] for r in y_test ]

  features=x_train_n.shape[1]*x_train_n.shape[2]*x_train_n.shape[3]
  x_train_new = np.reshape(x_train_n, (-1, features))
  x_test_new = np.reshape(x_test_n, (-1, features))

  x_train=x_train_new
  x_test=x_test_new
  y_train=y_train_n 
  y_test=y_test_n

  return x_train,x_test,y_train,y_test

"""#Feature Extraction from DL models

**DenseNet**
"""

x_train_densenet,x_test_densenet,y_train_densenet,y_test_densenet=extract(model_densenet,x_train,x_test,y_train,y_test)

"""**CNN**"""

x_train_cnn,x_test_cnn,y_train_cnn,y_test_cnn=extract(model_cnn,x_train,x_test,y_train,y_test)

"""**ResNet**"""

x_train_resnet,x_test_resnet,y_train_resnet,y_test_resnet=extract(model_resnet,x_train,x_test,y_train,y_test)

"""#Define Principal Component Analysis technique"""

def pca(x_train,x_test,model):
  if model=='densenet':
    components=361
  elif model=='cnn':
    components=256
  elif model=='vgg16':
    components=256
  
  pca_model = PCA(n_components=components)
  pca_model.fit(x_train)
  train_images_reduced = pca_model.transform(x_train)
  test_images_reduced = pca_model.transform(x_test)

  # verify shape after PCA
  print("Train images shape:", train_images_reduced.shape)
  print("Test images shape:", test_images_reduced.shape)
  
  # get exact variability retained
  print("\nVar retained (%):", 
        np.sum(pca_model.explained_variance_ratio_ * 100))

  x_train=train_images_reduced
  x_test=test_images_reduced

  return x_train,x_test

"""#Apply PCA on features extracted from DL models

**DenseNet**
"""

x_train_red_densenet,x_test_red_densenet=pca(x_train_densenet,x_test_densenet,densenet)

"""**CNN**"""

x_train_red_cnn,x_test_red_cnn=pca(x_train_cnn,x_test_cnn,cnn)

"""**ResNet**"""

x_train_red_resnet,x_test_red_resnet=pca(x_train_resnet,x_test_resnet,resnet)

"""#Define Performance Metrics for ML models"""

def display_metrics(a,b):
  conf_matrix = confusion_matrix(a,b)
  FP = conf_matrix[0,1]
  FN = conf_matrix[1,0]
  TP = conf_matrix[0,0]
  TN = conf_matrix[1,1]

  # Sensitivity, hit rate, recall, or true positive rate
  print("Recall/ Sensitivity: ",TP/(TP+FN))
  # Specificity or true negative rate
  print("Specificity: ",TN/(TN+FP)) 
  # Precision or positive predictive value
  print("Precision: ",TP/(TP+FP))
  # Fall out or false positive rate
  print("False positive rate: ",FP/(FP+TN))
  # Overall accuracy
  print("Accuracy: ",(TP+TN)/(TP+FP+FN+TN) *100)
  print("Classification Report: ")
  print(classification_report(a,b))

"""#Define Machine Learning classifiers

**K-Nearest Neighbor**
"""

def knn_ml(x_train,x_test,y_train,y_test):
  from sklearn.neighbors import KNeighborsClassifier
  knc=KNeighborsClassifier()
  knc.fit(x_train,y_train)
  knc.score(x_train,y_train)
  knn_y_pred=knc.predict(x_test)
  knn_x_pred=knc.predict(x_train)

  from sklearn.metrics import classification_report, confusion_matrix,accuracy_score
  print("Training Data : ")
  display_metrics(y_train,knn_x_pred)
  print("Testing Data : ")
  display_metrics(y_test,knn_y_pred) 

  return knc

"""**Support Vector Machine**"""

def svm_ml(x_train,x_test,y_train,y_test):
  from sklearn.svm import SVC
  svm = SVC(kernel='linear')
  svm.fit(x_train, y_train)
  svm_y_pred = svm.predict(x_test)
  svm_x_pred = svm.predict(x_train)

  from sklearn.metrics import classification_report, confusion_matrix,accuracy_score
  print("Training Data : ")
  display_metrics(y_train,svm_x_pred)
  print("Testing Data : ")
  display_metrics(y_test,svm_y_pred) 

  return svm

"""**Naive Bayes**"""

def naivebayes_ml(x_train,x_test,y_train,y_test):
  from sklearn.naive_bayes import GaussianNB
  nb = GaussianNB()
  nb.fit(x_train, y_train)
  nb_y_pred=nb.predict(x_test)
  nb_x_pred=nb.predict(x_train)

  from sklearn.metrics import classification_report, confusion_matrix,accuracy_score
  print("Training Data : ")
  display_metrics(y_train,nb_x_pred)
  print("Testing Data : ")
  display_metrics(y_test,nb_y_pred) 

  return nb

"""**Logistic Regression**"""

def logreg_ml(x_train,x_test,y_train,y_test):
  from sklearn.linear_model import LogisticRegression
  lr = LogisticRegression(solver='saga')
  lr.fit(x_train, y_train)
  lr_y_pred=lr.predict(x_test)
  lr_x_pred=lr.predict(x_train)

  from sklearn.metrics import classification_report, confusion_matrix,accuracy_score
  print("Training Data : ")
  display_metrics(y_train,lr_x_pred)
  print("Testing Data : ")
  display_metrics(y_test,lr_y_pred) 

  return lr

"""#Evaluate ML classifiers using DL extracted, reduced features

**DenseNet**
"""

densenet_knn = knn_ml(x_train_red_densenet,x_test_red_densenet,y_train_densenet,y_test_densenet)

densenet_svm = svm_ml(x_train_red_densenet,x_test_red_densenet,y_train_densenet,y_test_densenet)

densenet_nb = naivebayes_ml(x_train_red_densenet,x_test_red_densenet,y_train_densenet,y_test_densenet)

densenet_lr = logreg_ml(x_train_red_densenet,x_test_red_densenet,y_train_densenet,y_test_densenet)

"""**CNN**"""

cnn_knn = knn_ml(x_train_red_cnn,x_test_red_cnn,y_train_cnn,y_test_cnn)

cnn_svm = svm_ml(x_train_red_cnn,x_test_red_cnn,y_train_cnn,y_test_cnn)

cnn_nb = naivebayes_ml(x_train_red_cnn,x_test_red_cnn,y_train_cnn,y_test_cnn)

cnn_lr = logreg_ml(x_train_red_cnn,x_test_red_cnn,y_train_cnn,y_test_cnn)

"""**Resnet**"""

resnet_knn = knn_ml(x_train_red_resnet,x_test_red_resnet,y_train_resnet,y_test_resnet)

resnet_svm = svm_ml(x_train_red_resnet,x_test_red_resnet,y_train_resnet,y_test_resnet)

resnet_nb = naivebayes_ml(x_train_red_resnet,x_test_red_resnet,y_train_resnet,y_test_resnet)

resnet_lr = logreg_ml(x_train_red_resnet,x_test_red_resnet,y_train_resnet,y_test_resnet)

"""#Graphical User Interface"""

pip install gradio

import cv2
import gradio as gr

def densenet_svm_gui(image):
    image=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    image = cv2.resize(image, default_image_size)  
    l=[]
    l.append(img_to_array(image))
    l = np.array(l, dtype=np.float16) / 225.0
    data=np.reshape(l,(-1,224*224*1))
    result=densenet_svm.predict(data)
    if result==0:
        result="Healthy"
    else:
        result="Unhealthy"
    return result

#built interface with gradio to test the function
gr.Interface(fn=densenet_svm_gui, inputs="image", outputs="text",title='Densenet Model',allow_flagging="never").launch();
