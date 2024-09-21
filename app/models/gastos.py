from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as so
from app.db import db

class Gasto(db.Model):
    __tablename__ = 'gastos'
    _descripcion_char_limit = 256
    _tipo_char_limit = 32

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    descripcion: so.Mapped[str] = so.mapped_column(sa.String(_descripcion_char_limit))
    fecha: so.Mapped[datetime] = so.mapped_column(index=True, server_default=db.func.now())
    created_on: so.Mapped[datetime] = so.mapped_column(index=True, server_default=db.func.now())
    last_updated_on: so.Mapped[datetime] = so.mapped_column(index=True, server_default=db.func.now(),
                                                            server_onupdate=db.func.now())
    monto: so.Mapped[float] = so.mapped_column(sa.Float)
    tipo: so.Mapped[str] = so.mapped_column(sa.String(_tipo_char_limit))
    id_usuario: so.Mapped[int] = so.mapped_column(sa.ForeignKey("usuarios.id"))

    def __repr__(self):
        return f'Gasto ({self.monto}, {self.descripcion}, {self.id_usuario})'

    def __init__(self, usuario, descripcion, monto, tipo, fecha: datetime = None):
        self.id_usuario = usuario
        self.descripcion = descripcion
        self.monto = monto
        self.tipo = tipo
        if fecha:
            self.fecha = fecha
        else:
            self.fecha = db.func.now()
        self.created_on = db.func.now()
        self.last_updated_on = db.func.now()

    @property
    def tipo_char_limit(self):
        return self._tipo_char_limit

    @property
    def descripcion_char_limit(self):
        return self._descripcion_char_limit

    @classmethod
    def create(cls, ingreso):
        """Crea un gasto en la base de datos"""
        db.session.add(ingreso)
        db.session.commit()

    def update(self):
        """Actualiza un gasto en la base de datos"""
        db.session.commit()

    def delete(self):
        """Elimina un gasto de la base de datos"""
        db.session.delete(self)
        db.session.commit()