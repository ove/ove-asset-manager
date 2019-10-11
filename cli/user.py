from argparse import Namespace

from common.auth import AuthManager
from common.entities import UserAccessMeta
from common.util import to_bool


def add(auth: AuthManager, args: Namespace):
    _edit(user=UserAccessMeta(user=args.user), auth=auth, args=args, add_user=True)


def edit(auth: AuthManager, args: Namespace):
    _edit(user=auth.get_user(user=args.user), auth=auth, args=args, add_user=False)


def _edit(user: UserAccessMeta, auth: AuthManager, args: Namespace, add_user: bool):
    if user:
        for field in UserAccessMeta.EDITABLE_FIELDS:
            value = getattr(args, field, None)
            if value is not None:
                if field == "admin_access":
                    setattr(user, field, to_bool(value))
                else:
                    setattr(user, field, value)
        if auth.edit_user(access=user, password=args.password, hashed=False, add=add_user):
            _format_user(auth.get_user(user=args.user), multi=False)
        elif add_user:
            print("[Error] Could not add user")
        else:
            print("[Error] No changes were applied")
    else:
        print("[Error] User not found")


def remove(auth: AuthManager, args: Namespace):
    if auth.remove_user(user=args.user):
        print("User removed successfully")
    else:
        print("[Error] User not found")


def info_user(auth: AuthManager, args: Namespace):
    _format_user(auth.get_user(user=args.user), multi=False)


def list_users(auth: AuthManager, _args: Namespace):
    first = True
    for user in auth.get_users():
        _format_user(user, multi=not first)
        first = False


def _format_user(user: UserAccessMeta, multi: bool):
    if multi:
        print("")
    print("\tUser =", user.user)
    print("\tRead =", user.read_groups)
    print("\tWrite =", user.write_groups)
    print("\tAdmin =", user.admin_access)
