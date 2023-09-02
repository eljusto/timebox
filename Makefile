env: 
	env PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install -v 3.11.5
	
deps:
	pyenv exec pip install -r requirements.txt

run:
	./dist/Timebox.app/Contents/MacOS/Timebox

compile:
	pyenv exec python ./setup.py py2app

dmg:
	brew install create-dmg
	create-dmg \
  --volname "T3 Installer" \
  --volicon "icon.icns" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --app-drop-link 600 185 \
  "T3-Installer.dmg" \
  "dist/"
