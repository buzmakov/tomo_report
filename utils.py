#encoding: utf-8
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')

import numpy as np
import pylab as plt

import errno
import sys
import os
import subprocess
import yaml
import hashlib
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.join('..', 'fastlib'))
import fastlib
from fastlib.utils import phantom
from fastlib.imageprocessing.ispmd import rotate_square, project
from fastlib.tomography.sart import sart


def get_strorage_directory(size=None, nang=None, sub_dir=None):
    dir_path = os.path.join('.', 'static', 'data')
    if not (size is None and nang is None):
        dir_path = os.path.join(dir_path, 'sh_l_size_{0}_ang_{1}'.format(size, nang))
    if not sub_dir is None:
        dir_path = os.path.join(dir_path, sub_dir)
    return dir_path


def imsave(fname, arr, vmin=None, vmax=None, cmap=None, format=None, origin=None):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure

    fig = Figure(figsize=arr.shape[::-1], dpi=1, frameon=False)
    canvas = FigureCanvas(fig)
    fig.figimage(arr, cmap=cmap, vmin=vmin, vmax=vmax, origin=origin)
    fig.savefig(fname, dpi=1, format=format)


def genrate_sinogam(image, angles):
    size = image.shape[0]
    sinogram = np.zeros((size, len(angles)), dtype='float32')
    for ia, angle in enumerate(angles):
        tmp_proj = project(rotate_square(image, angle))
        sinogram[:, ia] = tmp_proj
    return sinogram.astype('float32'), angles.astype('float32')


def generate_phantom_sinogram(size, nang):
    dir_name = get_strorage_directory(size, nang)
    phantom_image = os.path.join(dir_name, 'phantom.png')
    sinogramm_image = os.path.join(dir_name, 'sinogramm.png')
    phantom_file = os.path.join(dir_name, 'phantom.txt')
    sinogramm_file = os.path.join(dir_name, 'sinogramm.txt')

    if not os.path.isdir(dir_name):
        ph = phantom.modified_shepp_logan(shape=(size, size, 3))[:, :, 1]
        ph = np.array(ph, dtype='float32')
        angles = np.arange(0, 180, 180.0 / nang).astype('float32')
        s, a = genrate_sinogam(ph, angles)

        try:
            os.mkdir(dir_name)
        except OSError:
            pass

        imsave(phantom_image, ph, cmap=plt.cm.Greys_r)
        imsave(sinogramm_image, s, cmap=plt.cm.Greys_r)

        np.savetxt(phantom_file, ph)
        np.savetxt(os.path.join(dir_name, 'ang.txt'), a)
        np.savetxt(sinogramm_file, s)

    return {'phantom': phantom_file, 'sinogramm': sinogramm_file,
            'sinogramm_image': sinogramm_image, 'phantom_image': phantom_image}


def reconstruct_buzmakov(nang, size):
    dir_name = get_strorage_directory(size, nang)
    res_name = os.path.join(dir_name, 'reconst_buzmakov.txt')
    image_name = os.path.join(dir_name, 'reconst_buzmakov.png')

    if not (os.path.exists(res_name) and os.path.exists(image_name)):
        angles = np.arange(0, 180, 180.0 / nang, dtype='float32')
        sinogramm = np.loadtxt(os.path.join(dir_name, 'sinogramm.txt'), dtype='float32')
        res = sart(sinogramm, angles)
        np.savetxt(res_name, res)
        imsave(image_name, res, cmap=plt.cm.Greys_r)

    return {'image': image_name, 'res': res_name}


def reconstruct_buzmakov_id(sinogramm_id):
    dir_name = get_strorage_directory(sub_dir=sinogramm_id)
    res_name = os.path.join(dir_name, 'reconst_buzmakov.txt')
    image_name = os.path.join(dir_name, 'reconst_buzmakov.png')

    if not (os.path.exists(res_name) and os.path.exists(image_name)):
        sinogramm = np.loadtxt(os.path.join(dir_name, 'sinogramm.txt'), dtype='float32')
        nang = sinogramm.shape[1]
        angles = np.arange(0, 180, 180.0 / nang, dtype='float32')
        res = sart(sinogramm, angles)
        np.savetxt(res_name, res)
        imsave(image_name, res, cmap=plt.cm.Greys_r)

    return {'image': image_name, 'res': res_name}


def generate_prun_config(data_directory):
    data = {'sinogramm': 'sinogramm.txt',
            'angles': 'ang.txt',
            'iterations': 400,
            'relaxation': 0.57,
            'reg_method': 'RM_RAW',
            'reg_params': [0.1, 0.001],
            'output_suffix': 'result',
            # 'phantom': phantom.txt,
            # 'rotation_center': [128, 128],
            'iterations_tosave': [200, 400, 600, 800]
    }
    with open(os.path.join(data_directory, 'config.yaml'), 'w') as f:
        yaml.dump(data, f)


def reconstruct_prun(nang, size):
    dir_name = get_strorage_directory(size, nang)
    binary_name = os.path.abspath(os.path.join('.', 'prun_data', 'tomoreconstruct'))
    image_name = os.path.join(dir_name, 'result_result.png')
    res_name = os.path.join(dir_name, 'result_result.txt')

    if not (os.path.exists(image_name) and os.path.exists(res_name)):
        generate_prun_config(dir_name)
        p = subprocess.Popen([binary_name, 'config.yaml'], cwd=dir_name)
        p.wait()
        p = subprocess.Popen(['convert', 'result_result.tiff', 'result_result.png'], cwd=dir_name)
        p.wait()

    return {'image': image_name, 'res': res_name}

def reconstruct_prun_id(sinogramm_id):
    dir_name = get_strorage_directory(sub_dir=sinogramm_id)
    binary_name = os.path.abspath(os.path.join('.', 'prun_data', 'tomoreconstruct'))
    image_name = os.path.join(dir_name, 'result_result.png')
    res_name = os.path.join(dir_name, 'result_result.txt')

    if not (os.path.exists(image_name) and os.path.exists(res_name)):
        sinogramm = np.loadtxt(os.path.join(dir_name, 'sinogramm.txt'), dtype='float32')
        nang = sinogramm.shape[1]
        angles = np.arange(0, 180, 180.0 / nang, dtype='float32')
        angels_file = os.path.join(dir_name, 'ang.txt')
        np.savetxt(angels_file, angles,delimiter='\n')
        generate_prun_config(dir_name)
        p = subprocess.Popen([binary_name, 'config.yaml'], cwd=dir_name)
        p.wait()
        p = subprocess.Popen(['convert', 'result_result.tiff', 'result_result.png'], cwd=dir_name)
        p.wait()

    return {'image': image_name, 'res': res_name}

def save_upload_sinogram(file_data):
    file_id = hashlib.sha1(file_data).hexdigest()
    dir_name = get_strorage_directory(sub_dir=file_id)

    try:
        os.makedirs(dir_name)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(dir_name):
            pass
        else:
            raise

    sinogramm_file = os.path.join(dir_name, 'sinogramm.txt')
    with open(sinogramm_file, 'w') as f:
        f.write(file_data)

    return file_id, sinogramm_file


def render_uploaded_sinogramm(sinogramm_file):
    image_name = os.path.splitext(sinogramm_file)[0] + '.png'
    data = np.loadtxt(sinogramm_file)
    imsave(image_name, data, cmap=plt.cm.Greys_r)
    return image_name