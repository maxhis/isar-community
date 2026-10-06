### Flutter binaries for the [Isar Database](https://github.com/isar-community/isar) please go there for documentation.

The `codex/isar-swiftpm-release-ready` branch includes native binaries so it can
be used directly as a Git dependency without a separate download step. The iOS
and macOS Swift packages use the bundled XCFrameworks; Android, Linux, Windows,
and CocoaPods retain their existing binary locations.

The binaries come from the official `isar_community_flutter_libs` 3.3.2 package:
https://pub.dev/api/archives/isar_community_flutter_libs-3.3.2.tar.gz
Archive SHA-256: `c44340fa38c81ef16d924202d443bbe799cde4826be9a31a9dc92ee612e1966f`.
The macOS XCFramework wraps the package's unchanged universal `libisar.dylib`.
