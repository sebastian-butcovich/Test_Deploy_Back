import re


def validar_email(email) -> bool:
    """Valida el formato de un correo electrónico"""
    # Expresión regular para validar el formato de un correo electrónico
    patron = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
    if re.match(patron, email):
        return True
    else:
        return False
