# -*- coding: utf-8 -*-

from flask import Flask, request, session
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from flask_babel import Babel
from flask_babel import gettext as _
import logging
import os
from distutils.util import strtobool
from werkzeug.contrib.fixers import ProxyFix
import pytz
import locale
import calendar
import re

'''
    Application configs
'''

app = Flask(__name__, static_url_path="")
app.wsgi_app = ProxyFix(app.wsgi_app)
# default config file
app.config.from_object("config")
# override, private config
app.config.from_pyfile("config.py")

if strtobool(os.environ.get("SQLALCHEMY_LOG", "False")):
    sql_logger = logging.getLogger('sqlalchemy.engine')
    sql_logger.setLevel(logging.INFO)
    loggers = [sql_logger]
    for logger in loggers:
        for handler in app.logger.handlers:
            logger.addHandler(handler)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = app.config['LOGIN_MESSAGE']

csrf = CSRFProtect()
csrf.init_app(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command("db", MigrateCommand)

babel = Babel(app)

'''
    Localization
'''


@app.before_request
def set_locale():
    lang = request.args.get("lang")
    if lang and lang in ['zh', 'en']:
        session["lang"] = lang
    else:
        session["lang"] = 'zh'


@babel.localeselector
def get_locale():
    lang = session.get("lang")
    if lang:
        return lang

    lang = "{}".format(request.accept_languages.best_match(
        ['zh-tw', 'zh', 'en'])).split("-", 1)[0]
    return lang


#@cache.memoize(timeout=300)
def current_tzinfo():
    tzinfo = None
    tz_name = app.config.get("BABEL_DEFAULT_TIMEZONE")
    if tz_name:
        tzinfo = pytz.timezone(tz_name)
    return tzinfo

'''
    Jinja2 Template filters
'''


@app.template_filter()
def datetimefilter(value, format='%Y/%m/%d %H:%M %z'):
    # 2017/01/03 23:38 +0800
    if value:
        # convert UTC to local time-zone
        value = value.replace(tzinfo=pytz.utc).astimezone(current_tzinfo())
        return value.strftime(format)
    else:
        return ""


@app.template_filter()
def currencyfilter(value):
    # 1,234,567
    return "{:,}".format(int(value))


@app.template_filter()
def coursetimefilter(value):
    # 週二 (1610-1730)
    locale.setlocale(locale.LC_ALL, "zh_TW.UTF-8")
    result = u""
    classes = ("" + value).split(",")
    for c in classes:
        w, t = c.split("(")
        t = re.sub(r'[\(\)]', '', t)
        result = result + \
            u"{} ({})\n".format(calendar.day_name[
                int(w) - 1].decode("UTF-8"), t)

    return result.strip()


@app.template_filter()
def coursestatefilter(value):
    states = {
        0: _('Normal'),
        1: _('Suspended'),
        2: _('Test'),
    }
    return states[int(value)]


@app.template_filter()
def iconfilter(value):
    maps = [
        {'rule': r'(直排輪|溜冰)', 'icon': 'skating'},
        {'rule': r'(鍵盤合奏)', 'icon': 'piano'},
        {'rule': r'(跆拳道)', 'icon': 'taekwondo'},
        {'rule': r'(珠心算)', 'icon': 'abacus'},
        {'rule': r'(足球)', 'icon': 'football'},
        {'rule': r'(淡彩|彩繪)', 'icon': 'artist'},
        {'rule': r'(鉛筆)', 'icon': 'pencil'},
        {'rule': r'(舞)', 'icon': 'dancer'},
        {'rule': r'(羽球)', 'icon': 'shuttlecock'},
        {'rule': r'(口琴)', 'icon': 'harmonica'},
        {'rule': r'(射箭)', 'icon': 'target'},
        {'rule': r'(鍵盤)', 'icon': 'karate'},
        {'rule': r'(烏克麗麗)', 'icon': 'ukelele'},
        {'rule': r'(籃球)', 'icon': 'basketball'},
        {'rule': r'(竹笛)', 'icon': 'flute'},
        {'rule': r'(扯鈴)', 'icon': 'diabolo'},
        {'rule': r'(桌球)', 'icon': 'ping-pong'},
        {'rule': r'(圍棋)', 'icon': 'chess-board'},
        {'rule': r'(游泳)', 'icon': 'swimming-figure'},
        {'rule': r'(書法|毛筆)', 'icon': 'chinese-paper-writing'},
        {'rule': r'(素描)', 'icon': 'sketch'},
        {'rule': r'(油畫)', 'icon': 'paint-brush'},
        {'rule': r'(樹脂土)', 'icon': 'pottery-man'},
        {'rule': r'(壘球|棒球)', 'icon': 'baseball'},
        {'rule': r'(提琴)', 'icon': 'violin'},
        {'rule': r'(功夫|武術)', 'icon': 'martial-arts'},
        {'rule': r'(版畫|水墨)', 'icon': 'rgb'},
        {'rule': r'(體適能)', 'icon': 'gymnastics'},
    ]

    for m in maps:
        if re.search(m['rule'], value.encode("UTF-8")):
            return m['icon']

    return 'brainstorm'


@app.template_filter()
def studenttagfilter(value):
    tags = {
        'N': u'一般',
        'K': u'幼兒園',

        'D': u'舞蹈班',
        'H': u'口琴班舊生',
        'P': u'鍵盤舊生',

        'X': u'舞蹈班、鍵盤舊生',
        'Y': u'口琴班舊生、鍵盤舊生',
        'Z': u'舞蹈班、口琴班舊生',

        'DX': u'舞蹈班',
        'DZ': u'舞蹈班',
        'XZ': u'舞蹈班',
        'DXZ': u'舞蹈班',

        'HY': u'口琴班舊生',
        'HZ': u'口琴班舊生',
        'YZ': u'口琴班舊生',
        'HYZ': u'口琴班舊生',

        'PX': u'鍵盤舊生',
        'PY': u'鍵盤舊生',
        'XY': u'鍵盤舊生',
        'PXY': u'鍵盤舊生',
    }

    result = ""

    for c in list(value):
        if tags.has_key(c):
            result += tags[c]
        else:
            result += c

    return result

app.jinja_env.filters['datetimefilter'] = datetimefilter
app.jinja_env.filters['currencyfilter'] = currencyfilter
app.jinja_env.filters['coursetimefilter'] = coursetimefilter
app.jinja_env.filters['coursestatefilter'] = coursestatefilter
app.jinja_env.filters['iconfilter'] = iconfilter
app.jinja_env.filters['studenttagfilter'] = studenttagfilter

'''
    Models
'''

from models import *
from views import *
