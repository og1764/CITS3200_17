import datetime
import glob
import io
import keras
import keras.callbacks
import numpy as np
import os
import os.path
import random
import requests
import shutil
import string
import sys
import tarfile
import time
import urllib.request
import zipfile
from Form import LoginForm
from Model import query_user, User
from PIL import Image, UnidentifiedImageError
from bs4 import BeautifulSoup
from config import Config
from flask import flash, Flask, json, redirect, render_template, request, Response, send_file, send_from_directory, \
    url_for
from flask_login import current_user, login_required, login_user, LoginManager, logout_user
from flask_wtf import FlaskForm
from keras import backend as K
from keras.datasets import mnist
from keras.layers import Conv2D, Dense, Dropout, Flatten, MaxPooling2D
from keras.models import model_from_json, Sequential
from keras.utils import np_utils
from os import listdir
from os.path import isfile, join
from stat import S_ISREG, ST_CTIME, ST_MODE
from werkzeug.urls import url_parse
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired, ValidationError

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
VALID_COMPRESSED = (".zip", ".tar.gz", ".tar")  # TODO: Add 7z, Add rar
IMG_TYPES = ['.jpg', '.png']
PROGRESS = {}
B_W_LIFETIME = 60 * 60 * 24 * 1  # [seconds] 60*60*24*1 = once a day
UPL_LIFETIME = 60 * 60 * 24 * 1  # [seconds] 60*60*24*1 = once a day
RES_LIFETIME = 60 * 60 * 24 * 1  # [seconds] 60*60*24*1 = once a day
BG_INDEX = 0
BG_SET_TIME = 0.0
SH = os.sep
RESULTS_FOLDER = str(APP_ROOT) + SH + "results" + SH
UPLOADS_FOLDER = str(APP_ROOT) + SH + "uploads" + SH
B_W_FOLDER = str(APP_ROOT) + SH + "black_and_white" + SH

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'SECRET KEY'
login = LoginManager(app)
login.login_view = 'login'


def process_compressed(compressed_list):
    """
    Takes an array of file paths to compressed folders, extracts them,
    and returns the file paths of the extracted folder in an array.

    :param compressed_list: array of file paths
    :type compressed_list: list
    :return array:
    """

    folder_list = []

    for file in compressed_list:
        if file.endswith((".tar", ".tar.gz")):
            tf = tarfile.open(file)
            os.mkdir(file + ".dir" + SH)
            folder_list.append(file + ".dir" + SH)
            tf.extractall(file + ".dir" + SH)
            tf.close()
        if file.endswith(".zip"):
            with zipfile.ZipFile(file, 'r') as zf:
                os.mkdir(file + ".dir" + SH)
                folder_list.append(file + ".dir" + SH)
                zf.extractall(file + ".dir" + SH)
    return folder_list


def files_in_folder(target):
    """
    Takes a file path of a target directory and returns an array containing the path of each file in the target.

    :param target: Uploads file path
    :type target: str
    :return array:
    """

    file_list = os.listdir(target)
    result = []

    # Iterate over all the entries
    for entry in file_list:
        # Create full path
        if not entry.startswith("._"):
            path = os.path.join(target, entry)
            if os.path.isdir(path):
                result = result + files_in_folder(path)
            elif not path.endswith(VALID_COMPRESSED):
                result.append(path)
    return result


