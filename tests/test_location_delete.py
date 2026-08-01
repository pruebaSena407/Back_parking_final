import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from flask import Flask

from db import db
from models import location_model
from models.rate_model import Rate
from models import reservation_model
from models import registro_model


class DeleteLocationTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_delete_location_unlinks_dependent_tariffs_before_deleting(self):
        location = Mock()
        location.id_ubicacion = 1

        rate_query = Mock()
        rate_query.filter_by.return_value.update.return_value = 1

        reservation_list_query = Mock()
        reservation_list_query.filter_by.return_value.all.return_value = [Mock(id_reserva=10)]

        pago_query = Mock()
        pago_query.filter.return_value.delete.return_value = 1

        reservation_delete_query = Mock()
        reservation_delete_query.filter_by.return_value.delete.return_value = 1

        registro_query = Mock()
        registro_query.filter_by.return_value.update.return_value = 1

        with patch.object(location_model, "find_by_id", return_value=location), \
             patch.object(db.session, "query", side_effect=[rate_query, reservation_list_query, pago_query, reservation_delete_query, registro_query]) as query_mock, \
             patch.object(db.session, "delete") as delete_mock, \
             patch.object(db.session, "commit") as commit_mock, \
             patch.object(db.session, "rollback") as rollback_mock:
            location_model.delete_location(1)

        assert query_mock.call_count == 4
        rate_query.filter_by.assert_called_once_with(id_ubicacion=1)
        rate_query.filter_by.return_value.update.assert_called_once_with({Rate.id_ubicacion: None})
        reservation_list_query.filter_by.assert_called_once_with(id_ubicacion=1)
        pago_query.filter.assert_called_once()
        assert delete_mock.call_count == 2
        delete_mock.assert_any_call(location)
        commit_mock.assert_called_once()
        rollback_mock.assert_not_called()

    def test_delete_reserva_removes_related_payments_and_registros_before_deleting(self):
        reservation = Mock()
        reservation.id_reserva = 7

        pago_query = Mock()
        pago_query.filter.return_value.delete.return_value = 1

        registro_query = Mock()
        registro_query.filter_by.return_value.update.return_value = 1

        with patch.object(reservation_model, "find_by_id", return_value=reservation), \
             patch.object(db.session, "query", side_effect=[pago_query, registro_query]) as query_mock, \
             patch.object(db.session, "delete") as delete_mock, \
             patch.object(db.session, "commit") as commit_mock, \
             patch.object(db.session, "rollback") as rollback_mock:
            reservation_model.delete_reserva(7)

        assert query_mock.call_count == 2
        pago_query.filter.assert_called_once()
        registro_query.filter_by.assert_called_once_with(id_reserva=7)
        registro_query.filter_by.return_value.update.assert_called_once()
        delete_mock.assert_called_once_with(reservation)
        commit_mock.assert_called_once()
        rollback_mock.assert_not_called()

    def test_delete_registro_removes_related_incidents_and_objects_before_deleting(self):
        registro = Mock()
        registro.id_registro = 5

        incidente_query = Mock()
        incidente_query.filter_by.return_value.delete.return_value = 1

        objeto_query = Mock()
        objeto_query.filter_by.return_value.delete.return_value = 1

        with patch.object(registro_model, "find_by_id", return_value=registro), \
             patch.object(db.session, "query", side_effect=[incidente_query, objeto_query]) as query_mock, \
             patch.object(db.session, "delete") as delete_mock, \
             patch.object(db.session, "commit") as commit_mock, \
             patch.object(db.session, "rollback") as rollback_mock:
            registro_model.delete_registro(5)

        assert query_mock.call_count == 2
        incidente_query.filter_by.assert_called_once_with(id_registro=5)
        objeto_query.filter_by.assert_called_once_with(id_registro=5)
        delete_mock.assert_called_once_with(registro)
        commit_mock.assert_called_once()
        rollback_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
