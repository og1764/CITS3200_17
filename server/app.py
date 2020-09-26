from config import Config
from Form import LoginForm
from Model import query_user, User
from flask import Flask, render_template, request, json
from flask import render_template, flash, redirect, url_for, request, send_from_directory, send_file, Response
from flask_login import logout_user, login_user, current_user, login_required, LoginManager
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
import shutil
from os import listdir
from os.path import isfile, join
import glob
from PIL import Image, UnidentifiedImageError
import sys

import tarfile
import zipfile
import datetime
import random
import string

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
VALID_COMPRESSED = (".zip", ".tar.gz", ".tar") # TODO: Add 7z, Add rar,
# tuple so it can be used with .endswith

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'SECRET KEY'
login = LoginManager(app)
login.login_view = 'login'

#if os.name == "nt":
#    sh = "\\"
#else:
#    sh = "/"
sh = os.sep


@app.route('/')
@app.route('/home')
def example():
    return render_template('example.html', title='Example')
    
# Helper function to iterate over directories
def files_in_folder(dirName):
    file_list = os.listdir(dirName)
    result = []
    # Iterate over all the entries
    for entry in file_list:
        # Create full path
        path = os.path.join(dirName, entry)
        if os.path.isdir(path):
            result = result + files_in_folder(path)
        elif not path.endswith(VALID_COMPRESSED):
            print(path)
            result.append(path)
    return result

@login.user_loader
def load_user(user_id):
    if query_user(user_id) is not None:
        curr_user = User()
        curr_user.id = user_id
        return curr_user


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = query_user(form.username.data)
        if user is not None and form.password.data == user['password']:
            curr_user = User()
            curr_user.id = form.username.data
            login_user(curr_user, remember=form.remember_me.data)
            return redirect(url_for('main'))
        flash('Invalid username or password')
        return redirect(url_for('login'))
    return render_template('log.html', form=form)


@app.route("/main", methods=['GET', 'POST'])
@login_required
def main():
    return render_template('main.html', title='Main')

# This is more than a little jank. We're going to have to figure out how to use identifiers here as well
@app.route('/getResults')
def returnFile():
    print("We're here!")
    with open(APP_ROOT + sh + "toSend" + sh +"ThisFileWillAlwaysHaveThisNameAndThatsBad.txt") as f:
        txt_content = f.read()
    toReturn = Response(
                txt_content,
                mimetype="text/txt",
                headers={"Content-disposition":
                 "attachment; filename=Results.txt"})
    return toReturn

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))


# Below is an example of how to add other pages
# To go to this webpage you would need to add "/Examplepage" to the end of the main page url


