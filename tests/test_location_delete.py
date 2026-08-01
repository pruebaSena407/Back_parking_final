import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from flask import Flask

from db import db
from models import location_model
from models.rate_model import Rate


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

        mock_query = Mock()
        mock_query.filter_by.return_value.update.return_value = 1

        with patch.object(location_model, "find_by_id", return_value=location), \
             patch.object(db.session, "query", return_value=mock_query) as query_mock, \
             patch.object(db.session, "delete") as delete_mock, \
             patch.object(db.session, "commit") as commit_mock, \
             patch.object(db.session, "rollback") as rollback_mock:
            location_model.delete_location(1)

        query_mock.assert_called_once_with(Rate)
        mock_query.filter_by.assert_called_once_with(id_ubicacion=1)
        mock_query.filter_by.return_value.update.assert_called_once_with({Rate.id_ubicacion: None})
        delete_mock.assert_called_once_with(location)
        commit_mock.assert_called_once()
        rollback_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
