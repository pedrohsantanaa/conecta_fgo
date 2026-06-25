from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class PreValidationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    codigoAgenteFinanceiro: int = Field(
        ...,
        description="Código do Agente Financeiro, atribuído pelo Administrador."
    )
    codigoIdentificadorExternoOperacao: str = Field(
        ...,
        max_length=20,
        description="Código que identifica a operação de crédito no âmbito do Agente."
    )
    codigoFundoGarantidor: int = Field(
        ...,
        description="Identifica o fundo garantidor da operação de crédito."
    )
    numeroAgenciaContratanteOperacao: int = Field(
        ...,
        description="Número que identifica a agência contratante da operação."
    )
    codigoIbgeMunicipio: int = Field(
        ...,
        description="Código IBGE do município onde se localiza o empreendimento financiado (sem DV)."
    )
    codigoTipoPessoa: int = Field(
        ...,
        description="Código do tipo de pessoa do mutuário (1: Pessoa Física, 2: Pessoa Jurídica)."
    )
    codigoIdentificadorSrf: str = Field(
        ...,
        max_length=14,
        description="CPF ou CNPJ do mutuário."
    )
    codigoTipoPublicoAlvo: int = Field(
        ...,
        description="Código do público alvo no qual o mutuário se enquadra."
    )
    valorFaturamentoBrutoAnual: float = Field(
        ...,
        description="Valor do faturamento bruto anual do mutuário ou renda da pessoa física."
    )
    valorOperacaoCredito: float = Field(
        ...,
        description="Valor da operação de crédito sem custos adicionais."
    )
    percentualGarantiaOperacaoCredito: float = Field(
        ...,
        description="Percentual da garantia FGO com duas casas decimais (ex: 80.05)."
    )
    codigoTipoModalidadeCredito: int = Field(
        ...,
        description="Identifica a modalidade do crédito concedido."
    )
    codigoTipoFinalidadeCredito: int = Field(
        ...,
        description="Identifica a finalidade do crédito concedido."
    )
    codigoTipoFonteRecurso: int = Field(
        ...,
        description="Código da fonte de recursos do financiamento."
    )
    codigoTipoProgramaCredito: int = Field(
        ...,
        description="Identifica o programa de crédito."
    )
    dataFormalizacaoOperacao: int = Field(
        ...,
        description="Data da formalização da operação no formato AAAAMMDD."
    )
    dataVencimentoOperacao: int = Field(
        ...,
        description="Data de vencimento da operação no formato AAAAMMDD."
    )
    codigoTipoCronogramaAmortizacao: int = Field(
        ...,
        description="Identifica o tipo de cronograma de amortizações."
    )
    codigoTipoCondicaoEspecial: int = Field(
        ...,
        description="Identifica o tipo de condição especial da operação."
    )
    dataDespachoExternoOperacao: int = Field(
        ...,
        description="Data de despacho externo (ou zero)."
    )
    codigoTipoFormalizacao: int = Field(
        ...,
        description="Código para indicar o tipo de formalização da operação."
    )
    valorSubsidioCredito: float = Field(
        ...,
        description="Valor do subsídio/subvenção da operação de crédito."
    )
    numeroCpfQualificadorOperacao: int = Field(
        ...,
        description="CPF qualificador das características da operação de crédito."
    )
    valorCondicaoEspecial: Optional[float] = Field(
        None,
        description="Valor da Condição Especial de acordo com o Código Tipo Condição Especial."
    )


class PreValidationResponse(BaseModel):
    valorTotalFinanciado: float = Field(
        ...,
        description="Retorna o valor total já financiado/garantido/comprometido do mutuário com garantia do Fundo Garantidor."
    )
    valorMargemDisponivelContratacao: float = Field(
        ...,
        description="Valor Margem Disponível para Contratação."
    )


class PreValidationReserveResponse(BaseModel):
    numeroReservaPreValidacao: Optional[int] = Field(
        None,
        description="Retorna o número da reserva da pré-validação registrada no Fundo Garantidor."
    )
    valorTotalFinanciado: float = Field(
        ...,
        description="Retorna o valor total já financiado/garantido/comprometido do mutuário com garantia do Fundo Garantidor."
    )
    valorMargemDisponivelContratacao: Optional[float] = Field(
        None,
        description="Valor Margem Disponível para Contratação."
    )


class CancellationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    codigo_agente_financeiro: int = Field(
        ...,
        alias="Codigo Agente Financeiro",
        description="Código do Agente Financeiro, atribuído pelo Administrador."
    )
    codigo_fundo_garantidor: int = Field(
        ...,
        alias="Codigo Fundo Garantidor",
        description="Identifica o código do fundo garantidor da operação de crédito."
    )
    numero_reserva_pre_validacao: int = Field(
        ...,
        alias="Numero Reserva Pre Validacao",
        description="Identifica o número da reserva da pré-validação registrada no GFG, a ser cancelada."
    )


class CancellationResponse(BaseModel):
    status: str = Field(..., description="Status do cancelamento.")
    mensagem: str = Field(..., description="Mensagem de retorno do cancelamento.")
    dados_cancelamento: Optional[dict] = Field(None, description="Dados originais retornados pela API se houver.")
