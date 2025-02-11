import unittest
from apple_reminders.test_helper import MockRemindersTestHelper
from apple_reminders import RemindersAPI

class TestRemindersAPIWithMock(unittest.TestCase):
    def test_create_list(self) -> None:
        with MockRemindersTestHelper():
            api = RemindersAPI()
            list_id = api.create_list("Test List")
            
            # The list should be created successfully
            self.assertIsNotNone(list_id)
            self.assertIsInstance(list_id, str)

            # Cleanup explicitly
            api.cleanup()

    def test_add_reminder_to_list(self) -> None:
        with MockRemindersTestHelper():
            api = RemindersAPI()
            list_id = api.create_list("Test List")

            # Add a reminder to the created list
            reminder_id = api.create_reminder(
                title="Test Reminder",
                list_id=list_id,
                notes="Some notes",
                due_date=None,
                priority=1
            )

            # The reminder should be created successfully
            self.assertIsNotNone(reminder_id)
            self.assertIsInstance(reminder_id, str)

            # Cleanup explicitly
            api.cleanup()

    def test_search_reminders(self) -> None:
        with MockRemindersTestHelper():
            api = RemindersAPI()
            list_id = api.create_list("Test List")
            api.create_reminder(
                title="Test Reminder 1",
                list_id=list_id,
                notes="Some notes",
                due_date=None,
                priority=1
            )
            api.create_reminder(
                title="Another Reminder",
                list_id=list_id,
                notes="Different notes",
                due_date=None,
                priority=1
            )

            # Search for reminders containing the word "Test"
            reminders = api.search_reminders("Test")
            self.assertEqual(len(reminders), 1)
            self.assertEqual(reminders[0].title, "Test Reminder 1")

            # Cleanup explicitly
            api.cleanup()

if __name__ == "__main__":
    unittest.main()