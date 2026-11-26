# Uso da API Conecta FGO — Passo a Passo

Guia pratico para subir, testar e usar a API de integracao com o Fundo de
Garantia de Operacoes (FGO) do Banco do Brasil. Para o registro tecnico da
homologacao (regras de negocio, errorCodes e configuracao validada), veja
[homologacao-fgo.md](homologacao-fgo.md).

## 1. Visao geral

A aplicacao tem tres camadas:

```
Frontend (Vue ou legado)  ->  Backend FastAPI (127.0.0.1:8001)  ->  API FGO do BB (homologacao)
                              /api/*  +  /docs (Swagger)             fgo.mtls.api.hm.bb.com.br/v2
```

O backend e uma fachada: recebe as requisicoes, valida o formato dos dados,
autentica no BB (OAuth2 + mTLS) e **mascara os erros** do banco — o detalhe vai
para o log do servidor, nao para a resposta.

### O fluxo de negocio (3 passos)

```
1. POST /api/pre-validacoes            PRE-VALIDAR SEM RESERVA
   Consulta se os dados da operacao passam nas regras do fundo e qual a margem
   do mutuario. NAO grava nada — pode chamar quantas vezes quiser.
   Resposta: valorTotalFinanciado, valorMargemDisponivelContratacao

2. POST /api/pre-validacoes/reservas   PRE-VALIDAR COM RESERVA
   Mesmas validacoes do passo 1, porem SE ACEITA reserva a margem e devolve
   numeroReservaPreValidacao. Faca isso quando for formalizar a operacao.
   Resposta: numeroReservaPreValidacao, valorTotalFinanciado, valorMargem...

3a. Operacao formalizada -> a reserva e consumida.
   (a formalizacao em si NAO e feita por esta API)

3b. Operacao NAO aconteceu -> PUT /api/reservas/cancelamentos
   Cancela a reserva do passo 2 e libera a margem. Use o numero da reserva.
   Resposta: status: "SUCESSO", mensagem
```

Regra de ouro: **so crie reserva (passo 2) quando estiver perto de formalizar**,
e sempre cancele reservas que nao forem usadas.

## 2. Pre-requisitos

| Item | Onde |
|---|---|
| Python com venv | `backend\.venv\Scripts\python.exe` (o Python do sistema nao tem `uvicorn`) |
| Dependencias | `python -m pip install -r requirements.txt` (em `backend/`) |
| Configuracao | `backend/.env` (HOST, PORT, MOCK_MODE, credenciais BB) |
| Certificados mTLS | `backend/certs/client_cert.pem` (somente o certificado "leaf") + `client_key.pem` |

> **Atencao ao certificado**: o `client_cert.pem` deve conter APENAS o
> certificado do cliente. Enviar a cadeia completa (leaf + intermediarias +
> raiz) faz o gateway do BB responder `400 The SSL certificate error`.

As credenciais (`BB_CLIENT_ID`, `BB_CLIENT_SECRET`, `BB_GW_DEV_APP_KEY`) vem do
portal de APIs do BB. Nunca commite o `.env` nem os certificados.

## 3. Subindo o backend

```powershell
cd backend
.venv\Scripts\python.exe run.py
```

O servidor sobe em `http://127.0.0.1:8001` e reinicia sozinho a cada alteracao
em `backend/app/` (`reload=True`).

