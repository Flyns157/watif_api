from faker import Faker
import requests
import PIL.Image
from io import BytesIO
import base64
import random
from tqdm import tqdm
from ..auth import Auth

class post_factory :
    @staticmethod
    def _get_img(url, path):
        try:
            response = requests.get(url)
            response.raise_for_status()
            img = PIL.Image.open(BytesIO(response.content)).convert('RGB')
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            img = PIL.Image.open(path).convert('RGB')
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    _image1_url = "https://th.bing.com/th/id/OIP.yLf7kQVaLpxqCZX1VRHw-wHaEK?rs=1&pid=ImgDetMain"
    _image1_path = r'..\images_tests\OIP1.jpg'
    _default_image1_base64 = _get_img(_image1_url, _image1_path)

    _image2_url = "https://th.bing.com/th/id/OIP.0_yGb353J_SPSma7_uTmzQHaEK?rs=1&pid=ImgDetMain"
    _image2_path = r'..\images_tests\OIP2.jpg'
    _default_image2_base64 = _get_img(_image2_url, _image2_path)

    _image3_url = "https://jadelcambre.fr/storage/images/profile.JPG"
    _image3_path = r'..\images_tests\profile.jpg'
    _default_image3_base64 = _get_img(_image3_url, _image3_path)

    _image4_url = "https://cdn-s-www.ledauphine.com/images/26B02385-FCED-407C-BE94-2D300FAAB9A8/NW_raw/nejat-arinik-partage-la-recette-du-borek-de-sa-grand-mere-1535387313.jpg"
    _image4_path = r'..\images_tests\nejat-arinik-partage-la-recette-du-borek-de-sa-grand-mere-1535387313.jpg'
    _default_image4_base64 = _get_img(_image4_url, _image4_path)

    _images = [_default_image1_base64,_default_image2_base64,_default_image3_base64,_default_image4_base64]

    _api_url = "http://localhost:8080/api/posts/add-comment/"
    _headers = {'Content-Type': 'application/json',"Authorization": f"Bearer {Auth.token}"}

    _faker = Faker('fr_FR')

    """
        Generates a random post for testing purposes.

        Returns:
            dict: A dictionary representing the randomly generated post with the following keys:
                - idAuthor (str): The ID of the user selected as the author of the post.
                - date (str): The creation date of the post, formatted as "YYYY-MM-DDTHH:MM:SS".
                - content (str): The text content of the post.
                - media (list[str]): A list of base64-encoded strings representing media associated with the post.
                - keys (list[str]): A list of randomly generated keywords for the post.
    """
    def create_random_post(self) :
        users = []
        try:
            response = requests.get("http://localhost:8080/api/users", headers=self._headers)
            response.raise_for_status()
            users = [u["idUser"] for u in response.json()]
        except Exception as e:
            print("Erreur:", e)

        if(len(users) == 0) :
            raise Exception("Aucun utilisateur dans la base de données")

        idAuthor = random.choice(users)

        return {
            "idAuthor": idAuthor,
            "date" : self._faker.date_object().strftime("%Y-%m-%dT%H:%M:%S"),
            "content" : self._faker.paragraph(),
            "media" : [self._images[i] for i in range(random.randint(1,4))],
            "keys" : [self._faker.word() for _ in range(random.randint(1,7))]
        }

    """
    Instances a post by sending it to the spring API.
    
    Parameters:
        post (dict): A dictionary containing the post data to be sent.
    """
    def instance_post (self,post) :
        posts = []
        try:
            response = requests.get("http://localhost:8080/api/posts", headers=self._headers)
            response.raise_for_status()
            posts = [p["idPost"] for p in response.json()]
        except Exception as e:
            print("Erreur:", e)

        if(len(posts) == 0) :
            raise Exception("Aucun post dans la base de données")

        idPost = random.choice(posts)

        response = requests.post(self._api_url+idPost, headers=self._headers, json=post)

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
    Creates and instances multiple random posts.
    
    Parameters:
        nb_posts (int): The number of random posts to create and instance.
    """
    def create_randoms_posts(self,nb_posts) :
        for _ in tqdm(range (nb_posts)) :
            post = self.create_random_post()
            self.instance_post(post)

    """
    Prompts the user for the number of posts to generate and creates them.
    """
    def input_post(self) :
        nb_posts = int(input("How many posts (comments) do you want to generate ?   "))
        self.create_randoms_posts(nb_posts)
