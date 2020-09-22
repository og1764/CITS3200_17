from config import Config
from Form import LoginForm
from flask import Flask, render_template, request, json
from flask import render_template, flash, redirect, url_for, request, send_from_directory
from flask_login import logout_user, login_user, current_user, login_required
from werkzeug.urls import url_parse
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import ValidationError, DataRequired

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
import os.path
import os
from PIL import Image

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'SECRET KEY'


@app.route('/')
@app.route('/home')
def example():
    return render_template('example.html', title='Example')


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        #user = User(username=form.username.data, password = form.password.data)
        if form.username.data != 'admin' or form.password.data != 'password':
            flash('Invalid username or password')
            return redirect(url_for('login'))
        #login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main'))
    return render_template('log.html', form=form)


@app.route("/main", methods=['GET', 'POST'])
def main():
    return render_template('main.html', title='Main')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # logout_user()
    return redirect(url_for('login'))


# Below is an example of how to add other pages
# To go to this webpage you would need to add "/Examplepage" to the end of the main page url


@app.route("/result", methods=['GET', 'POST'])
def process_images():
    image_values = []
    return_values = []
    for file in os.listdir(APP_ROOT + "\\uploads"):
        initial = Image.open(APP_ROOT + "\\uploads\\" + file)
        result = initial.resize((50, 50)).convert("L")
        pix_val = list(result.getdata())
        norm_val = [i/255 for i in pix_val]
        image_values.append(norm_val)
        os.remove(APP_ROOT+"\\uploads\\" + file)
    for i in image_values:
        return_values.append(CNN(i))
    return json.jsonify(return_values)


def CNN(lines):
    """ Takes an array of values """

    num_classes = 3
    # num_classes0 = 2 Not sure why this is here
    n_mesh = 50
    i_bin = 0
    j_bin = -1
    return_values = []
    nmodel = 1

    img_rows, img_cols = n_mesh, n_mesh
    n_mesh2 = n_mesh * n_mesh - 1
    n_mesh3 = n_mesh * n_mesh

    x_train = np.zeros((nmodel, n_mesh3))
    x_test = np.zeros((nmodel, n_mesh3))
    y_train = np.zeros(nmodel, dtype=np.int)
    y_test = np.zeros(nmodel, dtype=np.int)

    # For 2D density map data

    for num, j in enumerate(lines):
        j_bin = j_bin + 1
        tm = j
        x_train[i_bin, j_bin] = float(tm)
        x_test[i_bin, j_bin] = float(tm)
        if j_bin == n_mesh2:
            i_bin += 1
            j_bin = -1

    ntest = i_bin

    print('ntest', ntest)

    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)

    # load json and create model
    json_file = open(APP_ROOT + '\\ct3200.dir\\model.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)

    # load weights into new model
    loaded_model.load_weights(APP_ROOT + "\\ct3200.dir\\model.h5")
    print("Loaded model from disk")

    y_vec = np.zeros(num_classes)
    y_pred = loaded_model.predict(x_test)
    print(y_pred[:ntest])

    #return_values.append(str(ntest)+" || ")

    for i in range(ntest):
        for j in range(num_classes):
            y_vec[j] = y_pred[i, j]
        y_type = np.argmax(y_vec)
        prob = y_vec[y_type]

        print('i=', i, 'G-type=', y_type, 'P', prob)
    #  Original  type-1 is output
        #out_str = str(y_type) + ', ' + str(y_vec[0]) + ', '+ str(y_vec[1]) + ', ' + str(y_vec[2]) + "\n"
        out_str = '  i=' + str(i) + '  \nG-type=' + \
            str(y_type) + '  P=' + str(prob)
        # return_values.append(out_str)
        if y_type == 0:
            return_values.append("E")
        if y_type == 1:
            return_values.append("S0")
        if y_type == 2:
            return_values.append("Sp")
    return return_values


@app.route("/upload", methods=['POST'])
def upload():
    target = os.path.join(APP_ROOT, 'uploads/')
    for file in request.files.getlist("file"):
        filename = file.filename
        destination = "/".join([target, filename])
        file.save(destination)
    #output = process_images()
    # print(output)
    return "Done"


if __name__ == "__main__":
    app.run(debug=True, host='localhost', port=5001)
