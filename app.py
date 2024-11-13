from os import PathLike
from typing import Any
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token
from datetime import timedelta
from models.user import User
from config import Config

class WatifAPI(Flask):
    def __init__(self, import_name: str, static_url_path: str | None = None, static_folder: str | PathLike[str] | None = "static", static_host: str | None = None, host_matching: bool = False, subdomain_matching: bool = False, template_folder: str | PathLike[str] | None = "templates", instance_path: str | None = None, instance_relative_config: bool = False, root_path: str | None = None):
        super().__init__(import_name, static_url_path, static_folder, static_host, host_matching, subdomain_matching, template_folder, instance_path, instance_relative_config, root_path)
        self.config["JWT_SECRET_KEY"] = Config.SECRET_KEY
        self.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=Config.TOKEN_EXPIRES)  # Durée de validité du token
        self.jwt = JWTManager()

        @self.route('/login', methods=['POST'])
        def login():
            data = request.get_json()
            email = data.get("mail")
            password = data.get("password")

            user = User.get_by_email(email)
            if user and user.check_password(password):
                access_token = create_access_token(identity=str(user._id))
                return jsonify(access_token=access_token), 200

            return jsonify({"error": "Invalid email or password"}), 401

        from routes.user_routes import user_bp
        self.register_blueprint(user_bp)

    def run(self, host: str | None = None, port: int | None = None, debug: bool | None = None, load_dotenv: bool = True, **options: Any) -> None:
        self.jwt.init_app(self)
        return super().run(host, port, debug, load_dotenv, **options)


if __name__ == "__main__":
    WatifAPI().run(debug=True)