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

    # There is probably a less hacky way to escape single quotes safely
    # but I haven't gotten to it

    message = message.replace("'", '')

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
        message = 'Success!'
        result = ''
        try:
            _result = func(*args, **kwargs)
            if isinstance(_result, str):
                result = _result
        except:
            message = 'Failure'
            raise
        finally:
            notify(result,
                   title=getattr(func, '__name__') + ' finished',
                   subtitle=message
                   )

    return inner


@click.command()
@click.argument('message')
@click.option('--title', help='the notification title')
@click.option('--subtitle', help='the notification subtitle')
@click.option('--sound', help='the notification sound')
def notify_command(message, title, subtitle, sound):
    """Notification cli tool."""
    notify(message, title=title, subtitle=subtitle, sound=sound)
