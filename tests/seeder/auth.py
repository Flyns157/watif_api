import requests

class Auth:
    token = None

    @classmethod
    def login(cls, username, password):
        url = "http://localhost:8080/api/auth/login"
        data = {
            "username": username,
            "password": password
        }
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            cls.token = response.text
            print("Connexion réussie. Token stocké.")
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la connexion : {e}")

    @classmethod
    def get_token(cls):
        if cls.token is None:
            raise ValueError("Le token n'est pas encore initialisé. Veuillez vous connecter d'abord.")
        return cls.token
