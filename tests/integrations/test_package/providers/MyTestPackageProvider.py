from src.masonite.packages.providers import PackageProvider
from tests.integrations.test_package.commands.Command1 import Command1
from tests.integrations.test_package.commands.Command2 import Command2


"""
.../mypackage/templates/
 - admin.html
 - test.html

../myproject/templates/
"""


class MyTestPackageProvider(PackageProvider):
    def configure(self):
        (
            self.root("tests/integrations/test_package")
            .name("test_package")
            .config("config/test.py", publish=True)
            .views("templates", publish=True)
            .commands(Command1(), Command2())
            .migrations("migrations/create_some_table.py")
            .assets("assets")
            # .routes("routes/api.py", "routes/web.py")
        )
