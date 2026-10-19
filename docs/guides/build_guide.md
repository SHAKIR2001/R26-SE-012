# Flutter Build and Distribution Guide

Status basis: repository configuration inspected on 2026-10-18. The Railway
URL below is the currently configured deployment target, but its live
availability must be checked before each run.

The important distinction is:

- A release APK for your own testing can be built now.
- A public/Play Store release still needs a private release signing key and secure handling of Gemini/Anthropic credentials.

## 1. Open the mobile project

In PowerShell:

```powershell
cd "D:\work\Year - 4\pepper\project\multimodal-pepper-ai-decision-support\mobile"

$flutter = "C:\test-by-me\flutter\flutter\bin\flutter.bat"
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
```

Check the toolchain and installed devices:

```powershell
& $flutter doctor
& $flutter devices
```

`flutter pub get` may download packages. If this checkout already has a usable
package cache, run it only when Flutter reports missing dependencies:

```powershell
& $flutter pub get
```

Do not run multiple Flutter build/test commands simultaneously. The first Android build can take several minutes while Gradle prepares dependencies.

## 2. Verify the hosted backend

```powershell
Invoke-RestMethod `
  "https://r26-se-012-production-7883.up.railway.app/api/v1/grading-forecast/health"

Invoke-RestMethod `
  "https://r26-se-012-production-7883.up.railway.app/api/v1/grading-forecast/ready"
```

Both should return successful responses before testing grading. `/health`
checks liveness; `/ready` must report `status: ready` and is the required gate.
The bare Railway domain may return 404; that does not replace these endpoint
checks.

## 3. Run on the Android emulator

Start the emulator, then check its identifier:

```powershell
& $flutter devices
```

Run using the hosted backend:

```powershell
& $flutter run `
  -d emulator-5554 `
  --dart-define-from-file=.env `
  --dart-define=PEPPER_API_BASE_URL=https://r26-se-012-production-7883.up.railway.app
```

Because this uses the hosted HTTPS backend, you do not need `adb reverse` or `10.0.2.2`.

## 4. Run on a physical Android device

Enable Developer Options and USB debugging, connect the phone, and confirm it is visible:

```powershell
& $adb devices
& $flutter devices
```

Then replace `<device-id>`:

```powershell
& $flutter run `
  -d <device-id> `
  --dart-define-from-file=.env `
  --dart-define=PEPPER_API_BASE_URL=https://r26-se-012-production-7883.up.railway.app
```

## 5. Run in Chrome

```powershell
& $flutter run `
  -d chrome `
  --dart-define-from-file=.env `
  --dart-define=PEPPER_API_BASE_URL=https://r26-se-012-production-7883.up.railway.app
```

Browser testing is suitable for controlled development, especially the grading/forecast backend workflow. Do not publicly deploy a web build containing Gemini or Anthropic keys because browser users can extract them.

## 6. Run without Gemini/Anthropic keys

The grading and forecasting component does not need those cloud keys. The three disease-detection components can use their local fallback behavior.

Simply omit the `.env` argument:

```powershell
& $flutter run `
  -d emulator-5554 `
  --dart-define=PEPPER_API_BASE_URL=https://r26-se-012-production-7883.up.railway.app
```

## 7. Validate before building

```powershell
& $flutter analyze
& $flutter test
```

If `flutter test` stalls, stop it with `Ctrl+C`, ensure no other Flutter command is running, and try again. Do not treat `flutter analyze` as proof that runtime tests passed.

## 8. Build a release APK for testing

Build one universal APK:

```powershell
& $flutter build apk `
  --release `
  --dart-define-from-file=.env `
  --dart-define=PEPPER_API_BASE_URL=https://r26-se-012-production-7883.up.railway.app
```

Output:

```text
mobile\build\app\outputs\flutter-apk\app-release.apk
```

Install it on a connected device:

```powershell
& $adb install -r "build\app\outputs\flutter-apk\app-release.apk"
```

If Android reports a signing conflict with an existing installation, uninstall
the existing development version first. This removes that app's local data,
including its saved History:

