import os
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from flask_mysqldb import MySQL
import tensorflow as tf
import json
import numpy as np
import pandas as pd
import base64


#init flask and sql
app = Flask(__name__)
model = tf.keras.models.load_model('model.h5', compile=False)
CORS(app)
mysql = MySQL(app)

app.config['MYSQL_HOST'] = '34.101.145.133'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'democc15'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#JWT
app.config["JWT_SECRET_KEY"] = "rahasiakita" 
jwt = JWTManager(app)

@app.route('/', methods=['GET'])
def index():
    return "Hello World"

# POST - register Users
@app.route("/register", methods=["POST"])
def register():
    username = request.json['username']
    email = request.json['email']
    pwd = request.json['password']
    print(email)
    try:
        print("masuk")
        db = mysql.connection.cursor()
        print("test")
        user = db.execute("SELECT * FROM users WHERE email=(%s)",(email,))
        print(user)
        if user > 0:
            return jsonify({"message":"User already exist"}),401
        db.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, pwd))
        mysql.connection.commit()
        id = db.lastrowid
        db.execute("SELECT * FROM users where id=(%s)",(id,))
        userdetail = db.fetchall()
        db.close()
        return jsonify({
            "msg":"Registration successfull",
            "data":userdetail
        })
    except Exception as e:
         err = jsonify(msg=f'{e}'),500
         return err

@app.route("/login", methods=["POST"])
def login():
    email = request.json["email"]
    password = request.json["password"]
    try:
        db = mysql.connection.cursor()
        user = db.execute("SELECT username, email FROM users WHERE email = %s AND password = %s", (email, password))
        if user > 0:
            user = db.fetchall()
            db.close()
            token = create_access_token(identity=email)
            data = {"message": "login succes", "user": user, "token_jwt": token}
            return jsonify(data),200
        return jsonify({"message": "login gagal"}), 400
    except Exception as e:
        err = jsonify(msg=f'{e}'),500
        return err

@app.route("/predict", methods=['POST'])
@jwt_required()
def predict():
    file = open('labels.txt', 'r')
    labels = file.read().splitlines()
    image = generate_image_from_base64(
        request.json["fileName"], request.json["base64"])
    img = tf.keras.preprocessing.image.load_img(image, target_size=(224, 224))
    x = tf.keras.preprocessing.image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    images = np.vstack([x])
    result = model.predict(images)[0]
    print(result)
    classes = int(result.argmax(axis = -1))
    print(classes)
    os.remove(get_filename(request.json["fileName"]))
    data = {"message": "predict succes", "predict": labels[classes]}
    return jsonify(data),200

def generate_image_from_base64(filename, string):
    file = open('./{filename}.jpg'.format(filename=filename), 'wb')
    file.write(base64.b64decode((string)))
    file.close()

    return './{filename}.jpg'.format(filename=filename)
    
def get_filename(filename):
    return './{filename}.jpg'.format(filename=filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))