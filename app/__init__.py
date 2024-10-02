from functools import wraps

import jwt
from flask import Flask, request, jsonify, g
from flask_cors import CORS, cross_origin

from app.db import db
from app.db_config import db_config
from app import config as cfg

from app.models.usuarios import Usuario
from flask_migrate import Migrate

# Agregar los cambios de modelos a db: "flask db migrate"
# Commitear los cambios de modelos a db: "flask db upgrade"
# Si falla, eliminar el directorio 'migrations', ejecutar 'flask db init' y luego las dos instrucciones anteriores

def deploy_app() :
    app = Flask(__name__)
    CORS(app)
    app.config[
        "SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{db_config.get('USER')}:{db_config.get('PASSWORD')}@{db_config.get('HOST')}/{db_config.get('DATABASE')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = cfg.SECRET_KEY
    app.config["REFRESH_SECRET_KEY"] = cfg.REFRESH_SECRET_KEY
    app.config['CORS_HEADERS'] = 'Content-Type'

    db.init_app(app)

    with app.app_context():
        db.create_all()

    migrate = Migrate(app, db)

    @app.route("/about")
    @cross_origin()
    # @login_required
    def about():
        return "QmFja2VuZCBkZSBhcHAgZGUgZmluYW56YXMuIERlc2Fycm9sbGFkbyBwb3IgQnJhaWFuIEdhcmF0LiAyMDI0"


    @app.route("/health")
    @cross_origin()
    # @login_required
    def health():
        return jsonify({
            'health': 'ok'
        }), 200
    return app;
app = deploy_app()

def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            # jwt is passed in the request header
            if 'x-access-token' in request.headers:
                token = request.headers['x-access-token']
            # return 401 if token is not passed
            if not token:
                return jsonify({'message': 'Falta el token'}), 401

            try:
                # decoding the payload to fetch the stored details
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                g.user_id = data['id']
            except jwt.ExpiredSignatureError:
                return jsonify({'message': 'El token ha expirado'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'message': 'El token es invalido'}), 401
            # returns the current logged in users context to the routes
            return f(*args, **kwargs)

        return decorated

from app.controllers import auth, usuarios, ingresos, gastos, feedback
app.register_blueprint(auth.bp)
app.register_blueprint(usuarios.bp)
app.register_blueprint(ingresos.bp)
app.register_blueprint(gastos.bp)
app.register_blueprint(feedback.bp)


if __name__ == '__main__':
    app.run(debug=True)
