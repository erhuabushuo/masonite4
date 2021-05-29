from .Provider import Provider
from ..routes import Router, Route
from ..pipeline import Pipeline

# from ..middleware.route import VerifyCsrfToken
import pydoc


class RouteProvider(Provider):
    def __init__(self, application):
        self.application = application

    def register(self):
        # Register the routes?
        Route.set_controller_module_location(
            self.application.make("controller.location")
        )

    def boot(self):
        router = self.application.make("router")
        request = self.application.make("request")
        response = self.application.make("response")

        route = router.find(request.get_path(), request.get_request_method(), request.get_subdomain())

        # Run before middleware

        Pipeline(request, response).through(
            self.application.make("middleware").get_http_middleware(),
            handler="before",
        )
        if route:
            Pipeline(request, response).through(
                self.application.make("middleware").get_route_middleware(
                    route.list_middleware
                ),
                handler="before",
            )

            response.view(route.get_response(self.application))

            Pipeline(request, response).through(
                self.application.make("middleware").get_route_middleware(
                    route.list_middleware
                ),
                handler="after",
            )

        else:
            response.view("route not found", status=404)

        Pipeline(request, response).through(
            self.application.make("middleware").get_http_middleware(),
            handler="after",
        )