def normalise_images(files, target, token):
    """
    Takes an array of files and their base file path, and normalises the pixel value of images such that each image is
    black and white and the value of each pixel is between 0 and 1. If the file isn't an image, it adds an error message
    that can be processed later. Returns an array of tuples, holding the normalised pixel values and the image name.

    :param files: Array of files to be normalised
    :type files: list
    :param target: Base file path
    :type target: str
    :return array:
    """

    global PROGRESS
    image_values = []

    for file in files:
        name = file.replace(target, "")
        name = name.replace(".dir", "")
        path = name.split(SH)
        print(name)
        print(path)
        try:
            initial = Image.open(file)
            result = initial.resize((50, 50)).convert("L")
            pix_val = list(result.getdata())
            norm_val = [i / 255 for i in pix_val]
            image_values.append((norm_val, name + " <br>"))
            # save file to results\BW\
            # ah shit we're going to have to make all of the fucking directories....
            for i in range(len(path) - 1):
                subpath = B_W_FOLDER + token + SH + path[i]
                if not os.path.exists(subpath):
                    os.mkdir(subpath)
            # print(B_W_FOLDER + name)
            result.save(B_W_FOLDER + token + SH + name)

            initial.close()
        except UnidentifiedImageError:
            print("Unidentified Image Error")
            extension = name.split(".")[-1]
            error_message = 'Could not classify "<b>{}</b>" as <b>.{}</b> is not a valid file extension. <br>'.format(
                name.lstrip(), extension.rstrip())
            image_values.append((error_message, ""))
        except:
            print(str(sys.exc_info()[1]) + " @ Line " + str(sys.exc_info()[2].tb_lineno))
        PROGRESS[token]['normalise'] = PROGRESS[token]['normalise'] + 1

        os.remove(file)
    return image_values


def bulk_classify(files, loaded_model, token):
    """
    Takes an array of files and a model for the CNN, and classifies each file.

    :param files: Array of files to classify
    :type files: list
    :param loaded_model: Model loaded from disk
    :return array:
    """

    global PROGRESS
    return_values = []

    for i in files:
        if i[1] != "":
            return_values.append((CNN(i[0], loaded_model), i[1]))
        else:
            return_values.append((i[0], ""))
        # append token and filename to progress tracking dictionary
        PROGRESS[token]['classify'] = PROGRESS[token]['classify'] + 1
    return return_values


def file_cleanup(target, compressed, folders):
    """
    Deletes files after they have been used.

    :param target: Uploads file path
    :type target: str
    :param compressed: Array of compressed files
    :type compressed: list
    :param folders: Array of folders
    :type folders: list
    :return None:
    """

    for file in compressed:
        try:
            os.remove(file)
        except OSError:
            print(str(sys.exc_info()[1]) + " @ Line " + str(sys.exc_info()[2].tb_lineno))
        except:
            # Hopefully this line never gets reached. Not ideal to have bare except but I'm not convinced.
            print("You messed up error handling")
            print(str(sys.exc_info()[1]) + " @ Line " + str(sys.exc_info()[2].tb_lineno))
    for folder in folders:
        shutil.rmtree(folder)
    shutil.rmtree(target)


def format_results(token, results):
    """
    Takes a token and an array of results from the CNN, and parses those results. Generates a HTML string to be sent
    to the webpage, and generates files to be returned to the user.

    :param token: Identifier
    :type token: str
    :param results: Array of tuples from bulk_classify
    :type results: list
    :return str:
    """

    html_string = ""
    folders = {"orphaned": ""}
    left_path = str(RESULTS_FOLDER) + token + SH
    root_path = UPLOADS_FOLDER + token + SH
    results_path = RESULTS_FOLDER + token + SH + "results.txt"
    timeout_path = RESULTS_FOLDER + token + SH + "timeout.txt"
    done_path = RESULTS_FOLDER + token + SH + "done.txt"

    for i in results:
        for j in i:
            html_string = html_string + "".join(j).replace(root_path, "").replace(" <br>", "<br>")

    splitted = html_string.split("<br>")

    # Removing empty string from list
    splitted = [i for i in splitted if i]

    if html_string == "":
        html_string = "..."

    f = open(results_path, "w+")
    written = html_string.replace(" <br>", "\n")
    f.write(written)
    f.close()

    for i in splitted:
        files = str(i).split(",")
        if len(files) == 3:
            file_name = files[2].strip()
            left = file_name.split(SH)
            if len(left) > 1:
                if left[0] not in folders:
                    if left[0].endswith(VALID_COMPRESSED):
                        folders[left[0]] = i + "\n"
                    else:
                        print(left)
                        print("You shouldn't be here")
                else:
                    init = folders[left[0]]
                    folders[left[0]] = init + i + "\n"
            else:
                init = folders["orphaned"]
                folders["orphaned"] = init + i + "\n"

    keys = folders.keys()

    if keys != ["orphaned"]:
        for key in keys:
            if key != "orphaned":
                new_file_name = left_path + key + ".txt"
            else:
                new_file_name = left_path + "images.txt"
            f = open(new_file_name, "w+")
            text = folders[key].replace(" <br>", "\n")
            f.write(text)
            f.close()
    
    f = open(timeout_path, "w+")
    f.write(html_string)
    f.close()
    
    f = open(done_path, "w+")
    f.write(" ")
    f.close()
    
    return html_string[0:-4]


