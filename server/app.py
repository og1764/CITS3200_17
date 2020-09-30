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
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import multiprocessing
from multiprocessing import Pool

import time
import requests
from bs4 import BeautifulSoup
from stat import S_ISREG, ST_CTIME, ST_MODE
import urllib.request

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
VALID_COMPRESSED = (".zip", ".tar.gz", ".tar")  # TODO: Add 7z, Add rar,
#GLOBAL_FOLDER_DICT = {}
# tuple so it can be used with .endswith

app = Flask(__name__)
app.config.from_object(Config)
_pool = None
app.secret_key = 'SECRET KEY'
login = LoginManager(app)
login.login_view = 'login'

# if os.name == "nt":
#    sh = "\\"
# else:
#    sh = "/"
sh = os.sep

img_types = ['.jpg', '.png']
# global vars for updating site background sequentially from folder of images
bg_index = 0
bg_set_time = 0.0


@app.route('/')
@app.route('/home')
def example():
    return render_template('example.html', title='Example')


@app.route("/manual", methods=['GET', 'POST'])
def manual():
    choose_new_background(mode='latest', interval=60 * 60 * 6)  # [seconds] 60*60*24 = once every 24 hours
    return render_template('manual.html', title='Manual')

# Compressed_list = list of filepaths
def process_compressed(compressed_list):
    folder_list = []
    for file in compressed_list:
        if file.endswith((".tar", ".tar.gz")):
            tf = tarfile.open(file)
            os.mkdir(file + ".dir" + sh)
            folder_list.append(file + ".dir" + sh)
            tf.extractall(file + ".dir" + sh)
            tf.close()
        if file.endswith(".zip"):
            with zipfile.ZipFile(file, 'r') as zip:
                os.mkdir(file + ".dir" + sh)
                folder_list.append(file + ".dir" + sh)
                zip.extractall(file + ".dir" + sh)
    # Potentially also return tf in case it doesnt close properly?
    return folder_list

# target = FULL PATH of a folder
def files_in_folder(target):

    file_list = os.listdir(target)
    result = []
    # Iterate over all the entries
    for entry in file_list:
        # Create full path
        path = os.path.join(target, entry)
        if os.path.isdir(path):
            result = result + files_in_folder(path)
        elif not path.endswith(VALID_COMPRESSED):
            #print(path)
            result.append(path)
    return result

# files = array of images
def normalise_images(files, target):
    # classifies all files, gives an error if not a valid image type.
    
    for file in files:
        #name = " " + file.split(sh)[-1]
        name = file.replace(target, "")
        name = name.replace(".dir", "")
        print(name)
        #print(name)
        try:
            initial = Image.open(file)
            result = initial.resize((50, 50)).convert("L")
            pix_val = list(result.getdata())
            norm_val = [i / 255 for i in pix_val]
            image_values.append((norm_val, name + " <br>"))
            initial.close()
        except UnidentifiedImageError:
            print("Unidentified Image Error")
            extension = name.split(".")[-1]
            error_message = 'Could not classify "<b>{}</b>" as <b>.{}</b> is not a valid file extension. <br>'.format(
                name.lstrip(), extension.rstrip())
            image_values.append((error_message, ""))
        except:
            print(str(sys.exc_info()[1]) + " @ Line " + str(sys.exc_info()[2].tb_lineno))
        os.remove(file)
    return image_values

# files = array of images
# loaded_model = CNN model
# progress = Identifier
def bulk_classify(files, loaded_model, ID, GLOBAL_FOLDER_DICT):
    counter = 0
    return_values = []
    number_files = len(files)
    for i in files:
        # print(i)
        counter = counter + 1
        if i[1] != "":
            return_values.append((CNN(i[0], loaded_model, counter), i[1]))
        else:
            return_values.append((i[0], ""))
        # Potentially remove this if we don't want to keep a progress text file
        f = open(GLOBAL_FOLDER_DICT[ID][0], "w")
        f.write("S: " + "NOT_COMPLETE\n")
        f.write("T: " + str(number_files) + "\n")
        f.write("C: " + str(counter) + "\n")
        f.write("K: " + str(ID) + "\n")
        f.close()
    return return_values

# target = FULL PATH of parent folder
# compressed = array of compressed files
# folders = array of child folders
def file_cleanup(target, compressed, folders):
    # Might be able to remove these first 4 lines. Its just in case tf doesnt close :(
    print("cleanup")
    print(target)
    try:
        tf.close()
    except:
        print(str(sys.exc_info()[1]) + " @ Line " + str(sys.exc_info()[2].tb_lineno))
    for file in compressed:
        try:
            os.remove(file)
        except:
            print(str(sys.exc_info()[1]) + " @ Line " + str(sys.exc_info()[2].tb_lineno))
    # Removing the empty zipped folders.
    for folder in folders:
        shutil.rmtree(folder)
    shutil.rmtree(target)

