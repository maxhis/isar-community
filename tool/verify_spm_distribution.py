"""Validate a packaged SwiftPM distribution without rebuilding Isar Core."""

import ctypes
import hashlib
import re
import sys
from pathlib import Path


def verify(tag):
    match = re.fullmatch(r"(\d+\.\d+\.\d+)-spm\.[1-9]\d*", tag)
    if not match:
        raise ValueError(f"Invalid SwiftPM distribution tag: {tag}")
    version = match.group(1)
    root = Path(__file__).resolve().parent.parent

    for name in (
        "isar_community",
        "isar_community_flutter_libs",
        "isar_community_generator",
    ):
        pubspec = (root / "packages" / name / "pubspec.yaml").read_text()
        package_version = re.search(r"^version:\s*(\S+)", pubspec, re.MULTILINE)
        if not package_version or package_version.group(1).strip("\"'") != version:
            raise ValueError(f"{name} does not match core version {version}")

    source = (root / "packages/isar_community/lib/src/isar.dart").read_text()
    if not re.search(rf"static const version = ['\"]{re.escape(version)}['\"];", source):
        raise ValueError(f"Isar.version does not match core version {version}")

    libs = root / "packages/isar_community_flutter_libs"
    for platform in ("ios", "macos"):
        package = libs / platform / "isar_community_flutter_libs"
        if not (package / "Package.swift").is_file():
            raise ValueError(f"Missing {platform} SwiftPM manifest")
        if not (package / "isar.xcframework/Info.plist").is_file():
            raise ValueError(f"Missing {platform} SwiftPM XCFramework")

    checksums = (root / "tool/spm_binaries.sha256").read_text().splitlines()
    for entry in checksums:
        expected, relative = entry.split("  ", 1)
        binary = root / relative
        if not binary.is_file():
            raise ValueError(f"Missing packaged binary: {relative}")
        if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Packaged binary checksum mismatch: {relative}")

    if sys.platform == "darwin":
        native = libs / "macos/libisar.dylib"
    elif sys.platform.startswith("linux"):
        native = libs / "linux/libisar.so"
    else:
        raise ValueError(f"Unsupported validation platform: {sys.platform}")
    library = ctypes.CDLL(str(native))
    library.isar_version.restype = ctypes.c_char_p
    native_version = library.isar_version().decode("ascii")
    if native_version != version:
        raise ValueError(f"Native core version {native_version} != {version}")

    print(f"Verified {tag}: three packages and native core at {version}.")
    print(f"Verified SwiftPM XCFrameworks and {len(checksums)} packaged artifacts.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify_spm_distribution.py <version-spm.revision>")
    verify(sys.argv[1])
