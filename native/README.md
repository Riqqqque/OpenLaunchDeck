# Native Helper

OpenLaunchDeck does not require the native helper. The Python app is the supported path.

This folder contains a small PyO3/maturin Rust crate for focused helpers where native code can offer a clear reliability or performance win:

- Button ID validation and conversion
- Profile text hashing
- SHA256 verification

If the native helper is not built, disabled, or cannot be imported, the app continues using the Python implementation.

Build from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1 -BuildNative
```
