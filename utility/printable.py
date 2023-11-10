class Printable():

    # like a to_String method that returns a string
    def __repr__(self):
        return str(self.__dict__)