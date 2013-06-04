# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, request, g
import flask_sijax
import os
import sys

path = os.path.join('.', os.path.dirname(__file__), '../')
sys.path.append(path)

import utils

app = Flask(__name__)

# The path where you want the extension to create the needed javascript files
# DON'T put any of your files in this directory, because they'll be deleted!
app.config["SIJAX_STATIC_PATH"] = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')

# You need to point Sijax to the json2.js library if you want to support
# browsers that don't support JSON natively (like IE <= 7)
app.config["SIJAX_JSON_URI"] = '/static/js/sijax/json2.js'

flask_sijax.Sijax(app)


class SijaxHandler(object):
    """A container class for all Sijax handlers.

    Grouping all Sijax handler functions in a class
    (or a Python module) allows them all to be registered with
    a single line of code.
    """

    @staticmethod
    def _dump_data(obj_response, files, form_values, container_id):
        def dump_files():
            if 'file' not in files:
                return 'Bad upload'

            file_data = files['file']
            file_name = file_data.filename
            if file_name is None:
                return 'Nothing uploaded'

            file_type = file_data.content_type
            file_size = len(file_data.read())
            return 'Uploaded file %s (%s) - %sB' % (file_name, file_type, file_size)

        html = dump_files()

        obj_response.html('#%s' % container_id, html)

    @staticmethod
    def form_one_handler(obj_response, files, form_values):
        SijaxHandler._dump_data(obj_response, files, form_values, 'form-sinogram-upload-response')
        obj_response.reset_form()
        obj_response.html_append('#form-sinogram-upload-response',
                                 '<br>Генерирую изображения синограмм.')
        yield obj_response

        from time import sleep
        sleep(2)
        obj_response.html_append('#form-sinogram-upload-response', '<br />Finished!')


@app.route('/',methods=['GET', 'POST'])
@app.route('/index.html')
def index():
    # Notice how we're doing callback registration on each request,
    # instead of only when needed (when the request is a Sijax request).
    # This is because `register_upload_callback` returns some javascript
    # that prepares the form on the page.
    form_init_js = ''
    form_init_js += g.sijax.register_upload_callback('form-sinogram-upload', SijaxHandler.form_one_handler)

    if g.sijax.is_sijax_request:
        # The request looks like a valid Sijax request
        # The handlers are already registered above.. we can process the request
        return g.sijax.process_request()
    return render_template('index.html', form_init_js=form_init_js)

@app.route('/about.html')
def about():
    return render_template('about.html')

#ssh -g -R 5000:localhost:5000 user@rpi

@app.route('/_build_phantom')
def bulid_phantom_and_sinogramm():
    r = request.args
    size = request.args.get('size', -1, type=int)
    angles = request.args.get('angles', -1, type=int)

    res = utils.generate_phantom_sinogram(size, angles)
    phantom_file = res['phantom']
    phantom_image = res['phantom_image']
    sinogramm_file = res['sinogramm']
    sinogramm_image = res['sinogramm_image']
    return jsonify(phantom_file='/' + phantom_file, phantom_image='/' + phantom_image,
                   sinogramm_file='/' + sinogramm_file, sinogramm_image='/' + sinogramm_image)


@app.route('/_reconstruct_buzmakov')
def reconstruct_buzmakov():
    r = request.args
    if r['sinogram_mode'] == u'phantom':
        size = request.args.get('size', -1, type=int)
        angles = request.args.get('angles', -1, type=int)
        res = utils.reconstruct_buzmakov(angles, size)
        return jsonify(image=res['image'], status='', link=res['res'])


@app.route('/_reconstruct_prun')
def reconstruct_prun():
    r = request.args
    if r['sinogram_mode'] == u'phantom':
        size = request.args.get('size', -1, type=int)
        angles = request.args.get('angles', -1, type=int)
        res = utils.reconstruct_prun(angles, size)
        return jsonify(image=res['image'], status='', link=res['res'])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5510)
