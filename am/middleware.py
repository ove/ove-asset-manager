import logging

import falcon

from am import FileController


class RequireAuthGroups:
    def __init__(self, controller: FileController):
        self.controller = controller

    # the resource can configure that they perform the group validation internally
    def process_resource(self, req: falcon.Request, _resp: falcon.Response, resource, params):
        if getattr(resource, "internal_group_validation", False):
            return

        groups = getattr(req, "auth_groups", [])
        is_admin = getattr(req, "auth_admin_access", False)
        store_id = params.get("store_id", None)
        project_id = params.get("project_id", None)

        if store_id and project_id:
            if not self.controller.has_access(store_id=store_id, project_id=project_id, groups=groups, is_admin=is_admin):
                raise falcon.HTTPUnauthorized(title='Resource not accessible with this token',
                                              description='Please provide a valid access token with the right access groups.')
        else:
            logging.error("Something is wrong with this resource %s. It should either declare itself as 'internal_group_validation' "
                          "or have a valid store_id and project_id.", req.path)
            raise falcon.HTTPInternalServerError(title="Auth service configuration error", description="One of the resource is misconfigured")
