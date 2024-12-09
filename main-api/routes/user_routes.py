from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic import ValidationError
from dtos.user_dto import PrivateUserDTO
from models.user import User
from bson import ObjectId
from ..app import logger
import os

user_bp = Blueprint("user_bp", __name__, url_prefix="/api")

@user_bp.route("/user/<user_id>", methods=["GET"])
@jwt_required(optional=True)
def get_user(user_id):
    current_user_id = get_jwt_identity()
    logger.info(f"GET /user/{user_id} - Current user ID: {current_user_id}")
    user = User.get_by_id(user_id)
    if user:
        if str(user._id) == current_user_id or user.get_role().name != 'admin':
            user_dto = user.to_dto(private=True)
        else:
            user_dto = user.to_dto()
        logger.info(f"User {user_id} retrieved successfully")
        return jsonify(user_dto.model_dump()), 200
    else:
        logger.error(f"User {user_id} not found")
        return jsonify({"error": "User not found"}), 404

@user_bp.route("/register", methods=["POST"])
def create_user():
    # Gestion des erreurs pour le format de la donnée reçue
    try:
        data = request.get_json()
        if not data:
            raise ValueError("No data provided")

        # Validation via Pydantic
        user_data = PrivateUserDTO(**data)
        user = User(password=data["password"], **user_data.model_dump())

        # Gestion de l'upload de fichiers
        if len(request.files):
            pp_file = request.files[next(request.files.keys())]
            try:
                user.set_pp(user_bp.config['UPLOAD_FOLDER'], pp_file)
            except ValueError as e:
                logger.error("Invalid file format to new user's pp.")
                return jsonify({"error": "Invalid file format"}), 400

        user.save()
        logger.info(f"User created successfully - ID: {user._id}")
        return jsonify(user.to_dto(private=True).model_dump()), 201
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": "Invalid data", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@user_bp.route('/user/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    logger.info(f"PUT /user/{user_id} - Current user ID: {current_user_id}")
    current_user = User.get_by_id(ObjectId(user_id))
    
    # Gestion des erreurs pour le format de la donnée reçue
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            logger.error(f"Invalid input format - Expected a JSON object")
            return jsonify({"error": "Invalid input format; expected a JSON object"}), 400

        # Validation via Pydantic
        user_data = PrivateUserDTO(**data)
        user = User.get_by_id(user_id)

        # Mettre à jour les informations de l'utilisateur
        if user:
            if current_user.get_role().name != 'admin':
                if "role" in data:
                    logger.error(f"Unauthorized attempt to modify role - User ID: {user_id}")
                    return jsonify({"error": "You are not authorized to modify the role"}), 403
                
                # Si l'utilisateur essaie de modifier un autre compte que le sien
                if current_user_id != user_id:
                    logger.error(f"Unauthorized access - User ID: {user_id}")
                    return jsonify({"error": "Unauthorized access"}), 403

            user.update(**user_data.model_dump()
                        if "password" not in data else
                        {**user_data.model_dump(), "password": data["password"]})

            # Gestion de l'upload de fichiers
            if len(request.files):
                pp_file = request.files[next(request.files.keys())]
                try:
                    user.set_pp(user_bp.config['UPLOAD_FOLDER'], pp_file)
                except ValueError as e:
                    logger.error("Invalid file format to new user's pp.")
                    return jsonify({"error": "Invalid file format"}), 400

            logger.info(f"User {user_id} updated successfully")
            return jsonify({"message": "User updated successfully"}), 200
        else:
            logger.error(f"User {user_id} not found")
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@user_bp.route("/user/<user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    logger.info(f"DELETE /user/{user_id} - Current user ID: {current_user_id}")
    user = User.get_by_id(ObjectId(user_id))

    # Autoriser uniquement l'utilisateur ou un administrateur
    if current_user_id != user_id and user.get_role().name != 'admin':
        logger.error(f"Unauthorized access - User ID: {user_id}")
        return jsonify({"error": "Unauthorized access"}), 403

    if user:
        user.delete()
        logger.info(f"User {user_id} deleted successfully")
        return jsonify({"message": "User deleted successfully"}), 200
    else:
        logger.error(f"User {user_id} not found")
        return jsonify({"error": "User not found"}), 404

@user_bp.route("/user/<user_id>/followed", methods=["GET"])
def get_followed_users(user_id):
    logger.info(f"GET /user/{user_id}/followed")
    user = User.get_by_id(user_id)
    if not user:
        logger.error(f"User {user_id} not found")
        return jsonify({"error": "User not found"}), 404

    # Récupération des utilisateurs suivis
    followed_users = user.get_followed()

    # Conversion en DTO pour chaque utilisateur suivi (en public DTO par défaut)
    followed_dtos = [followed_user.to_dto().model_dump() for followed_user in followed_users]

    logger.info(f"Followed users retrieved successfully for user {user_id}")
    return jsonify(followed_dtos), 200

@user_bp.route("/user/<user_id>/follow", methods=["POST"])
@jwt_required()
def follow_user(user_id):
    current_user_id = get_jwt_identity()
    logger.info(f"POST /user/{user_id}/follow - Current user ID: {current_user_id}")
    current_user = User.get_by_id(current_user_id)
    target_user = User.get_by_id(user_id)

    # Vérification de l'existence des utilisateurs
    if not current_user:
        logger.error(f"Current user not found - ID: {current_user_id}")
        return jsonify({"error": "Current user not found"}), 404
    if not target_user:
        logger.error(f"Target user not found - ID: {user_id}")
        return jsonify({"error": "Target user not found"}), 404

    # Ajouter l'utilisateur cible dans la liste des suivis s'il n'est pas déjà suivi
    if user_id not in [str(f) for f in current_user.followed]:
        current_user.followed.append(target_user._id)
        current_user.save()
        logger.info(f"User {current_user_id} is now following user {user_id}")
        return jsonify({"message": f"You are now following {target_user.username}"}), 200
    else:
        logger.info(f"User {current_user_id} is already following user {user_id}")
        return jsonify({"message": "You are already following this user"}), 400

@user_bp.route("/user/<user_id>/unfollow", methods=["POST"])
@jwt_required()
def unfollow_user(user_id):
    current_user_id = get_jwt_identity()
    logger.info(f"POST /user/{user_id}/unfollow - Current user ID: {current_user_id}")
    current_user = User.get_by_id(current_user_id)
    target_user = User.get_by_id(user_id)

    # Vérification de l'existence des utilisateurs
    if not current_user:
        logger.error(f"Current user not found - ID: {current_user_id}")
        return jsonify({"error": "Current user not found"}), 404
    if not target_user:
        logger.error(f"Target user not found - ID: {user_id}")
        return jsonify({"error": "Target user not found"}), 404

    # Supprimer l'utilisateur cible de la liste des suivis s'il est suivi
    if user_id in [str(f) for f in current_user.followed]:
        current_user.followed = [f for f in current_user.followed if str(f) != user_id]
        current_user.save()
        logger.info(f"User {current_user_id} has unfollowed user {user_id}")
        return jsonify({"message": f"You have unfollowed {target_user.username}"}), 200
    else:
        logger.info(f"User {current_user_id} is not following user {user_id}")
        return jsonify({"message": "You are not following this user"}), 400

@user_bp.route("/user/<user_id>/block", methods=["POST"])
@jwt_required()
def block_user(user_id):
    current_user_id = get_jwt_identity()
    logger.info(f"POST /user/{user_id}/block - Current user ID: {current_user_id}")
    current_user = User.get_by_id(current_user_id)
    target_user = User.get_by_id(user_id)

    # Vérification de l'existence des utilisateurs
    if not current_user:
        logger.error(f"Current user not found - ID: {current_user_id}")
        return jsonify({"error": "Current user not found"}), 404
    if not target_user:
        logger.error(f"Target user not found - ID: {user_id}")
        return jsonify({"error": "Target user not found"}), 404

    # Ajouter l'utilisateur cible dans la liste des bloqués s'il n'est pas déjà bloqué
    if user_id not in [str(b) for b in current_user.blocked]:
        current_user.blocked.append(target_user._id)
        current_user.save()
        logger.info(f"User {current_user_id} has blocked user {user_id}")
        return jsonify({"message": f"You have blocked {target_user.username}"}), 200
    else:
        logger.info(f"User {current_user_id} is already blocking user {user_id}")
        return jsonify({"message": "This user is already blocked"}), 400

@user_bp.route("/user/<user_id>/unblock", methods=["POST"])
@jwt_required()
def unblock_user(user_id):
    current_user_id = get_jwt_identity()
    logger.info(f"POST /user/{user_id}/unblock - Current user ID: {current_user_id}")
    current_user = User.get_by_id(current_user_id)
    target_user = User.get_by_id(user_id)

    # Vérification de l'existence des utilisateurs
    if not current_user:
        logger.error(f"Current user not found - ID: {current_user_id}")
        return jsonify({"error": "Current user not found"}), 404
    if not target_user:
        logger.error(f"Target user not found - ID: {user_id}")
        return jsonify({"error": "Target user not found"}), 404

    # Supprimer l'utilisateur cible de la liste des bloqués s'il est bloqué
    if user_id in [str(b) for b in current_user.blocked]:
        current_user.blocked = [b for b in current_user.blocked if str(b) != user_id]
        current_user.save()
        logger.info(f"User {current_user_id} has unblocked user {user_id}")
        return jsonify({"message": f"You have unblocked {target_user.username}"}), 200
    else:
        logger.info(f"User {current_user_id} is not blocking user {user_id}")
        return jsonify({"message": "This user is not in your blocked list"}), 400

@user_bp.route("/users", methods=["POST"])
@jwt_required()
def get_users():
    logger.info("POST /users - Retrieving users")
    # Obtenir les filtres et la limite depuis le corps de la requête
    data = request.json or {}
    filters = {k: v for k, v in data.items() if k != "limit"}
    limit = int(data.get("limit", 30))  # Par défaut, on limite à 30 utilisateurs

    # Obtenir les utilisateurs en appliquant les filtres avec la limite
    users = User.all(limit=limit, **filters)

    # Identifier l'utilisateur actuel pour adapter la visibilité des informations
    current_user_id = get_jwt_identity()
    current_user = User.get_by_id(current_user_id)

    # Renvoyer une liste avec les DTOs publics ou privés en fonction de l'utilisateur courant
    logger.info(f"Users retrieved successfully - Count: {len(users)}")
    return jsonify([
        user.to_dto(
            private = (
                current_user.get_role().name == 'admin' or str(user._id) == current_user_id
            )
        ).model_dump()
        for user in users
    ]), 200

@user_bp.route('/user/<user_id>/pp', methods=['GET'])
def get_pp(user_id):
    user = User.get_by_id(ObjectId(user_id))
    if user and user.pp:
        return send_from_directory(user_bp.config['UPLOAD_FOLDER'], os.path.basename(user.pp))
    else:
        return jsonify({"error": "Profile picture not found"}), 404
