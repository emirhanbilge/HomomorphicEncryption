#!/usr/bin/env python
import os
import time
from flask import Flask, abort, request, jsonify, g, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
import os
import urllib.request
from flask import Flask, request, redirect, jsonify
from werkzeug.utils import secure_filename
from Pyfhel import Pyfhel, PyPtxt, PyCtxt
from flask import Flask,send_from_directory
from shutil import copyfile
import requests

# initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
UPLOAD_FOLDER = '/home/ebb/Desktop/Crypto/server'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

basePath = "/home/ebb/Desktop/Crypto/server/"

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))
    iban = db.Column(db.String(20))

    def setIban(self, iban):
        self.iban = iban

    def getIban(self):
        return self.iban

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expires_in=600):
        return jwt.encode(
            {'id': self.id, 'exp': time.time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_auth_token(token):
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'],
                              algorithms=['HS256'])
        except:
            return
        return User.query.get(data['id'])


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/api/users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    iban = request.json.get('iban')
    if username is None or password is None or iban is None:
        abort(400)    # missing arguments
    if User.query.filter_by(username=username).first() is not None and User.query.filter_by(iban=iban).first():
        abort(400)    # existing user
    user = User(username=username)
    user.hash_password(password)
    user.setIban(iban)
    db.session.add(user)
    db.session.commit()
    directory = str(username)
    #parent_dir = "\home\ebb\Desktop\Crypto\server\\"+directory
    #print("Director : ",parent_dir)
    path = os.path.join(directory)     
    try:
        os.mkdir(path) 
    except Exception as e:
        print(e)
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('upload_file', id=user.id, _external=True)})

    


ALLOWED_EXTENSIONS = set(['txt', 'ctxt', 'con', 'pk'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/fileUpload' , methods=['POST'])
@auth.login_required
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        resp.status_code = 400
        return resp
    file = request.files['file']
    if file.filename == '':
        resp = jsonify({'message' : 'No file selected for uploading'})
        resp.status_code = 400

        return resp
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join((app.config['UPLOAD_FOLDER']+'/'+str(g.user.username)), filename))
        resp = jsonify({'message' : 'File successfully uploaded'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message' : 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'})
        resp.status_code = 400
        return resp

@app.route('/api/balance' , methods=['GET'])
@auth.login_required
def sendBalance():
    userPath =  basePath+ "/"+g.user.username+"/"
    return send_from_directory(userPath,filename="balance.ctxt", as_attachment=True)


@app.route('/api/transferFile' , methods=['GET'])
@auth.login_required
def sendTransferFile():
    userPath =  basePath+ "/"+g.user.username+"/"
    return send_from_directory(userPath,filename="transfer.txt", as_attachment=True)


#$ Para yatırma
@app.route('/api/deposit' , methods=['POST'])
@auth.login_required
def deposit():
    
    userPath =  basePath+g.user.username+"/"
    print(userPath)
    os.chdir(userPath)
    HE_Cl = Pyfhel()    
    HE_Cl.restoreContext(userPath+(g.user.username+".con"))
    HE_Cl.restorepublicKey(userPath+(g.user.username+".pk"))
    # loading the two ciphertexts. There is clearly potential for improvement here
    userBalance = PyCtxt(pyfhel=HE_Cl, fileName=(userPath+"balance.ctxt"), encoding=float)
    tempMoney = PyCtxt(pyfhel=HE_Cl, fileName=(userPath+"temp.ctxt"), encoding=float)
    userBalanceNew  = (userBalance + tempMoney) 
    userBalanceNew.to_file(userPath+"balance.ctxt")
    os.remove(userPath+"temp.ctxt")
    resp = jsonify({'message' : 'Deopsit successfully '})
    resp.status_code = 201
    return resp


#$ Para çekme
@app.route('/api/withdraw' , methods=['POST'])
@auth.login_required
def withdraw():
    
    userPath =  basePath+g.user.username+"/"
    print(userPath)
    os.chdir(userPath)
    HE_Cl = Pyfhel()    
    HE_Cl.restoreContext(userPath+(g.user.username+".con"))
    HE_Cl.restorepublicKey(userPath+(g.user.username+".pk"))
 
    # loading the two ciphertexts. There is clearly potential for improvement here
    userBalance = PyCtxt(pyfhel=HE_Cl, fileName=(userPath+"balance.ctxt"), encoding=float)
    tempMoney = PyCtxt(pyfhel=HE_Cl, fileName=(userPath+"temp.ctxt"), encoding=float)
    userBalanceNew  = (userBalance - tempMoney) 
    userBalanceNew.to_file(userPath+"balance.ctxt")
    os.remove(userPath+"temp.ctxt")
    resp = jsonify({'message' : 'Withdraw successfully '})
    resp.status_code = 201
    return resp

#$ Para transfer
@app.route('/api/transfer' , methods=['POST'])
@auth.login_required
def transfer():
    # gönderen taraf bakiye
    iban = request.json.get('iban')
    sendMoney = request.json.get('sendMoney')
    userSend =  User.query.filter_by(iban=iban).first()
    userPath =  basePath+g.user.username+"/"
    os.chdir(userPath)
    copyfile("transfer.txt", basePath+userSend.username+"/transfer.txt")
    HE_Cl = Pyfhel()    
    HE_Cl.restoreContext(userPath+(g.user.username+".con"))
    HE_Cl.restorepublicKey(userPath+(g.user.username+".pk"))
 
    # loading the two ciphertexts. There is clearly potential for improvement here
    userBalance = PyCtxt(pyfhel=HE_Cl, fileName=(userPath+"balance.ctxt"), encoding=float)
    tempMoney = PyCtxt(pyfhel=HE_Cl, fileName=(userPath+"temp.ctxt"), encoding=float)
    userBalanceNew  = (userBalance - tempMoney) 
    userBalanceNew.to_file(userPath+"balance.ctxt")


    # Alıcı taraf
    os.chdir(basePath+userSend.username+"/")
    f = open("transfer.txt","w")
    f.write(str(sendMoney))
    resp = jsonify({'message' : 'Transfer successfully '})
    resp.status_code = 201
    return resp

@app.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


@app.route('/api/resource')
@auth.login_required
def get_resource():
    print(g.user)
    return jsonify({'data': 'Hello, %s!' % g.user.username})


if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()
    app.run(host="192.168.1.5",port=5000)
    #app.run(debug=True)

