import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI, Body, Header
from fastapi.responses import JSONResponse

app = FastAPI()
SECRET_KEY = os.getenv('JWT_SECRET', os.urandom(32).hex())
USUARIO = 'admin'
SALT = b'api-tarefas-demo'
SENHA_HASH = bytes.fromhex('dc096549bf5638d76a0f6c27d536f60b26fbc5dc4d97d13b495e59705778aa5b')
tarefas = [{'id': 1, 'titulo': 'Estudar API REST', 'situacao': 'pendente'}]


@app.post('/login')
async def login(dados: dict = Body(default={}, examples=[{'usuario': 'admin', 'senha': '123456'}])):
    senha = dados.get('senha')
    if dados.get('usuario') != USUARIO or not isinstance(senha, str):
        return JSONResponse({'erro': 'Credenciais incorretas'}, status_code=401)
    senha_hash = hashlib.pbkdf2_hmac('sha256', senha.encode(), SALT, 600000)
    if not hmac.compare_digest(senha_hash, SENHA_HASH):
        return JSONResponse({'erro': 'Credenciais incorretas'}, status_code=401)
    token = jwt.encode({'sub': USUARIO, 'exp': datetime.now(timezone.utc) + timedelta(hours=1)}, SECRET_KEY, algorithm='HS256')
    return {'access_token': token}


@app.get('/tarefas')
def consultar_tarefas():
    return tarefas


@app.post('/tarefas', status_code=201)
async def cadastrar_tarefa(dados: dict = Body(default={}, examples=[{'titulo': 'Estudar para a prova'}]), authorization: str = Header(default='')):
    partes = authorization.split()
    if len(partes) != 2 or partes[0].lower() != 'bearer':
        return JSONResponse({'erro': 'Token obrigatório'}, status_code=401)
    try:
        dados_token = jwt.decode(partes[1], SECRET_KEY, algorithms=['HS256'], options={'require': ['exp', 'sub']})
        if dados_token['sub'] != USUARIO:
            raise jwt.InvalidTokenError()
    except jwt.InvalidTokenError:
        return JSONResponse({'erro': 'Token inválido ou expirado'}, status_code=401)
    titulo = dados.get('titulo')
    if not isinstance(titulo, str) or not titulo.strip():
        return JSONResponse({'erro': 'Título obrigatório'}, status_code=400)
    tarefa = {'id': max((t['id'] for t in tarefas), default=0) + 1, 'titulo': titulo.strip(), 'situacao': 'pendente'}
    tarefas.append(tarefa)
    return JSONResponse(tarefa, status_code=201)
