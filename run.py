import os
import sys
import webbrowser
from threading import Timer

def open_browser():
    webbrowser.open('http://localhost:5000')

def main():
    print("Starting SK ShopKeep...")
    sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
    Timer(1.5, open_browser).start()
    print("Server: http://localhost:5000")
    from backend.app import create_app
    app = create_app()
    app.run(host='127.0.0.1', port=5000)

if __name__ == '__main__':
    main()
