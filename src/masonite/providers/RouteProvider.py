from .Provider import Provider
from ..routes import RouteCapsule, Route


class RouteProvider(Provider):
    def __init__(self, application):
        self.application = application

    def register(self):
        # Register the routes?
        Route.set_controller_module_location(
            self.application.make("controller.location")
        )
        self.application.bind(
            "router",
            RouteCapsule(
                Route.get("/", "WelcomeController@show"),
                Route.get("/test", "WelcomeController@test"),
            ),
        )

    def boot(self):
        router = self.application.make("router")
        request = self.application.make("Request")
        response = self.application.make("Response")

        route = router.find(request.get_path(), request.get_request_method())

        if route:
            response.view(route.get_response(self.application))
