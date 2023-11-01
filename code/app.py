# -*- coding: utf-8 -*-

import os
import yaml
import json
from deepmerge import always_merger

from pymongo import MongoClient

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap5, SwitchField
from flask_wtf import FlaskForm, CSRFProtect
from wtforms.validators import DataRequired, Length, Regexp
from wtforms.fields import *

import secrets
import datetime
import humanize
import redis

app = Flask(__name__)

# config for application {{
baseCfg = {
    'mongo': {
        'url': 'mongodb://mongo:27017/',
        'db': 'coordinator',
    },
    'salt': 'CHANGE_ME',
    'auth': {
        'enable': True,
        'header': 'X-Email',
        'allow': [],
    },
}
configFile = os.environ.get('CONFIG_FILE', False)
if configFile:
    if os.path.isfile(configFile):
        try:
            with open(configFile, 'r') as ymlfile:
                yamlCfg = yaml.load(ymlfile,Loader=yaml.Loader)
        except Exception as e:
            app.logger.error('failed load config file: "%s", error: "%s"' % (configFile, e))
            exit(1)
        cfg = always_merger.merge(baseCfg,yamlCfg)
    else:
        cfg = baseCfg
else:
    cfg = baseCfg
app.logger.debug("cfg='%s'" % json.dumps(cfg,indent=4))
# }}

app.secret_key = secrets.token_urlsafe(16)
bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)

mongoClient = MongoClient(cfg['mongo']['url'])
mongoDb = mongoClient[cfg['mongo']['db']]
redisClient = redis.cluster.RedisCluster.from_url(cfg['redis']['url'])

@app.errorhandler(404)
def page_not_found(e):
    flash('Page not found!', 'warning')
    return render_template('error.html', errorCode='404', error='404'), 404

class SetLimitForm(FlaskForm):
    identity = TextAreaField('User identity:', validators=[DataRequired(), Length(1, 99999)])
    spaceLimitGb = TextAreaField('Space limit in Gb:', validators=[DataRequired(), Length(1, 99999)])
    reason = TextAreaField('Reason for change:', validators=[DataRequired(), Length(1, 99999)])
    submit = SubmitField()

class ShowLimitForm(FlaskForm):
    identity = TextAreaField('User identity:', validators=[DataRequired(), Length(1, 99999)])
    submit = SubmitField()

def getUserInfo(identity):
    collectionSpaces = mongoDb['spaces']
    try:
        data = collectionSpaces.find_one({"identity": identity })
    except Exception as e:
        app.logger.error("failed get user data from mongodb, url='%s', db='%s', collection='%s', identity='%s', error='%s'" % (cfg['mongo']['url'],cfg['mongo']['db'],'spaces',identity,str(e)))
        return None
    if data == None:
        try:
            data = collectionSpaces.find_one({"oldIdentity": identity })
        except Exception as e:
            app.logger.error("failed get user data from mongodb, url='%s', db='%s', collection='%s', identity='%s', error='%s'" % (cfg['mongo']['url'],cfg['mongo']['db'],'spaces',identity,str(e)))
            return None
    if data == None:
        app.logger.error("user not found in mongodb, url='%s', db='%s', collection='%s', identity='%s'" % (cfg['mongo']['url'],cfg['mongo']['db'],'spaces',identity))
        return None
    else:
        return data

def getFileLimit(identity):
    collectionFileLimit = mongoDb['fileLimit']
    try:
        data = collectionFileLimit.find_one({"_id": identity})
    except Exception as e:
        app.logger.error("failed get file limit from mongodb, url='%s', db='%s', collection='%s', error='%s'" % (cfg['mongo']['url'],cfg['mongo']['db'],'fileLimit',str(e)))
        return None
    if data == None:
        app.logger.error("file limit not found in mongodb, url='%s', db='%s', collection='%s', _id='%s'" % (cfg['mongo']['url'],cfg['mongo']['db'],'fileLimit',identity))
        return None
    else:
        return data

def getCurrentUsage(identity):
    userInfo = getUserInfo(identity)
    if userInfo == None:
        return None
    try:
        redisInfo = redisClient.hget('s:'+userInfo['_id'], 'size').decode()
    except Exception as e:
        app.logger.error("failed hget from redis, url='%s', identity='%s', _id='%s', error='%s'" % (cfg['redis']['url'],identity,userInfo['_id'],str(e)))
        return None

    return redisInfo