def check_folder():
    """
    Loops over results and uploads folder and removes old files that haven't been deleted. This is mainly for the
    results folder.
    Ideally this never removes anything from the uploads folder, as they should already be deleted, but it acts as a
    nice backup.

    :return None:
    """

    now = time.time()

    for r in os.listdir(RESULTS_FOLDER):
        r_path = os.path.join(RESULTS_FOLDER, r)
        if os.stat(r_path).st_mtime < now - RES_LIFETIME:
            if os.path.isdir(r_path):
                shutil.rmtree(r_path)
             
    for r in os.listdir(B_W_FOLDER):
        r_path = os.path.join(B_W_FOLDER, r)
        if os.stat(r_path).st_mtime < now - B_W_LIFETIME:
            if os.path.isdir(r_path):
                shutil.rmtree(r_path)

    try:
        now = time.time()
        for u in os.listdir(UPLOADS_FOLDER):
            u_path = os.path.join(UPLOADS_FOLDER, u)
            u_create = os.stat(u_path).st_mtime
            if u_create < now - UPL_LIFETIME:
                if os.path.isdir(u_path):
                    shutil.rmtree(u_path)
    except:
        print(str(sys.exc_info()[1]) + " @ Line " + str(sys.exc_info()[2].tb_lineno))


def process_images(target, neural_network):
    """
    Takes in a file path to a folder, and processes the images in that folder. Essentially the main loop of the program.
    Returns a html string to show on the webpage.

    :param target: Uploads file path (+sh)
    :type target: str
    :return str:
    """

    t1 = datetime.datetime.now()
    token = target.split(SH)[-2]
    global PROGRESS
    print(neural_network)
    compressed_list = [target + filename for filename in os.listdir(target) if filename.endswith(VALID_COMPRESSED)]

    # Loop over and extract compressed folders
    folder_list = process_compressed(compressed_list)

    # Get array of the files in a folder
    only_files = files_in_folder(target)

    # Store the total number of files to be processed in the progress dict
    PROGRESS[token]['total'] = len(only_files)

    if neural_network in ["shape"]:
        # Moved this out of the CNN function because its expensive, so its better to only call once.
        json_file = open(APP_ROOT + SH + 'ct3200.dir' + SH + 'model.json', 'r')
        loaded_model_json = json_file.read()
        json_file.close()
        loaded_model = model_from_json(loaded_model_json)
        # load weights into new model
        loaded_model.load_weights(APP_ROOT + SH + "ct3200.dir" + SH + "model.h5") 
    else:
        # Whatever you need for the other nural network
        pass

    if neural_network in ["shape"]:
        # normalises image files, gives an error if not a valid image type.
        image_values = normalise_images(only_files, target, token)
    else:
        # if normalise_images isn't suitable for your function
        # image_values = ?
        pass

    if neural_network in ["shape"]:
        # sends normalised images into the classifier
        return_values = bulk_classify(image_values, loaded_model, token)
    else:
        # Your version of bulk_classify that works with the other neural network
        # return_values = ?
        pass

    if neural_network in ["shape"]:
        # removes compressed files and folders after they've been extracted.
        file_cleanup(target, compressed_list, folder_list)
    else:
        # if file_cleanup isn't suitable for your function
        pass

    if neural_network in ["shape"]:
        # This formats results to be sent back and creates a text file
        to_send = format_results(token, return_values)
    else:
        # if format_results isn't suitable for your function
        to_send = ""

    t2 = datetime.datetime.now()
    tot_time = t2 - t1
    print("\nTime taken for this request: " + str(tot_time) + "\n")

    return to_send


