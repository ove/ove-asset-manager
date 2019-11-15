# Administering users

The OVE Asset Manager allows limited guest access, but creating and editing projects, or viewing projects that are not public require users to log in.

Projects can be added to *access groups* by clicking on the shield icon on the table of projects, or by clicking the "Edit access controls" button on the table of assets.
Each user account has a list of groups for which it has read access, and a list of groups for which it has write access.

Account details are stored in a MongoDB database (as configured in `config/auth.json`).

Users can be managed using a command-line tool.
This provides help for either all user management actions (`./am-cli.sh user -h`) or specific actions (`./am-cli.sh user add -h`, `./am-cli.sh user info -h`, `./am-cli.sh user edit -h`, `./am-cli.sh user remove -h`).

## Adding a user

The command `./am-cli.sh user add <username>` creates a new user.
By default, a user will not have read or write access to any groups, and will not be an admin.

To grant access, lists of space-separated group names can be provided to the ``--read`` and ``--write`` arguments.
To grant a user admin rights, the ``--admin`` argument can be provided.

Example:

`./am-cli.sh user add <username> --read <group1 group2> --write <group1 group2> --admin`

## Listing user permissions

The permissions of all users can be listed with `./am-cli.sh user info`.

The permissions of a single user can be listed with `./am-cli.sh user info <username>`.

## Editing a user

You can reset a user's password using `./am-cli.sh user edit --password <username>`.

You can update the groups to which a user has read or write access by providing `--read <group1 group2 ...>` or `--write <group1 group2 ...>` in place of `--password`.

You can remove reading/writing permissions for all groups using `--noread` or `--nowrite`.

You can grant admin rights with `--admin`, or remove admin rights using `--noadmin`.

## Removing a user

A user account can be removed with the command `./am-cli.sh user remove <username>`.
