# Timebox Installation

Here is the list of instructions I followed to build Timebox (on an M1 Mac):

1. `env PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install -v 3.8.10`
   i. Set up virtualenv, `pip install rumps`
2. `brew install create-dmg`
3. `python setup.py py2app`
   i. It would be in `dist/Timebox.app
4.

```
create-dmg \
  --volname "Timebox Installer" \
  --volicon "icon.icns" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --app-drop-link 600 185 \
  "Timebox-Installer.dmg" \
  "dist/"
```
