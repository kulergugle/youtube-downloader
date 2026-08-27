[app]
title = YouTube Downloader
package.name = ytdownloader
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,yt-dlp
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 28c
android.archs = arm64-v8a
android.private_storage = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
