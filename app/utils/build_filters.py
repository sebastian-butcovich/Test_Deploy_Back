import datetime

from sqlalchemy import and_


def build_filters(params, current_user, model_object, ranges: bool = False) -> list:
    filters = []

    if ranges:  # El filtro es para una lista de elementos

        monto_min = params.get('monto_min')
        monto_max = params.get('monto_max')

        try:
            if monto_min and monto_max:
                monto_min = float(monto_min)
                monto_max = float(monto_max)
                if monto_max <= monto_min:
                    raise ValueError('El monto minimo debe ser menor al monto maximo')
                filters.append(and_(model_object.monto >= monto_min, model_object.monto <= monto_max))
        except TypeError:
            raise ValueError('El monto ingresado es invalido')

        fecha_inicio = params.get('fecha_inicio')
        fecha_fin = params.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            try:
                fecha_inicio = datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d')
                fecha_fin = datetime.datetime.strptime(fecha_fin, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Formato de fecha incorrecto')
            if fecha_fin <= fecha_inicio:
                raise ValueError('La fecha de inicio debe ser anterior a la fecha de fin')
            filters.append(and_(model_object.fecha >= fecha_inicio, model_object.fecha <= fecha_fin))

    else:  # El filtro es para un unico elemento
        monto = params.get('monto')
        if monto:
            try:
                monto = float(monto)
                filters.append(model_object.monto == monto)
            except (ValueError, TypeError):
                raise ValueError("El monto ingresado es invalido")

        fecha = params.get('fecha')
        if fecha:
            try:
                fecha = datetime.datetime.strptime(fecha, '%Y-%m-%d')
                filters.append(model_object.fecha == fecha)
            except ValueError:
                raise ValueError('Formato de fecha incorrecto')

    tipo = params.get('tipo')
    if tipo:
        filters.append(model_object.tipo.like(f'%{tipo}%'))

    if not current_user.is_admin:
        filters.append(model_object.id_usuario == current_user.get_id())

    return filters
