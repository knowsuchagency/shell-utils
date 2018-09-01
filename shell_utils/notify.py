import subprocess as sp
import typing as typ
import logging
import shlex
import sys
from functools import wraps

import click


def notify(message: str, title=None, subtitle=None, sound=None):
    """
    Send a Mac OS notification.

    Args:
        message: the notification body
        title: the title of the notification
        subtitle: the subtitle of the notification
        sound: the sound the notification makes

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


def notice(message: typ.Optional[str] = None, title=None, subtitle=None, sound=None):
    """
    Returns a decorator that allows you to be notified when a function returns.

    Args:
        message: the notification body
        title: the title of the notification
        subtitle: the subtitle of the notification
        sound: the sound the notification makes

    Returns: a function
    """

    def decorator(func):
        """
        Send notification that task has finished.

        Especially useful for long-running tasks
        """

        @wraps(func)
        def inner(*args, **kwargs):
            nonlocal message, title, subtitle, sound

            title = getattr(func, '__name__') + ' finished' if title is None else title
            subtitle = 'Success!' if subtitle is None else subtitle
            result = None

            try:
                _result = func(*args, **kwargs)
                if isinstance(_result, str):
                    result = _result
            except:
                subtitle = 'Failure'
                raise
            finally:
                if message is not None:
                    pass
                elif result is not None:
                    message = result
                else:
                    message = ''
                notify(message, title=title, subtitle=subtitle, sound=sound)

        return inner

    return decorator


@click.command()
@click.argument('message')
@click.option('--title', help='the notification title')
@click.option('--subtitle', help='the notification subtitle')
@click.option('--sound', help='the notification sound')
def notify_command(message, title, subtitle, sound):
    """Notification cli tool."""
    notify(message, title=title, subtitle=subtitle, sound=sound)
