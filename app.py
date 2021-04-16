from pathlib import Path

from flask import Flask, render_template, redirect, url_for

from projects.stahh_besger import stahh_besger
from projects.stahh_besger.routes import stahh_besger_bp

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')
app.register_blueprint(stahh_besger_bp)

required_directories = [Path(f'{app.instance_path}')]
required_directories.extend(stahh_besger.Constants.REQUIRED_DIRS)

for dir in required_directories: # todo check permissions & properly return Errors
    if not dir.exists():
        try: # todo properly check permissions first
            Path.mkdir(dir)
        except OSError:
            pass # todo proper exception feedback

@app.route('/')
def index():
    return redirect(url_for ('stahh_besger.stahh_besger_form'))

if __name__ == '__main__':
    app.run()
