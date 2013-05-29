from flask import Flask, render_template, jsonify, request
import os

import utils
app = Flask(__name__)

@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')


@app.route('/about.html')
def about():
    return render_template('about.html')
#ssh -g -R 5000:localhost:5000 user@rpi

@app.route('/_build_phantom')
def bulid_phantom_and_sinogramm():
    r=request.args
    size = request.args.get('size', -1, type=int)
    angles = request.args.get('angles', -1, type=int)

    res = utils.generate_phantom_sinogram(size, angles)
    phantom_file = res['phantom']
    phantom_image = res['phantom_image']
    sinogramm_file = res['sinogramm']
    sinogramm_image = res['sinogramm_image']
    return jsonify(phantom_file='/'+phantom_file, phantom_image='/'+phantom_image,
                   sinogramm_file='/'+sinogramm_file,sinogramm_image='/'+sinogramm_image)

@app.route('/_reconstruct_buzmakov')
def reconstruct_buzmakov():
    r=request.args
    if r['sinogram_mode'] == u'phantom':
        size = request.args.get('size', -1, type=int)
        angles = request.args.get('angles', -1, type=int)
        res = utils.reconstruct_buzmakov(angles, size)
        return jsonify(image=res['image'], status='', link=res['res'])

@app.route('/_reconstruct_prun')
def reconstruct_prun():
    r=request.args
    if r['sinogram_mode'] == u'phantom':
        size = request.args.get('size', -1, type=int)
        angles = request.args.get('angles', -1, type=int)
        res = utils.reconstruct_prun(angles, size)
        return jsonify(image=res['image'], status='', link=res['res'])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5510)
