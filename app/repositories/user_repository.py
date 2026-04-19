from app.models.base import db
from app.models.user import User


class UserRepository:
    def __init__(self):
        self.session = db.session

    def save(self, user: User):
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_by_id(self, user_id: int):
        return self.session.query(User).filter(User.id == user_id).first()

    def get_by_google_id(self, google_id: str):
        return self.session.query(User).filter(User.google_id == google_id).first()

    def get_by_email(self, email: str):
        return self.session.query(User).filter(User.email == email).first()

    def rollback(self):
        self.session.rollback()
