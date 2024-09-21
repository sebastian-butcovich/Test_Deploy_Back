import datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, and_

from flask import g

from app.models.usuarios import Usuario
from app.utils.build_criterion import build_criterion
from app.utils.convert_to_foreign_currency import convert_to_foreign_currency, convert_list_to_foreign_currency

from app.utils.paginated_query import paginated_query
from app.utils.build_filters import build_filters


def get_tipos_distinct(model_object) -> list:
    """Devuelve una lista de todos los tipos"""

    tipos = model_object.query.with_entities(model_object.tipo).filter_by(id_usuario=g.user_id).distinct().all()
    tipos_list = [tipo.tipo for tipo in tipos]
    return tipos_list


def get_all(args, model_object, contents_name: str = "elementos") -> (dict, int):
    """Devuelve un JSON con info de todos los elementos generados por un usuario en base a diferentes filtros"""

    # Realizo los seteos necesarios para el paginado
    page_number = args.get('page', default=1, type=int)
    page_size = args.get('page_size', default=10, type=int)
    if page_size <= 0 or page_number <= 0:
        return {'message': 'Los campos de paginado no admiten valores negativos o cero'}, 400

    try:
        current_user = Usuario.query.filter_by(id=g.user_id).first()
        filters = build_filters(args, current_user, model_object, True)
        contents = build_criterion(args, filters, model_object, True)
    except ValueError as e:
        return {"message": str(e)}, 400

    currency = args.get('currency', default="ars", type=str)
    currency_type = "oficial"
    if contents and currency != "ars".casefold():
        if currency == "usd".casefold():
            currency_type = args.get('currency_type', default="oficial", type=str)
        try:
            contents = convert_list_to_foreign_currency(contents, currency, currency_type)
        except Exception as e:
            return {"message": str(e)}, 400
    info_cotizaciones = {"cotizacion": currency, "tipo_de_cotizacion": currency_type}

    output = []
    for content in contents:
        output.append({
            'id': content.id,
            'monto': format(content.monto, ".2f"),
            'descripcion': content.descripcion,
            'fecha': content.fecha,
            'tipo': content.tipo,
            'id_usuario': content.id_usuario
        })

    return paginated_query(page_number, page_size, output, contents_name, info_cotizaciones)


def get(args, model_object, content_name: str = "elemento") -> (dict, int):
    """Devuelve un JSON con info de un elemento generado por un usuario en base a diferentes filtros"""

    try:
        current_user = Usuario.query.filter_by(id=g.user_id).first()
        filters = build_filters(args, current_user, model_object, False)
        content = build_criterion(args, filters, model_object, False)
    except ValueError as e:
        return {"message": str(e)}, 400

    currency = args.get('currency', default="ars", type=str)
    currency_type = "oficial"
    if content and currency != "ars".casefold():
        if currency == "usd".casefold():
            currency_type = args.get('currency_type', default="oficial", type=str)
        try:
            monto_convertido = convert_to_foreign_currency(content.monto, currency, currency_type)
        except Exception as e:
            return {"message": str(e)}, 400
        content.monto = monto_convertido
    info_cotizaciones = {"cotizacion": currency, "tipo_de_cotizacion": currency_type}

    output = {}
    if content:
        # Convierto el ingreso traido a json
        output = {
            'id': content.id,
            'monto': format(content.monto, ".2f"),
            'descripcion': content.descripcion,
            'fecha': content.fecha,
            'tipo': content.tipo,
            'id_usuario': content.id_usuario
        }
    return {content_name: output, 'additional_info': info_cotizaciones}, 200