# ID = identifier
# results = results from classification
def format_results(ID, results, GLOBAL_FOLDER_DICT):
    ret = ""
    f = open(GLOBAL_FOLDER_DICT[ID][1], "w+")
    for i in results:
        for j in i:
            ret = ret + "".join(j).replace(GLOBAL_FOLDER_DICT[ID][2], "")
    f.write(ret)
    f.close()
    if ret == "":
        ret = "Example text"
    else:  # If something was actually classified
        # This is all for the returnFile() function. We need to figure out how to use identifiers though
        # Because it's a bit of a jank-fest atm, and it really only supports one user.
        # This one needs to be fixed
        f = open(APP_ROOT + sh + "toSend" + sh + "ThisFileWillAlwaysHaveThisNameAndThatsBad.txt", "w")
        toSend = ret.replace("<br>", "\n")
        f.write(toSend)
        f.close()

    return ret


def download_img(url):
    destination = str(APP_ROOT) + sh + "backgrounds" + sh
    split_list = url.split("/")
    name = split_list[len(split_list) - 1]
    filename = destination + str(name)
    urllib.request.urlretrieve(url, filename)


def scrape_img_url(url, root_url):
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"}
    response = requests.request("GET", url, headers=headers)
    data = BeautifulSoup(response.text, 'html.parser')

    # find all with the image tag
    images = data.find_all('img', src=True)
    # select src tag
    image_src = [x['src'] for x in images]
    img_adr = ""
    # select the first image on the page
    if len(image_src) > 0:
        img_adr = image_src[0]

    img_url = root_url + img_adr
    return img_url


def create_backgrounds_folder():
    # make backgrounds folder if it doesn't already exist
    destination = str(APP_ROOT) + sh + "backgrounds" + sh
    if not os.path.exists(destination):
        os.mkdir(destination)


def download_background():
    url = "https://apod.nasa.gov/apod/astropix.html"
    root_url = "https://apod.nasa.gov/apod/"
    img_url = scrape_img_url(url, root_url)
    download_img(img_url)


def choose_new_background(mode='latest', interval=0):  # mode latest|sequence, interval in seconds
    global bg_index
    global bg_set_time

    if time.time() > bg_set_time + interval:
        create_backgrounds_folder()
        ###run updates to the background here
        ###background downloaded and prepared for detection by css once every time interval

        bg_dir_location = str(APP_ROOT) + sh + "backgrounds" + sh
        bg_destination = str(APP_ROOT) + sh + "static" + sh + "img" + sh + "background.jpg"

        if mode == 'latest':
            try:
                download_background()
                file_list = files_sorted_by_date(bg_dir_location)
                latest_file = file_list[0]
                bg_location = bg_dir_location + latest_file[1]
                print(latest_file)
                shutil.copy2(bg_location, bg_destination)
            except:
                print("No images found in " + bg_dir_location)

        elif mode == 'sequence':
            try:
                file_list = files_sorted_by_date(bg_dir_location)
                bg_index = (bg_index + 1) % len(file_list)
                next_file = file_list[bg_index]
                bg_location = bg_dir_location + next_file[1]
                print(next_file)
                shutil.copy2(bg_location, bg_destination)

            except:
                print("No images found in " + bg_dir_location)

        # record the time at which the background updates were run
        bg_set_time = time.time()


def files_sorted_by_date(dir_path):
    # all entries in the directory w/ stats
    data = (os.path.join(dir_path, fn) for fn in os.listdir(dir_path)
            if fn.endswith(img_types[0]) or fn.endswith(img_types[1]))
    data = ((os.stat(path), path) for path in data)
    # regular files, insert creation date
    data = ((stat[ST_CTIME], path) for stat, path in data if S_ISREG(stat[ST_MODE]))

    file_list = []
    for cdate, path in sorted(data):
        file_list.append([time.ctime(cdate), os.path.basename(path)])
    file_list.reverse()

    return file_list


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
    # json_file = open(APP_ROOT + sh + 'ct3200.dir' + sh + 'model.json', 'r')
    # loaded_model_json = json_file.read()
    # json_file.close()
    # loaded_model = model_from_json(loaded_model_json)

    # load weights into new model
    # loaded_model.load_weights(APP_ROOT + sh + "ct3200.dir" + sh + "model.h5")
    # print("Loaded model from disk")

    y_vec = np.zeros(num_classes)
    y_pred = loaded_model.predict(x_test)
    # print(y_pred[:ntest])

    # return_values.append(str(ntest)+" || ")

    for i in range(ntest):
        for j in range(num_classes):
            y_vec[j] = y_pred[i, j]
        y_type = np.argmax(y_vec)
        prob = y_vec[y_type]

        # print('i=', i, 'G-type=', y_type, 'P', prob)
        #  Original  type-1 is output
        # out_str = str(y_type) + ', ' + str(y_vec[0]) + ', '+ str(y_vec[1]) + ', ' + str(y_vec[2]) + "\n"
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

