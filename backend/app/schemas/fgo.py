"""
Modelos Pydantic das requisicoes e respostas da API FGO do Banco do Brasil.

PreValidationRequest -> corpo dos passos 1 e 2 (pre-validacao, com ou sem reserva).
CancellationRequest  -> corpo do passo 3 (cancelamento), com aliases no padrao do BB.
Os modelos de resposta espelham exatamente o contrato devolvido pelo fundo.

Os validadores replicam regras de negocio/formato descobertas na homologacao
(consulte docs/homologacao-fgo.md para a cadeia completa de validacoes do BB).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class PreValidationRequest(BaseModel):
    """
    Corpo da pre-validacao (POST /pre-validacoes e /pre-validacoes/reservas).

    Os nomes dos campos seguem o contrato do BB (camelCase) e sao encaminhados
    como estao. Regras validadas localmente aqui evitam uma ida ao BB tola
    (datas invalidas, percentual fora da faixa, CPF/CNPJ com tamanho errado).
    """

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
    codigoInstituicaoFinanceira: Optional[int] = Field(
        None,
        description="Código da instituição financeira (presente nos dados de homologação do BB)."
    )

    # --- Validadores locais (antes de chamar o BB) ---
    # Reproduzem restricoes de formato do contrato; as regras de NEGOCIO
    # (fundo habilitado, programa permitido, margem etc.) so o BB valida.

    @field_validator(
        "codigoAgenteFinanceiro", "codigoFundoGarantidor", "numeroAgenciaContratanteOperacao",
        "codigoIbgeMunicipio", "codigoTipoPessoa", "codigoTipoPublicoAlvo",
        "codigoTipoModalidadeCredito", "codigoTipoFinalidadeCredito", "codigoTipoFonteRecurso",
        "codigoTipoProgramaCredito", "codigoTipoCronogramaAmortizacao",
        "codigoTipoCondicaoEspecial", "codigoTipoFormalizacao", "numeroCpfQualificadorOperacao",
    )
    @classmethod
    def validate_positive_codes(cls, value: int) -> int:
        """Codigos de dominio do BB sao inteiros positivos."""
        if value <= 0:
            raise ValueError("O valor deve ser positivo.")
        return value

    @field_validator("valorFaturamentoBrutoAnual", "valorOperacaoCredito", "valorSubsidioCredito")
    @classmethod
    def validate_financial_values(cls, value: float) -> float:
        """Valores financeiros nao podem ser negativos."""
        if value < 0:
            raise ValueError("O valor nao pode ser negativo.")
        return value

    @field_validator("percentualGarantiaOperacaoCredito")
    @classmethod
    def validate_guarantee_percentage(cls, value: float) -> float:
        """Percentual da garantia FGO: 0 a 100, com duas casas decimais (ex.: 80.05)."""
        if not 0 <= value <= 100:
            raise ValueError("O percentual de garantia deve estar entre 0 e 100.")
        return value

    @field_validator("dataFormalizacaoOperacao", "dataVencimentoOperacao")
    @classmethod
    def validate_dates(cls, value: int) -> int:
        """Datas no formato AAAAMMDD (ex.: 20261126), como inteiro, e validas no calendario."""
        try:
            datetime.strptime(str(value), "%Y%m%d")
        except ValueError as error:
            raise ValueError("A data deve estar no formato AAAAMMDD e ser valida.") from error
        return value

    @model_validator(mode="after")
    def validate_identifiers(self) -> "PreValidationRequest":
        """
        Tamanho do documento do mutuario conforme o tipo de pessoa:
        codigoTipoPessoa 1 (PF) -> codigoIdentificadorSrf com 11 digitos (CPF);
        codigoTipoPessoa 2 (PJ) -> codigoIdentificadorSrf com 14 digitos (CNPJ).
        """
        expected_length = 11 if self.codigoTipoPessoa == 1 else 14
        if len(self.codigoIdentificadorSrf) != expected_length:
            raise ValueError("CPF ou CNPJ deve conter somente digitos e ter o tamanho esperado.")
        return self

class PreValidationResponse(BaseModel):
    """Resposta do passo 1 (pre-validacao sem reserva)."""
    valorTotalFinanciado: float = Field(
        ...,
        description="Retorna o valor total já financiado/garantido/comprometido do mutuário com garantia do Fundo Garantidor."
    )
    valorMargemDisponivelContratacao: float = Field(
        ...,
        description="Valor Margem Disponível para Contratação."
    )


class PreValidationReserveResponse(BaseModel):
    """
    Resposta do passo 2 (pre-validacao com reserva).

    numeroReservaPreValidacao e o campo-chave: guarde-o para o cancelamento
    (passo 3) caso a operacao nao seja formalizada.
    """
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
    """
    Corpo do passo 3 (cancelamento de reserva).

    O contrato do BB exige chaves COM ESPACOS — por isso os aliases
    ("Codigo Agente Financeiro", etc.). No JSON enviado, use exatamente essas
    chaves; em codigo Python, use os nomes snake_case.
    """

    model_config = ConfigDict(populate_by_name=True)

    codigo_agente_financeiro: int = Field(
        ...,
        alias="codigoAgenteFinanceiro",
        description="Código do Agente Financeiro, atribuído pelo Administrador."
    )
    codigo_fundo_garantidor: int = Field(
        ...,
        alias="codigoFundoGarantidor",
        description="Identifica o código do fundo garantidor da operação de crédito."
    )
    numero_reserva_pre_validacao: int = Field(
        ...,
        alias="numeroReservaPreValidacao",
        description="Identifica o número da reserva da pré-validação registrada no GFG, a ser cancelada."
    )


class CancellationResponse(BaseModel):
    """Resposta do passo 3: status legivel + dados brutos do BB quando houver."""
    status: str = Field(..., description="Status do cancelamento.")
    mensagem: str = Field(..., description="Mensagem de retorno do cancelamento.")
    dados_cancelamento: Optional[dict] = Field(None, description="Dados originais retornados pela API se houver.")
