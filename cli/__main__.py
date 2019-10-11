import argparse
import sys

from cli import user
from common.auth import AuthManager
from common.consts import DEFAULT_AUTH_CONFIG


def main():
    parser = argparse.ArgumentParser(prog="AssetManager CLI")
    parser.add_argument("--config", default=DEFAULT_AUTH_CONFIG, type=str, help="Auth config file")

    subparsers = parser.add_subparsers()

    parser_user = subparsers.add_parser("user", help="User commands")
    subparsers_user = parser_user.add_subparsers()

    parser_user_add = subparsers_user.add_parser("add", help="User add command")
    parser_user_add.add_argument("user", type=str, help="Username to add")
    parser_user_add.add_argument("password", type=str, help="Password")
    parser_user_add.add_argument("--read", dest="read_groups", type=str, nargs="+", default=[], help="Read access groups")
    parser_user_add.add_argument("--write", dest="write_groups", type=str, nargs="+", default=[], help="Write access groups")
    parser_user_add.add_argument('--admin', dest='admin_access', action='store_const', const=True, default=False, help='Admin access')
    parser_user_add.set_defaults(function=user.add)

    parser_user_edit = subparsers_user.add_parser("edit", help="User edit command")
    parser_user_edit.add_argument("user", type=str, help="Username to edit")
    parser_user_edit.add_argument("--password", type=str, default=None, help="Password")

    parser_user_edit_read = parser_user_edit.add_mutually_exclusive_group()
    parser_user_edit_read.add_argument("--read", dest="read_groups", type=str, nargs="+", help="Read access groups")
    parser_user_edit_read.add_argument("--noread", dest="read_groups", action='store_const', const=[], help="Remove all read access groups")

    parser_user_edit_write = parser_user_edit.add_mutually_exclusive_group()
    parser_user_edit_write.add_argument("--write", dest="write_groups", type=str, nargs="+", help="Write access groups")
    parser_user_edit_write.add_argument("--nowrite", dest="write_groups", action='store_const', const=[], help="Remove all write access groups")

    parser_user_edit.add_argument('--admin', dest='admin_access', type=str, help='Admin access (y or n)')
    parser_user_edit.set_defaults(function=user.edit)

    parser_user_remove = subparsers_user.add_parser("remove", help="User remove command")
    parser_user_remove.add_argument("user", type=str, help="Username to add")
    parser_user_remove.set_defaults(function=user.remove)

    parser_user_info = subparsers_user.add_parser("info", help="User info command")
    parser_user_info.add_argument("user", type=str, help="Username to add")
    parser_user_info.set_defaults(function=user.info_user)

    parser_user_list = subparsers_user.add_parser("list", help="User list command")
    parser_user_list.set_defaults(function=user.list_users)

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