Confira a configuracao antes de testar:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
```

```json
{ "status": "healthy", "mock_mode": false, "mtls_configured": true }
```

- `mock_mode: false` -> as chamadas vao para o BB de verdade.
- `mtls_configured: true` -> certificado e chave privada encontrados.

## 4. Passo a passo no Swagger

Abra **http://127.0.0.1:8001/docs** e siga os 3 passos na ordem.

### Passo 1 — `POST /api/pre-validacoes`

Clique no endpoint, em **Try it out**, e use este corpo (payload validado na
homologacao — passa em todas as regras conhecidas, menos a regra 277, ver
secao 8):

```json
{
  "codigoAgenteFinanceiro": 77,
  "codigoIdentificadorExternoOperacao": "ABC1234",
  "codigoFundoGarantidor": 5,
  "numeroAgenciaContratanteOperacao": 1,
  "codigoIbgeMunicipio": 354340,
  "codigoTipoPessoa": 2,
  "codigoIdentificadorSrf": "00000000123ABC",
  "codigoTipoPublicoAlvo": 2,
  "valorFaturamentoBrutoAnual": 81000,
  "valorOperacaoCredito": 20000,
  "percentualGarantiaOperacaoCredito": 100.0,
  "codigoTipoModalidadeCredito": 1,
  "codigoTipoFinalidadeCredito": 1,
  "codigoTipoFonteRecurso": 11,
  "codigoTipoProgramaCredito": 44,
  "dataFormalizacaoOperacao": 20261126,
  "dataVencimentoOperacao": 20271127,
  "codigoTipoCronogramaAmortizacao": 1,
  "codigoTipoCondicaoEspecial": 1,
  "dataDespachoExternoOperacao": 0,
  "codigoTipoFormalizacao": 1,
  "valorSubsidioCredito": 0,
  "numeroCpfQualificadorOperacao": "52998224725",
  "valorCondicaoEspecial": 50000,
  "codigoInstituicaoFinanceira": 1
}
```

> **Datas**: `dataFormalizacaoOperacao` deve ser a **data atual** (AAAAMMDD) e
> `dataVencimentoOperacao` deve ser posterior. Se usar uma data antiga, o BB
> reprova com errorCode 222/35 (regra 9) antes de checar o resto.

Sucesso esperado (200):

```json
{
  "valorTotalFinanciado": 0.0,
  "valorMargemDisponivelContratacao": 1000000.0
}
```

### Passo 2 — `POST /api/pre-validacoes/reservas`

Use **o mesmo corpo** do passo 1. Sucesso esperado (200):

```json
{
  "numeroReservaPreValidacao": 123456789,
  "valorTotalFinanciado": 0.0,
  "valorMargemDisponivelContratacao": 1000000.0
}
```

**Anote o `numeroReservaPreValidacao`** — e ele que o passo 3 cancela.

### Passo 3 — `PUT /api/reservas/cancelamentos`

O corpo e diferente: os campos usam **aliases com espacos** (padrao do BB).
Substitua pelo numero real obtido no passo 2:

```json
{
  "Codigo Agente Financeiro": 77,
  "Codigo Fundo Garantidor": 5,
  "Numero Reserva Pre Validacao": 123456789
}
```

Sucesso esperado (200):

```json
{
  "status": "SUCESSO",
  "mensagem": "Cancelamento de reserva FGO realizado com sucesso.",
  "dados_cancelamento": { }
}
```

## 5. Testando por linha de comando

Os mesmos passos via `Invoke-RestMethod` (PowerShell):

```powershell
# Passo 1 — pre-validacao sem reserva
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/api/pre-validacoes `
  -ContentType 'application/json' -InFile payload.json

# Passo 2 — pre-validacao com reserva (mesmo payload.json)
$reserva = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/api/pre-validacoes/reservas `
  -ContentType 'application/json' -InFile payload.json
$reserva.numeroReservaPreValidacao

# Passo 3 — cancelamento (atencao aos aliases com espacos)
$cancel = @{
  'Codigo Agente Financeiro'      = 77
  'Codigo Fundo Garantidor'       = 5
  'Numero Reserva Pre Validacao'  = $reserva.numeroReservaPreValidacao
} | ConvertTo-Json
Invoke-RestMethod -Method Put -Uri http://127.0.0.1:8001/api/reservas/cancelamentos `
  -ContentType 'application/json' -Body $cancel
