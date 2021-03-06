import pandas as pd
import numpy as np
import os
import sys
import gzip
import argparse

import math
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from keras_utils import plot_prfrm_metrics

# import tensorflow as tf

# import keras as ke
# from keras import backend as K

# from keras.layers import Input, Dense, Dropout, Activation
# from keras.optimizers import SGD, Adam, RMSprop
# from keras.models import Sequential, Model, model_from_json, model_from_yaml
# from keras.utils import np_utils, multi_gpu_model

# from keras.callbacks import ModelCheckpoint, CSVLogger, ReduceLROnPlateau, EarlyStopping

# ------------------------------------------------------------------------
try:
    import tensorflow as tf
    if int(tf.__version__.split('.')[0]) < 2:
        import keras
        from keras import backend as K
        from keras.models import load_model
        from keras.callbacks import ModelCheckpoint, CSVLogger, ReduceLROnPlateau, EarlyStopping, TensorBoard
        from keras.utils import plot_model
    else:
        from tensorflow.keras.models import load_model, model_from_json, model_from_yaml
        from tensorflow.keras.callbacks import ModelCheckpoint, CSVLogger, ReduceLROnPlateau, EarlyStopping
        from tensorflow.keras.utils import plot_model

        from tensorflow.keras import backend as K
        from tensorflow.keras.layers import Input, Layer, Dense, Dropout, Activation, BatchNormalization
        from tensorflow.keras import optimizers
        from tensorflow.keras.optimizers import SGD, Adam
        from tensorflow.keras.models import Sequential, Model
except:
    print('Could not import tensorflow.')
# ------------------------------------------------------------------------

from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler, MinMaxScaler, MaxAbsScaler

file_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.abspath(os.path.join(file_path, '..', '..', 'common'))
sys.path.append(lib_path)

psr = argparse.ArgumentParser(description='input csv file')
psr.add_argument('--in',  default='in_file')
psr.add_argument('--ep',  type=int, default=400)
args=vars(psr.parse_args())
print(args)

EPOCH = args['ep']
BATCH = 32
#nb_classes = 2

data_path = args['in']
from pathlib import Path
data_path = Path(data_path)

data_path = data_path.with_suffix('')
outdir=Path('./out')/data_path.name
os.makedirs(outdir, exist_ok=True)

# df_toss = (pd.read_csv(data_path,nrows=1).values)
# df_toss = pd.read_parquet(data_path).values

# print('df_toss:', df_toss.shape)

# # PL = df_toss.size
# PL = df_toss.shape[1]
# PS = PL - 1

# print('PL=',PL)

#PL     = 6213   # 38 + 60483
#PS     = 6212   # 60483
DR    = 0.1      # Dropout rate

def r2(y_true, y_pred):
    SS_res =  K.sum(K.square(y_true - y_pred))
    SS_tot = K.sum(K.square(y_true - K.mean(y_true)))
    return (1 - SS_res/(SS_tot + K.epsilon()))

# class Attention(ke.layers.Layer):
class Attention(Layer):
   def __init__(self, output_dim, **kwargs):
       self.output_dim = output_dim
       super(Attention, self).__init__(**kwargs)

   def build(self, input_shape):
       self.kernel = self.add_weight(name='kernel',
                                     shape=(input_shape[1], self.output_dim),
                                     initializer='uniform',
                                     trainable=True)
       super(Attention, self).build(input_shape)

   def call(self, V):
       # Q = ke.backend.dot(V, self.kernel)
       Q = keras.backend.dot(V, self.kernel)
       Q =  Q * V
       Q = Q / math.sqrt(self.output_dim)
       # Q = ke.activations.softmax(Q)
       Q = keras.activations.softmax(Q)
       return Q

   def compute_output_shape(self, input_shape):
       return input_shape



def load_data():

    data_path = args['in']
    data_path = Path(data_path)
        
    # df = (pd.read_csv(data_path,skiprows=1).values).astype('float32')
    if data_path.suffix=='.parquet':
        df = pd.read_parquet(data_path)
        if 'SMILES' in df.columns:
            df = df.drop(columns=['cls','binner','TITLE','SMILES'])
        df = df.values
        df = df.astype('float32')
    else:
        df = (pd.read_csv(data_path,skiprows=1).values).astype('float32')

    df_y = df[:,0].astype('float32')
    # df_x = df[:, 1:PL].astype(np.float32)
    df_x = df[:, 1:].astype(np.float32)


#    scaler = MaxAbsScaler()
        
    scaler = StandardScaler()
    df_x = scaler.fit_transform(df_x)
        
    X_train, X_test, Y_train, Y_test = train_test_split(df_x, df_y, test_size= 0.20, random_state=42)
    
    print('x_train shape:', X_train.shape)
    print('x_test shape:', X_test.shape)

    
    return X_train, Y_train, X_test, Y_test

X_train, Y_train, X_test, Y_test = load_data()

print('X_train shape:', X_train.shape)
print('X_test shape:', X_test.shape)

print('Y_train shape:', Y_train.shape)
print('Y_test shape:', Y_test.shape)


PS=X_train.shape[1]
inputs = Input(shape=(PS,))
x = Dense(250, activation='relu')(inputs) #b = Attention(1000)(a)
#x = ke.layers.multiply([b, a])

#b = Dense(1000, activation='softmax')(inputs)
#x = ke.layers.multiply([a,b])

