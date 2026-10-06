"""Build the iOS SwiftPM product and verify FFI exports after release stripping."""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def verify(flutter):
    root = Path(__file__).resolve().parent.parent
    source = root / "packages/isar_community_flutter_libs/ios"
    bindings = (root / "packages/isar_community/lib/src/native/bindings.dart").read_text()
    required = set(re.findall(r"'(isar_\w+)'", bindings))
    if not required:
        raise ValueError("No Isar FFI bindings found")

    with tempfile.TemporaryDirectory(prefix="isar-ios-release-") as directory:
        work = Path(directory)
        package = work / "isar_community_flutter_libs"
        shutil.copytree(
            source / "isar_community_flutter_libs", package,
            ignore=shutil.ignore_patterns("isar.xcframework", ".build", ".swiftpm"),
        )
        (package / "isar.xcframework").symlink_to(source / "isar.xcframework")
        framework = work / "FlutterFramework"
        framework.mkdir()
        (framework / "Flutter.xcframework").symlink_to(flutter.resolve())
        (framework / "Package.swift").write_text('''// swift-tools-version: 5.9
import PackageDescription
let package = Package(
    name: "FlutterFramework",
    products: [.library(name: "FlutterFramework", targets: ["Flutter"])],
    targets: [.binaryTarget(name: "Flutter", path: "Flutter.xcframework")]
)
''')
        result = subprocess.run(
            ["xcodebuild", "-scheme", "isar_community_flutter_libs",
             "-configuration", "Release", "-destination", "generic/platform=iOS",
             "-derivedDataPath", str(work / "DerivedData"),
             "CODE_SIGNING_ALLOWED=NO", "build"],
            cwd=package, text=True, capture_output=True,
        )
        if result.returncode:
            raise RuntimeError((result.stdout + result.stderr)[-6000:])
        products = work / "DerivedData/Build/Products/Release-iphoneos"
        candidates = list(products.rglob("isar-community-flutter-libs.framework"))
        if not candidates:
            raise ValueError("The iOS SwiftPM product must build a dynamic framework")
        binary = candidates[0] / "isar-community-flutter-libs"
        subprocess.run(["xcrun", "strip", "-x", "-S", "-D", str(binary)], check=True)
        exports = subprocess.check_output(
            ["xcrun", "dyld_info", "-exports", str(binary)], text=True
        )
        actual = set(re.findall(r"\b_(isar_\w+)\b", exports))
        missing = sorted(required - actual)
        if missing:
            raise ValueError(f"Release framework missing {len(missing)} FFI exports: {missing[:5]}")
        print(f"Verified {len(required)} Isar FFI exports after iOS SwiftPM release stripping.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify_ios_spm_release.py <Flutter.xcframework>")
    verify(Path(sys.argv[1]))
