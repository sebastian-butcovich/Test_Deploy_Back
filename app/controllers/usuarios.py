from flask_cors import cross_origin
from werkzeug.security import generate_password_hash

from app import token_required
from flask import Blueprint, jsonify, request, g

from app.models.gastos import Gasto
from app.models.ingresos import Ingreso
from app.models.usuarios import Usuario
from app.utils.email_validation import validar_email

from app import config as cfg

from app.utils.paginated_query import paginated_query

bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')


@bp.route('/saldo', methods=['GET'])
@cross_origin()
@token_required
def saldo():

    # Obtengo el id de usuario del token
    id_usuario = g.user_id

    current_saldo = 0.0

    ingresos = Ingreso.query.filter_by(id_usuario=id_usuario).all()
    for ingreso in ingresos:
        current_saldo += ingreso.monto

    gastos = Gasto.query.filter_by(id_usuario=id_usuario).all()
    for gasto in gastos:
        current_saldo -= gasto.monto

    return jsonify({
        'saldo': format(current_saldo, ".2f"),
    }), 200


@bp.route('/list', methods=['GET'])
@cross_origin()
@token_required
def get_all_users():
    """Devuelve un JSON con info de todos los usuarios"""
    current_user: Usuario = Usuario.query.filter_by(id=g.user_id).first()
    if current_user.is_admin:  # Si es admin, traigo el listado de todos los usuarios
        usuarios = Usuario.query.all()
    else:  # Si NO es admin, rechazo el listado
        return jsonify({
            'message': 'No tiene permisos para esta operación'
        }), 401

    page_number = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)

    # converting the query objects
    # to list of jsons
    output = []
    for usuario in usuarios:
        # appending the user data json
        # to the response list
        output.append({
            'id': usuario.id,
            'username': usuario.username,
            'email': usuario.email,
            'created_on': usuario.created_on,
            'last_updated_on': usuario.last_updated_on,
            'last_login': usuario.last_login,
            'is_admin': usuario.is_admin,
            'is_verified': usuario.is_verified,
            'is_money_visible': usuario.is_money_visible
        })

    return paginated_query(page_number, page_size, output, "Usuarios")


@bp.route('/whoami', methods=['GET'])
@cross_origin()
@token_required
def who_am_i():
    """Muestra info del usuario logueado via JWT"""
    current_user: Usuario = Usuario.query.filter_by(id=g.user_id).first()
    output = {
        'id': current_user.get_id(),
        'username': current_user.username,
        'email': current_user.email,
        'created_on': current_user.created_on,
        'last_updated_on': current_user.last_updated_on,
        'is_admin': current_user.is_admin,
        'is_verified': current_user.is_verified,
        'is_money_visible': current_user.is_money_visible
    }
    return jsonify(output), 200


@bp.route('/update', methods=['PUT'])
@cross_origin()
@token_required
def update():
    try:
        username = request.json["username"]
        password = request.json["password"]
        email = request.json["email"]
        is_money_visible = request.json["is_money_visible"]
    except KeyError:
        return jsonify({
            'message': 'Uno o más campos de entrada obligatorios están faltantes'
        }), 400

    if not username or not password or not email or not is_money_visible:
        return jsonify({
            'message': 'Uno o más campos de entrada obligatorios se encuentran vacios'
        }), 400

    usuario: Usuario = Usuario.query.filter_by(id=g.user_id).first()

    # ---------- INICIO DE VALIDACIONES ---------------------

    if len(username) > usuario.username_char_limit or len(email) > usuario.email_char_limit:  # 'superan los caracteres maximos permitidos'
        return jsonify({
            'message': 'Uno o más campos de entrada superan la cantidad maxima de caracteres permitidos',
            'username_max_characters': f"{usuario.username_char_limit}",
            'email_max_characters': f"{usuario.email_char_limit}"
        }), 400
    if not validar_email(email):
        return jsonify({
            'message': 'Email invalido'
        }), 403
    existing_user = Usuario.query.filter_by(username=username).first()
    if existing_user and existing_user.id != g.user_id:
        return jsonify({
            'message': "Nombre de usuario ya existente"
        }), 409

    # ---------- FIN DE VALIDACIONES ---------------------

    usuario.username = username
    usuario.password = generate_password_hash(password)

    if cfg.EMAIL_VERIFICATION and usuario.email != email:
        usuario.email = email
        usuario.is_verified = False  # Debe validar de nuevo el email para usar uno nuevo
    elif not cfg.EMAIL_VERIFICATION:
        usuario.email = email

    usuario.is_money_visible = is_money_visible
    # Agrego el usuario en la base de datos
    usuario.update()
    if usuario.is_verified:
        return jsonify({
            'message': 'Usuario actualizado correctamente'  # 'Usuario creado exitosamente en la base de datos'
        }), 200
    else:
        return jsonify({
            'message': 'Usuario actualizado correctamente. Debe verificar su email'  # 'Usuario creado exitosamente en la base de datos pero debe verificar email
        }), 200


@bp.route('/delete', methods=['DELETE'])
@cross_origin()
@token_required
def delete():

    id_usuario = g.user_id
    current_user: Usuario = Usuario.query.filter_by(id=g.user_id).first()

    ingresos = Ingreso.query.filter_by(id_usuario=id_usuario).all()
    for ingreso in ingresos:
        ingreso.delete()

    gastos = Gasto.query.filter_by(id_usuario=id_usuario).all()
    for gasto in gastos:
        gasto.delete()

    current_user.delete()
    return jsonify({
        'message': 'Usuario eliminado exitosamente'
    }), 200