#x = Dense(1000, activation='relu')(x)
#x = Dropout(DR)(x)
#x = Dense(500, activation='relu')(x)
#x = Dropout(DR)(x)
#x = Dense(250, activation='relu')(x)
x = Dropout(DR)(x)
x = Dense(125, activation='relu')(x)
x = Dropout(DR)(x)
x = Dense(60, activation='relu')(x)
x = Dropout(DR)(x)
x = Dense(30, activation='relu')(x)
x = Dropout(DR)(x)
outputs = Dense(1, activation='relu')(x)

model = Model(inputs=inputs, outputs=outputs)

model.summary()

#parallel_model = multi_gpu_model(model, gpus=4)
#parallel_model.compile(loss='mean_squared_error',
#         optimizer=SGD(lr=0.0001, momentum=0.9),    
#              metrics=['mae',r2])

model.compile(loss='mean_squared_error',
              optimizer=SGD(lr=0.0001, momentum=0.9),
              metrics=['mae',r2])

# set up a bunch of callbacks to do work during model training..                                                                              

checkpointer = ModelCheckpoint(filepath=str(outdir/'reg_go.autosave.model.h5'), verbose=1, save_weights_only=False, save_best_only=True)
csv_logger = CSVLogger(str(outdir/'reg_go.training.log'))
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.75, patience=20, verbose=1, mode='auto', min_delta=0.0001, cooldown=3, min_lr=0.000000001)
early_stop = EarlyStopping(monitor='val_loss', patience=100, verbose=1, mode='auto')


#history = parallel_model.fit(X_train, Y_train,

history = model.fit(X_train, Y_train,                             
                    batch_size=BATCH,
                    epochs=EPOCH,
                    verbose=1,
                    validation_data=(X_test, Y_test),
                    callbacks = [checkpointer, csv_logger, reduce_lr, early_stop])

score = model.evaluate(X_test, Y_test, verbose=0)

print(score)

print(history.history.keys())

his = plot_prfrm_metrics(history=history, logfile_path=None, title=str(data_path),
        name=None, skp_ep=1, outdir=outdir, add_lr=False)

# # summarize history for MAE                                                                                                              
# plt.plot(history.history['mean_absolute_error'])
# plt.plot(history.history['val_mean_absolute_error'])
# plt.title('Model Mean Absolute Error')
# plt.ylabel('mae')
# plt.xlabel('epoch')
# plt.legend(['train', 'test'], loc='upper left')

# plt.savefig('reg_go.mae.png', bbox_inches='tight')
# plt.savefig('reg_go.mae.pdf', bbox_inches='tight')

# plt.close()

# # summarize history for loss                                                                                                                  
# plt.plot(history.history['loss'])
# plt.plot(history.history['val_loss'])
# plt.title('Model Loss')
# plt.ylabel('loss')
# plt.xlabel('epoch')
# plt.legend(['train', 'test'], loc='upper left')

# plt.savefig('reg_go.loss.png', bbox_inches='tight')
# plt.savefig('reg_go.loss.pdf', bbox_inches='tight')

# plt.close()

print('Test val_loss:', score[0])
print('Test val_mae:', score[1])

#exit()

# serialize model to JSON                                                                                                                     
model_json = model.to_json()
with open((outdir/'reg_go.model.json'), "w") as json_file:
        json_file.write(model_json)

# serialize model to YAML                                                                                                                     
model_yaml = model.to_yaml()
with open(str(outdir/'reg_go.model.yaml'), "w") as yaml_file:
        yaml_file.write(model_yaml)


# serialize weights to HDF5                                                                                                                   
model.save_weights(str(outdir/"reg_go.model.h5"))
print("Saved model to disk")

#exit()

# load json and create model                                                                                                                  
json_file = open(str(outdir/'reg_go.model.json'), 'r')
loaded_model_json = json_file.read()
json_file.close()
loaded_model_json = model_from_json(loaded_model_json)


# load yaml and create model                                                                                                                  
yaml_file = open(str(outdir/'reg_go.model.yaml'), 'r')
loaded_model_yaml = yaml_file.read()
yaml_file.close()
loaded_model_yaml = model_from_yaml(loaded_model_yaml)


# load weights into new model                                                                                                                 
loaded_model_json.load_weights(str(outdir/'reg_go.model.h5'))
print("Loaded json model from disk")

# evaluate json loaded model on test data                                                                                                     
loaded_model_json.compile(loss='mean_squared_error', optimizer='SGD', metrics=['mean_absolute_error'])
score_json = loaded_model_json.evaluate(X_test, Y_test, verbose=0)

print('json Validation loss:', score_json[0])
print('json Validation mae:', score_json[1])

# load weights into new model                                                                                                                 
loaded_model_yaml.load_weights(str(outdir/'reg_go.model.h5'))
print("Loaded yaml model from disk")

# evaluate loaded model on test data                                                                                                          
loaded_model_yaml.compile(loss='mean_squared_error', optimizer='SGD', metrics=['mean_absolute_error'])
score_yaml = loaded_model_yaml.evaluate(X_test, Y_test, verbose=0)

print('yaml Validation loss:', score_yaml[0])
print('yaml Validation mae:', score_yaml[1])

# predict using loaded yaml model on test and training data

predict_yaml_train = loaded_model_yaml.predict(X_train)

predict_yaml_test = loaded_model_yaml.predict(X_test)

pred_train = predict_yaml_train[:,0]
pred_test = predict_yaml_test[:,0]

np.savetxt(str(outdir/'pred_train.csv'), pred_train, delimiter=".", newline='\n', fmt="%.3f")
np.savetxt(str(outdir/'pred_test.csv'), pred_test, delimiter=",", newline='\n',fmt="%.3f")

print('Correlation prediction on test and Y_test:', np.corrcoef( pred_test, Y_test))
print('Correlation prediction on train and Y_train:', np.corrcoef( pred_train, Y_train))

