import time
from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['CORS_HEADER'] = 'Content-Type'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if (UPLOAD_FOLDER not in os.listdir()):
    os.mkdir(UPLOAD_FOLDER)

mongo_url = os.environ["MONGODB_URI"]
client = MongoClient(mongo_url)
db = client.get_database("geotales")
image_collection = db["images"]


@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    data = request.form

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    new_image = {
        "id": data["id"],
        "userId": data["userId"],
        "userEmail": data["userEmail"],
        "fileName": data["fileName"],
        "fileType": data["fileType"],
        "latitude": float(data["latitude"]),
        "longitude": float(data["longitude"]),
        "uploadTimestamp": time.time(),       
        "imagePath": file_path
    }

    try:
        image_collection.insert_one(new_image)
        return jsonify({"message": "Image uploaded successfully"}, 201)
    except Exception as err:
        print(err)
        return jsonify({"error": "Failed to save image"}), 500


def convert_objectid_to_string(image):
    image['_id'] = str(image['_id'])
    image['uploadTimestamp'] = datetime.utcfromtimestamp(image['uploadTimestamp']).isoformat()
    return image

def __bake_response(images:list):
    images = [convert_objectid_to_string(image) for image in images]
    response = []
    for image in images:
        image_info = image.copy()
        image_info['fileURL'] = url_for('uploaded_file', filename=image['fileName'], _external=True)
        response.append(image_info)
    return response


@app.route('/images', methods=['GET'])
def get_all_images():
    images = list(image_collection.find())
    return jsonify(__bake_response(images)), 200


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename), 200


@app.route('/images/location/<latitude>/<longitude>', methods=['GET'])
def get_images_by_location(latitude, longitude):
    images = list(image_collection.find({"longitude": longitude, "latitude":latitude}))
    return jsonify(__bake_response(images)), 200


@app.route('/images/user/<userId>', methods=['GET'])
def get_images_by_user(userId):
    images = list(image_collection.find({"userId": userId}))
    return jsonify(__bake_response(images)), 200


@app.route('/images_info', methods=['GET'])
def get_images_info():
    images = list(image_collection.find())
    return jsonify(images), 200


@app.route('/images/id/<image_id>', methods=['GET'])
def get_image_by_id(image_id):
    images = list(image_collection.find({"id": image_id}))
    return jsonify(__bake_response(images)), 200


@app.route('/coordinates', methods=['GET'])
def get_coordinates():
    coordinates = list(image_collection.find({}, {"_id": 0, "latitude": 1, "longitude": 1}))
    return jsonify(coordinates), 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)

