from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_id, email):
        self.id = user_id
        self.email = email
