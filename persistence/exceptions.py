

class RepositoryException(Exception):
    """
    Общий класс для ошибок репозитория.
    """
    pass


class DatabaseConnectionException(RepositoryException):
    """
    Ошибка подключения к базе данных.
    """
    def __init__(self):
        super().__init__("Не удалось подключиться к базе данных.")
