from argparse import Namespace

from common.auth import AuthManager
from common.entities import DbAccessMeta
from common.util import to_bool


def add(auth: AuthManager, args: Namespace):
    access = DbAccessMeta(user=args.user, groups=args.groups, write_access=args.write_access, admin_access=args.admin_access)
    auth.edit_user(access=access, password=args.password, hashed=False, add=True)
    print("User added successfully")
    _format_user(auth.get_user(user=args.user), multi=False)


def edit(auth: AuthManager, args: Namespace):
    user = auth.get_user(user=args.user)
    if user:
        for field in DbAccessMeta.EDITABLE_FIELDS:
            value = getattr(args, field, None)
            if value:
                if field == "write_access" or field == "admin_access":
                    setattr(user, field, to_bool(value))
                else:
                    setattr(user, field, value)
        auth.edit_user(access=user, password=args.password, hashed=False, add=False)
        _format_user(auth.get_user(user=args.user), multi=False)
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


def _format_user(user: DbAccessMeta, multi: bool):
    if multi:
        print("")
    print("\tUser =", user.user)
    print("\tGroups =", user.groups)
    print("\tWrite access =", user.write_access)
    print("\tAdmin access =", user.admin_access)
