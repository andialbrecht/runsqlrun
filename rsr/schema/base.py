class BaseSchemaProvider:

    def __init__(self, driver):
        self.driver = driver

    def refresh(self, schema):
        raise NotImplementedError

