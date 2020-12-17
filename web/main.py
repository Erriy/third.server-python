#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import os
import traceback
from flask import Flask, send_file
from flask_cors import CORS
from web_common import ErrorMsg, build_response
from api_pubkey import pubkey
from api_seed import seed
from api_admin import admin


app = Flask("third")
CORS(app, supports_credentials=True)


@app.errorhandler(ErrorMsg)
def error_return(err):
    return build_response(code=err.code, message=err.msg)


@app.errorhandler(Exception)
def error_return(err):
    traceback.print_exc()
    return build_response(code=500, message="服务器未知错误")


@app.route("/")
def root():
    index_path = os.path.join(app.static_folder, "index.html")
    return send_file(index_path)


@app.route("/<path:path>")
def route_frontend(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    else:
        index_path = os.path.join(app.static_folder, "index.html")
        return send_file(index_path)


app.register_blueprint(pubkey, url_prefix="/api/pubkey")
app.register_blueprint(seed, url_prefix="/api/seed")
app.register_blueprint(admin, url_prefix='/api/admin')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8000)

