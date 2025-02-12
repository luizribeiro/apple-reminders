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

struct CreateReminderInput: Codable {
    let title: String
    let notes: String?
    let dueDate: String?
    let priority: Int?
    let listId: String
}

struct CreateListInput: Codable {
    let title: String
    let color: String?
}

struct OperationResult: Codable {
    let success: Bool
    let error: String?
    let id: String?
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

    func createReminder(_ inputJson: String) -> String {
        guard accessGranted else {
            let result = OperationResult(success: false, error: "Access to Reminders was denied", id: nil)
            return (try? JSONEncoder().encode(result)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
        
        guard let input = try? JSONDecoder().decode(CreateReminderInput.self, from: inputJson.data(using: .utf8)!) else {
            let result = OperationResult(success: false, error: "Invalid input format", id: nil)
            return (try? JSONEncoder().encode(result)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
        
        guard let calendar = eventStore.calendar(withIdentifier: input.listId) else {
            let result = OperationResult(success: false, error: "List not found", id: nil)
            return (try? JSONEncoder().encode(result)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
        
        let reminder = EKReminder(eventStore: eventStore)
        reminder.calendar = calendar
        reminder.title = input.title
        reminder.notes = input.notes
        
        if let dueDateStr = input.dueDate,
           let dueDate = dateFormatter.date(from: dueDateStr) {
            reminder.dueDateComponents = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: dueDate)
        }
        
        if let priority = input.priority {
            reminder.priority = priority
        }
        
        do {
            try eventStore.save(reminder, commit: true)
            let result = OperationResult(success: true, error: nil, id: reminder.calendarItemIdentifier)
            return (try? JSONEncoder().encode(result)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        } catch {
            let result = OperationResult(success: false, error: error.localizedDescription, id: nil)
            return (try? JSONEncoder().encode(result)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
    }

    func createList(_ inputJson: String) -> String {
        guard accessGranted else {
            let result = OperationResult(success: false, error: "Access to Reminders was denied", id: nil)
            return (try? JSONEncoder().encode(result)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
        
        guard let input = try? JSONDecoder().decode(CreateListInput.self, from: inputJson.data(using: .utf8)!) else {
            let result = OperationResult(success: false, error: "Invalid input format", id: nil)
            return (try? JSONEncoder().encode(result)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
        
        let list = EKCalendar(for: .reminder, eventStore: eventStore)
        list.title = input.title
        
        if let colorHex = input.color {
            list.cgColor = hexStringToColor(colorHex)
        }
        
        // Get default source
        guard let source = eventStore.defaultCalendarForNewReminders()?.source else {
            let result = OperationResult(success: false, error: "Failed to get default calendar source", id: nil)
            return (try? JSONEncoder().encode(result)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
        
        list.source = source
        
        do {
            try eventStore.saveCalendar(list, commit: true)
            let result = OperationResult(success: true, error: nil, id: list.calendarIdentifier)
            return (try? JSONEncoder().encode(result)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        } catch {
            let result = OperationResult(success: false, error: error.localizedDescription, id: nil)
            return (try? JSONEncoder().encode(result)).flatMap { String(data: $0, encoding: .utf8) } ?? "{\"error\": \"Unknown error\"}"
        }
    }

    private func hexStringToColor(_ hex: String) -> CGColor? {
        var hexSanitized = hex.trimmingCharacters(in: .whitespacesAndNewlines)
        hexSanitized = hexSanitized.replacingOccurrences(of: "#", with: "")
        
        var rgb: UInt64 = 0
        
        guard Scanner(string: hexSanitized).scanHexInt64(&rgb) else {
            return nil
        }
        
        let r = CGFloat((rgb & 0xFF0000) >> 16) / 255.0
        let g = CGFloat((rgb & 0x00FF00) >> 8) / 255.0
        let b = CGFloat(rgb & 0x0000FF) / 255.0
        
        return CGColor(red: r, green: g, blue: b, alpha: 1.0)
    }

    private func getReminder(_ reminderId: String) -> Result<EKReminder, Error> {
        guard accessGranted else {
            return .failure(NSError(domain: "", code: -1, userInfo: [NSLocalizedDescriptionKey: "Access to Reminders was denied"]))
        }

        let semaphore = DispatchSemaphore(value: 0)
        var fetchResult: Result<EKReminder, Error> = .failure(NSError(domain: "", code: -1, userInfo: [NSLocalizedDescriptionKey: "Reminder not found"]))

        let predicate = eventStore.predicateForReminders(in: nil)
        eventStore.fetchReminders(matching: predicate) { reminders in
            defer { semaphore.signal() }
            
            if let reminders = reminders,
               let reminder = reminders.first(where: { $0.calendarItemIdentifier == reminderId }) {
                fetchResult = .success(reminder)
            }
        }
        
        _ = semaphore.wait(timeout: .now() + 30.0)
        return fetchResult
    }

    func completeReminder(_ reminderId: String) -> String {
        let result: OperationResult
        
        switch getReminder(reminderId) {
        case .success(let reminder):
            reminder.isCompleted = true
            do {
                try eventStore.save(reminder, commit: true)
                result = OperationResult(success: true, error: nil, id: reminder.calendarItemIdentifier)
            } catch {
                result = OperationResult(success: false, error: error.localizedDescription, id: nil)
            }
        case .failure(let error):
            result = OperationResult(success: false, error: error.localizedDescription, id: nil)
        }
        
        return (try? JSONEncoder().encode(result)).flatMap { String(data: $0, encoding: .utf8) }
            ?? "{\"error\": \"Failed to encode result\"}"
    }

    func uncompleteReminder(_ reminderId: String) -> String {
        let result: OperationResult
        
        switch getReminder(reminderId) {
        case .success(let reminder):
            reminder.isCompleted = false
            do {
                try eventStore.save(reminder, commit: true)
                result = OperationResult(success: true, error: nil, id: reminder.calendarItemIdentifier)
            } catch {
                result = OperationResult(success: false, error: error.localizedDescription, id: nil)
            }
        case .failure(let error):
            result = OperationResult(success: false, error: error.localizedDescription, id: nil)
        }
        
        return (try? JSONEncoder().encode(result)).flatMap { String(data: $0, encoding: .utf8) }
            ?? "{\"error\": \"Failed to encode result\"}"
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

@_cdecl("CreateReminder")
public func CreateReminder(_ readerRef: UnsafeMutableRawPointer, _ inputJson: UnsafePointer<Int8>) -> UnsafeMutablePointer<Int8> {
    let reader = Unmanaged<RemindersReader>.fromOpaque(readerRef).takeUnretainedValue()
    let input = String(cString: inputJson)
    let result = reader.createReminder(input)
    return strdup(result)
}

@_cdecl("CreateList")
public func CreateList(_ readerRef: UnsafeMutableRawPointer, _ inputJson: UnsafePointer<Int8>) -> UnsafeMutablePointer<Int8> {
    let reader = Unmanaged<RemindersReader>.fromOpaque(readerRef).takeUnretainedValue()
    let input = String(cString: inputJson)
    let result = reader.createList(input)
    return strdup(result)
}

@_cdecl("CompleteReminder")
public func CompleteReminder(_ readerRef: UnsafeMutableRawPointer, _ reminderId: UnsafePointer<Int8>) -> UnsafeMutablePointer<Int8> {
    let reader = Unmanaged<RemindersReader>.fromOpaque(readerRef).takeUnretainedValue()
    let reminderIdString = String(cString: reminderId)
    let result = reader.completeReminder(reminderIdString)
    return strdup(result)
}

@_cdecl("UncompleteReminder")
public func UncompleteReminder(_ readerRef: UnsafeMutableRawPointer, _ reminderId: UnsafePointer<Int8>) -> UnsafeMutablePointer<Int8> {
    let reader = Unmanaged<RemindersReader>.fromOpaque(readerRef).takeUnretainedValue()
    let reminderIdString = String(cString: reminderId)
    let result = reader.uncompleteReminder(reminderIdString)
    return strdup(result)
}

@_cdecl("FreeString")
public func FreeString(_ ptr: UnsafeMutablePointer<Int8>) {
    free(ptr)
}