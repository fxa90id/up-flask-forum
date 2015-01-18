import hashlib
from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey

from database import Base

class Thread(Base):
    __tablename__ = 'threads'
    id = Column(Integer, primary_key=True)
    topic = Column(String(60), unique=True)
    post_id= Column(Integer, ForeignKey('posts.id'))
    add_time = Column(String(19))

    def __init__(self, topic=None, post_id=None, add_time=None):
        self.topic = topic
        self.post_id = post_id
        self.add_time = add_time or datetime.now().strftime('%Y.%m.%d, %H:%M:%S')


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('posts.id'), nullable=True)
    author_id = Column(Integer, ForeignKey('users.id'))
    content = Column(String(500))
    add_time = Column(String(19))

    def __init__(self, parent_id=None, author_id=None, content=None, add_time=None):
        self.parent_id = parent_id
        self.author_id = author_id
        self.content = content
        self.add_time = add_time or datetime.now().strftime('%Y.%m.%d, %H:%M:%S')

    def __repr__(self):
        return "<Post(id='%d', parent_id='%d', author_id='%d', content='%s', add_time='%s')>" % (
            self.id, self.parent_id, self.author_id, self.content, self.add_time)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String(50), unique=True)
    password = Column(String(120))
    is_active = lambda *args: True
    is_authenticated = lambda *args: True
    is_anonymous = lambda *args: False

    def __init__(self, login=None, password=None):
        self.login = login
        self.password = self.make_password(password)

    def __repr__(self):
        return "<User(login='%s', password='%s')>" % (self.login, self.password)

    def get_id(self):
        return self.id

    def make_password(self, password):
        return hashlib.sha1(password).hexdigest()

    def check_password(self, password):
        return self.password == self.make_password(password)
