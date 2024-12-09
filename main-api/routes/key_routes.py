from flask import Blueprint, request, jsonify
from ..models.key import Key
from bson import ObjectId

key_bp = Blueprint("key_bp", __name__)

@key_bp.route("/keys/<key_id>", methods=["GET"])
def get_key(key_id):
    key = keys.get_by_id(ObjectId(key_id))
    return jsonify(key.__dict__) if key else {"error": "keys not found"}, 404

@key_bp.route("/keys", methods=["POST"])
def create_key():
    data = request.json
    key = keys(**data)
    key.save()
    return jsonify(key.__dict__), 201

@key_bp.route("/keys/<key_id>", methods=["DELETE"])
def delete_key(key_id):
    key = keys.get_by_id(ObjectId(key_id))
    if key:
        key.delete()
        return jsonify({"message": "keys deleted successfully"}), 200
    else:
        return jsonify({"error": "keys not found"}), 404
