"""Supervise web and optional training processes on one disk-backed instance."""

import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    training = os.environ.get('RENDER_TRAINING_ENABLED', 'False') == 'True'
    if training:
        root = Path('/var/data')
        if not root.is_mount():
            raise SystemExit('Training requires a persistent disk mounted at /var/data.')
        for name in ('media', 'models'):
            directory = root / name
            directory.mkdir(exist_ok=True)
            if not os.access(directory, os.W_OK):
                raise SystemExit(f'Training directory is not writable: {directory}')

    children = []
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        if training:
            # One worker on the only instance sharing this mounted disk.
            children.append(subprocess.Popen([
                sys.executable, '-u', 'manage.py', 'process_training_jobs',
                '--recover-interrupted',
            ], start_new_session=True))
        children.append(subprocess.Popen([
            sys.executable, '-m', 'gunicorn', 'config.wsgi:application',
            '--bind', f'0.0.0.0:{os.environ.get("PORT", "10000")}',
            '--workers', '1', '--threads', '2', '--timeout', '120',
            '--access-logfile', '-', '--error-logfile', '-',
        ], start_new_session=True))
        while not stopping:
            for child in children:
                if child.poll() is not None:
                    print(f'Render child process exited ({child.returncode}); stopping service.', flush=True)
                    return 1
            time.sleep(1)
        return 0
    finally:
        # Signal entire process groups, including Gunicorn workers.
        for child in children:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + 20
        for child in children:
            try:
                child.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()


if __name__ == '__main__':
    sys.exit(main())
