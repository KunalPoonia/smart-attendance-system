from flask import Flask, render_template
from config import Config
from extensions import db
from utils.helpers import create_directory_structure, setup_logging
import os
import logging
from datetime import datetime, date

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    db.init_app(app)
    Config.init_app(app)

    # Setup Logging and Dirs
    setup_logging()
    create_directory_structure()

    # Register Blueprints
    from routes.main import bp as main_bp
    from routes.students import bp as students_bp
    from routes.attendance import bp as attendance_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(attendance_bp)

    # Context Processors
    @app.context_processor
    def inject_datetime():
        return {'datetime': datetime, 'date': date}

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('index.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('index.html'), 500

    # Create Tables
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)