from flask import Blueprint, request, jsonify
import jwt
import datetime

from flask_cors import cross_origin

from app import app

from werkzeug.security import check_password_hash, generate_password_hash

from app.models.usuarios import Usuario
from app.utils.email_validation import validar_email

from app import config as cfg


def generate_access_token(user_id):
    return jwt.encode({
        'id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)  # utcnow() DEPRECATED, solucion abajo funciona en windows, no en linux
        # 'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=15)
    }, app.config['SECRET_KEY'], algorithm="HS256")


def generate_refresh_token(user_id):
    return jwt.encode({
        'id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)  # utcnow() DEPRECATED, solucion abajo funciona en windows, no en linux
        # 'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=7)
    }, app.config['REFRESH_SECRET_KEY'], algorithm="HS256")


bp = Blueprint('auth', __name__, url_prefix='/auth')
# route for logging user in


@bp.route('/login', methods=['POST'])
@cross_origin()
def user_login():
    """Realiza el login del usuario"""
    # creates dictionary of form data
    auth = request.json
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({
            'message': 'Uno o más campos de entrada obligatorios se encuentran vacios'
        }), 400

    username = auth.get('username')
    password = auth.get('password')

    usuario: Usuario = Usuario.query.filter_by(username=username).first()

    if not usuario:
        # returns 401 if user does not exist
        return jsonify({
            'message': 'Username o password invalidos'  # 'Usuario no encontrado'
        }), 401  # Siempre se envia la misma respuesta ante 401 por motivos de ciberseguridad

    if not usuario.is_verified:
        return jsonify({
            'message': 'Usuario no validado'
        }), 403

    if check_password_hash(usuario.password_hash, password):
        # generates the JWT Token
        access_token = generate_access_token(usuario.get_id())
        refresh_token = generate_refresh_token(usuario.get_id())

        usuario.last_login = datetime.datetime.now()
        usuario.update()

        return jsonify({'access_token': access_token, 'refresh_token': refresh_token})

    # returns 403 if password is wrong
    return jsonify({
            'message': 'Username o password invalidos'  # 'Password incorrecta'
        }), 401  # Siempre se envia la misma respuesta ante 401 por motivos de ciberseguridad


# signup route
@bp.route('/signup', methods=['POST'])
@cross_origin()
def user_signup():
    """Genera un nuevo usuario"""
    try:
        username = request.json["username"]
        password = request.json["password"]
        email = request.json["email"]
    except KeyError:
        return jsonify({
            'message': 'Uno o más campos de entrada obligatorios estan faltantes'
        }), 400

    if not username or not password or not email:
        return jsonify({
            'message': 'Uno o más campos de entrada obligatorios se encuentran vacios'
        }), 400

    # checking for existing user
    usuario = Usuario.query.filter_by(username=username).first()

    if not usuario:
        # database ORM object
        verified_on_creation = not cfg.EMAIL_VERIFICATION  # Si no se verifica email, se asume verificacion correcta
        usuario = Usuario(username = username, password_hash = generate_password_hash(password), email = email, is_verified = verified_on_creation)

        # ---------- INICIO DE VALIDACIONES ---------------------

        if len(username) > usuario.username_char_limit or len(email) > usuario.email_char_limit:  # 'superan los caracteres maximos permitidos'
            return jsonify({
                'message': 'Uno o más campos de entrada superan la cantidad maxima de caracteres permitidos',
                'username_max_characters': f"{usuario.username_char_limit}",
                'email_max_characters': f"{usuario.email_char_limit}"
            }), 400
        if not validar_email(email):
            return jsonify({
                'message': 'Email invalido'  # 'email no cumple con sintaxis'
            }), 400

        # ---------- FIN DE VALIDACIONES ---------------------

        # Agrego el usuario en la base de datos
        Usuario.create(usuario)
        if not verified_on_creation:
            return jsonify({
                'message': 'Usuario registrado correctamente. Debe verificar el email para loguearse'
            }), 201
        else:
            return jsonify({
                'message': 'Usuario registrado correctamente'
            }), 201
    else:
        # returns 202 if user already exists
        return jsonify({
            'message': 'Usuario existente'  # 'Usuario ya existe en la base de datos'
        }), 202


@bp.route('/refresh', methods=['POST'])
@cross_origin()
def refresh():
    token = request.json.get('refresh_token')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 401

    try:
        data = jwt.decode(token, app.config['REFRESH_SECRET_KEY'], algorithms=["HS256"])
        new_access_token = generate_access_token(data['id'])
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Refresh token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Refresh token is invalid!'}), 401

    return jsonify({'access_token': new_access_token})
