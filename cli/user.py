import getpass
from argparse import Namespace

from common.auth import AuthManager
from common.entities import UserAccessMeta
from common.util import to_bool


def verify(auth: AuthManager, args: Namespace):
    pswd = getpass.getpass("[{}] password:".format(args.user))
    user = auth.auth_user(user=args.user, password=pswd)
    if user:
        _format_user(user, multi=False)
    else:
        print("[Error] Invalid username or password")


def add(auth: AuthManager, args: Namespace):
    password = get_password_input(args.user)

    if password:
        setattr(args, "password", password)
        _edit(user=UserAccessMeta(user=args.user), auth=auth, args=args, add_user=True)


def edit(auth: AuthManager, args: Namespace):
    if args.reset_password:
        password = get_password_input(args.user)
        if not password:
            return

        setattr(args, "password", password)
    else:
        setattr(args, "password", None)

    _edit(user=auth.get_user(user=args.user), auth=auth, args=args, add_user=False)


def get_password_input(user):
    valid_password = False
    while not valid_password:
        print()
        pass1 = getpass.getpass("New password for [{}]:".format(user))
        pass2 = getpass.getpass("Type the password again:".format(user))

        if pass1 != pass2:
            valid_password = False
            continue

        if pass1 and len(pass1) >= 8:
            return pass1
        else:
            print("[Error] Passwords should be longer than 8 characters")
            return


def _edit(user: UserAccessMeta, auth: AuthManager, args: Namespace, add_user: bool):
    if user:
        value = getattr(args, "admin_access", None)
        if value is not None:
            setattr(user, "admin_access", to_bool(value))

        value = getattr(args, "write_groups", None)
        if value is not None:
            setattr(user, "write_groups", value)

        # make sure that the read groups contain the write groups as well
        value = getattr(args, "read_groups", None)
        if value is not None:
            value = list(set(value + user.write_groups))
            setattr(user, "read_groups", value)
        else:
            value = list(set(user.read_groups + user.write_groups))
            setattr(user, "read_groups", value)

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
