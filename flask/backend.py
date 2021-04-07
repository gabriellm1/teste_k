import os
from flask import Flask, flash, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS, cross_origin
import json
import logging
from ParserFuncs import *
from salesforce_connect import *



UPLOAD_FOLDER = './contratos/'
ALLOWED_EXTENSIONS = set(['pdf'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'

sf = Salesforce(instance=instance, session_id=session_id)
contratos_re__c = SFType('Contrato_RE__c',session_id,instance)
desconto__c = SFType('Desconto__c',session_id,instance)

# cors = CORS(app, resources={r"/foo": {"origins": "http://localhost:5000"}})
cors = CORS(app, origins=['http://localhost:5000'])

@app.route('/upload', methods=['POST'])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def fileUpload():
    target=os.path.join(UPLOAD_FOLDER)
    if not os.path.isdir(target):
        os.mkdir(target)
    # logger.info("Recebendo Contrato")
    file = request.files['file'] 
    filename = secure_filename(file.filename)
    destination="".join([target, filename])
    file.save(destination)
    session['uploadFilePath']=destination
    data_entrega_chaves = request.form['entrega_de_chaves']
    if data_entrega_chaves:
        test = data_entrega_chaves.split('/')
        if len(test) == 3:
            if (len(test[0])==2 and len(test[1])==2 and len(test[2])==4):
                print('Formato Correto')
            else:
                data_entrega_chaves = None
        else:
            data_entrega_chaves = None
    else:
        data_entrega_chaves = None
    response = do_all(destination,data_entrega_chaves)
    # print(response)
    os.remove(destination)
    return response

# Rota para cadastrar contrato
@app.route('/salesforce', methods=['POST'])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def dataUpload():
    dados = request.get_json()
    try:
        # Caso tenha tido sucesso, retorna ID e 200
        res = adiciona_contrato(sf,contratos_re__c,desconto__c,dados)
        return res, 200
    except:
        # Caso tenha não tenha tido sucesso, retorna Error e 500
        return "Error", 500



if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(debug=True,host="0.0.0.0", port=5051 ,use_reloader=False)

CORS(app, expose_headers='Authorization')