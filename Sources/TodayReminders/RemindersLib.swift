import EventKit
import Foundation

struct ReminderOutput: Codable {
    let id: String
    let title: String
    let dueDate: String?
    let completed: Bool
    let notes: String?
    let priority: Int
    let listId: String
    let creationDate: String?
    let modificationDate: String?
}

struct ReminderListOutput: Codable {
    let id: String
    let title: String
    let color: String?
}

class RemindersReader {
    private let eventStore = EKEventStore()
    private var accessGranted = false
    private let dateFormatter = ISO8601DateFormatter()
    
    init() {
        let semaphore = DispatchSemaphore(value: 0)
        eventStore.requestAccess(to: .reminder) { [weak self] granted, error in
            self?.accessGranted = granted
            semaphore.signal()
        }
        _ = semaphore.wait(timeout: .now() + 30.0)
    }
    
    private func convertColorToHex(_ cgColor: CGColor?) -> String? {
        guard let components = cgColor?.components else { return nil }
        guard components.count >= 3 else { return nil }
        
        let red = Int(components[0] * 255)
        let green = Int(components[1] * 255)
        let blue = Int(components[2] * 255)
        
        return String(format: "#%02X%02X%02X", red, green, blue)
    }
    
    func getReminderLists() -> String {
        guard accessGranted else {
            let error = ["error": "Access to Reminders was denied"]
            return (try? JSONEncoder().encode(error)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
        
        let lists = eventStore.calendars(for: .reminder)
        var outputLists: [ReminderListOutput] = []
        
        for list in lists {
            let output = ReminderListOutput(
                id: list.calendarIdentifier,
                title: list.title,
                color: convertColorToHex(list.cgColor)
            )
            outputLists.append(output)
        }
        
        return (try? JSONEncoder().encode(outputLists)).flatMap { String(data: $0, encoding: .utf8) }
            ?? "{\"error\": \"Failed to encode lists\"}"
    }
    
    private func convertReminderToOutput(_ reminder: EKReminder) -> ReminderOutput {
        return ReminderOutput(
            id: reminder.calendarItemIdentifier,
            title: reminder.title ?? "Untitled",
            dueDate: reminder.dueDateComponents?.date.map { self.dateFormatter.string(from: $0) },
            completed: reminder.isCompleted,
            notes: reminder.notes,
            priority: reminder.priority,
            listId: reminder.calendar.calendarIdentifier,
            creationDate: reminder.creationDate.map { self.dateFormatter.string(from: $0) },
            modificationDate: reminder.lastModifiedDate.map { self.dateFormatter.string(from: $0) }
        )
    }
    
    func getReminders() -> String {
        guard accessGranted else {
            let error = ["error": "Access to Reminders was denied"]
            return (try? JSONEncoder().encode(error)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
        
        let semaphore = DispatchSemaphore(value: 0)
        var result = ""
        
        let predicate = eventStore.predicateForReminders(in: nil)
        
        eventStore.fetchReminders(matching: predicate) { reminders in
            defer { semaphore.signal() }
            
            guard let reminders = reminders else {
                let error = ["error": "Failed to fetch reminders"]
                result = (try? JSONEncoder().encode(error)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
                return
            }
            
            var outputReminders: [ReminderOutput] = []
            for reminder in reminders {
                outputReminders.append(self.convertReminderToOutput(reminder))
            }
            
            result = (try? JSONEncoder().encode(outputReminders)).flatMap { String(data: $0, encoding: .utf8) }
                ?? "{\"error\": \"Failed to encode reminders\"}"
        }
        
        _ = semaphore.wait(timeout: .now() + 30.0)
        return result
    }
    
    func getRemindersInList(_ listId: String) -> String {
        guard accessGranted else {
            let error = ["error": "Access to Reminders was denied"]
            return (try? JSONEncoder().encode(error)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
        
        guard let calendar = eventStore.calendar(withIdentifier: listId) else {
            let error = ["error": "List not found"]
            return (try? JSONEncoder().encode(error)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
        
        let semaphore = DispatchSemaphore(value: 0)
        var result = ""
        
        let predicate = eventStore.predicateForReminders(in: [calendar])
        
        eventStore.fetchReminders(matching: predicate) { reminders in
            defer { semaphore.signal() }
            
            guard let reminders = reminders else {
                let error = ["error": "Failed to fetch reminders"]
                result = (try? JSONEncoder().encode(error)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
                return
            }
            
            var outputReminders: [ReminderOutput] = []
            for reminder in reminders {
                outputReminders.append(self.convertReminderToOutput(reminder))
            }
            
            result = (try? JSONEncoder().encode(outputReminders)).flatMap { String(data: $0, encoding: .utf8) }
                ?? "{\"error\": \"Failed to encode reminders\"}"
        }
        
        _ = semaphore.wait(timeout: .now() + 30.0)
        return result
    }
    
    func searchReminders(_ query: String) -> String {
        guard accessGranted else {
            let error = ["error": "Access to Reminders was denied"]
            return (try? JSONEncoder().encode(error)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
        
        let semaphore = DispatchSemaphore(value: 0)
        var result = ""
        
        let predicate = eventStore.predicateForReminders(in: nil)
        
        eventStore.fetchReminders(matching: predicate) { reminders in
            defer { semaphore.signal() }
            
            guard let reminders = reminders else {
                let error = ["error": "Failed to fetch reminders"]
                result = (try? JSONEncoder().encode(error)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
                return
            }
            
            var outputReminders: [ReminderOutput] = []
            for reminder in reminders {
                let searchString = [
                    reminder.title ?? "",
                    reminder.notes ?? ""
                ].joined(separator: " ").lowercased()
                
                if searchString.contains(query.lowercased()) {
                    outputReminders.append(self.convertReminderToOutput(reminder))
                }
            }
            
            result = (try? JSONEncoder().encode(outputReminders)).flatMap { String(data: $0, encoding: .utf8) }
                ?? "{\"error\": \"Failed to encode reminders\"}"
        }
        
        _ = semaphore.wait(timeout: .now() + 30.0)
        return result
    }
}

// MARK: - C Interface

@_cdecl("CreateRemindersReader")
public func CreateRemindersReader() -> UnsafeMutableRawPointer {
    let reader = RemindersReader()
    return Unmanaged.passRetained(reader).toOpaque()
}

@_cdecl("DestroyRemindersReader")
public func DestroyRemindersReader(_ readerRef: UnsafeMutableRawPointer) {
    Unmanaged<RemindersReader>.fromOpaque(readerRef).release()
}

@_cdecl("GetReminders")
public func GetReminders(_ readerRef: UnsafeMutableRawPointer) -> UnsafeMutablePointer<Int8> {
    let reader = Unmanaged<RemindersReader>.fromOpaque(readerRef).takeUnretainedValue()
    let result = reader.getReminders()
    return strdup(result)
}

@_cdecl("GetReminderLists")
public func GetReminderLists(_ readerRef: UnsafeMutableRawPointer) -> UnsafeMutablePointer<Int8> {
    let reader = Unmanaged<RemindersReader>.fromOpaque(readerRef).takeUnretainedValue()
    let result = reader.getReminderLists()
    return strdup(result)
}

@_cdecl("GetRemindersInList")
public func GetRemindersInList(_ readerRef: UnsafeMutableRawPointer, _ listId: UnsafePointer<Int8>) -> UnsafeMutablePointer<Int8> {
    let reader = Unmanaged<RemindersReader>.fromOpaque(readerRef).takeUnretainedValue()
    let listIdString = String(cString: listId)
    let result = reader.getRemindersInList(listIdString)
    return strdup(result)
}

@_cdecl("SearchReminders")
public func SearchReminders(_ readerRef: UnsafeMutableRawPointer, _ query: UnsafePointer<Int8>) -> UnsafeMutablePointer<Int8> {
    let reader = Unmanaged<RemindersReader>.fromOpaque(readerRef).takeUnretainedValue()
    let queryString = String(cString: query)
    let result = reader.searchReminders(queryString)
    return strdup(result)
}

@_cdecl("FreeString")
public func FreeString(_ ptr: UnsafeMutablePointer<Int8>) {
    free(ptr)
}