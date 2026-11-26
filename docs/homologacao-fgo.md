# Homologação FGO — Mapa de Validação e Configuração

Registro dos testes de integração com a API FGO do Banco do Brasil em homologação
(`fgo.mtls.api.hm.bb.com.br`), realizados em 24/11/2026. Consolida as regras de
negócio descobertas, os códigos de erro do BB e a configuração técnica validada.

## Configuração técnica validada

Ponto a ponto que foi resolvido para o canal funcionar — não regredir:

1. **mTLS — apresentar somente o certificado "leaf"**:
   `backend/certs/client_cert.pem` deve conter apenas o certificado do cliente.
   Enviar a cadeia completa (leaf + intermediárias + raiz) faz o gateway responder
   `400 The SSL certificate error` (openresty). A chave privada deve corresponder
   ao certificado.
2. **Certificado registrado no portal do BB**: o portal de vocês usa modelo BYOC
   ("Lista dos seus certificados para consumir API mTLS"). O par utilizado é o
   `CN=*.fomento.to.gov.br` (Sectigo/SSL2BUY, vence 23/04/2027), registrado em
   24/11/2026 no ambiente TESTE.
3. **OAuth — URL com barra final**: `BB_OAUTH_TOKEN_URL` deve terminar em
   `/oauth/token/`. Requisições sem barra final (e sem credenciais válidas) caem
   na página de bloqueio do WAF do BB ("Ops! Não foi possível completar...").
4. **Fluxo de token**: `POST` com header `Basic base64(clientID:clientSecret)`,
   corpo `grant_type=client_credentials&scope=fgo.requisicao`. Retorno válido:
   `expires_in: 600`.
5. **Chamadas FGO**: `Authorization: Bearer <token>` + query param
   `gw-dev-app-key`. Sem o app key a API responde
   `403 "A chave de aplicacao (AppKey) nao foi informada"`.
6. **Backend**: usar o interpretador do venv (`backend\.venv\Scripts\python.exe run.py`);
   o Python do sistema não tem `uvicorn`. O servidor sobe em `127.0.0.1:8001`
   com `MOCK_MODE=false`; `/health` confirma `mock_mode: false` e
   `mtls_configured: true`.

Observação: o par `client_cert.pem`/`client_key.pem` antigo (GlobalSign,
`*.fomento.to.gov.br`, vencido em 17/10/2026) está preservado como `.old`.
As pastas `certs/api.hm.bb.com.br/` (cadeia do servidor do BB) e `certs/novo/`
(fonte do par ativo) podem ser removidas após a estabilização.

## Credenciais e ambiente

- Ambiente: **homologação** (`"ambiente":"homologacao"` no clientSecret).
- `clientID` e `clientSecret` são strings base64 (JSON embutido) fornecidos pelo
  portal; `BB_GW_DEV_APP_KEY` é a "developer application key" (hex), enviada como
  query param `gw-dev-app-key`.
- Agente Financeiro da FOMENTO TO: **77** (atribuído pelo BB, conforme e-mail de
  adesão ao BB-SIA).
- O `registrationAccessToken` do portal não é usado pelas operações da API.

## Cadeia de validação do `POST /v2/pre-validacoes`

Ordem real das validações de negócio, descoberta por sondagem. Cada linha é o
primeiro valor que passa na regra correspondente (mantidos os demais campos do
payload abaixo).