# token = Identifier
def check_folder(token, GLOBAL_FOLDER_DICT):
    # Checks all folders in the global dict to see if expired
    # If any are expired, it removes them
    # return value is specific to input value
    # Do this... somewhere. On Get request for file?

    keys = list(GLOBAL_FOLDER_DICT.keys())
    expired = False
    for tkn in keys:
        try:
            best_before = GLOBAL_FOLDER_DICT[tkn][4]
            time_now = datetime.datetime.now(timezone.utc)
            prog = GLOBAL_FOLDER_DICT[tkn][0]
            res = GLOBAL_FOLDER_DICT[tkn][1]
            img = GLOBAL_FOLDER_DICT[tkn][2]
            txt = GLOBAL_FOLDER_DICT[tkn][3]
            if time_now > best_before:
                try:
                    # remove all of everything. If it errors it will still be marked as expired and will be dealt with later
                    if prog != "":
                        os.remove(prog)
                        prog = ""
                        GLOBAL_FOLDER_DICT[tkn] = ["", res, img, txt, best_before]
                    if res != "":
                        os.remove(res)
                        res = ""
                        GLOBAL_FOLDER_DICT[tkn] = [prog, "", img, txt, best_before]
                    if img != "":
                        shutil.rmtree(img)
                        img = ""
                        GLOBAL_FOLDER_DICT[tkn] = [prog, res, "", txt, best_before]
                    if txt != "":
                        shutil.rmtree(txt)
                        txt = ""
                        GLOBAL_FOLDER_DICT[tkn] = [prog, res, img, "", best_before]
                    GLOBAL_FOLDER_DICT.pop(tkn)
                    if tkn == token:
                        expired = True
                except:
                    if tkn == token:
                        expired = True
        except:
            if tkn == token:
                expired = True
    return expired


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
    choose_new_background(mode='latest', interval=60 * 60 * 6)  # [seconds] 60*60*24 = once every 24 hours
    return render_template('main.html', title='Main')


# This is more than a little jank. We're going to have to figure out how to use identifiers here as well
@app.route('/getResults/<token>')
def returnFile(token):
    print("We're here!")
    with open(GLOBAL_FOLDER_DICT[1]) as f:
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


