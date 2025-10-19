class IncorrectDataValue(Exception):
    def __init__(self, message):
        self.message = message


class GroupNotAllowed(Exception):
    def __init__(self):
        pass