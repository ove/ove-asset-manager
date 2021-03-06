import argparse
import sys

from cli import user
from common.auth import AuthManager
from common.consts import DEFAULT_AUTH_CONFIG


def main():
    parser = argparse.ArgumentParser(prog="am-cli", description="A commandline interface for the OVE Asset Manager.")
    parser.add_argument("--config", default=DEFAULT_AUTH_CONFIG, type=str, help="Auth config file")

    subparsers = parser.add_subparsers()

    parser_user = subparsers.add_parser("user", help="User commands")
    subparsers_user = parser_user.add_subparsers()

    parser_user_add = subparsers_user.add_parser("verify", help="Verify user password")
    parser_user_add.add_argument("username", type=str, help="Username to verify")
    parser_user_add.set_defaults(function=user.verify)

    parser_user_add = subparsers_user.add_parser("add", help="Add user")
    parser_user_add.add_argument("username", type=str, help="Username to add")
    parser_user_add.add_argument("--read", dest="read_groups", type=str, nargs="+", default=[], help="Read access groups")
    parser_user_add.add_argument("--write", dest="write_groups", type=str, nargs="+", default=[], help="Write access groups")
    parser_user_add.add_argument('--admin', dest='admin_access', action='store_const', const=True, default=False, help='Admin access')
    parser_user_add.add_argument('--ignore', dest='ignore', action='store_const', const=True, default=False, help='Ignore validation')
    parser_user_add.set_defaults(function=user.add)

    parser_user_edit = subparsers_user.add_parser("edit", help="Edit user")
    parser_user_edit.add_argument("username", type=str, help="Username to edit")
    parser_user_edit.add_argument("--password", dest='reset_password', action='store_const', const=True, default=False, help="Password")

    parser_user_edit_read = parser_user_edit.add_mutually_exclusive_group()
    parser_user_edit_read.add_argument("--read", dest="read_groups", type=str, nargs="+", help="Read access groups")
    parser_user_edit_read.add_argument("--noread", dest="read_groups", action='store_const', const=[], help="Remove all read access groups")

    parser_user_edit_write = parser_user_edit.add_mutually_exclusive_group()
    parser_user_edit_write.add_argument("--write", dest="write_groups", type=str, nargs="+", help="Write access groups")
    parser_user_edit_write.add_argument("--nowrite", dest="write_groups", action='store_const', const=[], help="Remove all write access groups")

    parser_user_edit_admin = parser_user_edit.add_mutually_exclusive_group()
    parser_user_edit_admin.add_argument('--admin', dest='admin_access', action='store_const', const=True, help='Grant Admin access')
    parser_user_edit_admin.add_argument('--noadmin', dest='admin_access', action='store_const', const=False, help='Remove Admin access')

    parser_user_edit.add_argument('--ignore', dest='ignore', action='store_const', const=True, default=False, help='Ignore validation')
    parser_user_edit.set_defaults(function=user.edit)

    parser_user_remove = subparsers_user.add_parser("remove", help="Remove user")
    parser_user_remove.add_argument("username", type=str, help="Username to remove")
    parser_user_remove.set_defaults(function=user.remove)

    parser_user_info = subparsers_user.add_parser("info", help="List permissions for specific user, or all users")
    parser_user_info.add_argument("username", type=str, nargs='?', default='', help="Username to list info about")
    parser_user_info.set_defaults(function=user.info_user)

    args = parser.parse_args()

    if getattr(args, "function", None):
        try:
            auth = AuthManager(config_file=args.config)
            args.function(auth, args)
        except:
            print("[Error]", sys.exc_info()[1])
    else:
        parser.print_usage()


if __name__ == "__main__":
    main()