# @app.route("/result")
# target = FULL PATH to folder
def process_images(target, GLOBAL_FOLDER_DICT):
    
    print("started")
    print(datetime.datetime.now())
    t1 = datetime.datetime.now()
    
    rand_identifier = target.split(sh)[-2]
    uploads_path = target
    results_path = GLOBAL_FOLDER_DICT[rand_identifier][1]

    compressed_list = [target + sh + filename for filename in os.listdir(target) if filename.endswith(VALID_COMPRESSED)]

    print(datetime.datetime.now())
    
    # Loop over and extract compressed folders
    
    folder_list = process_compressed(compressed_list)

    print("extracting done")
    print(datetime.datetime.now())

    # Check out my onlyfiles ;)
    onlyfiles = files_in_folder(target)
    print(onlyfiles)

    # Moved this out of the CNN function because its expensive, so its better to only call once.
    json_file = open(APP_ROOT + sh + 'ct3200.dir' + sh + 'model.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    # load weights into new model
    loaded_model.load_weights(APP_ROOT + sh + "ct3200.dir" + sh + "model.h5")
    
    # normalises image files, gives an error if not a valid image type.
    image_values = normalise_images(onlyfiles, target)

    # sends normalised images into the classifier
    return_values = bulk_classify(image_values, loaded_model, rand_identifier, GLOBAL_FOLDER_DICT)

    # removes compressed files and folders after they've been extracted.
    file_cleanup(target, compressed_list, folder_list)

    # This formats results to be sent back and creates a text file
    to_send = format_results(rand_identifier, return_values, GLOBAL_FOLDER_DICT)
    # to_send is an array

    ''' CREATE FILE '''
    print(rand_identifier)
    # this updates the progress.txt file
    f = open(GLOBAL_FOLDER_DICT[rand_identifier][0], "w")
    f.write("S: " + "CLASSIFICATION_COMPLETE\n")
    f.write("T: " + str(len(onlyfiles)) + "\n")
    f.write("C: " + str(len(onlyfiles)) + "\n")
    f.write("K: " + str(rand_identifier) + "\n")
    f.close()

    print(datetime.datetime.now())
    t3 = datetime.datetime.now()
    tot_time = t3 - t1
    print("\nTime taken for this request: " + str(tot_time) + "\n")

    return to_send



@app.route("/upload", methods=['POST'])
def upload():
    up_folder = str(APP_ROOT) + sh + "uploads" + sh
    res_folder = str(APP_ROOT) + sh + "results" + sh

    if not os.path.exists(up_folder):
        os.mkdir(up_folder)
    if not os.path.exists(res_folder):
        os.mkdir(res_folder)

    rand_identifier = ''.join(random.choice(string.ascii_letters) for i in range(12))
    up_target = str(APP_ROOT) + sh + "uploads" + sh + rand_identifier + sh
    res_target = str(APP_ROOT) + sh + "results" + sh + rand_identifier + sh
    print(up_target)

    while os.path.exists(up_target) or os.path.exists(res_target):
        rand_identifier = ''.join(random.choice(string.ascii_letters) for i in range(12))
        up_target = str(APP_ROOT) + sh + "uploads" + sh + rand_identifier + sh
        res_target = str(APP_ROOT) + sh + "results" + sh + rand_identifier + sh

    os.mkdir(up_target)
    os.mkdir(res_target)

    rand_progress = res_target + "progress.txt"
    f = open(rand_progress, "w")
    f.write("S: " + "NOT_COMPLETE\n")
    f.write("T: " + "-1\n")
    f.write("C: " + "0\n")
    f.write("K: " + rand_identifier)
    f.close()

    rand_results = res_target + "results.txt"
    f = open(rand_results, "w")
    f.write(" ")
    f.close()

    for file in request.files.values():
        filename = file.filename
        destination = sh.join([up_target, filename])
        file.save(destination)

    # output = process_images()
    # print(output)
    time_now = datetime.datetime.now(datetime.timezone.utc)
    LIFETIME = datetime.timedelta(days=1)
    expiry = time_now + LIFETIME

    GLOBAL_FOLDER_DICT[rand_identifier] = [rand_progress, rand_results, up_target, res_target, expiry]
    print(rand_identifier)
    ''' START SUBPROCESS '''
    ''' process_images(rand_identifier) '''
    #thread = multiprocessing.Process(target=process_images, args=(GLOBAL_FOLDER_DICT[rand_identifier][2],))
    #thread.start()
    #f = _pool.apply_async(process_images,[GLOBAL_FOLDER_DICT[rand_identifier][2], GLOBAL_FOLDER_DICT])
    #r = f.get()
    #print(r)
    #return 'Result is %d'%r

    #process_images(GLOBAL_FOLDER_DICT[rand_identifier][2])

    # 202 Accepted
    return rand_identifier, 202


@app.route('/start/<token>', methods=["GET"])
def start_processing(token):
    return process_images(GLOBAL_FOLDER_DICT[token][2], GLOBAL_FOLDER_DICT)


@app.route('/results/<token>', methods=["GET"])
def check_results(token):
    lines = []
    file = str(request.headers.get('x-customtoken'))
    print("x-customtoken")
    print(file)
    if check_folder(token, GLOBAL_FOLDER_DICT):
        if file == "0":
            print("0")
            with open(GLOBAL_FOLDER_DICT[token][1]) as f:
                for line in f:
                    lines.append(line)
            return_values = "".join(lines)
            return_values = return_values.replace("\n", "\n<br>")
            return return_values
        return GLOBAL_FOLDER_DICT[token][1]
    return 404


@app.route('/progress/<token>', methods=["GET"])
def check_progress(token):
    lines = []
    while lines == []:
        with open(GLOBAL_FOLDER_DICT[token][0]) as f:
            for line in f:
                lines.append(line)
    return "".join(lines)


if __name__ == "__main__":
    #_pool = Pool(processes=4)
    #manager = multiprocessing.Manager()
    #GLOBAL_FOLDER_DICT = manager.dict()
    print("results folder gets cleared with the check_folder function, called in check_results")
    print(" currently this isn't being called anywhere, but we can throw it somewhere")
    app.run()
