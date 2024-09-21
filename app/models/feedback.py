from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as so
from app.db import db

class Feedback(db.Model):
    __tablename__ = 'feedback'
    _descripcion_char_limit = 256
    _tipo_char_limit = 32

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    descripcion: so.Mapped[str] = so.mapped_column(sa.String(_descripcion_char_limit))
    created_on: so.Mapped[datetime] = so.mapped_column(index=True, server_default=db.func.now())
    tipo: so.Mapped[str] = so.mapped_column(sa.String(_tipo_char_limit))
    id_usuario: so.Mapped[int] = so.mapped_column(sa.ForeignKey("usuarios.id"))

    def __repr__(self):
        return f'Feedback ({self.id}, {self.descripcion}, {self.created_on}, {self.id_usuario})'

    def __init__(self, usuario, descripcion, tipo):
        self.id_usuario = usuario
        self.descripcion = descripcion
        self.tipo = tipo
        self.created_on = db.func.now()

    @property
    def tipo_char_limit(self):
        return self._tipo_char_limit

    @property
    def descripcion_char_limit(self):
        return self._descripcion_char_limit

    @classmethod
    def create(cls, feedback):
        """Crea un feedback en la base de datos"""
        db.session.add(feedback)
        db.session.commit()

    def update(self):
        """Actualiza un feedback en la base de datos"""
        db.session.commit()

    def delete(self):
        """Elimina un feedback de la base de datos"""
        db.session.delete(self)
        db.session.commit()