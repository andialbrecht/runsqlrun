class BaseSchemaProvider:

    def __init__(self, driver):
        self.driver = driver

    def refresh_tables(self, schema, cb):
        raise NotImplementedError
