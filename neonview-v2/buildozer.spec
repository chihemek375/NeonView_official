[app]
title = NeonVIEW
package.name = neonview
package.domain = org.neonview
source.dir = .
source.include_exts = py
version = 1.0

requirements = python3,kivy==2.3.0,pyjnius,android
p4a.branch = v2024.01.21

orientation = all
fullscreen = 1

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 0
