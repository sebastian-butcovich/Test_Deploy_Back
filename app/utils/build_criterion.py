from sqlalchemy import desc


def build_criterion(params, filters, model_object, fetch_all=False):
    criterion = params.get('criterion')
    order_fields = {
        "fecha_min": (model_object.fecha, False),
        "fecha_max": (model_object.fecha, True),
        "monto_min": (model_object.monto, False),
        "monto_max": (model_object.monto, True),
        "created_on_min": (model_object.created_on, False),
        "created_on_max": (model_object.created_on, True),
        "last_updated_on_min": (model_object.last_updated_on, False),
        "last_updated_on_max": (model_object.last_updated_on, True),
    }

    if not criterion:
        query = model_object.query.filter(*filters)
    else:
        if criterion in order_fields:
            field, desc_order = order_fields[criterion]
            query = model_object.query.filter(*filters)
            if desc_order:
                query = query.order_by(desc(field))
            else:
                query = query.order_by(field)
        else:
            raise ValueError("Parametro invalido en 'criterion'")

    result = query.all() if fetch_all else query.first()
    return result