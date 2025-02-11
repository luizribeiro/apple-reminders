// swift-tools-version:5.5
import PackageDescription

let package = Package(
    name: "reminders",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .library(
            name: "RemindersLib",
            type: .dynamic,
            targets: ["TodayReminders"]),
    ],
    dependencies: [],
    targets: [
        .target(
            name: "TodayReminders",
            dependencies: [],
            publicHeadersPath: "include"
        )
    ]
)