def CNN(lines, loaded_model):
    # Initialising Variables

    num_classes = 3
    n_mesh = 50
    i_bin = 0
    j_bin = -1
    return_values = []
    nmodel = 1

    img_rows, img_cols = n_mesh, n_mesh
    n_mesh2 = n_mesh * n_mesh - 1
    n_mesh3 = n_mesh * n_mesh

    # Setting up numpy arrays
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

    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)

    y_vec = np.zeros(num_classes)
    y_pred = loaded_model.predict(x_test)

    for i in range(ntest):
        for j in range(num_classes):
            y_vec[j] = y_pred[i, j]
        y_type = np.argmax(y_vec)
        prob = y_vec[y_type]

        # Our value for y type defines the type of galaxy we are getting, and in all instances we provide the probability
        galaxy_type = ""
        if y_type == 0:
            galaxy_type = "E"
        if y_type == 1:
            galaxy_type = "S0"
        if y_type == 2:
            galaxy_type = "Sp"

        return_values.append("{0}, {1:.2f}%, ".format(galaxy_type, prob * 100))

    return return_values


def files_sorted_by_date(dir_path):
    """
    Returns files in directory sorted by creation date.

    :param dir_path: Path of folder
    :type dir_path: str
    :return array:
    """

    # all entries in the directory w/ stats
    data = (os.path.join(dir_path, fn) for fn in os.listdir(dir_path)
            if fn.endswith(IMG_TYPES[0]) or fn.endswith(IMG_TYPES[1]))
    data = ((os.stat(path), path) for path in data)
    # regular files, insert creation date
    data = ((stat[ST_CTIME], path) for stat, path in data if S_ISREG(stat[ST_MODE]))

    file_list = []
    for cdate, path in sorted(data):
        file_list.append([time.ctime(cdate), os.path.basename(path)])
    file_list.reverse()

    return file_list


def center_crop():
    """
    Crops background.jpg such that it can be used as a header image for the website.

    :return None:
    """

    try:
        location = str(APP_ROOT) + SH + "static" + SH + "img" + SH + "background.jpg"
        im = Image.open(location)
        width, height = im.size  # Get dimensions

        left = 0
        right = width
        top = height / 3
        bottom = 2 * height / 3

        # Crop the image
        im = im.crop((left, top, right, bottom))
        im.save(location)
    except UnidentifiedImageError:
        print("image crop failed")
    except:
        print(str(sys.exc_info()[1]) + " @ Line " + str(sys.exc_info()[2].tb_lineno))


def default_bg():
    """
    Copy default background to background.jpg.

    :return None:
    """

    default_bg = str(APP_ROOT) + SH + "static" + SH + "img" + SH + "background_default.jpg"
    bg_destination = str(APP_ROOT) + SH + "static" + SH + "img" + SH + "background.jpg"
    try:
        shutil.copy2(default_bg, bg_destination)
    except:
        print("Failed to use default background")


def choose_new_background(mode='latest', interval=0):
    """
    Updates the background file to be used by the site's css.
    Latest mode will download and set a new background once per interval.
    Sequence mode will iterate through a folder of backgrounds at one iteration per interval.

    :param mode: latest OR sequence
    :type mode: str
    :param interval: Interval in seconds
    :type interval: int
    :return None:
    """

    global BG_INDEX
    global BG_SET_TIME

    if time.time() > BG_SET_TIME + interval:
        create_backgrounds_folder()
        ###run updates to the background here
        ###background downloaded and prepared for detection by css once every time interval

        bg_dir_location = str(APP_ROOT) + SH + "backgrounds" + SH
        bg_destination = str(APP_ROOT) + SH + "static" + SH + "img" + SH + "background.jpg"

        if mode == 'latest':
            try:
                download_background()
                file_list = files_sorted_by_date(bg_dir_location)
                latest_file = file_list[0]
                bg_location = bg_dir_location + latest_file[1]
                print(latest_file)
                shutil.copy2(bg_location, bg_destination)
                center_crop()
            except:
                print("Setting background from backgrounds folder (latest) failed")
                default_bg()

        elif mode == 'sequence':
            try:
                file_list = files_sorted_by_date(bg_dir_location)
                bg_index = (BG_INDEX + 1) % len(file_list)
                next_file = file_list[bg_index]
                bg_location = bg_dir_location + next_file[1]
                print(next_file)
                shutil.copy2(bg_location, bg_destination)
                center_crop()
            except:
                print("Setting background from backgrounds folder (sequence) failed")
                default_bg()

        # record the time at which the background updates were run
        BG_SET_TIME = time.time()


