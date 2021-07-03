from .Input import Input
from urllib.parse import parse_qs
from collections import defaultdict
import urllib
import re
import json
import cgi
import re
from ..utils.structures import Dot
from ..filesystem import UploadedFile


class InputBag:
    def __init__(self):
        self.query_string = {}
        self.post_data = {}
        self.environ = {}

    def load(self, environ):
        self.environ = environ
        self.query_string = {}
        self.post_data = {}
        self.parse(environ)
        return self

    def parse(self, environ):
        if "QUERY_STRING" in environ:
            self.query_string = self.query_parse(environ["QUERY_STRING"])

        if "wsgi.input" in environ:
            if "application/json" in environ.get("CONTENT_TYPE", ""):
                try:
                    request_body_size = int(environ.get("CONTENT_LENGTH", 0))
                except (ValueError):
                    request_body_size = 0

                request_body = environ["wsgi.input"].read(request_body_size)

                if isinstance(request_body, bytes):
                    request_body = request_body.decode("utf-8")

                json_payload = json.loads(request_body or "{}")
                if isinstance(json_payload, list):
                    pass
                else:
                    for name, value in json.loads(request_body or "{}").items():
                        self.post_data.update({name: Input(name, value)})

            elif "application/x-www-form-urlencoded" in environ.get("CONTENT_TYPE", ""):
                try:
                    request_body_size = int(environ.get("CONTENT_LENGTH", 0))
                except (ValueError):
                    request_body_size = 0

                request_body = environ["wsgi.input"].read(request_body_size)
                parsed_request_body = parse_qs(
                    bytes(request_body).decode("utf-8")
                )
                
                self.post_data = self.parse_dict(parsed_request_body)

            elif "multipart/form-data" in environ.get("CONTENT_TYPE", ""):
                try:
                    request_body_size = int(environ.get("CONTENT_LENGTH", 0))
                except (ValueError):
                    request_body_size = 0

                fields = cgi.FieldStorage(
                    fp=environ["wsgi.input"],
                    environ=environ,
                    keep_blank_values=1,
                )

                for name in fields:
                    value = fields.getvalue(name)
                    if isinstance(value, bytes):
                        self.post_data.update(
                            {
                                name: UploadedFile(
                                    fields[name].filename, fields.getvalue(name)
                                )
                            }
                        )
                    else:
                        self.post_data.update(
                            {name: Input(name, fields.getvalue(name))}
                        )
                
                self.post_data = self.parse_dict(self.post_data)
            else:
                try:
                    request_body_size = int(environ.get("CONTENT_LENGTH", 0))
                except (ValueError):
                    request_body_size = 0

                request_body = environ["wsgi.input"].read(request_body_size)
                if request_body:
                    self.post_data.update(
                        json.loads(bytes(request_body).decode("utf-8"))
                    )

    def get(self, name, default=None, clean=True, quote=True):
        input = Dot().dot(name, self.all(), default=default)
        if isinstance(input, (str,)):
            return input
        elif isinstance(input, (dict,)):
            rendered = {}
            for key, inp in input.items():
                rendered.update({key: inp.value})
            return rendered
        elif hasattr(input, "value"):
            if isinstance(input.value, list) and len(input.value) == 1:
                return input.value[0]
            elif isinstance(input.value, dict):
                return input.value
            return input.value
        else:
            return input

        return default

    def has(self, *names):
        return all((name in self.all()) for name in names)

    def all(self):
        all = {}
        qs = self.query_string
        if isinstance(qs, list):
            qs = {str(i): v for i, v in enumerate(qs)}

        all.update(qs)
        all.update(self.post_data)
        return all

    def all_as_values(self, internal_variables=False):
        all = self.all()
        new = {}
        for name, input in all.items():
            if not internal_variables:
                if name.startswith("__"):
                    continue
            new.update({name: self.get(name)})

        return new

    def only(self, *args):
        all = self.all()
        new = {}
        for name, input in all.items():
            if name not in args:
                continue
            new.update({name: self.get(name)})

        return new

    def query_parse(self, query_string):
        d = {}
        for name, value in parse_qs(query_string).items():
            regex_match = re.match(r"(?P<name>[^\[]+)\[(?P<value>[^\]]+)\]", name)
            if regex_match:
                gd = regex_match.groupdict()
                d.setdefault(gd["name"], {})[gd["value"]] = Input(name, value[0])
            else:
                d.update({name: Input(name, value)})
        return d

    def parse_dict(self, dictionary):
        d = {}
        for name, value in dictionary.items():
            regex_match = re.match(r"(?P<name>[^\[]+)\[(?P<value>[^\]]+)\]", name)
            if regex_match:
                gd = regex_match.groupdict()
                if isinstance(value, Input):
                    d.setdefault(gd["name"], {})[gd["value"]] = value
                else:
                    d.setdefault(gd["name"], {})[gd["value"]] = Input(name, value[0])
            else:
                d.update({name: Input(name, value)})
        return d
