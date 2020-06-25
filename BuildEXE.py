import os
import shutil

import PyInstaller.__main__

PyInstaller.__main__.run([
    '--name=%s' % "WinNATLoopback",
    '--onefile',
    '-r WinNATLoopback.exe.manifest,1',
    '--uac-admin',
    'WinNATLoopback.py'
])

shutil.rmtree("build")
os.remove("WinNATLoopback.spec")