def average(args, model_object) -> (dict, int):
    """Devuelve un JSON con el monto promedio entre fechas de los elementos de un usuario"""

    fecha_inicio = args.get('fecha_inicio')
    fecha_fin = args.get('fecha_fin')

    if fecha_inicio and fecha_fin:
        try:
            fecha_inicio = datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin = datetime.datetime.strptime(fecha_fin, '%Y-%m-%d')
        except ValueError:
            return {
                'message': 'Formato de fecha incorrecto'
            }, 400
        if fecha_fin <= fecha_inicio:
            return {
                'message': 'La fecha de inicio debe ser anterior a la fecha de fin'
            }, 400
    else:
        fecha_inicio = datetime.datetime.utcnow() - relativedelta(months=1)
        fecha_fin = datetime.datetime.utcnow()

    average_value = model_object.query.with_entities(func.avg(model_object.monto)).filter(
        model_object.fecha >= fecha_inicio,
        model_object.fecha <= fecha_fin
    ).scalar()
    average_value = average_value if average_value else 0.0  # Devuelve None si no trae datos de query

    currency = args.get('currency', default="ars", type=str)
    currency_type = "oficial"
    if average_value and currency != "ars".casefold():
        if currency == "usd".casefold():
            currency_type = args.get('currency_type', default="oficial", type=str)
        try:
            average_value = convert_to_foreign_currency(average_value, currency, currency_type)
        except Exception as e:
            return {"message": str(e)}, 400
    info_cotizaciones = {"cotizacion": currency, "tipo_de_cotizacion": currency_type}

    return {'average': format(average_value, ".2f"), 'additional_info': info_cotizaciones}, 200


def total(args, model_object) -> (dict, int):
    """Devuelve un JSON con el monto total entre fechas de los elementos de un usuario"""

    fecha_inicio = args.get('fecha_inicio')
    fecha_fin = args.get('fecha_fin')

    filters = []
    if fecha_inicio and fecha_fin:
        try:
            fecha_inicio = datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin = datetime.datetime.strptime(fecha_fin, '%Y-%m-%d')
        except ValueError:
            return {
                'message': 'Formato de fecha incorrecto'
            }, 400
        if fecha_fin <= fecha_inicio:
            return {
                'message': 'La fecha de inicio debe ser anterior a la fecha de fin'
            }, 400
        filters.append(and_(model_object.fecha >= fecha_inicio, model_object.fecha <= fecha_fin))

    # Si existe fecha_inicio, fecha_fin filtro por eso. Sino, devuelvo la suma total
    total_value = model_object.query.with_entities(func.sum(model_object.monto)).filter(*filters).scalar()
    total_value = total_value if total_value else 0.0  # Devuelve None si no trae datos de query

    currency = args.get('currency', default="ars", type=str)
    currency_type = "oficial"
    if total_value and currency != "ars".casefold():
        if currency == "usd".casefold():
            currency_type = args.get('currency_type', default="oficial", type=str)
        try:
            total_value = convert_to_foreign_currency(total_value, currency, currency_type)
        except Exception as e:
            return {"message": str(e)}, 400
    info_cotizaciones = {"cotizacion": currency, "tipo_de_cotizacion": currency_type}

    return {'total': format(total_value, ".2f"), 'additional_info': info_cotizaciones}, 200


def count(args, model_object) -> (dict, int):
    """Devuelve un JSON con la cantidad de entradas entre fechas de los elementos de un usuario"""

    fecha_inicio = args.get('fecha_inicio')
    fecha_fin = args.get('fecha_fin')

    filters = []
    if fecha_inicio and fecha_fin:
        try:
            fecha_inicio = datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin = datetime.datetime.strptime(fecha_fin, '%Y-%m-%d')
        except ValueError:
            return {
                'message': 'Formato de fecha incorrecto'
            }, 400
        if fecha_fin <= fecha_inicio:
            return {
                'message': 'La fecha de inicio debe ser anterior a la fecha de fin'
            }, 400
        filters.append(and_(model_object.fecha >= fecha_inicio, model_object.fecha <= fecha_fin))

    # Si existe fecha_inicio, fecha_fin filtro por eso. Sino, devuelvo la cantidad total
    count_value = model_object.query.with_entities(func.count(model_object.monto)).filter(*filters).scalar()
    count_value = count_value if count_value else 0  # Devuelve None si no trae datos de query

    return {'count': count_value}, 200


def add(json, model_object) -> (dict, int):
    """Agrega un elemento al usuario logueado"""
    # Obtengo los datos necesarios para crear el elemento desde json enviado en el body
    try:
        descripcion = json["descripcion"]
        monto = json["monto"]
        tipo = json["tipo"]
    except KeyError:
        return {
            'message': 'Uno o más campos de entrada obligatorios estan faltantes'
        }, 400
    try:
        fecha = json["fecha"]
    except KeyError:
        fecha = None

