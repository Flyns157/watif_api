from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from models.user import User
from bson import ObjectId

user_bp = Blueprint("user_bp", __name__, url_prefix="/api/users")

@user_bp.route("/<user_id>", methods=["GET"])
def get_user(user_id):
    user = User.get_by_id(user_id)
    if user:
        user_dto = user.to_dto()
        return jsonify(user_dto.model_dump()), 200
    else:
        return jsonify({"error": "User not found"}), 404

@user_bp.route("/users", methods=["POST"])
def create_user():
    data = request.json
    user = User(**data)
    user.save()
    user_dto = user.to_dto()  # Conversion en DTO avant envoi
    return jsonify(user_dto.model_dump()), 201

@user_bp.route('/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()

    # Vérifiez que l'utilisateur modifie ses propres informations
    if current_user_id != user_id:
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.get_json()
    user = User.get_by_id(ObjectId(user_id))

    if user:
        user.update(**data)  # Assurez-vous que la méthode `update` gère les mises à jour de manière sécurisée
        return jsonify({"message": "User updated successfully"}), 200
    else:
        return jsonify({"error": "User not found"}), 404

@user_bp.route("/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.get_by_id(ObjectId(user_id))
    if user:
        user.delete()
        return jsonify({"message": "User deleted successfully"}), 200
    else:
        return jsonify({"error": "User not found"}), 404
