from faker import Faker
import requests
import PIL.Image
from io import BytesIO
import base64
import random
from tqdm import tqdm

from ..auth import Auth

class user_factory :

    _image_url = "https://static.vecteezy.com/system/resources/previews/009/292/244/original/default-avatar-icon-of-social-media-user-vector.jpg"
    _init_image = requests.get(_image_url).content
    _default_avatar = PIL.Image.open(BytesIO(_init_image)).convert('RGB')

    buffered = BytesIO()
    _default_avatar.save(buffered, format="PNG")
    _default_avatar_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    _api_url = "http://localhost:8080/api/users"
    _headers = {'Content-Type': 'application/json',"Authorization": f"Bearer {Auth.token}"}

    _faker = Faker('fr_FR')

    """
    Generates a random user for testing purposes.
    
    This function creates a dictionary representing a user with randomly generated attributes, including personal details, profile picture, and interests.
    
    Returns:
        dict: A dictionary representing the randomly generated user with the following keys:
            - username (str): The username of the user.
            - password (str): The password for the user's account.
            - mail (str): The user's email address.
            - name (str): The user's first name.
            - surname (str): The user's last name.
            - pp (str): A base64-encoded string representing the user's profile picture.
            - birthDate (str): The user's date of birth, formatted as "YYYY-MM-DDTHH:MM:SS".
            - interest (list[str]): A list of randomly generated interests.
            - description (str): A paragraph describing the user.
            - status (str): A status message or tagline for the user.
    """
    def create_random_user(self) :
        return {
            "username": self._faker.user_name(),
            "password" : self._faker.password(),
            "mail": self._faker.email(),
            "name": self._faker.first_name(),
            "surname": self._faker.last_name(),
            "pp": self._default_avatar_base64,
            "birthDate" : self._faker.date_of_birth().strftime("%Y-%m-%dT%H:%M:%S"),
            "interest" : [self._faker.word() for _ in range (random.randint(1,6))],
            "description" : self._faker.paragraph(),
            "status" : self._faker.sentence()
        }

    """
    Instances a user by sending it to the spring API.
    
    Parameters:
        user (dict): A dictionary containing the user data to be sent.
    """
    def instance_user (self, user, random_follows: bool = False) -> None:
        response = requests.post(self._api_url, headers=self._headers, json=user)
        user_id = response.json()['idUser']

        if response.status_code == 201 and random_follows and self.created_users:
            try:
                response = requests.get("http://localhost:8080/api/users", headers=self._headers)
                response.raise_for_status()
                users = [u["idUser"] for u in response.json()]
            except Exception as e:
                print("Erreur:", e)

            response = requests.post(f"{self._api_url}/{user_id}/follow?followId={random.choice(users)}", headers=self._headers)

        user['idUser'] = user_id
        self.created_users.append(user)

        try:
            error_message = response.json()
            if 'error' in error_message:
                print(f"Error: {error_message['error']}")
        except ValueError:
            if response.status_code != 200:
                print(f"Unknow error, HTTP code : {response.status_code}")
            else:
                print("GOOD")

    """
    Creates and instances multiple random users.
    
    Parameters:
        nb_users (int): The number of random users to create and instance.
    """
    def create_randoms_users(self,nb_users, random_follows) :
        for _ in tqdm(range(nb_users)) :
            user = self.create_random_user()
            self.instance_user(user, random_follows)

    """
        Prompts the user for the number of users to generate and creates them.
    """
    def input_user(self) :

        nb_users = int(input("How many users do you want to generate ?   "))
        random_follows = input("Do you want to randomly follow users ? (y/n)   ") == 'y'

        self.created_users = []
        self.created_users_infos = []
        self.create_randoms_users(nb_users, random_follows)

        for user in self.created_users:
            print(f"User {user['username']} created with id {user['idUser']} and password {user['password']}")
