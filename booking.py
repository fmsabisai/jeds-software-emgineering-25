import firebase_admin
from firebase_admin import credentials, db

# TODO: Replace with your actual Firebase project credentials
cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

print("Firebase Admin SDK initialized successfully.")

def create_booking(user_id, date, time, service):
  """Creates a new booking and saves it to Firebase Realtime Database.

  Args:
    user_id: The ID of the user making the booking.
    date: The date of the booking.
    time: The time of the booking.
    service: The service being booked.

  Returns:
    The ID of the newly created booking.
  """
  # Input validation
  if not all([user_id, date, time, service]):
    print("Error: Missing required fields for booking.")
    return None
  if not all(isinstance(arg, str) for arg in [user_id, date, time, service]):
    print("Error: All booking fields must be strings.")
    return None

  booking_data = {
      "user_id": user_id,
      "date": date,
      "time": time,
      "service": service,
      "status": "confirmed"  # Default status
  }

  try:
    ref = db.reference("bookings")
    new_booking_ref = ref.push(booking_data)
    return new_booking_ref.key
  except firebase_admin.exceptions.FirebaseError as e:
    print(f"An error occurred: {e}")
    return None

def get_booking(booking_id=None):
  """Retrieves a specific booking or all bookings from Firebase.

  Args:
    booking_id: Optional. The ID of the booking to retrieve.

  Returns:
    A dictionary representing the booking data if booking_id is provided,
    or a list of dictionaries if booking_id is not provided.
    Returns None if the booking is not found (for specific booking_id).
  """
  try:
    ref = db.reference("bookings")
    if booking_id:
      return ref.child(booking_id).get()
    else:
      return ref.get()
  except firebase_admin.exceptions.FirebaseError as e:
    print(f"An error occurred: {e}")
    return None

def update_booking(booking_id, updated_data):
  """Updates an existing booking in Firebase.

  Args:
    booking_id: The ID of the booking to update.
    updated_data: A dictionary containing the fields to update.

  Returns:
    True if the update was successful, False otherwise.
  """
  # Input validation
  if not booking_id or not isinstance(booking_id, str):
    print("Error: Invalid booking_id provided.")
    return False
  if not updated_data or not isinstance(updated_data, dict):
    print("Error: Invalid updated_data provided.")
    return False

  try:
    booking_ref = db.reference(f"bookings/{booking_id}")
    # First, check if the booking exists
    if booking_ref.get() is None:
      print(f"Error: Booking with ID {booking_id} not found. Cannot update.")
      return False

    # If booking exists, proceed with update
    booking_ref.update(updated_data)
    return True
  except firebase_admin.exceptions.FirebaseError as e:
    print(f"An error occurred during update: {e}")
    return False

def delete_booking(booking_id):
  """Deletes a booking from Firebase.

  Args:
    booking_id: The ID of the booking to delete.

  Returns:
    True if the deletion was successful, False otherwise.
  """
  try:
    booking_ref = db.reference(f"bookings/{booking_id}")
    # First, check if the booking exists
    if booking_ref.get() is None:
      print(f"Error: Booking with ID {booking_id} not found. Cannot delete.")
      return False

    # If booking exists, proceed with deletion
    booking_ref.delete()
    return True
  except firebase_admin.exceptions.FirebaseError as e:
    print(f"An error occurred during delete: {e}")
    return False
