import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

import sys
sys.path.insert(0, "../")

from ppg import Euler

UPLOAD_FOLDER = './'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mov'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print("Saving File")
            file.save(full_filename)
            print("File Saved")
            print("Processing...")
            euler = Euler()
            euler.get_signals(full_filename)
            print("File Saved")
            hr = euler.simple_average()
            return '''
                <!doctype html>
                <title>PPG</title>
                <h1>Your HR was: {:d}</h1>
                <form method=post enctype=multipart/form-data>
                <input type=file name=file>
                <input type=submit value=Upload>
                </form>
                '''.format(int(hr))
    return '''
    <!doctype html>
    <title>PPG</title>
    <h1>Upload new .mov file of your face (over 30 seconds!)</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''