def setFileLimit(identity, limit, reason):
    collectionFileLimit = mongoDb['fileLimit']
    try:
        data = collectionFileLimit.update_one(
            { '_id': identity },
            { '$set':
                {
                    "limit": limit,
                    "updatedTime": int(datetime.datetime.now().timestamp()),
                    "reason": reason
                }
            },
            upsert=True
        )
    except Exception as e:
        app.logger.error("failed update file limit mongodb, url='%s', db='%s', collection='%s', error='%s'" % (cfg['mongo']['url'],cfg['mongo']['db'],'fileLimit', str(e)))
        return None,"failed update file limit mongodb, url='%s', db='%s', collection='%s', error='%s'" % (cfg['mongo']['url'],cfg['mongo']['db'],'fileLimit', str(e))

    return data,"succes"

def checkAuth(headers):
    if cfg['auth']['enable']:
        auth = headers.get(cfg['auth']['header'])
        app.logger.debug("auth header='%s'" % (auth))
        if auth in cfg['auth']['allow']:
            return True
        else:
            return False
    else:
        return True

@app.route('/')
def index():
    if not checkAuth(request.headers):
        return render_template('error.html', errorCode='401', error="user not authorized"), 401
    return render_template('index.html')

@app.route('/setLimit')
def setLimit():
    if not checkAuth(request.headers):
        return render_template('error.html', errorCode='401', error="user not authorized"), 401
    return render_template('setLimit.html', form=SetLimitForm())

@app.route('/showLimit')
def showLimit():
    if not checkAuth(request.headers):
        return render_template('error.html', errorCode='401', error="user not authorized"), 401
    return render_template('showLimit.html', form=ShowLimitForm())

@app.route('/showLimitResult',methods = ['POST'])
def showLimitResult():
    if not checkAuth(request.headers):
        return render_template('error.html', errorCode='401', error="user not authorized"), 401
    if request.method == 'POST':
        result = request.form
        identity = None
        for key,value in result.items():
            if key == 'identity':
                identity = value
    result = getFileLimit(identity)
    usage = getCurrentUsage(identity)
    app.logger.debug("usage='%s'" % usage)
    if result == None:
        return render_template("result.html", result = { "limit not found": "used default" })
    result['identity'] = identity
    if 'limit' in result:
        result['limit'] = humanize.naturalsize(value=result['limit'], binary=True)
    if 'updatedTime' in result:
        result['updatedTime'] = datetime.datetime.fromtimestamp(result['updatedTime']).astimezone()
    if usage:
        result['usage'] = humanize.naturalsize(value=usage, binary=True)
    app.logger.debug("result='%s'" % (result))
    return render_template("result.html", result = result)

@app.route('/updateLimit',methods = ['POST'])
def updateLimit():
    if not checkAuth(request.headers):
        return render_template('error.html', errorCode='401', error="user not authorized"), 401
    if request.method == 'POST':
        formData = request.form
        identity = None
        spaceLimitGb = None
        reason = None
        for key,value in formData.items():
            if key == 'identity':
                identity = value
            if key == 'spaceLimitGb':
                spaceLimitGb = value
            if key == 'reason':
                reason = value

        spaceLimitGb = int(spaceLimitGb) * 1024 * 1024 * 1024
        limitInfo = getFileLimit(identity)
        app.logger.debug("identity='%s', spaceLimitGb='%s', reason='%s', data='%s'" % (identity,spaceLimitGb,reason,limitInfo))
        if limitInfo and limitInfo['limit'] == spaceLimitGb:
            errorInfo = "new limit is equal to the current limit. new limit='%s', limitInfo='%s'" % (spaceLimitGb,limitInfo)
            app.logger.warning(errorInfo)
            return render_template('error.html', errorCode='200', error=errorInfo), 200
        data = setFileLimit(identity, spaceLimitGb, reason)
        if data[0]:
            result = { "status": "success" }
        else:
            result = { "status": "failed", "error": data[1] }
        return render_template("result.html", result = result)

@app.route("/logout")
def logout():
    response = redirect("/oauth2/sign_out?rd=" + url_for('index'), 302)
    return response

if __name__ == '__main__':
    app.run(debug = True)
