from src.masonite.configuration import config

from tests import TestCase


class TestPackageProvider(TestCase):
    def test_config_is_loaded(self):
        self.assertEqual(config("test_package.param_2"), 1)

    def test_config_is_merged(self):
        self.assertEqual(config("test_package.param_1"), 0)

    # def test_package_config_can_be_published(self):
    #     pp = self.application.providers[-1]
    #     import pdb

    #     pdb.set_trace()

    def test_views_are_registered(self):
        self.application.make("view").exists("test_package:package")
        self.application.make("view").exists("test_package:admin.settings")
        # this one has been published in project and overriden
        # check that the project view is used and not the package view
        self.assertEqual(
            self.application.make("view")
            .render("test_package:admin.settings")
            .rendered_template,
            "overriden",
        )

    def test_commands_are_registered(self):
        self.craft("test_package:command1").assertSuccess()
        self.craft("test_package:command2").assertSuccess()

    def test_routes_are_registered(self):
        # nb = len(self.application.make("router").routes)
        # import pdb

        # pdb.set_trace()
        for r in self.application.make("router").routes:
            print(r)
        self.get("/package/test/").assertContains("index")
        self.get("/api/package/test/").assertCreated()
