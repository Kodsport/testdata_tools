import sys

def cmdlinearg(name, default=None):
    for arg in sys.argv:
        if arg.startswith(name + "="):
            return arg.split("=")[1]
    assert default is not None, name
    return default

need_mode = cmdlinearg('mode')
have_mode, seed = raw_input().split()
assert 0 <= int(seed)
assert have_mode == need_mode
sys.exit(42)