# ---------- INICIO DE VALIDACIONES ---------------------

    if not monto or not tipo:
        return {
            'message': 'Uno o más campos de entrada obligatorios se encuentran vacios'
        }, 400

    try:
        if float(monto) < 0.0:
            return {
                'message': 'monto negativo'  # 'No se permite crear elementos con monto negativo'
            }, 400
    except ValueError:
        return {
            'message': "Valor invalido en 'monto'"  # 'No se permite crear elementos con monto invalido'
        }, 400

    # Creo el elemento
    elemento = model_object(g.user_id, descripcion, monto, tipo, fecha)

    if len(descripcion) > elemento.descripcion_char_limit or len(tipo) > elemento.tipo_char_limit:  # 'superan los caracteres maximos permitidos'
        return {
            'message': 'Uno o más campos de entrada superan la cantidad maxima de caracteres permitidos.',
            'descripcion_max_characters': f"{elemento.descripcion_char_limit}",
            'tipo_max_characters': f"{elemento.tipo_char_limit}"
        }, 400

    # ---------- FIN DE VALIDACIONES ---------------------

    # Cargo el elemento en la base de datos
    model_object.create(elemento)

    return {
        'message': 'Ingreso registrado exitosamente'
    }, 201


def update(json, model_object, content_name: str = "elemento") -> (dict, int):
    """Actualiza un elemento al usuario logueado"""
    # Obtengo los datos necesarios para actualizar el elemento desde json enviado en el body
    try:
        id_elemento = json["id"]
        descripcion = json["descripcion"]
        monto = json["monto"]
        tipo = json["tipo"]
    except KeyError:
        return {
            'message': 'Uno o más campos de entrada obligatorios estan faltantes'
        }, 400
    try:
        fecha = json["fecha"]
    except KeyError:
        fecha = None

    if not id_elemento or not monto or not tipo:
        return {
            'message': 'Uno o más campos de entrada obligatorios se encuentran vacios'
        }, 400

    # Obtengo el id de usuario del token
    current_user: Usuario = Usuario.query.filter_by(id=g.user_id).first()

    # ---------- INICIO DE VALIDACIONES ---------------------

    try:
        if float(monto) < 0.0:
            return {
                'message': 'monto negativo'  # 'No se permite crear ingresos con monto negativo'
            }, 400
    except ValueError:
        return {
            'message': "Valor invalido en 'monto'"  # 'No se permite crear ingresos con monto invalido'
        }, 400

    # Busco el elemento
    elemento = model_object.query.filter_by(id=id_elemento).first()

    if not (elemento and (current_user.is_admin or elemento.id_usuario != g.user_id)):
        return {
            'message': 'No se ha encontrado el elemento'
        }, 404

    if len(descripcion) > elemento.descripcion_char_limit or len(tipo) > elemento.tipo_char_limit:  # 'superan los caracteres maximos permitidos'
        return {
            'message': 'Uno o más campos de entrada superan la cantidad maxima de caracteres permitidos.',
            'descripcion_max_characters': f"{elemento.descripcion_char_limit}",
            'tipo_max_characters': f"{elemento.tipo_char_limit}"
        }, 400

    # ---------- FIN DE VALIDACIONES ---------------------

    # Actualizo los valores del elemento
    elemento.descripcion = descripcion
    elemento.monto = monto
    elemento.tipo = tipo
    if fecha:
        elemento.fecha = fecha

    # Actualizo el elemento en la base de datos
    elemento.update()

    return {
        'message': f'{content_name} actualizado exitosamente'
    }, 200


def delete(args, model_object, content_name: str = "elemento") -> (dict, int):
    """Elimina un elemento al usuario logueado"""

    id_elemento = args.get('id', type=int)
    # Obtengo el id de usuario del token
    current_user: Usuario = Usuario.query.filter_by(id=g.user_id).first()

    elemento = model_object.query.filter_by(id=id_elemento).first()

    if not (elemento and (current_user.is_admin or elemento.id_usuario != g.user_id)):
        return {
            'message': f'No se ha encontrado el {content_name}'
        }, 404

    elemento.delete()
    return {
        'message': f'{content_name} eliminado exitosamente'
    }, 200
