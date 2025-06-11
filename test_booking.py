import unittest
from unittest import mock
import booking # Assuming booking.py is in the same directory or accessible in PYTHONPATH

# Mock firebase_admin before it's imported by booking.py
# This is a common pattern for mocking modules that are initialized at import time.
firebase_admin_mock = mock.MagicMock()
db_mock = mock.MagicMock()
firebase_admin_mock.db = db_mock
firebase_admin_mock.credentials = mock.MagicMock() # Mock credentials too

# This is a bit of a hack to replace the actual firebase_admin module
# with our mock BEFORE booking.py tries to import and use it.
import sys
sys.modules['firebase_admin'] = firebase_admin_mock
sys.modules['firebase_admin.db'] = db_mock
sys.modules['firebase_admin.credentials'] = firebase_admin_mock.credentials


class TestBooking(unittest.TestCase):

    @mock.patch('booking.db.reference') # Patch db.reference within the booking module
    def test_create_booking_success(self, mock_db_reference):
        # Arrange
        mock_push_ref = mock.MagicMock()
        mock_push_ref.key = "test_booking_id_123"

        mock_ref_instance = mock.MagicMock()
        mock_ref_instance.push.return_value = mock_push_ref
        mock_db_reference.return_value = mock_ref_instance

        user_id = "user123"
        date = "2024-01-15"
        time = "10:00"
        service = "Haircut"
        expected_booking_data = {
            "user_id": user_id,
            "date": date,
            "time": time,
            "service": service,
            "status": "confirmed"
        }

        # Act
        # Need to reload booking after mocks are in place for it to use them
        import importlib
        importlib.reload(booking)

        booking_id = booking.create_booking(user_id, date, time, service)

        # Assert
        self.assertIsNotNone(booking_id)
        self.assertEqual(booking_id, "test_booking_id_123")
        mock_db_reference.assert_called_once_with("bookings")
        mock_ref_instance.push.assert_called_once_with(expected_booking_data)

        # Ensure firebase_admin.initialize_app was called (implicitly by booking.py)
        # We can check this on our top-level mock.
        # Note: The actual call happens when booking.py is first imported/reloaded.
        firebase_admin_mock.initialize_app.assert_called()

    @mock.patch('booking.db.reference')
    def test_get_booking_by_id_success(self, mock_db_reference):
        # Arrange
        sample_booking_id = "booking_abc"
        expected_booking_data = {"user_id": "user789", "date": "2024-02-01", "time": "14:00", "service": "Manicure"}

        mock_child_ref = mock.MagicMock()
        mock_child_ref.get.return_value = expected_booking_data

        mock_ref_instance = mock.MagicMock()
        mock_ref_instance.child.return_value = mock_child_ref
        mock_db_reference.return_value = mock_ref_instance

        import importlib
        importlib.reload(booking)

        # Act
        retrieved_booking = booking.get_booking(sample_booking_id)

        # Assert
        self.assertEqual(retrieved_booking, expected_booking_data)
        mock_db_reference.assert_called_once_with("bookings")
        mock_ref_instance.child.assert_called_once_with(sample_booking_id)
        mock_child_ref.get.assert_called_once()

    @mock.patch('booking.db.reference')
    def test_get_booking_by_id_not_found(self, mock_db_reference):
        # Arrange
        non_existent_booking_id = "booking_xyz"

        mock_child_ref = mock.MagicMock()
        mock_child_ref.get.return_value = None # Simulate not found

        mock_ref_instance = mock.MagicMock()
        mock_ref_instance.child.return_value = mock_child_ref
        mock_db_reference.return_value = mock_ref_instance

        import importlib
        importlib.reload(booking)

        # Act
        retrieved_booking = booking.get_booking(non_existent_booking_id)

        # Assert
        self.assertIsNone(retrieved_booking)
        mock_db_reference.assert_called_once_with("bookings")
        mock_ref_instance.child.assert_called_once_with(non_existent_booking_id)
        mock_child_ref.get.assert_called_once()

    @mock.patch('booking.db.reference')
    def test_get_all_bookings_success(self, mock_db_reference):
        # Arrange
        all_bookings_data = {
            "booking1": {"user_id": "user1", "service": "ServiceA"},
            "booking2": {"user_id": "user2", "service": "ServiceB"}
        }
        mock_ref_instance = mock.MagicMock()
        mock_ref_instance.get.return_value = all_bookings_data
        mock_db_reference.return_value = mock_ref_instance

        import importlib
        importlib.reload(booking)

        # Act
        retrieved_bookings = booking.get_booking()

        # Assert
        self.assertEqual(retrieved_bookings, all_bookings_data)
        mock_db_reference.assert_called_once_with("bookings")
        mock_ref_instance.get.assert_called_once()
        mock_ref_instance.child.assert_not_called() # Ensure child() wasn't called

    @mock.patch('booking.db.reference')
    def test_get_all_bookings_no_bookings(self, mock_db_reference):
        # Arrange
        mock_ref_instance = mock.MagicMock()
        mock_ref_instance.get.return_value = None # Or {} depending on Firebase behavior for empty node
        mock_db_reference.return_value = mock_ref_instance

        import importlib
        importlib.reload(booking)

        # Act
        retrieved_bookings = booking.get_booking()

        # Assert
        self.assertIsNone(retrieved_bookings) # Based on current get_booking, it returns None
        mock_db_reference.assert_called_once_with("bookings")
        mock_ref_instance.get.assert_called_once()

    @mock.patch('booking.db.reference')
    def test_update_booking_success(self, mock_db_reference):
        # Arrange
        booking_id = "booking_to_update_123"
        updated_data = {"status": "cancelled", "reason": "User request"}

        mock_booking_ref = mock.MagicMock()
        mock_booking_ref.get.return_value = {"user_id": "test_user"} # Simulate booking exists
        mock_db_reference.return_value = mock_booking_ref

        import importlib
        importlib.reload(booking)

        # Act
        result = booking.update_booking(booking_id, updated_data)

        # Assert
        self.assertTrue(result)
        mock_db_reference.assert_called_once_with(f"bookings/{booking_id}")
        mock_booking_ref.get.assert_called_once()
        mock_booking_ref.update.assert_called_once_with(updated_data)

    @mock.patch('booking.db.reference')
    def test_update_booking_non_existent(self, mock_db_reference):
        # Arrange
        booking_id = "non_existent_booking_789"
        updated_data = {"status": "cancelled"}

        mock_booking_ref = mock.MagicMock()
        mock_booking_ref.get.return_value = None # Simulate booking does NOT exist
        mock_db_reference.return_value = mock_booking_ref

        import importlib
        importlib.reload(booking)

        # Act
        result = booking.update_booking(booking_id, updated_data)

        # Assert
        self.assertFalse(result)
        mock_db_reference.assert_called_once_with(f"bookings/{booking_id}")
        mock_booking_ref.get.assert_called_once()
        mock_booking_ref.update.assert_not_called() # Update should not be called

    @mock.patch('booking.db.reference')
    def test_update_booking_firebase_error_on_get(self, mock_db_reference):
        # Arrange
        booking_id = "booking_error_get_456"
        updated_data = {"status": "pending"}

        mock_booking_ref = mock.MagicMock()
        # Simulate a FirebaseError during the get call
        mock_booking_ref.get.side_effect = firebase_admin_mock.exceptions.FirebaseError("mock_code_get", "Mock Firebase get error")
        mock_db_reference.return_value = mock_booking_ref

        import importlib
        importlib.reload(booking)

        # Act
        result = booking.update_booking(booking_id, updated_data)

        # Assert
        self.assertFalse(result)
        mock_db_reference.assert_called_once_with(f"bookings/{booking_id}")
        mock_booking_ref.get.assert_called_once()
        mock_booking_ref.update.assert_not_called()

    @mock.patch('booking.db.reference')
    def test_update_booking_firebase_error_on_update(self, mock_db_reference):
        # Arrange
        booking_id = "booking_error_update_123"
        updated_data = {"status": "pending"}

        mock_booking_ref = mock.MagicMock()
        mock_booking_ref.get.return_value = {"user_id": "test_user"} # Simulate booking exists
        # Simulate a FirebaseError during update
        mock_booking_ref.update.side_effect = firebase_admin_mock.exceptions.FirebaseError("mock_code_update", "Mock Firebase update error")
        mock_db_reference.return_value = mock_booking_ref

        import importlib
        importlib.reload(booking)

        # Act
        result = booking.update_booking(booking_id, updated_data)

        # Assert
        self.assertFalse(result)
        mock_db_reference.assert_called_once_with(f"bookings/{booking_id}")
        mock_booking_ref.get.assert_called_once()
        mock_booking_ref.update.assert_called_once_with(updated_data)

    @mock.patch('booking.db.reference')
    def test_delete_booking_success(self, mock_db_reference):
        # Arrange
        booking_id = "booking_to_delete_123"

        mock_booking_ref = mock.MagicMock()
        mock_booking_ref.get.return_value = {"user_id": "test_user"} # Simulate booking exists
        mock_db_reference.return_value = mock_booking_ref

        import importlib
        importlib.reload(booking)

        # Act
        result = booking.delete_booking(booking_id)

        # Assert
        self.assertTrue(result)
        mock_db_reference.assert_called_once_with(f"bookings/{booking_id}")
        mock_booking_ref.get.assert_called_once()
        mock_booking_ref.delete.assert_called_once()

    @mock.patch('booking.db.reference')
    def test_delete_booking_non_existent(self, mock_db_reference):
        # Arrange
        booking_id = "non_existent_booking_456"

        mock_booking_ref = mock.MagicMock()
        mock_booking_ref.get.return_value = None # Simulate booking does NOT exist
        mock_db_reference.return_value = mock_booking_ref

        import importlib
        importlib.reload(booking)

        # Act
        result = booking.delete_booking(booking_id)

        # Assert
        self.assertFalse(result)
        mock_db_reference.assert_called_once_with(f"bookings/{booking_id}")
        mock_booking_ref.get.assert_called_once()
        mock_booking_ref.delete.assert_not_called()

    @mock.patch('booking.db.reference')
    def test_delete_booking_firebase_error_on_get(self, mock_db_reference):
        # Arrange
        booking_id = "booking_error_get_789"

        mock_booking_ref = mock.MagicMock()
        mock_booking_ref.get.side_effect = firebase_admin_mock.exceptions.FirebaseError("mock_code_get", "Mock Firebase get error")
        mock_db_reference.return_value = mock_booking_ref

        import importlib
        importlib.reload(booking)

        # Act
        result = booking.delete_booking(booking_id)

        # Assert
        self.assertFalse(result)
        mock_db_reference.assert_called_once_with(f"bookings/{booking_id}")
        mock_booking_ref.get.assert_called_once()
        mock_booking_ref.delete.assert_not_called()

    @mock.patch('booking.db.reference')
    def test_delete_booking_firebase_error_on_delete(self, mock_db_reference):
        # Arrange
        booking_id = "booking_error_delete_012"

        mock_booking_ref = mock.MagicMock()
        mock_booking_ref.get.return_value = {"user_id": "test_user"} # Simulate booking exists
        mock_booking_ref.delete.side_effect = firebase_admin_mock.exceptions.FirebaseError("mock_code_delete", "Mock Firebase delete error")
        mock_db_reference.return_value = mock_booking_ref

        import importlib
        importlib.reload(booking)

        # Act
        result = booking.delete_booking(booking_id)

        # Assert
        self.assertFalse(result)
        mock_db_reference.assert_called_once_with(f"bookings/{booking_id}")
        mock_booking_ref.get.assert_called_once()
        mock_booking_ref.delete.assert_called_once()

if __name__ == '__main__':
    unittest.main()
