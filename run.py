from threading import Thread
from app import create_app
from app.bot import run_bot

app = create_app()

def run_flask():
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8000)

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    run_bot()