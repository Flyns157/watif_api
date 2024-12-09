from flask import Blueprint, request, jsonify
from models.interest import Interest
from bson import ObjectId

interest_bp = Blueprint("interest_bp", __name__)

@interest_bp.route("/interests/<interest_id>", methods=["GET"])
def get_interest(interest_id):
    interest = Interest.get_by_id(ObjectId(interest_id))
    return jsonify(interest.__dict__) if interest else {"error": "Interest not found"}, 404

@interest_bp.route("/interests", methods=["POST"])
def create_interest():
    data = request.json
    interest = Interest(**data)
    interest.save()
    return jsonify(interest.__dict__), 201

@interest_bp.route("/interests/<interest_id>", methods=["DELETE"])
def delete_interest(interest_id):
    interest = Interest.get_by_id(ObjectId(interest_id))
    if interest:
        interest.delete()
        return jsonify({"message": "Interest deleted successfully"}), 200
    else:
        return jsonify({"error": "Interest not found"}), 404
