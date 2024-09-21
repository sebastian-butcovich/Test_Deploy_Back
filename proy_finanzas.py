import sqlalchemy as sa
import sqlalchemy.orm as so
from app.db import db
from app import app
from app.models.gastos import Gasto
from app.models.ingresos import Ingreso
from app.models.usuarios import Usuario
from app.models.feedback import Feedback


@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'Usuario': Usuario, 'Gasto': Gasto, 'Ingreso': Ingreso, 'Feedback': Feedback}