```

## 6. Payload campo a campo

| Campo | Tipo | Significado | Valor que passa na homologacao |
|---|---|---|---|
| `codigoAgenteFinanceiro` | int | Codigo do agente (atribuido pelo BB) | `77` (FOMENTO TO) |
| `codigoIdentificadorExternoOperacao` | str (max 20) | ID da operacao no seu sistema | unico por operacao (ex.: `"ABC1234"`) |
| `codigoFundoGarantidor` | int | Fundo garantidor | `5` (unico habilitado p/ agente 77) |
| `numeroAgenciaContratanteOperacao` | int | Agencia contratante | `1` |
| `codigoIbgeMunicipio` | int | Codigo IBGE do municipio (sem DV) | `354340` |
| `codigoTipoPessoa` | int | 1 = PF, 2 = PJ | `2` (caminho PJ) |
| `codigoIdentificadorSrf` | str | CPF (11) ou CNPJ (14) do mutuario | 14 digitos p/ PJ |
| `codigoTipoPublicoAlvo` | int | Enquadramento do mutuario | `2` (PJ) ou `7` (PF, exige tipo 1) |
| `valorFaturamentoBrutoAnual` | float | Faturamento bruto anual / renda | `81000` (teto atual) |
| `valorOperacaoCredito` | float | Valor da operacao sem custos | `20000` (limite atual) |
| `percentualGarantiaOperacaoCredito` | float | % da garantia FGO (0–100) | `100.0` (minimo p/ INVESTIMENTO) |
| `codigoTipoModalidadeCredito` | int | Modalidade do credito | `1` |
| `codigoTipoFinalidadeCredito` | int | Finalidade do credito | `1` (INVESTIMENTO) ou `2` (CAP. GIRO) |
| `codigoTipoFonteRecurso` | int | Fonte de recursos | `11` |
| `codigoTipoProgramaCredito` | int | Programa de credito | `44` (unico p/ fundo 5) |
| `dataFormalizacaoOperacao` | int | Data da formalizacao (AAAAMMDD) | **data atual** (ex.: `20261126`) |
| `dataVencimentoOperacao` | int | Vencimento (AAAAMMDD) | posterior a formalizacao |
| `codigoTipoCronogramaAmortizacao` | int | Tipo de amortizacao | `1` |
| `codigoTipoCondicaoEspecial` | int | Tipo de condicao especial | `1` |
| `dataDespachoExternoOperacao` | int | Data despacho externo (ou zero) | `0` |
| `codigoTipoFormalizacao` | int | Tipo de formalizacao | `1` |
| `valorSubsidioCredito` | float | Subsidio/subvencao | `0` (obrigatorio zero) |
| `numeroCpfQualificadorOperacao` | str/int | CPF do qualificador da operacao | `"52998224725"` ou `11144477735` |
| `valorCondicaoEspecial` | float (opcional) | Valor da condicao especial | `50000` |
| `codigoInstituicaoFinanceira` | int (opcional) | Codigo da IF (so no dado de homologacao) | `1` |

## 7. Mock x Live

| | `MOCK_MODE=true` | `MOCK_MODE=false` |
|---|---|---|
| Destino | Nenhum (respostas simuladas) | BB homologacao (mTLS + OAuth) |
| Credenciais/cert | Nao precisa | Obrigatorios |
| Passo 1 devolve | 45% do valor da operacao como "financiado" | Resposta real do fundo |
| Passo 2 devolve | Numero de reserva sorteado | Reserva real no fundo |
| Passo 3 devolve | `SUCESSO` sempre | Cancelamento real |
| Quando usar | Desenvolvimento, testes de contrato | Testes de integracao e homologacao |

Troque `MOCK_MODE` em `backend/.env` e **reinicie o servidor**.

## 8. Erros e diagnostico

### A mascara do backend

O backend **nao repassa os erros do BB**. Voce ve apenas:

```json
{ "detail": "O Banco do Brasil recusou os dados informados." }
```

O detalhe (errorCode, userHelp, correlationId) vai para o **log JSON no terminal
onde o `run.py` roda**. Desde a melhoria de diagnostico, cada erro traz campos
estruturados: `bb_error_code`, `bb_user_help`, `bb_detail`,
`bb_correlation_id`, `bb_additional_info` (alem do `response_body` bruto).

> Dica: para iterar sobre as regras de negocio sem a mascara, chame o BB
> diretamente (token + Bearer + `gw-dev-app-key`) — veja o script de exemplo em
> homologacao-fgo.md.

### Tabela de errorCodes do BB

| errorCode | Significado | O que fazer |
|---|---|---|
| 12 | Fundo garantidor nao habilitado a operar | Usar `codigoFundoGarantidor: 5` |
| 23 | Agente financeiro nao cadastrado no fundo | Agente `77` so opera no fundo `5` |
| 110 | Publico-alvo nao permitido pelo fundo | `2` (PJ) ou `7` (PF) |
| 189 | Publico-alvo incompativel com tipo de pessoa | alvo `7` exige `codigoTipoPessoa: 1` |
| 240 | Programa de credito nao permitido | `44` para o fundo `5` |
| 255 | Finalidade nao permitida | `1` (INVESTIMENTO) ou `2` (CAP. GIRO) |
| 259 | Valor de subsidio invalido | `valorSubsidioCredito: 0` |
| 123 | Vencimento <= formalizacao | datas distintas, vencimento maior |
| 222 / 35 | Formalizacao fora do periodo permitido | `dataFormalizacaoOperacao` = hoje |
| 94 / 95 | Percentual de garantia abaixo do minimo | `100` (95 ainda reprova p/ INVESTIMENTO) |
| 16 | Faturamento bruto anual acima do teto | `valorFaturamentoBrutoAnual` <= 81000 |
| 280 | Limite de saldo comprometido do mutuario | `valorOperacaoCredito` <= 20000 |
| 275 | CPF qualificador invalido na Receita Federal | CPF com digitos verificadores validos |
| 281 | CPF qualificador fora do CadUnico | ex.: `52998224725`, `11144477735` |
| 5 | Mutuario nao cadastrado (caminho PF) | exigido CPF de mutuario cadastrado pelo BB |
| 277 | Operacao nao qualificada como "mulher" | **pendente de dado de teste do BB** |
| 901 | Dados inconsistentes (ex.: reserva inexistente) | conferir o numero da reserva |
| E6500 (500) | Erro transitório do gateway do BB | **repetir a chamada** |

### Quando acionar o suporte do BB

Guarde o `correlationId` do log (campo `bb_correlation_id`) — e ele que o suporte
do BB usa para rastrear a requisicao em caso de incidente.

## 9. Boas praticas

1. **`codigoIdentificadorExternoOperacao` unico por operacao** — e o rastro da
   operacao no seu sistema; reutilizar pode confundir a conciliacao.
2. **Reserva so quando for formalizar** — o passo 1 (sem reserva) e gratuito de
   efeitos; o passo 2 compromete margem do mutuario.
3. **Cancele reservas nao usadas** (passo 3) — reserva abandonada trava margem.
4. **`dataFormalizacaoOperacao` = data atual** — o BB rejeita datas antigas.
5. **Nao trate o erro mascarado como diagnostico** — olhe o log (ou chame o BB
   diretamente) para saber a regra que reprova.
6. **Nunca commite** `.env`, certificados ou chaves privadas.
