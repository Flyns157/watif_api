from .auth import Auth

"""
    Call up factories to create entities.
    
    If you don't want to generate some entities, juste type 0 when it ask the number of generation.
"""
if __name__ == '__main__':
    Auth.login("admin", "adminPassword")
    print(f"Token : {Auth.token}")

    from factories.userFactory import user_factory
    u_factory = user_factory()
    u_factory.input_user()

    from factories.threadFactory import thread_factory
    t_factory = thread_factory()
    t_factory.input_thread()

    from factories.postFactory import post_factory
    p_factory = post_factory()
    p_factory.input_post()
