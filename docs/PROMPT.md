# Sistema de Integração FGO

## Objetivo

Desenvolver uma aplicação web simples para integração com a API do Fundo de Garantia de Operações (FGO) do Banco do Brasil.

## Stack Obrigatória

### Backend
- Python 3.12+
- FastAPI
- Pydantic
- HTTPX
- Uvicorn

### Frontend
- HTML5
- CSS3
- JavaScript ES6+

Não utilizar:
- React
- Vue
- Angular
- Bootstrap

## Funcionalidades

### Pré-validação sem reserva

Consumir:

POST /pre-validacoes

Permitir preenchimento dos campos obrigatórios e exibir:

- valorTotalFinanciado
- valorMargemDisponivelContratacao

### Pré-validação com reserva

Consumir:

POST /pre-validacoes/reservas

Exibir:

- numeroReservaPreValidacao
- valorTotalFinanciado
- valorMargemDisponivelContratacao

### Cancelamento de Reserva

Consumir:

PUT /reservas/cancelamentos

Exibir resultado do cancelamento.

## API Externa

A especificação OpenAPI encontra-se no arquivo:

fgo-openapi.json

A implementação deve utilizar os endpoints definidos nesse arquivo.

## Autenticação

Implementar:

- OAuth2 Client Credentials
- gw-dev-app-key
- Suporte a mTLS

As credenciais devem ser carregadas por variáveis de ambiente.

## Estrutura Esperada

backend/
├── app/
│ ├── main.py
│ ├── config.py
│ ├── routers/
│ ├── services/
│ ├── schemas/
│ └── utils/
├── certs/
├── requirements.txt
└── .env.example

frontend/
├── index.html
├── css/
│ └── style.css
└── js/
└── app.js

## Requisitos de Código

- Código totalmente tipado
- Async/Await
- Tratamento de exceções
- Logs estruturados
- Swagger automático
- Comentários apenas quando necessários

## Requisitos de Interface

- Responsiva
- Layout institucional
- Formulários organizados
- Loading durante requisições
- Toasts de sucesso e erro

## Entrega

Gerar todos os arquivos completos.

Não omitir código.

Não utilizar pseudocódigo.

A aplicação deve estar pronta para execução local.