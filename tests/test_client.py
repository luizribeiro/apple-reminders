import unittest

from apple_reminders import Client
from apple_reminders.mock import MockRemindersTestHelper


class TestClient(unittest.TestCase):
    def test_create_list(self) -> None:
        with MockRemindersTestHelper():
            client = Client()
            list_id = client.create_list("Test List")

            # The list should be created successfully
            self.assertIsNotNone(list_id)
            self.assertIsInstance(list_id, str)

            # Cleanup explicitly
            client.cleanup()

    def test_add_reminder_to_list(self) -> None:
        with MockRemindersTestHelper():
            client = Client()
            list_id = client.create_list("Test List")

            # Add a reminder to the created list
            reminder_id = client.create_reminder(
                title="Test Reminder",
                list_id=list_id,
                notes="Some notes",
                due_date=None,
                priority=1,
            )

            # The reminder should be created successfully
            self.assertIsNotNone(reminder_id)
            self.assertIsInstance(reminder_id, str)

            # Cleanup explicitly
            client.cleanup()

    def test_search_reminders(self) -> None:
        with MockRemindersTestHelper():
            client = Client()
            list_id = client.create_list("Test List")
            client.create_reminder(
                title="Test Reminder 1",
                list_id=list_id,
                notes="Some notes",
                due_date=None,
                priority=1,
            )
            client.create_reminder(
                title="Another Reminder",
                list_id=list_id,
                notes="Different notes",
                due_date=None,
                priority=1,
            )

            # Search for reminders containing the word "Test"
            reminders = client.search_reminders("Test")
            self.assertEqual(len(reminders), 1)
            self.assertEqual(reminders[0].title, "Test Reminder 1")

            # Cleanup explicitly
            client.cleanup()

    def test_get_reminder(self) -> None:
        with MockRemindersTestHelper():
            client = Client()
            # Create a list and a reminder
            list_id = client.create_list("Test List")
            reminder_id = client.create_reminder(
                title="Test Reminder",
                list_id=list_id,
                notes="Some notes",
                due_date=None,
                priority=1,
            )

            # Get the specific reminder
            reminder = client.get_reminder(reminder_id)
            self.assertEqual(reminder.id, reminder_id)
            self.assertEqual(reminder.title, "Test Reminder")
            self.assertEqual(reminder.notes, "Some notes")
            self.assertEqual(reminder.priority, 1)
            self.assertEqual(reminder.list_id, list_id)

            # Try to get a non-existent reminder
            with self.assertRaises(RuntimeError):
                client.get_reminder("non-existent-id")

            # Cleanup explicitly
            client.cleanup()


if __name__ == "__main__":
    unittest.main()