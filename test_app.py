import pytest
from fastapi.testclient import TestClient
from app import app, tarefas

client = TestClient(app)


@pytest.fixture(autouse=True)
def restaurar_tarefas():
    original = [t.copy() for t in tarefas]
    yield
    tarefas[:] = original


def autenticar():
    resposta = client.post('/login', json={'usuario': 'admin', 'senha': '123456'})
    return {'Authorization': 'Bearer ' + resposta.json()['access_token']}


def test_login_correto():
    resposta = client.post('/login', json={'usuario': 'admin', 'senha': '123456'})
    assert resposta.status_code == 200
    assert resposta.json()['access_token']


def test_login_incorreto():
    resposta = client.post('/login', json={'usuario': 'admin', 'senha': 'errada'})
    assert resposta.status_code == 401
    assert 'access_token' not in resposta.json()


def test_consultar_tarefas():
    resposta = client.get('/tarefas')
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)
    assert resposta.json() == tarefas


def test_cadastrar_sem_token():
    antes = client.get('/tarefas').json()
    resposta = client.post('/tarefas', json={'titulo': 'Nova tarefa'})
    assert resposta.status_code == 401
    assert client.get('/tarefas').json() == antes


def test_cadastrar_com_token():
    antes = client.get('/tarefas').json()
    resposta = client.post('/tarefas', json={'titulo': 'Revisar os testes da API'}, headers=autenticar())
    assert resposta.status_code == 201
    tarefa = resposta.json()
    assert tarefa['titulo'] == 'Revisar os testes da API'
    assert tarefa['situacao'] == 'pendente'
    assert tarefa['id'] not in [t['id'] for t in antes]
    assert tarefa in client.get('/tarefas').json()


def test_cadastrar_titulo_vazio():
    antes = client.get('/tarefas').json()
    headers = autenticar()
    for dados in ({'titulo': ''}, {'titulo': '   '}, {}):
        resposta = client.post('/tarefas', json=dados, headers=headers)
        assert resposta.status_code == 400
        assert client.get('/tarefas').json() == antes