def download_background():
    """
    Downloads background image.

    :return None:
    """

    url = "https://apod.nasa.gov/apod/astropix.html"
    root_url = "https://apod.nasa.gov/apod/"
    img_url = scrape_img_url(url, root_url)
    download_img_from_url(img_url)


def create_backgrounds_folder():
    """
    Make backgrounds folder if it doesn't exist already.

    :return None:
    """

    # make backgrounds folder if it doesn't already exist
    destination = str(APP_ROOT) + SH + "backgrounds" + SH
    if not os.path.exists(destination):
        os.mkdir(destination)


def scrape_img_url(url, root_url):
    """
    Scrapes URL of an image embedded in html page.
    Used for when the latest image url changes but is linked to by the same page.
    Currently programmed to look for the first image on the page.

    :param url: URL of the html page the image is embedded in, eg. http://example.com/main.html
    :type url: str
    :param root_url: URL stub where the image will be located, eg. http://example.com/images/ <-- image.jpg will be appended here
    :type root_url: str
    :return url:
    """

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


def download_img_from_url(url):
    """
    Download image from URL to backgrounds folder.

    :param url: URL
    :type url: str
    :return None:
    """

    destination = str(APP_ROOT) + SH + "backgrounds" + SH
    split_list = url.split("/")
    name = split_list[len(split_list) - 1]
    filename = destination + str(name)
    urllib.request.urlretrieve(url, filename)


@login.user_loader
def load_user(user_id):
    """ Checks if user is logged in (?) """
    # @Grey is this docstring correct?
    if query_user(user_id) is not None:
        curr_user = User()
        curr_user.id = user_id
        return curr_user


@app.route('/')
@app.route('/home')
def home():
    """ Homepage """
    return render_template('home.html')


