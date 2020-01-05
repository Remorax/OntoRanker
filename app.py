from flask import Flask

UPLOAD_FOLDER = 'uploads/'

app = Flask(__name__)
app.secret_key = b"}y\xf4\xfbq\x8e}k\xb36\xff K\t\xa5\xe9\x08teB\x8e\x90&F"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['TEMPLATES_AUTO_RELOAD'] = True