| # | Regra (userHelp do BB) | errorCode | Valor que passa |
|---|---|---|---|
| 1 | Fundo Garantidor habilitado a operar | 12 | `codigoFundoGarantidor: 5` |
| 2 | Agente Financeiro cadastrado no fundo | 23 | `codigoAgenteFinanceiro: 77` |
| 3 | Público-alvo permitido pelo fundo | 110 | `codigoTipoPublicoAlvo: 2` (PJ) ou `7` (PF) |
| 4 | Tipo de público-alvo compatível com tipo de pessoa | 189 | alvo 7 exige `codigoTipoPessoa: 1` |
| 5 | Programa de crédito permitido pelo fundo | 240 | `codigoTipoProgramaCredito: 44` |
| 6 | Finalidade de crédito permitida | 255 | `codigoTipoFinalidadeCredito: 1` (INVESTIMENTO) ou `2` (CAPITAL DE GIRO) |
| 7 | Valor do subsídio de crédito | 259 | `valorSubsidioCredito: 0` |
| 8 | Vencimento posterior à formalização | 123 | datas distintas, vencimento maior |
| 9 | Operação formalizada no período permitido | 222 / 35 | `dataFormalizacaoOperacao` = data atual (AAAAMMDD) |
| 10 | Percentual de garantia mínimo | 94 / 95 | `percentualGarantiaOperacaoCredito: 100` (95 ainda reprova) |
| 11 | Teto de faturamento bruto anual | 16 | `valorFaturamentoBrutoAnual` ≤ 81000 (100000 reprova) |
| 12 | Limite de saldo comprometido do mutuário | 280 | `valorOperacaoCredito` ≤ 20000 |
| 13 | CPF qualificador na Receita Federal | 275 | CPF com dígitos verificadores válidos |
| 14 | CPF qualificador no CadÚnico | 281 | ex.: `52998224725`, `11144477735` |
| 15 | Operação qualificada como "mulher" (mínimo da carteira do agente) | 277 | **pendente de dado de teste do BB** |
| 16 | CPF-CNPJ do mutuário válido (caminho PF/alvo 7) | 5 | **pendente de dado de teste do BB** |

Valores que NÃO passam (para evitar repetir testes):

- `codigoFundoGarantidor`: 1, 7, 8 → errorCode 12 (não habilitados);
  2, 3, 4, 6 → errorCode 23 (agente 77 não cadastrado neles).
- `codigoTipoPublicoAlvo`: 1, 3, 4, 5, 6, 8 → errorCode 110; 9 → 110;
  10–20 → errorCode 999 (fora do catálogo). **Em 26/11 o alvo 1 passou da
  regra 3** e chegou ao errorCode 277 — ver "Reteste de 26/11/2026".
- `codigoTipoProgramaCredito`: 1–43 e 45–120 → errorCode 240 (para o fundo 5).
- `percentualGarantiaOperacaoCredito`: 80.05, 85, 90, 95 → errorCode 94
  (finalidade INVESTIMENTO).
- `numeroCpfQualificadorOperacao`: `12345678911` (exemplo da spec) e
  `12345678909` → errorCode 275/281.
- Datas antigas (ex.: 20200623/20200623) → errorCode 123/222.

## Payload mais avançado (parado no errorCode 277)

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
  "dataFormalizacaoOperacao": 20261124,
  "dataVencimentoOperacao": 20271124,
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

Observações sobre o payload:

- `codigoInstituicaoFinanceira` não consta no `docs/fgo-openapi.json`; foi
  adicionado como campo opcional em `PreValidationRequest` para encaminhar o
  payload com fidelidade.
- `numeroCpfQualificadorOperacao` é aceito como string numérica (o schema
  converte para int).
- Para o caminho PF (`codigoTipoPublicoAlvo: 7`), `codigoTipoPessoa` deve ser 1 e
  `codigoIdentificadorSrf` um CPF de 11 dígitos cadastrado na base de teste
  (erro 5 para CPFs não cadastrados como mutuário).

## Reteste de 26/11/2026 (sem dados novos do BB)

Teste manual via Swagger (`/docs`) e chamadas diretas ao BB (para ver os erros
sem a máscara do backend). Payload base: o "mais avançado" acima, com
`dataFormalizacaoOperacao: 20261126` e `dataVencimentoOperacao: 20271127` —
a regra 9 exige formalização na data atual, então o payload de 24/11
(`20261124`) reprovaria hoje com errorCode 222/35 antes de chegar na regra 15.

