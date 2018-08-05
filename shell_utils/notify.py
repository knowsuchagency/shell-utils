import subprocess as sp
import logging
import types
import shlex
import sys
from functools import singledispatch, wraps

import click


@singledispatch
def notify(message: str, title=None, subtitle=None, sound=None):
    """
    Wraps osascript.

    see https://apple.stackexchange.com/questions/57412/how-can-i-trigger-a-notification-center-notification-from-an-applescript-or-shel/115373#115373
    """
    if title is None:
        title = 'heads up'
    if subtitle is None:
        subtitle = 'something happened'

    if sys.platform != 'darwin':
        logging.warning('This function is designed to work on Mac OS')

    command = f"""osascript -e 'display notification "{message}" with title "{title}" subtitle "{subtitle}" sound name "{sound}"' """
    sp.run(shlex.split(command), check=False)


@notify.register(types.FunctionType)
def _(func):
    """
    Send notification that task has finished.

    Especially useful for long-running tasks
    """

    @wraps(func)
    def inner(*args, **kwargs):
        result = None
        message = 'Succeeded!'

        try:
            result = func(*args, **kwargs)
        except Exception:
            message = 'Failed'
            raise
        else:
            return result
        finally:
            notify(message, title=getattr(func, '__name__'))

    return inner


@click.command()
@click.argument('message')
@click.option('--title', help='the notification title')
@click.option('--subtitle', help='the notification subtitle')
@click.option('--sound', help='the notification sound')
def notify_command(message, title, subtitle, sound):
    """Notification cli tool."""
    notify(message, title=title, subtitle=subtitle, sound=sound)
