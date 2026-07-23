import os, sys, textwrap

APP_CODE = ""
with open("ui/_app_template.py", "r", encoding="utf-8") as f:
    APP_CODE = f.read()

with open("ui/app.py", "w", encoding="utf-8") as f:
    f.write(APP_CODE)

import py_compile
try:
    py_compile.compile("ui/app.py", doraise=True)
    print("SYNTAX OK - Lines:", len(APP_CODE.splitlines()))
except py_compile.PyCompileError as e:
    print("SYNTAX ERROR:", e)