| Teste | Resultado |
|---|---|
| `POST /v2/pre-validacoes` (alvo 2, pessoa 2) | 422 errorCode 277 (mesmo gargalo de 24/11) |
| `POST /v2/pre-validacoes` (alvo 1, pessoa 2) | 422 errorCode 277 — ⚠️ passou pela regra 3 |
| `POST /v2/pre-validacoes/reservas` (alvo 2) | 422 errorCode 277; `additionalInfo` inclui `numeroReservaPrevalidacao: 0` |
| `PUT /v2/reservas/cancelamentos` (reservas inexistentes) | 422 errorCode 901 "Dados inconsistentes na requisicao" |

Achados novos:

- **Divergência na regra 3**: `codigoTipoPublicoAlvo: 1` com
  `codigoTipoPessoa: 2` chegou até a regra 15 em 26/11; o mapeamento de 24/11
  registrava errorCode 110 para o alvo 1. Revalidar a cadeia quando houver
  novos dados de teste.
- **`additionalInfo` também vem nos erros**: `valorTotalFinanciado`,
  `valorMargemDisponivelContratacao` (e `numeroReservaPrevalidacao` na rota de
  reserva), zerados quando a operação não qualifica. O backend agora grava
  `bb_error_code`, `bb_user_help`, `bb_detail`, `bb_correlation_id` e
  `bb_additional_info` no log JSON.
- **Erro transitório do gateway**: chamadas podem retornar `500
  UNEXPECTED_ERROR` "Ocorreu um erro no serviço acionado pelo Gateway [E6500]".
  Repetir a chamada resolveu em todos os casos observados.
- **Cancelamento com reserva inexistente** responde errorCode 901. O cancelamento
  real só será validável quando uma reserva for criada (gargalo 277).
- correlationIds de 26/11: alvo 1 `5b5a7c96-f0a5-496c-9ecd-8df398c7c33c`;
  alvo 2 `885fcb03-5ac4-4549-8b15-47159c10655e`; reservas
  `dbdb5d36-b316-452f-ba3c-3e70d959cf24` e `c0df5172-952e-451a-87f0-cb29053c29d8`;
  cancelamentos `fb9a73b2-7514-4809-a8da-62575c23e3d5` e
  `55ee868a-e840-41bf-8cc0-67622fd88dca`.

## Pendências (dados de teste do BB)

O gargalo atual exige o pacote de dados de homologação do BB:

1. **CPF/CNPJ de mutuário** cadastrado na base de teste (caminho alvo 7/PF
   retorna errorCode 5 para CPFs comuns, mesmo com dígitos válidos).
2. **CPF qualificador qualificado como "mulher"** — a regra 277 exige que a
   operação se qualifique como mulher (percentual mínimo da carteira do agente).
   A qualificação provavelmente vem do qualificador/mutuário, não de campo do
   payload.
3. Confirmação sobre a regra do percentual mínimo "mulher" para o agente 77 com
   carteira zerada.

## Sequência de teste quando os dados chegarem

1. `POST /api/pre-validacoes` — sem reserva (conferir `valorTotalFinanciado` e
   `valorMargemDisponivelContratacao`).
2. `POST /api/pre-validacoes/reservas` — anotar `numeroReservaPreValidacao`.
3. `PUT /api/reservas/cancelamentos` — cancelar a reserva retornada (campos com
   aliases: `Codigo Agente Financeiro`, `Codigo Fundo Garantidor`,
   `Numero Reserva Pre Validacao`).

## Diagnóstico de erros

- O backend mascara os erros do BB ("O Banco do Brasil recusou os dados
  informados"). O detalhe (`userHelp`, `errorCode`, `correlationId`) fica no log
  JSON do servidor (`response_body`).
- Para iterar sobre as regras de negócio, chamar o BB diretamente (token + Bearer
  + `gw-dev-app-key`) evita a máscara.
- `correlationId` deve ser informado ao suporte do BB em caso de incidente.
