from flask_cors import cross_origin

from app import token_required
from flask import Blueprint, jsonify, request, g

from app.models.feedback import Feedback
from app.models.usuarios import Usuario

from app.utils.paginated_query import paginated_query

bp = Blueprint('feedback', __name__, url_prefix='/feedback')


@bp.route('/tipos', methods=['GET'])
@cross_origin()
@token_required
def get_tipos_distinct():
    tipos = Feedback.query.with_entities(Feedback.tipo).filter_by(id_usuario=g.user_id).distinct().all()
    tipos_list = [tipo.tipo for tipo in tipos]
    return tipos_list


@bp.route('/get_all', methods=['GET'])
@cross_origin()
@token_required
def get_all():
    """Devuelve un JSON con info de todas las entradas de feedback generados por un usuario"""

    current_user: Usuario = Usuario.query.filter_by(id=g.user_id).first()
    if current_user.is_admin:  # Si es admin, traigo el listado del feedback de todos los usuarios
        feedbacks = Feedback.query.all()
    else:  # Si NO es admin, rechazo el listado
        feedbacks = Feedback.query.filter_by(id_usuario=g.user_id).all()

    page_number = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)

    # converting the query objects
    # to list of jsons
    output = []
    for feedback in feedbacks:
        # appending the feedback data json
        # to the response list
        output.append({
            'descripcion': feedback.descripcion,
            'created_on': feedback.created_on,
            'tipo': feedback.tipo,
            'id_usuario': feedback.id_usuario,
        })

    return paginated_query(page_number, page_size, output, "Feedbacks")


@bp.route('/add', methods=['POST'])
@cross_origin()
@token_required
def add():
    """Agrega un ingreso al usuario logueado"""
    # Obtengo los datos necesarios para crear el elemento desde json enviado en el body
    try:
        descripcion = request.json["descripcion"]
        tipo = request.json["tipo"]
    except KeyError:
        return jsonify({
            'message': 'Uno o más campos de entrada obligatorios estan faltantes'
        }), 400

# ---------- INICIO DE VALIDACIONES ---------------------

    if not tipo:
        return jsonify({
            'message': 'Uno o más campos de entrada obligatorios se encuentran vacios'
        }), 400

    # Creo el elemento
    feedback = Feedback(g.user_id, descripcion, tipo)

    if len(descripcion) > feedback.descripcion_char_limit or len(tipo) > feedback.tipo_char_limit:  # 'superan los caracteres maximos permitidos'
        return jsonify({
            'message': 'Uno o más campos de entrada superan la cantidad maxima de caracteres permitidos.',
            'descripcion_max_characters': f"{feedback.descripcion_char_limit}",
            'tipo_max_characters': f"{feedback.tipo_char_limit}"
        }), 400

    # ---------- FIN DE VALIDACIONES ---------------------

    # Cargo el elemento en la base de datos
    Feedback.create(feedback)

    return jsonify({
        'message': 'Feedback registrado exitosamente'
    }), 201
