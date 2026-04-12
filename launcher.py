import os
import sys
import webbrowser
from threading import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def open_browser():
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    from backend.app import create_app
    app = create_app()
    app.run(host='127.0.0.1', port=5000)
