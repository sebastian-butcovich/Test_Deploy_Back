from flask_cors import cross_origin

from app import token_required
from flask import Blueprint, request, jsonify

from app.models.ingresos import Ingreso

from app.services import elemento_financiero as ef

bp = Blueprint('ingresos', __name__, url_prefix='/ingresos')


@bp.route('/tipos', methods=['GET'])
@cross_origin()
@token_required
def get_tipos_distinct():
    """Devuelve una lista con todos los tipos de ingresos"""

    return jsonify(ef.get_tipos_distinct(Ingreso)), 200


@bp.route('/get_all', methods=['GET'])
@cross_origin()
@token_required
def get_all():
    """Devuelve un JSON con info de todos los ingresos generados por un usuario en base a diferentes filtros"""

    message, status_code = ef.get_all(request.args, Ingreso, "ingresos")
    return jsonify(message), status_code


@bp.route('/get', methods=['GET'])
@cross_origin()
@token_required
def get():
    """Devuelve un JSON con info de un ingreso generado por un usuario en base a diferentes filtros"""

    message, status_code = ef.get(request.args, Ingreso, "ingreso")
    return jsonify(message), status_code


@bp.route('/average', methods=['GET'])
@cross_origin()
@token_required
def average():
    """Devuelve un JSON con el promedio entre fechas de los ingresos de un usuario"""

    message, status_code = ef.average(request.args, Ingreso)
    return jsonify(message), status_code


@bp.route('/total', methods=['GET'])
@cross_origin()
@token_required
def total():
    """Devuelve un JSON con el total entre fechas de los gastos de un usuario"""

    message, status_code = ef.total(request.args, Ingreso)
    return jsonify(message), status_code


@bp.route('/count', methods=['GET'])
@cross_origin()
@token_required
def count():
    """Devuelve un JSON con la cantidad de ingresos entre fechas de los gastos de un usuario"""

    message, status_code = ef.count(request.args, Ingreso)
    return jsonify(message), status_code


@bp.route('/add', methods=['POST'])
@cross_origin()
@token_required
def add():
    """Agrega un ingreso al usuario logueado"""

    message, status_code = ef.add(request.json, Ingreso)
    return jsonify(message), status_code


@bp.route('/update', methods=['PUT'])
@cross_origin()
@token_required
def update():
    """Actualiza un ingreso al usuario logueado"""

    message, status_code = ef.update(request.json, Ingreso)
    return jsonify(message), status_code


@bp.route('/delete', methods=['DELETE'])
@cross_origin()
@token_required
def delete():
    """Elimina un ingreso al usuario logueado"""

    message, status_code = ef.delete(request.args, Ingreso)
    return jsonify(message), status_code
