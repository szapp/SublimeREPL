"""
Launch REPL on startup
"""
import os
import sublime

try:
    from .sublimerepl import manager
    from .run_existing_command import SUBLIMEREPL_DIR, SUBLIMEREPL_USER_DIR
except (ImportError, ValueError):
    from sublimerepl import manager
    from run_existing_command import SUBLIMEREPL_DIR, SUBLIMEREPL_USER_DIR


def plugin_loaded():

    # Copied from run_existing_command to ensure functionality
    # irrespective of plugin loading order
    global SUBLIMEREPL_DIR
    global SUBLIMEREPL_USER_DIR
    SUBLIMEREPL_DIR = "Packages/SublimeREPL"
    SUBLIMEREPL_USER_DIR = os.path.join(sublime.packages_path(), "User",
                                        "SublimeREPL")

    window = sublime.active_window()
    s = window.active_view().settings()
    kind = s.get('autostart_repl')
    if not kind:
        return

    for rv in manager.find_repl(kind.lower()):
        return

    print('No {} REPL found. Opening a new instance.'.format(kind))

    if kind.lower() == 'ipython':
        window.run_command('run_existing_window_command',
                           {'id': 'repl_python_ipython',
                            'file': 'config/Python/Main.sublime-menu'})
    else:
        print('{} REPL not supported.'.format(kind))
