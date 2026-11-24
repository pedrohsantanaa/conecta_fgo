# Homologacao FGO BB

## Configuracao local

1. Copie `.env.example` para `.env` dentro de `backend/`.
2. Preencha `BB_CLIENT_ID`, `BB_CLIENT_SECRET`, `BB_GW_DEV_APP_KEY` e `BB_OAUTH_SCOPE` com os valores da aplicacao de homologacao no Portal Developers BB.
3. Salve o certificado cliente e a chave privada em `backend/certs/` ou informe caminhos absolutos em `BB_CERT_PATH` e `BB_KEY_PATH`.
4. Defina `MOCK_MODE=false`. Em modo real, a aplicacao nao inicia sem credenciais e mTLS validos.

Os arquivos `.env` e `backend/certs/` sao locais e nao devem ser enviados ao Git. No servidor de teste, injete as mesmas variaveis por um cofre de segredos e monte o certificado como arquivo protegido.

## Execucao e validacao

```powershell
cd backend
python -m pip install -r requirements.txt
python run.py
python -m unittest discover -s tests -v
```

O backend inicia em `HOST` e `PORT` definidos no `.env` (padrao: `127.0.0.1:8001`). Para o frontend Vue, use `npm run dev` em `frontend-vue/`; defina `VITE_BACKEND_URL` apenas se o backend nao estiver em `http://127.0.0.1:8001`.

Em homologacao, valide na sequencia: pre-validacao sem reserva, pre-validacao com reserva e cancelamento usando o numero de reserva retornado.