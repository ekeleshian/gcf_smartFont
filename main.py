from package1.helpers import name_to_path, path_to_name, generate_trial_font_selection
from flask import jsonify, request
import numpy as np
import pandas as pd
import json
from google.cloud import storage
import linecache
import tempfile
import os

GOOGLE = False

BUCKET_NAME = "distance_matrix"
BLOB_NAME = "pers_distance_matrix.csv"

PATH = tempfile.gettempdir()

def download_blob():
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(BLOB_NAME)
    return blob


def insert_http_header(r):
    if r.method == "OPTIONS":
        headers = {
        "Access-Control-Allow-Origin": "*", 
        "Access-Control-Allow-Mehtods": "GET",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "3600"
        }
        return headers
    headers = {"Access-Control-Allow-Origin": "*"}

    return headers


def load_data(model):
    global GOOGLE

    if model == 'google':
        GOOGLE = True
        font_list = pd.read_csv('package1/static/images/google_font_infos.csv')
        font_list = font_list['font_name'].apply(lambda x: x.split('/')[-1].split('.')[0])
        font_paths = np.array([("package1/static/images/fonts/" +
                        name_to_path(item)) for item in font_list])
        distance_matrix = pd.read_csv('package1/static/images/google_distance_matrix.csv', index_col=0) 
        data_num = 803
    else:
        GOOGLE = False
        font_list = pd.read_csv("package1/static/images/pers_font_infos.csv", index_col=0).iloc[:,0]
        font_paths = np.array([("package1/static/images/fonts/" +
                                name_to_path(item)) for item in font_list])
        data_num = 4400
        distance_matrix = download_blob()
    return font_list, font_paths, distance_matrix, data_num




def select_data(r):
    header = {
        "Access-Control-Allow-Origin": "*", 
        "Access-Control-Allow-Mehtods": "GET",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "3600"
        }
    category = r.args.get('category')
    _, font_paths, _, data_num = load_data(category)
    results = initialize(font_paths, data_num)
    return (results, 200, header)


def initialize(font_paths, data_num):

    idx = np.random.randint(data_num, size=5)

    result = font_paths[idx].tolist() # I have to change the numpy to list because Object of type 'ndarray' is not JSON serializable

    return jsonify(result=result, google=GOOGLE)


def neighbors(r):
    global GOOGLE
    google = r.args.get("category")

    if google == "google":
        GOOGLE = True
    else:
        GOOGLE = False

    if GOOGLE:
        font_list, font_paths, distance_matrix, data_num = load_data('google')
    else:
        font_list, font_paths, distance_matrix, data_num = load_data('other')


    font_name = r.args.get('clicked_font')

    font_name = font_name.replace("%20", " ")
    header = {
        "Access-Control-Allow-Origin": "*", 
        "Access-Control-Allow-Mehtods": "GET",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "3600"
        }
    idx = font_list[font_list == font_name].index[0]
#global model variable to be replaced
    if GOOGLE:
        relevant_row = np.array(distance_matrix.iloc[[idx], :]).reshape(-1)
    else:
        offset = 20901
        relevant_row = distance_matrix.download_as_string(start=offset*(idx+1), end=offset*(idx+2)-1)
        relevant_row = np.array(relevant_row.split(b','))
        relevant_row = relevant_row[np.where(relevant_row != b'')].astype(int)
        relevant_row = relevant_row[2:]
        # relevant_row = [int(elem) for elem in filter(lambda i: i != '', relevant_row)]
        # relevant_row = np.array(relevant_row[2:])

    idx_top5,dist_top5 = generate_trial_font_selection(idx,
                                        relevant_row)
    # set_trace()
    name = font_name.replace('%20', ' ')
    file_path = f'package1/static/images/fonts/{name}.png'
    neighbor_paths = font_paths[idx_top5].tolist()
    neighbs = []
    result = {'name': name, 'img': file_path, 'children': neighbs}
    for i, n in enumerate(neighbor_paths):
        font_name = n.split('/')[-1].split('.')[0].replace('%20', ' ')
        distance = dist_top5[i]
        distance = np.int(distance)
        path = n.replace('%20', ' ')
        sub_result = {'name': font_name, 'img': path, 'distance': distance}
        neighbs.append(sub_result)
    final_result = {"name":"bubble", "children":[result]}

    return (jsonify(final_result), 200, header)