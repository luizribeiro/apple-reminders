#ifndef RemindersLib_h
#define RemindersLib_h

#include <stdint.h>

// Opaque pointer to our reminders reader
typedef void* RemindersReaderRef;

// Create and destroy the reader
RemindersReaderRef CreateRemindersReader(void);
void DestroyRemindersReader(RemindersReaderRef reader);

// Basic reminder operations
char* GetReminders(RemindersReaderRef reader);
char* GetReminderLists(RemindersReaderRef reader);
char* GetRemindersInList(RemindersReaderRef reader, const char* listId);
char* SearchReminders(RemindersReaderRef reader, const char* query);

// Memory management
void FreeString(char* str);

#endif /* RemindersLib_h */