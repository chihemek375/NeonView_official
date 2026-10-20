[app]
title = NeonVIEW
package.name = neonview
package.domain = org.neonview
source.dir = .
source.include_exts = py
version = 1.0

requirements = python3,kivy==2.3.0,pyjnius,android

orientation = all
fullscreen = 1

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
