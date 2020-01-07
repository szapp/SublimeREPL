import os
import sys
import json
import socket
import threading

activate_this = os.environ.get("SUBLIMEREPL_ACTIVATE_THIS", None)

# turn off pager
os.environ['TERM'] = 'emacs'

if activate_this:
    with open(activate_this, "r") as f:
        exec(f.read(), {"__file__": activate_this})

try:
    import IPython
    IPYTHON = True
    version = IPython.version_info[0]
except ImportError:
    IPYTHON = False

if not IPYTHON:
    # for virtualenvs w/o IPython
    import code
    code.InteractiveConsole().interact()

# IPython 4
if version > 3:
    from traitlets.config.loader import Config
# all other versions
else:
    from IPython.config.loader import Config

editor = "subl -w"

cfg = Config()
cfg.ZMQTerminalInteractiveShell.simple_prompt = True

exec_lines = []
exec_lines.append('import sys')
exec_lines.append('sys.stdout.flush_interval = 0')
exec_lines.append('sys.stderr.flush_interval = 0')
backend = os.environ.get('SUBLIMEREPL_MATPLOTLIB')
if backend:
    exec_lines.append(r'%matplotlib ' + backend)

    if backend == 'inline':
        # Set inline rc params
        exec_lines.append(r'_x = %config InlineBackend.rc')
        exec_lines.append('_x.update('
                          + os.environ.get('SUBLIMEREPL_PYPLOT_INLINERC')
                          + ')')
        exec_lines.append(r'%config InlineBackend.rc=_x')
        exec_lines.append('del _x')
        exec_lines.append(r'%matplotlib inline')
    elif not int(os.environ.get('SUBLIMEREPL_PYPLOT_INTER')):
        # Set plotting to non-interactive
        exec_lines.append('from matplotlib import pyplot as plt')
        exec_lines.append('plt.ioff()')

exec_lines += os.environ.get('SUBLIMEREPL_EXEC_LINES', '').split('\n')

exec_lines = [el.replace(
    '[LCURLYBRACKET]', '{').replace(
    '[RCURLYBRACKET]', '}') for el in exec_lines]

# Temporary fix to prevent import error of removed function
if IPYTHON:
    def no_code(x, encoding=None):
        return x
    IPython.utils.py3compat.cast_unicode_py2 = no_code

# IPython 4.0.0
if version > 3:
    try:
        from jupyter_console.app import ZMQTerminalIPythonApp

        def kernel_client(zmq_shell):
            return zmq_shell.kernel_client
    except ImportError:
        raise ImportError("jupyter_console required for IPython 4")
# IPython 2-3
elif version > 1:
    from IPython.terminal.console.app import ZMQTerminalIPythonApp

    def kernel_client(zmq_shell):
        return zmq_shell.kernel_client
else:
    # Ipython 1.0
    from IPython.frontend.terminal.console.app import ZMQTerminalIPythonApp

    def kernel_client(zmq_shell):
        return zmq_shell.kernel_manager

embedded_shell = ZMQTerminalIPythonApp(config=cfg, user_ns={})
embedded_shell.initialize()
embedded_shell.shell.run_cell('\n'.join(exec_lines), store_history=False)

if os.name == "nt":
    import IPython.utils.io as io
    io.stdout = sys.stdout
    io.stderr = sys.stderr

ac_port = int(os.environ.get("SUBLIMEREPL_AC_PORT", "0"))
ac_ip = os.environ.get("SUBLIMEREPL_AC_IP", "127.0.0.1")
if ac_port:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ac_ip, ac_port))

def read_netstring(s):
    size = 0
    while True:
        ch = s.recv(1)
        if ch == b':':
            break
        size = size * 10 + int(ch)
    msg = b""
    while size != 0:
        msg += s.recv(size)
        size -= len(msg)
    ch = s.recv(1)
    assert ch == b','
    return msg

def send_netstring(sock, msg):
    payload = b"".join([str(len(msg)).encode("ascii"), b':', msg.encode("utf-8"), b','])
    sock.sendall(payload)

def complete(zmq_shell, req):
    kc = kernel_client(zmq_shell)
    # Ipython 4
    if version > 3:
        msg_id = kc.complete(req['line'], req['cursor_pos'])
    # Ipython 1-3
    else:
        msg_id = kc.shell_channel.complete(**req)
    msg = kc.shell_channel.get_msg(timeout=50)
    # end new stuff
    if msg['parent_header']['msg_id'] == msg_id:
        return msg["content"]["matches"]
    return []

def handle():
    while True:
        try:
            msg = read_netstring(s).decode("utf-8")
        except ConnectionAbortedError:
            break

        try:
            req = json.loads(msg)
            completions = complete(embedded_shell, req)
            result = (req["text"], completions)
            res = json.dumps(result)
            send_netstring(s, res)
        except Exception:
            send_netstring(s, b"[]")

    if ac_port:
        s.close()

def inline_image(data):
    if embedded_shell.shell.mime_preference[0] not in data.keys():
        return False
    msg = 'data:{};base64,{}'.format(
        embedded_shell.shell.mime_preference[0],
        data[embedded_shell.shell.mime_preference[0]])
    print(msg)  # Picked up and replaced by REPL
    return True

if ac_port:
    t = threading.Thread(target=handle)
    t.setDaemon(True)
    t.start()

embedded_shell.shell.callable_image_handler = inline_image
embedded_shell.shell.image_handler = 'callable'
embedded_shell.start()

if ac_port:
    s.close()
