import os
from collections import defaultdict
from os.path import relpath, join, abspath, basename, isdir, isfile

from ...providers.Provider import Provider
from ...exceptions import InvalidPackageName
from ...utils.location import (
    base_path,
    config_path,
    views_path,
    migrations_path,
    resources_path,
)
from ...facades import Config
from ...utils.time import migration_timestamp
from ...routes import Route
from ...utils.structures import load

from ..reserved_names import PACKAGE_RESERVED_NAMES
from ..Package import Package
from ..PublishableResource import PublishableResource


class PackageProvider(Provider):

    vendor_prefix = "vendor"

    def __init__(self, application):
        self.application = application
        self.package = Package()
        self.files = {}
        self.default_resources = ["config", "views", "migrations", "assets"]

    def register(self):
        self.configure()

    def boot(self):
        pass

    # api
    def configure(self):
        pass

    def publish(self, resources, dry=False):
        project_root = base_path()
        resources_list = resources or self.default_resources
        published_resources = defaultdict(lambda: [])
        for resource in resources_list:
            resource_files = self.files.get(resource, [])
            for source, dest in resource_files:
                if not dry:
                    # TODO: perform copying resources and do not override !
                    pass
                published_resources[resource].append(relpath(dest, project_root))
        return published_resources

    def root(self, abs_root_dir):
        # TODO ensure abs path here!
        self.package.root_dir = abs_root_dir
        return self

    def name(self, name):
        if name in PACKAGE_RESERVED_NAMES:
            raise InvalidPackageName(
                f"{name} is a reserved name. Please choose another name for your package."
            )
        self.package.name = name
        return self

    def vendor_name(self, name):
        self.package.vendor_name = name
        return self

    def add_config(self, config_filepath, publish=False):
        # TODO: a name must be specified !
        self.package.add_config(config_filepath)
        Config.merge_with(self.package.name, self.package.config)
        if publish:
            resource = PublishableResource("config")
            resource.add(self.package.config, config_path(f"{self.package.name}.py"))
            self.files.update({resource.key: resource.files})
        return self

    def add_views(self, *locations, publish=False):
        """Register views location in the project.
        locations must be a folder containinng the views you want to publish.
        """
        self.package.add_views(*locations)
        # register views into project
        # TODO: the issue here is that package can override project views are views cannot be
        # namespaced...
        # for location in locations:
        # self.application.make("view").add_from_package(
        #     "tests.integrations.test_package", location
        # )
        self.application.make("view").add_namespace(
            self.package.name, self.package.views[0]
        )

        if publish:
            resource = PublishableResource("views")
            for location in self.package.views:
                # views = get all files in this folder
                for dirpath, _, filenames in os.walk(location):
                    for f in filenames:
                        resource.add(
                            abspath(join(dirpath, f)),
                            views_path(
                                join(
                                    self.vendor_prefix,
                                    self.package.name,
                                    relpath(dirpath, location),
                                    f,
                                )
                            ),
                        )
            self.files.update({resource.key: resource.files})
        return self

    def add_commands(self, *commands):
        self.application.make("commands").add(*commands)
        return self

    def add_migrations(self, *migrations):
        self.package.add_migrations(*migrations)
        resource = PublishableResource("migrations")
        for migration in self.package.migrations:
            resource.add(
                migration,
                migrations_path(f"{migration_timestamp()}_{basename(migration)}"),
            )
        self.files.update({resource.key: resource.files})
        return self

    def add_routes(self, *routes):
        self.package.add_routes(*routes)
        # TODO: For route to work controller location needs to be registered...
        # but for now only one location can be registered in the framework
        # also how to handle naming conflict between two packages or with the project
        for route_group in self.package.routes:
            self.application.make("router").add(
                Route.group(
                    load(route_group, "ROUTES", []),
                )
            )
        return self

    def add_assets(self, *assets):
        self.package.add_assets(*assets)
        resource = PublishableResource("assets")
        for asset_dir_or_file in self.package.assets:
            # views = get all files in this folder
            if isdir(asset_dir_or_file):
                for dirpath, _, filenames in os.walk(asset_dir_or_file):
                    for f in filenames:
                        resource.add(
                            abspath(join(dirpath, f)),
                            resources_path(
                                join(
                                    self.vendor_prefix,
                                    self.package.name,
                                    relpath(dirpath, asset_dir_or_file),
                                    f,
                                )
                            ),
                        )
            elif isfile(asset_dir_or_file):
                resource.add(
                    abspath(asset_dir_or_file),
                    resources_path(
                        join(
                            self.vendor_prefix,
                            self.package.name,
                            asset_dir_or_file,
                        )
                    ),
                )
        self.files.update({resource.key: resource.files})