@app.route("/manual", methods=['GET', 'POST'])
@login_required
def manual():
    """ Manual page """
    choose_new_background(mode='latest', interval=60 * 60 * 6)  # [seconds] 60*60*24 = once every 24 hours
    return render_template('manual.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    """ Login page """
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


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """ Logs a user out and redirects to login """
    logout_user()
    return redirect(url_for('login'))


@app.route("/main", methods=['GET', 'POST'])
@login_required
def main():
    """ Main webpage """
    choose_new_background(mode='latest', interval=60 * 60 * 6)  # [seconds] 60*60*24 = once every 24 hours
    return render_template('main.html')


@app.route("/upload", methods=['POST'])
def upload():
    """
    Takes a POST request and saves uploaded files to the correct subfolder of uploads. Generates any required folders
    and tokens, and returns 202: ACCEPTED and the token to the webpage

    :return token:
    """

    if not os.path.exists(UPLOADS_FOLDER):
        os.mkdir(UPLOADS_FOLDER)
    if not os.path.exists(RESULTS_FOLDER):
        os.mkdir(RESULTS_FOLDER)
    if not os.path.exists(B_W_FOLDER):
        os.mkdir(B_W_FOLDER)

    new_token = ''.join(random.choice(string.ascii_letters) for i in range(12))
    upl_target = UPLOADS_FOLDER + new_token + SH
    res_target = RESULTS_FOLDER + new_token + SH
    b_w_target = B_W_FOLDER + new_token + SH

    while os.path.exists(upl_target) or os.path.exists(res_target):
        new_token = ''.join(random.choice(string.ascii_letters) for i in range(12))
        upl_target = UPLOADS_FOLDER + new_token + SH
        res_target = RESULTS_FOLDER + new_token + SH
        b_w_target = B_W_FOLDER + new_token + SH

    os.mkdir(upl_target)
    os.mkdir(res_target)
    os.mkdir(b_w_target)

    rand_results = res_target + "results.txt"
    f = open(rand_results, "w")
    f.write(" ")
    f.close()

    # Save each uploaded file to the correct subfolder in uploads.
    for file in request.files.values():
        filename = file.filename
        destination = SH.join([upl_target, filename])
        file.save(destination)

    PROGRESS[new_token] = {}
    PROGRESS[new_token]['total'] = 0
    PROGRESS[new_token]['normalise'] = 0
    PROGRESS[new_token]['classify'] = 0

    # 202 Accepted
    return (new_token, 202)


@app.route('/start', methods=["GET"])
def start_processing():
    """
    Receives a GET request with a TOKEN in the header. Processes corresponding files and returns the results formatted
    correctly as HTML for display on the webpage.

    :return str:
    """

    token = request.headers.get("TOKEN")
    neural_network = request.headers.get("NETWORK").lower()
    check_folder()
    target = UPLOADS_FOLDER + token + SH
    print(neural_network)
    # Make uploads folder if doesn't exist
    if not os.path.exists(target):
        os.mkdir(target)
    return process_images(target, neural_network)


@app.route('/getResults/<token>')
def return_file(token):
    """
    Gets results files based on the token. If there are multiple files, zip them and return the zip file to the user,
    otherwise return just one text file.

    :param token: Unique Identifier
    :type token: str
    :return file:
    """

    left_path = RESULTS_FOLDER + token + SH
    files = [f for f in os.listdir(left_path)]
    output_files = [i for i in files if i not in ['progress.txt', 'results.txt', 'done.txt', 'timeout.txt']]
    if len(output_files) > 0 and output_files != ["images.txt"]:
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for i in output_files:
                zf.write(left_path + i, i)
        memory_file.seek(0)
        to_return = Response(
            memory_file,
            mimetype="application/zip",
            headers={"Content-disposition":
                         "attachment; filename=Results.zip"})
    else:
        file = RESULTS_FOLDER + token + SH + "results.txt"
        with open(file) as f:
            txt_content = f.read()
        to_return = Response(
            txt_content,
            mimetype="text/txt",
            headers={"Content-disposition":
                         "attachment; filename=Results.txt"})
    return to_return


@app.route('/getProgress/<token>', methods=["GET"])
def getProgress(token):
    """
    Gets progress of request based on the token. Returns the percentage completeness.

    :param token: Unique Identifier
    :type token: str
    :return progress:
    """

    global PROGRESS
    percentage = 0
    if PROGRESS[token]['total'] > 0:
        percentage = int(round(((0.02 * PROGRESS[token]['normalise'] + 0.98 * PROGRESS[token]['classify']) /
                                PROGRESS[token]['total']) * 100))
        if percentage > 100:
            percentage = 100
    print(percentage)
    to_return = Response(str(percentage))
    return to_return


@app.route('/timeout', methods=["GET"])
def on_timeout():
    """
    Allows results to be collected even if Heroku times out. 
    
    :return 408 timeout OR results:
    """
    
    token = request.headers.get("TOKEN")
    if os.path.exists(RESULTS_FOLDER + token + SH + "done.txt"):
        file = RESULTS_FOLDER + token + SH + "results.txt"
        with open(file) as f:
            txt_content = f.read()
        return txt_content
    # Ideally I have some sort of wait so that it doesn't spam the timeout function, but idk how to do that without slowing everything down with a time.sleep or some shit
    return 408


@app.route('/getImages/<token>', methods=["GET"])
def return_images(token):
    """
    Gets black and white image files based on the token, zips them and returns the zip file to the user,

    :param token: Unique Identifier
    :type token: str
    :return file:
    """
    
    left_path = B_W_FOLDER + token + SH
    files = [f for f in os.listdir(left_path)]
    output_files = [i for i in files if i not in ['progress.txt', 'results.txt', 'done.txt']]
    print(output_files)
    if len(output_files) > 0 and output_files != ["images.txt"]:
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for root, dirs, files in os.walk(left_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    sub_path = full_path.replace(left_path, "")
                    zf.write(full_path, sub_path)
        memory_file.seek(0)
        to_return = Response(
            memory_file,
            mimetype="application/zip",
            headers={"Content-disposition":
                         "attachment; filename=B_W_images.zip"})
        return to_return
    print("idk why we're here. this is an issue")
    return 0


if __name__ == "__main__":
    app.run()
