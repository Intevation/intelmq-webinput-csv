# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, make_response
import tempfile
import os
import atexit


TEMPORARY_FILES = []


app = Flask('intelmq-webinput-csv')


@app.route('/')
def form():
    return('''<html><body>
    <form action="/upload" method="POST" enctype="multipart/form-data">
    <input type="file" name="file">
    <input type="text" name="text">
    <input type="submit" value="Submit">
    </form></body></html>
    ''')


@app.route('/upload', methods=['POST'])
def upload_file():
    success = False
    if request.method == 'POST':
        if 'file' in request.files and request.files['file'].filename:
            filedescriptor, filename = tempfile.mkstemp(suffix=".csv", text=True)
            request.files['file'].save(filename)
            success = True
        elif 'text' in request.form and request.form['text']:
            filedescriptor, filename = tempfile.mkstemp(suffix=".csv", text=True)
            with os.fdopen(filedescriptor, mode='w') as handle:
                handle.write(request.form['text'])
            success = True
    if success == True:
        TEMPORARY_FILES.append((filedescriptor, filename))
        preview = []
        with open(filename) as handle:
            for counter in range(100):
                line = handle.readline()
                if line:
                    preview.append(line)
        response = make_response(jsonify(preview))
        response.mimetype = 'application/json'
        response.headers['Content-Type'] = "text/json; charset=utf-8"
        return response
    return ''


def delete_temporary_files():
    for filedescriptor, filename in TEMPORARY_FILES:
        os.remove(filename)


def main():
    atexit.register(delete_temporary_files)
    app.run()


if __name__ == "__main__":
    main()
