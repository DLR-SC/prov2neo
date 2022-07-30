import functools
import typing

import click
import py2neo


class ConnectionError(Exception):
    pass


def on_error(error: typing.Type[Exception] = Exception, msg: str = "", hint: str = ""):
    def wrap(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except error as err:
                text = f"{msg}{'; ' if msg else ''}{err}\n"
                if hint:
                    text += f"Hint: {hint}"
                ctx = click.get_current_context()
                ctx.fail(text)

        return wrapped

    return wrap


def on_database_error(msg="", hint=""):
    return on_error(py2neo.DatabaseError, msg=msg, hint=hint)


def on_client_error(msg="", hint=""):
    return on_error(py2neo.ClientError, msg=msg, hint=hint)


def on_connection_error(msg="", hint=""):
    return on_error(ConnectionError, msg=msg, hint=hint)


def on_value_error(msg="", hint=""):
    return on_error(ValueError, msg=msg, hint=hint)
