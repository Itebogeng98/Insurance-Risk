"""Run inside the built image; uses no real database or credentials."""
import os
import subprocess
import time
import urllib.request


os.environ.update({
    'DJANGO_SETTINGS_MODULE': 'config.production',
    'SECRET_KEY': 'image-smoke-test-only-43aa29da71a14b218fbfb873ee0623025f25b945',
    'DB_NAME': 'smoke', 'DB_USER': 'smoke', 'DB_PASSWORD': 'smoke',
    'ALLOWED_HOSTS': '127.0.0.1',
})
subprocess.run(['python', 'manage.py', 'check', '--deploy'], check=True)
subprocess.run(['python', 'manage.py', 'collectstatic', '--noinput'], check=True)
server = subprocess.Popen(['gunicorn', 'config.wsgi:application', '--bind', '127.0.0.1:18080'])
try:
    for attempt in range(30):
        try:
            request = urllib.request.Request(
                'http://127.0.0.1:18080/accounts/login/',
                headers={'X-Forwarded-Proto': 'https'},
            )
            with urllib.request.urlopen(request, timeout=2) as response:
                assert response.status == 200
                assert response.headers['X-Frame-Options'] == 'DENY'
                assert 'Secure' in response.headers['Set-Cookie']
                assert b'csrfmiddlewaretoken' in response.read()
            print('Production Gunicorn login response and secure CSRF cookie verified.')
            break
        except OSError:
            if server.poll() is not None or attempt == 29:
                raise
            time.sleep(1)
finally:
    server.terminate()
    server.wait(timeout=10)
