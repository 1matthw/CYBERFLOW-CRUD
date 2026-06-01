from flask import Flask
from config import Config
from models import close_db, init_database
from routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_database(app.config)
    register_routes(app)

    app.teardown_appcontext(close_db)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
