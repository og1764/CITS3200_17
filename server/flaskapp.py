from flask import Flask, render_template, request
import os
from PIL import Image
import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K
from keras.utils import np_utils
from keras.models import model_from_json
import keras.callbacks
import numpy as np
#import keras.backend.tensorflow_backend as KTF
#import tensorflow as tf
import os.path

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def main():
    return render_template('main.html', title='Main')

# Below is an example of how to add other pages
# To go to this webpage you would need to add "/Examplepage" to the end of the main page url
@app.route("/Examplepage", methods=['GET', 'POST'])
def example():
    return render_template('example.html', title='Example')


def process_images():
    image_values = []
    return_values = []
    for file in os.listdir(APP_ROOT+"\\uploads"):
        initial = Image.open(APP_ROOT+"\\uploads\\" + file)
        result = initial.resize((50,50)).convert("L")
        pix_val = list(result.getdata())
        norm_val = [i/255 for i in pix_val]
        image_values.append(norm_val)
        os.remove(APP_ROOT+"\\uploads\\" + file)
    print(image_values)
    for i in image_values:
        return_values.append(CNN(i))
    return return_values

def CNN(lines):
    """ Takes an array of values """

    ### Original values
    #batch_size = 128
    #num_classes = 10
    #epochs = 12
    #batch_size = 200

    num_classes = 3
    num_classes0 = 2

    #epochs = 1
    #nb_epoch=epochs

    n_mesh=50

    img_rows, img_cols = n_mesh, n_mesh
    n_mesh2=n_mesh*n_mesh-1
    n_mesh3=n_mesh*n_mesh

    
    return_values = []
    nmodel=1

    x_train=np.zeros((nmodel,n_mesh3))
    x_test=np.zeros((nmodel,n_mesh3))
    y_train=np.zeros(nmodel,dtype=np.int)
    y_test=np.zeros(nmodel,dtype=np.int)



    #y_test=np.zeros(nmodel)
    #print(y_train)

    # For 2D density map data
    ibin=0
    jbin=-1
    for num,j in enumerate(lines):
      jbin=jbin+1
      #tm=j.strip().split()
      tm = j
      #print(j)
      #print(num)
      x_train[ibin,jbin]=float(tm)
      x_test[ibin,jbin]=float(tm)
      #x_train[ibin,jbin]=float(j)
      #x_test[ibin,jbin]=float(j)
    #  print('ibin,jbin',ibin,jbin)
      if jbin == n_mesh2:
        ibin+=1
        jbin=-1

    ntest=ibin
    print('ntest',ntest)

    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
    #y_train = keras.utils.np_utils.to_categorical(y_train, num_classes)
    #y_test =  keras.utils.np_utils.to_categorical(y_test, num_classes)


    # load json and create model
    json_file = open(APP_ROOT + '\\ct3200.dir\\model.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    # load weights into new model
    loaded_model.load_weights(APP_ROOT + "\\ct3200.dir\\model.h5")
    print("Loaded model from disk")

    #y_vec=np.zeros(3)
    #y_vec=np.zeros(num_classes)
    y_vec=np.zeros(num_classes)
    #print(y_vec)

    y_pred=loaded_model.predict(x_test)
    print(y_pred[:ntest])

    #f1.write( str(ntest) + "\n" )
    return_values.append(str(ntest))

    for i in range(ntest):
    #  for j in range(num_classes0):
      for j in range(num_classes):
        y_vec[j]=y_pred[i,j]
    #  print(y_vec)
    #    print(j)
      y_type=np.argmax(y_vec)
    #  y_type=y_type+1
      prob=y_vec[y_type]
      print('i=',i,'G-type=',y_type,'P',prob)
    #  Original  type-1 is output
      arr = str(y_type) + ' ' + str(y_vec[0]) + ' '+ str(y_vec[1]) + ' ' + str(y_vec[2]) + "\n"
      return_values.append(arr)
    #  f1.write( str(y_type) +
    #   "\n" )

    return return_values


@app.route("/upload", methods=['POST'])
def upload():
    target = os.path.join(APP_ROOT, 'uploads/')
    for file in request.files.getlist("file"):

        # get the filename
        filename = file.filename

        # combine filename and path
        destination = "/".join([target, filename])

        # save the file
        file.save(destination)
    output = process_images()
    print(output)
    return "Done"

        

if __name__ == "__main__":
    app.run(debug=True, host='localhost', port=443)
