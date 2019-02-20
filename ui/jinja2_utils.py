from typing import Callable, List

import falcon
from falcon.response import Response
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound


# Original code imported from https://github.com/mikeylight/falcon-jinja
# Custom modifications made to suit our needs


class FalconTemplateNotFound(Exception):
    pass


class FalconTemplate:
    def __init__(self, path: str = None, error_handler: Callable = None):
        self.template_path = path or 'templates'
        self.loader = FileSystemLoader(self.template_path)
        self._env = Environment(loader=self.loader)
        self._error_handler = error_handler

    @staticmethod
    def __get_response(objects: tuple):
        for response in objects:
            if isinstance(response, Response):
                return response
        return False

    def _make_template(self, template: str, context: dict, alerts: List):
        try:
            template = self._env.get_template(template)
        except TemplateNotFound:
            raise FalconTemplateNotFound('Template {} not found in {} folder'.format(template, self.template_path))
        return template.render(**context, alerts=alerts)

    def render(self, template: str):
        def render_template(func):
            def wrapper(*args, **kwargs):
                response = self.__get_response(args)
                response.alerts = []

                try:
                    func(*args, **kwargs)
                except Exception as ex:
                    if self._error_handler:
                        self._error_handler(ex, response)

                response.content_type = falcon.MEDIA_HTML
                response.status = falcon.HTTP_200
                response.body = self._make_template(template, response.context, response.alerts)

            return wrapper

        return render_template
