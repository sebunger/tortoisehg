# delaylock.py - insert delay before locking so that mtime should change

import time

def reposetup(ui, repo):
    delay = ui.configint('debug', 'delaylock', 0)
    if delay <= 0:
        return
    class delaylockrepo(repo.__class__):
        def _lock(self, *args, **kwargs):
            time.sleep(delay)
            return super(delaylockrepo, self)._lock(*args, **kwargs)
    repo.__class__ = delaylockrepo
