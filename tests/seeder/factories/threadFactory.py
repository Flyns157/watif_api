from faker import Faker
import requests
import PIL.Image
from io import BytesIO
import base64
import random
from tqdm import tqdm
from ..auth import Auth

class thread_factory :
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

    _api_url = "http://localhost:8080/api/posts"
    _headers = {'Content-Type': 'application/json',"Authorization": f"Bearer {Auth.token}"}

    _faker = Faker('fr_FR')

    """
        Generates a random thread with an associated initial post for testing purposes.

        Returns:
            dict: A dictionary representing the randomly generated thread and its initial post with the following structure:
                - thread (dict): Details about the thread, including:
                    - name (str): The name/title of the thread.
                    - range (str): The visibility of the thread, either "private" or "public".
                    - idOwner (str): The ID of the user who owns the thread.
                    - admins (list[str]): A list of user IDs assigned as admins of the thread.
                - post (dict): Details about the initial post in the thread, including:
                    - idAuthor (str): The ID of the user who authored the post.
                    - date (str): The creation date of the post, formatted as "YYYY-MM-DDTHH:MM:SS".
                    - title (str): The title of the post.
                    - content (str): The text content of the post.
                    - media (list[str]): A list of base64-encoded strings representing media associated with the post.
                    - keys (list[str]): A list of randomly generated keywords for the post.
    """
    def create_random_thread(self) :
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
        admins = random.sample(users,k=random.randint(0,4))
        if not idAuthor in admins : admins.append(idAuthor)

        return {
            "thread": {
                "name": self._faker.sentence(),
                "range" : random.choice(["private","public"]),
                "idOwner" : idAuthor,
                "admins" : admins
            },
            "post" : {
                "idAuthor" : idAuthor,
                "date" : self._faker.date_object().strftime("%Y-%m-%dT%H:%M:%S"),
                "title" : self._faker.sentence(),
                "content" : self._faker.paragraph(),
                "media" : [self._default_image1_base64,self._default_image2_base64],
                "keys" : [self._faker.word() for _ in range(random.randint(1,7))]
            }
        }

    """
    Instances a thread by sending it to the spring API.
    
    Parameters:
        thread (dict): A dictionary containing the thread data to be sent.
    """
    def instance_thread (self,thread) :
        response = requests.post(self._api_url, headers=self._headers, json=thread)

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
    Creates and instances multiple random threads.
    
    Parameters:
        nb_threads (int): The number of random threads to create and instance.
    """
    def create_randoms_threads(self,nb_threads) :
        for _ in tqdm(range(nb_threads)) :
            thread = self.create_random_thread()
            self.instance_thread(thread)

    """
        Prompts the user for the number of theads to generate and creates them.
    """
    def input_thread(self) :
        nb_threads = int(input("How many threads do you want to generate ?   "))
        self.create_randoms_threads(nb_threads)