```powershell
& $adb uninstall com.example.mobile
& $adb install "build\app\outputs\flutter-apk\app-release.apk"
```

## 9. Build smaller architecture-specific APKs

```powershell
& $flutter build apk `
  --release `
  --split-per-abi `
  --dart-define-from-file=.env `
  --dart-define=PEPPER_API_BASE_URL=https://r26-se-012-production-7883.up.railway.app
```

The outputs will be under:

```text
build\app\outputs\flutter-apk\
```

Most current physical Android devices use:

```text
app-arm64-v8a-release.apk
```

## 10. Important: current signing limitation

The current `mobile/android/app/build.gradle.kts` signs release builds using the debug signing configuration.

That is acceptable for:

- Your own phone
- Emulator testing
- Supervisor demonstrations
- Internal controlled testing

It is not appropriate for:

- Google Play publishing
- Long-term public APK distribution
- Application updates under a permanent signing identity

## 11. Create a proper release-signing key

Create the key outside the repository:

```powershell
keytool -genkeypair -v `
  -keystore "$env:USERPROFILE\pepper-upload-keystore.jks" `
  -keyalg RSA `
  -keysize 2048 `
  -validity 10000 `
  -alias upload
```

Back up this keystore and its passwords securely. Losing it can prevent you from publishing compatible updates.

Create:

```text
mobile/android/key.properties
```

with:

```properties
storePassword=YOUR_STORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=upload
storeFile=C:\\Users\\YOUR_USERNAME\\pepper-upload-keystore.jks
```

Never commit this file or the keystore.

You must then update `mobile/android/app/build.gradle.kts` to load `key.properties` and replace:

```kotlin
signingConfig = signingConfigs.getByName("debug")
```

with a proper release signing configuration.

Also replace the placeholder identifier:

```text
com.example.mobile
```

with a permanent application ID that your team controls before publishing.

## 12. Build a Play Store App Bundle

After proper signing is configured:

```powershell
& $flutter build appbundle `
  --release `
  --build-name=1.0.0 `
  --build-number=1 `
  --dart-define-from-file=.env `
  --dart-define=PEPPER_API_BASE_URL=https://r26-se-012-production-7883.up.railway.app
```

Output:

```text
mobile\build\app\outputs\bundle\release\app-release.aab
```

Upload the `.aab` to Google Play Console, preferably through an Internal Testing track first.

For later releases:

```text
1.0.0+1
1.0.1+2
1.1.0+3
```

The build number must increase with every Play Store upload.

## 13. Critical cloud-key warning

`GEMINI_API_KEY` and `ANTHROPIC_API_KEY` supplied through Dart defines are compiled into the application. They can be recovered from a distributed APK or browser bundle.

Therefore:

- Using the keys in controlled development builds is acceptable temporarily.
- Do not distribute an unrestricted public APK containing valuable permanent keys.
- Restrict key usage and quotas where the provider supports it.
- For a genuine public release, route Gemini/Anthropic requests through an authenticated backend so the keys remain server-side.
- `PEPPER_API_BASE_URL` is not a secret and can safely remain a build-time definition.

## 14. Final release verification

Before distributing the APK, test on a physical device:

- Language selection and persistence
- Pest detection
- Leaf disease detection
- Berry disease detection
- Grade 1 routing to Grade 1 evidence
- Grade 2 routing to Grade 2 evidence
- Non-pepper rejection
- Poor-image rejection
- Uncertain-grade stopping before pricing
- Camera and gallery permissions
- App behavior without cloud keys
- Railway backend unavailable/timeout behavior
- History saves the completed result and original selected image locally
- Opening a History detail does not rerun inference or call the backend
- Clear-all removes the app's saved History records and image copies

The detailed application procedure is in
[PHASE7_APPLICATION_RUN_GUIDE.md](PHASE7_APPLICATION_RUN_GUIDE.md). The concise
current command index is in
[project_commands_guide.md](project_commands_guide.md).
