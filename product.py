class Product:
    def __init__(self, identifier, source_name, code, converted_name):
        self.identifier = int(identifier)
        self.code = code[3: ] if code.lower().startswith('sco') else code
        self.source_name = source_name

        self.converted_name = converted_name

    def __repr__(self):
        return 'Product: [code: {}, name: {}]'.format(self.code, self.source_name)

    def __str__(self):
        return self.__repr__()
