from ..container import Container


class Application(Container):
    def __init__(self, base_path=None):
        self.base_path = base_path
        self.storage_path = None
        self.response_handler = None
        self.providers = []
        self.routes = []

    def load_routes(self, routes):
        self.routes = routes

    def set_response_handler(self, response_handler):
        self.response_handler = response_handler

    def register_providers(self, *providers):
        for provider in providers:
            provider = provider(self)
            provider.register()
            print(provider)
        return self

    def add_providers(self, *providers):
        for provider in providers:
            provider = provider(self)
            provider.register()
            self.providers.append(provider)
            print(provider)

        return self

    def set_controller_module_location(self, location):
        self._controller_module_location = location

    def get_controller_module_location(self, location):
        return self._controller_module_location

    def get_providers(self):
        return self.providers

    def __call__(self, *args, **kwargs):
        return self.response_handler(self, *args, **kwargs)