#@app.route("/result", methods=['GET', 'POST'])
@app.route("/result")
def process_images(target):
    print("started")
    print(datetime.datetime.now())
    t1 = datetime.datetime.now()
    image_values = []
    return_values = []
    folder_list = []
    uploads_path = target 
    compressed_list = [uploads_path + sh + filename for filename in os.listdir(uploads_path) if filename.endswith(VALID_COMPRESSED)]
    print(compressed_list)
    
    # Loop over and extract compressed folders
    for file in compressed_list:
        if file.endswith((".tar", ".tar.gz")):
            tf = tarfile.open(file)
            os.mkdir(file + ".dir" + sh)
            folder_list.append(file + ".dir" + sh)
            tf.extractall(file+".dir" + sh)
            tf.close()
        if file.endswith(".zip"):
            with zipfile.ZipFile(file, 'r') as zip:
                os.mkdir(file+".dir" + sh)
                folder_list.append(file+".dir"+sh)
                zip.extractall(file+".dir"+sh)
        
    print("extracting done")
    print(datetime.datetime.now())
    t2 = datetime.datetime.now()
    
    # Check out my onlyfiles ;)
    onlyfiles = files_in_folder(uploads_path)
    print(onlyfiles)
    
    # Moved this out of the CNN function because its expensive, so its better to only call once.
    json_file = open(APP_ROOT + sh + 'ct3200.dir' + sh + 'model.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    # load weights into new model
    loaded_model.load_weights(APP_ROOT + sh + "ct3200.dir" + sh + "model.h5")
    
    # classifies all files, gives an error if not a valid image type.
    for file in onlyfiles:
        name = " " + file.split(sh)[-1]
        print(name)
        try:
            initial = Image.open(file)
            result = initial.resize((50, 50)).convert("L")
            pix_val = list(result.getdata())
            norm_val = [i/255 for i in pix_val]
            image_values.append((norm_val, name+ " <br>"))
            initial.close()
        except UnidentifiedImageError:
            print("Unidentified Image Error")
            extension = name.split(".")[-1]
            error_message = 'Could not classify "<b>{}</b>" as <b>.{}</b> is not a valid file extension. <br>'.format(name.lstrip(), extension.rstrip())
            image_values.append((error_message, ""))
        except:
            print(str(sys.exc_info()[1]) + " @ Line "+ str(sys.exc_info()[2].tb_lineno))
        os.remove(file)
    
    
    # counter is not really useful, but it's nice to see the console doing things.
    counter = 0
    for i in image_values:
        #print(i)
        counter = counter + 1 
        if i[1] != "":
            return_values.append((CNN(i[0], loaded_model, counter),i[1]))
        else:
            return_values.append((error_message, ""))

    # removes compressed files after they've been extracted.
    # this isnt in the above loop because I was getting weird permission errors where the zip was still in use
    # Even after moving it all the way down here it still thinks its in use >:(
    # 
    # This was the best solution I could come up with. We're going to get a lot of errors on this first try-catch but if it works...
    try:
        tf.close()
    except:
        print(str(sys.exc_info()[1]) + " @ Line "+ str(sys.exc_info()[2].tb_lineno))
    for file in compressed_list:
        try:
            os.remove(file)
        except:
            print(str(sys.exc_info()[1]) + " @ Line "+ str(sys.exc_info()[2].tb_lineno))
    
    # Removing the empty zipped folders.
    for folder in folder_list:
        shutil.rmtree(folder)
    shutil.rmtree(target)
    print(datetime.datetime.now())
    t4 = datetime.datetime.now()
    tot_time = t4 - t1
    print("\nTime taken for this request: " + str(tot_time)+"\n")

    # Just a bit of formatting
    ret = ""
    for i in return_values:
        for j in i:
            ret = ret + "".join(j).replace(target,"")
    if ret == "":
        ret = "Example text"
    else: # If something was actually classified
        # This is all for the returnFile() function. We need to figure out how to use identifiers though
        # Because it's a bit of a jank-fest atm, and it really only supports one user.
        f = open(APP_ROOT + sh + "toSend" + sh +"ThisFileWillAlwaysHaveThisNameAndThatsBad.txt", "w")
        toSend = ret.replace("<br>", "\n")
        f.write(toSend)
        f.close()
    print(ret)
    return ret
    


def CNN(lines, loaded_model, number):
    """ Takes an array of values """
    print(number)

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
    #json_file = open(APP_ROOT + sh + 'ct3200.dir' + sh + 'model.json', 'r')
    #loaded_model_json = json_file.read()
    #json_file.close()
    #loaded_model = model_from_json(loaded_model_json)

    # load weights into new model
    #loaded_model.load_weights(APP_ROOT + sh + "ct3200.dir" + sh + "model.h5")
    #print("Loaded model from disk")

    y_vec = np.zeros(num_classes)
    y_pred = loaded_model.predict(x_test)
    #print(y_pred[:ntest])

    #return_values.append(str(ntest)+" || ")

    for i in range(ntest):
        for j in range(num_classes):
            y_vec[j] = y_pred[i, j]
        y_type = np.argmax(y_vec)
        prob = y_vec[y_type]

        #print('i=', i, 'G-type=', y_type, 'P', prob)
    #  Original  type-1 is output
        #out_str = str(y_type) + ', ' + str(y_vec[0]) + ', '+ str(y_vec[1]) + ', ' + str(y_vec[2]) + "\n"
        out_str = '  i=' + str(i) + '  \nG-type=' + \
            str(y_type) + '  P=' + str(prob)
        # return_values.append(out_str)
        formatted_prob = prob * 100
        if y_type == 0:
            return_values.append("E - {0:.2f}% -".format(formatted_prob))
        if y_type == 1:
            return_values.append("S0 - {0:.2f}% -".format(formatted_prob))
        if y_type == 2:
            return_values.append("Sp - {0:.2f}% -".format(formatted_prob))
    return return_values


@app.route("/upload", methods=['POST'])
def upload():
    up_folder = str(APP_ROOT) + sh + "uploads" + sh
    if not os.path.exists(up_folder):
        os.mkdir(up_folder)
    rand_folder = ''.join(random.choice(string.ascii_letters) for i in range(12))
    target = str(APP_ROOT) + sh + "uploads" + sh + rand_folder + sh
    print(target)
    while os.path.exists(target):
        rand_folder = ''.join(random.choice(string.ascii_letters) for i in range(12))
        target = str(APP_ROOT) + sh + "uploads" + sh + rand_folder + sh

    
    os.mkdir(target)
    
    for file in request.files.values():
        filename = file.filename
        destination = sh.join([target, filename])
        file.save(destination)

    #output = process_images()
    # print(output)
    return process_images(target)

if __name__ == "__main__":
    app.run()
