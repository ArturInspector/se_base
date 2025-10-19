from .entities import *
from errors import *
from db import Session


def get_user_by_id(user_id):
    """
    Метод получение пользователя по ID
    :param user_id: user_id
    :return: user or None
    """
    with Session() as session:
        user = session.query(User).get(user_id)
    return user


def get_user_by_login(login):
    """
    Метод получение пользователя по логину
    :param login: логин
    :return: user or None
    """
    with Session() as session:
        user = session.query(User).filter(User.login == login).first()
    return user


def get_users():
    """
    Метод получения списка всех пользователей
    :return: список всех пользователей
    """
    with Session() as session:
        users_list = session.query(User).all()
    return users_list


def create_user(login, password):
    """
    Метод добавления нового пользователя
    :param login: логин
    :param password: пароль
    :return:
    """
    if len(login) == 0:
        raise IncorrectDataValue('Логин не может быть пустым')
    if len(password) == 0:
        raise IncorrectDataValue('Пароль не может быть пустым')

    if get_user_by_login(login):
        raise IncorrectDataValue('Такой логин уже занят')

    with Session() as session:
        user = User(login=login, password=password)
        session.add(user)
        session.commit()


def auth(login, password, session):
    """
    Метод авторизации
    :param login: логин
    :param password: пароль
    :param session: http сессия
    :return: True or False
    """
    user = get_user_by_login(login)
    if user is None:
        return False
    if user.password != password:
        return False

    session['user_id'] = user.id
    return True