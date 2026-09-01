"""Ponto de entrada do bot de conferência de lotes.

O fluxo implementado segue o BPMN da versão inicial: carregar a planilha,
validar a estrutura, executar RN02-RN07, gerar as evidências e registrar o
resultado da execução.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from config import settings
from src.core.base_referencia import carregar_base_referencia, verificar_existencia_lote
from src.ml.classificador_divergencia import ClassificadorDivergencia, ResultadoClassificacao
from src.core.regras_negocio import normalizar_status, validar_dominio_status
from src.reporting.relatorio import gerar_relatorio_divergencias
from src.reporting.sistema_alertas import SistemaAlertas
from src.utils.time_utils import now_local
from src.core.validacao import (
    DATA_REFERENCIA_PADRAO,
    ErroEstrutural,
    carregar_planilha,
    valida_campos_obrigatorios,
    valida_estrutura,
    validar_data_referencia,
    validar_observacao_reprovado,
)



ARQUIVO_PADRAO = settings.default_input_file
DIRETORIO_SAIDA_PADRAO = settings.output_dir


def _indice_original(linha: pd.Series, indice: Any) -> int:
    """Obtém o índice original depois que uma regra resetou o DataFrame."""
    valor = linha.get("index", indice)
    return int(valor) if pd.notna(valor) else int(indice)


def _erro(
    *,
    indice: int,
    lote_id: Any,
    regra: str,
    descricao: Any,
    acao: str,
    severidade: str,
    origem_decisao: str = "fallback",
    confianca_ml: float = 0.0,
    causa_provavel_ml: str = "nao_classificado",
    motivo_fallback: str = "",
) -> dict[str, Any]:
    """Cria o formato comum consumido pelo relatório e pelo cálculo de válidos."""
    return {
        "_indice": indice,
        "lote_id": lote_id,
        "regra_violada": regra,
        "descricao_do_erro": str(descricao),
        "acao_recomendada": acao,
        "severidade": severidade,
        "origem_decisao": origem_decisao,
        "confianca_ml": confianca_ml,
        "causa_provavel_ml": causa_provavel_ml,
        "motivo_fallback": motivo_fallback,
    }


def _log_exception(
    logger: logging.Logger | None,
    exc: BaseException,
    *,
    context: str,
    lote_id: Any = "N/A",
) -> None:
    """Registra exceções sem incluir credenciais ou dados sensíveis."""
    if logger is not None:
        logger.error(
            "%s | lote_id=%s | erro=%s",
            context,
            lote_id if lote_id not in (None, "") else "N/A",
            exc,
        )


def _coletar_erros(
    df: pd.DataFrame,
    arquivo: str | None,
    *,
    logger: logging.Logger | None = None,
    lotes_validos: set[str] | None = None,
    data_referencia: str = DATA_REFERENCIA_PADRAO,
) -> tuple[list[dict[str, Any]], pd.DataFrame]:
    """Executa RN02-RN07 e retorna erros e casos para revisão."""
    erros: list[dict[str, Any]] = []

    erros_rn02 = valida_campos_obrigatorios(df)
    for indice, linha in erros_rn02.iterrows():
        original = _indice_original(linha, indice)
        erros.append(
            _erro(
                indice=original,
                lote_id=linha.get("lote_id"),
                regra="RN02",
                descricao=f"Campos obrigatórios vazios: {linha['campos_vazios']}.",
                acao="Preencher os campos obrigatórios.",
                severidade="Alta",
            )
        )

    erros_rn01_data = validar_data_referencia(
        df,
        data_referencia=data_referencia,
    )
    for indice, linha in erros_rn01_data.iterrows():
        original = _indice_original(linha, indice)
        erros.append(
            _erro(
                indice=original,
                lote_id=linha.get("lote_id"),
                regra="RN01",
                descricao=linha["divergencia_rn01"],
                acao="Corrigir a data para a referência do processo.",
                severidade="Média",
            )
        )

    if lotes_validos is None:
        if arquivo is None:
            raise ValueError(
                "A base de referência ou o arquivo de origem é obrigatório."
            )
        lotes_validos = carregar_base_referencia(arquivo)
    erros_rn03 = verificar_existencia_lote(df, lotes_validos)
    for indice, linha in erros_rn03.iterrows():
        original = _indice_original(linha, indice)
        erros.append(
            _erro(
                indice=original,
                lote_id=linha.get("lote_id"),
                regra="RN03",
                descricao=linha["divergencia_rn03"],
                acao="Confirmar o cadastro do lote na Base_Referencia.",
                severidade="Alta",
            )
        )

    df_normalizado = normalizar_status(df)
    erros_rn05 = df_normalizado[df_normalizado["divergencia_rn05"].notna()]
    for indice, linha in erros_rn05.iterrows():
        erros.append(
            _erro(
                indice=int(indice),
                lote_id=linha.get("lote_id"),
                regra="RN05",
                descricao=linha["divergencia_rn05"],
                acao="Registrar a normalização e seguir o fluxo automático.",
                severidade="Baixa",
            )
        )

    erros_rn06 = validar_dominio_status(df_normalizado)
    revisao_humana: list[dict[str, Any]] = []
    for indice, linha in erros_rn06.iterrows():
        original = _indice_original(linha, indice)
        descricao = linha["divergencia_rn04"]
        erros.append(
            _erro(
                indice=original,
                lote_id=linha.get("lote_id"),
                regra="RN06",
                descricao=descricao,
                acao="Encaminhar para revisão humana sem decidir o status.",
                severidade="Alta",
            )
        )
        revisao_humana.append(
            {
                "lote_id": linha.get("lote_id"),
                "status_original": linha.get("status_original", linha.get("status")),
                "status": linha.get("status"),
                "data": linha.get("data"),
                "descricao_do_erro": descricao,
                "observacao_analista": "",
            }
        )

    for indice, registro in enumerate(df_normalizado.to_dict("records")):
        try:
            registro_validado = validar_observacao_reprovado(registro)
            for divergencia in registro_validado.get("divergencias", []):
                erros.append(
                    _erro(
                        indice=indice,
                        lote_id=registro.get("lote_id"),
                        regra="RN07",
                        descricao=divergencia["descricao"],
                        acao=divergencia["acao_recomendada"],
                        severidade=divergencia["severidade"],
                    )
                )
        except (KeyError, TypeError, ValueError) as exc:
            _log_exception(
                logger,
                exc,
                context="Falha na validação da observação",
                lote_id=registro.get("lote_id"),
            )
            erros.append(
                _erro(
                    indice=indice,
                    lote_id=registro.get("lote_id"),
                    regra="ERRO_PROCESSAMENTO",
                    descricao="Falha controlada durante a validação do registro.",
                    acao="Encaminhar o lote para revisão técnica.",
                    severidade="Alta",
                )
            )

    return erros, pd.DataFrame(revisao_humana)


def _consolidar_erros(erros: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa falhas do mesmo registro em uma linha auditável do relatório."""
    agrupados: dict[int, dict[str, Any]] = {}
    for erro in erros:
        indice = int(erro["_indice"])
        atual = agrupados.setdefault(
            indice,
            {
                "_indice": indice,
                "lote_id": erro.get("lote_id"),
                "_regras": [],
                "_descricoes": [],
                "_acoes": [],
                "_severidades": [],
                "origem_decisao": erro.get("origem_decisao", "fallback"),
                "confianca_ml": erro.get("confianca_ml", 0.0),
                "causa_provavel_ml": erro.get("causa_provavel_ml", "nao_classificado"),
                "motivo_fallback": erro.get("motivo_fallback", ""),
            },
        )
        if erro["regra_violada"] not in atual["_regras"]:
            atual["_regras"].append(erro["regra_violada"])
        atual["_descricoes"].append(erro["descricao_do_erro"])
        atual["_acoes"].append(erro["acao_recomendada"])
        atual["_severidades"].append(erro["severidade"])
        if erro.get("origem_decisao") == "ml":
            atual["origem_decisao"] = "ml"
            atual["confianca_ml"] = erro.get("confianca_ml", 0.0)
            atual["causa_provavel_ml"] = erro.get("causa_provavel_ml", "nao_classificado")
            atual["motivo_fallback"] = ""

    resultado: list[dict[str, Any]] = []
    for atual in agrupados.values():
        resultado.append(
            {
                "_indice": atual["_indice"],
                "lote_id": atual["lote_id"],
                "regra_violada": "; ".join(atual["_regras"]),
                "descricao_do_erro": " | ".join(atual["_descricoes"]),
                "acao_recomendada": " | ".join(dict.fromkeys(atual["_acoes"])),
                "severidade": "Alta"
                if "Alta" in atual["_severidades"]
                else "Média",
                "origem_decisao": atual["origem_decisao"],
                "confianca_ml": atual["confianca_ml"],
                "causa_provavel_ml": atual["causa_provavel_ml"],
                "motivo_fallback": atual["motivo_fallback"],
            }
        )
    return resultado



def _escrever_log(
    *,
    caminho: Path,
    inicio: datetime,
    fim: datetime,
    arquivo: Path,
    total_registros: int,
    total_divergencias: int,
    status: str,
    hash_md5: str | None = None,
    erro: str | None = None,
) -> Path:
    """Escreve o log de execução definido no PDD seção 15."""
    dados: dict[str, Any] = {
        "timestamp_inicio": inicio.isoformat(),
        "timestamp_fim": fim.isoformat(),
        "arquivo_processado": str(arquivo),
        "hash_md5": hash_md5,
        "total_registros": total_registros,
        "total_divergencias": total_divergencias,
        "status_execucao": status,
    }
    if erro:
        dados["erro"] = erro

    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return caminho


def _calcular_md5(arquivo: Path) -> str:
    """Calcula o hash MD5 do arquivo para rastreabilidade do PDD."""
    hash_md5 = hashlib.md5()
    with arquivo.open("rb") as stream:
        for bloco in iter(lambda: stream.read(1024 * 1024), b""):
            hash_md5.update(bloco)
    return hash_md5.hexdigest()


def validar_dataframe(
    df: pd.DataFrame,
    *,
    lotes_validos: set[str],
    diretorio_saida: str | Path,
    data_referencia: str = DATA_REFERENCIA_PADRAO,
    logger: logging.Logger | None = None,
    indices_excluidos: set[int] | None = None,
    rejeicoes_cadastro: list[dict[str, Any]] | None = None,
    falhas_tecnicas: list[dict[str, Any]] | None = None,
    classificador: ClassificadorDivergencia | None = None,
    sistema_alertas: SistemaAlertas | None = None,
) -> dict[str, Any]:
    """Aplica RN01-RN07 a dados vindos de Excel ou DataPool.

    Esta função contém o núcleo compartilhado do bot validador. A adaptação de
    entrada é responsável apenas por montar o DataFrame e fornecer o snapshot
    da base de referência.
    """
    valida_estrutura(df)
    erros, revisao_humana = _coletar_erros(
        df,
        None,
        logger=logger,
        lotes_validos=lotes_validos,
        data_referencia=data_referencia or DATA_REFERENCIA_PADRAO,
    )
    df_normalizado = normalizar_status(df)

    # Classificação Híbrida RPA+ML para os itens com divergência
    clf = classificador or ClassificadorDivergencia(
        api_url=settings.ml_api_url,
        enabled=settings.ml_enabled,
        timeout_ms=settings.ml_timeout_ms,
        confianca_minima=settings.ml_confianca_minima,
        logger_instance=logger,
    )
    alertas = sistema_alertas or SistemaAlertas(
        telegram_token=settings.telegram_token,
        telegram_chat_id=settings.telegram_chat_id,
        whatsapp_enabled=settings.whatsapp_enabled,
        twilio_account_sid=settings.twilio_account_sid,
        twilio_auth_token=settings.twilio_auth_token,
        whatsapp_to=settings.whatsapp_to,
        whatsapp_from=settings.whatsapp_from,
        email_enabled=settings.email_enabled,
        smtp_server=settings.smtp_server,
        smtp_port=settings.smtp_port,
        email_from=settings.email_from,
        email_to=settings.email_to,
        gmail_enabled=settings.gmail_enabled,
        gmail_credentials_file=settings.gmail_credentials_file,
        gmail_token_file=settings.gmail_token_file,
        gmail_from=settings.gmail_from,
        gmail_to=settings.gmail_to,
        logger_instance=logger,
    )

    for erro in erros:
        idx = int(erro["_indice"])
        row = df_normalizado.iloc[idx] if idx < len(df_normalizado) else {}
        lote_id = str(erro.get("lote_id") or "")
        obs = str(row.get("observacao", "") if hasattr(row, "get") else "")
        status_raw = str(row.get("status_original", row.get("status", "")) if hasattr(row, "get") else "")
        turno = str(row.get("turno", "") if hasattr(row, "get") else "")

        res_ml: ResultadoClassificacao = clf.classificar(
            lote_id=lote_id,
            observacao=obs,
            status_raw=status_raw,
            turno=turno,
        )
        erro["origem_decisao"] = res_ml.origem_decisao
        erro["confianca_ml"] = res_ml.confianca_ml
        erro["causa_provavel_ml"] = res_ml.causa_provavel_ml
        erro["motivo_fallback"] = res_ml.motivo_fallback or ""

    indices_divergentes = {int(erro["_indice"]) for erro in erros}
    indices_nao_validados = indices_divergentes | set(indices_excluidos or set())
    indices_validos = [
        indice
        for indice in df_normalizado.index
        if indice not in indices_nao_validados
    ]
    lotes_validados = df_normalizado.loc[indices_validos].copy()
    erros_consolidados = _consolidar_erros(erros)

    # Dispara alerta se 100% dos itens de divergência operaram em fallback de ML
    if erros_consolidados and clf.operando_100_percent_fallback:
        alertas.notificar_pipeline_sem_ml(len(erros_consolidados))

    # Dead Letter file para falhas de dados irrecuperáveis
    if falhas_tecnicas or rejeicoes_cadastro:
        dead_letter_path = settings.dead_letter_file
        dead_letter_gravado = False
        try:
            dead_letter_path.parent.mkdir(parents=True, exist_ok=True)
            with dead_letter_path.open("a", encoding="utf-8") as f:
                for item in list(falhas_tecnicas or []) + list(rejeicoes_cadastro or []):
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            dead_letter_gravado = True
        except Exception as exc:
            if logger:
                logger.warning(f"Não foi possível gravar no dead letter file {dead_letter_path}: {exc}")

        if falhas_tecnicas:
            alertas.notificar(
                mensagem=(
                    f"{len(falhas_tecnicas)} falha(s) técnica(s) ocorreram no "
                    "cadastro web e foram encaminhadas para análise."
                ),
                nivel="ERRO",
                evento="FALHA_TECNICA_CADASTRO",
                anexos=[dead_letter_path] if dead_letter_gravado else (),
            )

    relatorio = gerar_relatorio_divergencias(
        erros_consolidados,
        diretorio_saida,
        lotes_validados=lotes_validados,
        revisao_humana=revisao_humana,
        rejeicoes_cadastro=rejeicoes_cadastro,
        falhas_tecnicas=falhas_tecnicas,
        resumo={
            "total_registros": len(df),
            "total_divergencias": len(erros_consolidados),
            "total_regras_violadas": len(erros),
            "total_lotes_validados": len(lotes_validados),
            "total_revisao_humana": len(revisao_humana),
            "total_rejeicoes_cadastro": len(rejeicoes_cadastro or []),
            "total_falhas_tecnicas": len(falhas_tecnicas or []),
        },
    )

    return {
        "status_execucao": "SUCESSO",
        "relatorio": relatorio,
        "total_registros": len(df),
        "total_divergencias": len(erros_consolidados),
        "total_regras_violadas": len(erros),
        "total_lotes_validados": len(lotes_validados),
        "total_revisao_humana": len(revisao_humana),
        "total_rejeicoes_cadastro": len(rejeicoes_cadastro or []),
        "total_falhas_tecnicas": len(falhas_tecnicas or []),
        "indices_divergentes": sorted(indices_divergentes),
        "divergencias": erros_consolidados,
    }


def executar_bot(
    caminho_arquivo: str | Path = ARQUIVO_PADRAO,
    diretorio_saida: str | Path = DIRETORIO_SAIDA_PADRAO,
    *,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Executa o fluxo inicial do bot e retorna as evidências produzidas.

    O retorno contém ``status_execucao`` e os caminhos de relatório/log. Em
    erro de arquivo ou estrutura, o bot registra o motivo no log e encerra
    sem tentar processar os registros.
    """
    inicio = now_local()
    arquivo = Path(caminho_arquivo)
    saida = Path(diretorio_saida)
    log = saida / "log_execucao.json"
    hash_md5: str | None = None

    if not arquivo.is_file():
        _log_exception(
            logger,
            FileNotFoundError(str(arquivo)),
            context="Arquivo de entrada não encontrado",
        )
        fim = now_local()
        log_path = _escrever_log(
            caminho=log,
            inicio=inicio,
            fim=fim,
            arquivo=arquivo,
            total_registros=0,
            total_divergencias=0,
            status="ERRO_ARQUIVO",
            hash_md5=hash_md5,
            erro=f"Arquivo não encontrado: {arquivo}",
        )
        return {
            "status_execucao": "ERRO_ARQUIVO",
            "log": log_path,
            "relatorio": None,
            "total_registros": 0,
            "total_divergencias": 0,
        }

    try:
        hash_md5 = _calcular_md5(arquivo)
        df = carregar_planilha(str(arquivo))
        valida_estrutura(df)
    except ErroEstrutural as exc:
        _log_exception(logger, exc, context="Estrutura da planilha inválida")
        fim = now_local()
        log_path = _escrever_log(
            caminho=log,
            inicio=inicio,
            fim=fim,
            arquivo=arquivo,
            total_registros=0,
            total_divergencias=0,
            status="ERRO_ESTRUTURA",
            hash_md5=hash_md5,
            erro=str(exc),
        )
        return {
            "status_execucao": "ERRO_ESTRUTURA",
            "log": log_path,
            "relatorio": None,
            "total_registros": 0,
            "total_divergencias": 0,
        }
    except (OSError, ValueError, ImportError) as exc:
        _log_exception(logger, exc, context="Falha na leitura da planilha")
        fim = now_local()
        log_path = _escrever_log(
            caminho=log,
            inicio=inicio,
            fim=fim,
            arquivo=arquivo,
            total_registros=0,
            total_divergencias=0,
            status="ERRO_ARQUIVO",
            hash_md5=hash_md5,
            erro=str(exc),
        )
        return {
            "status_execucao": "ERRO_ARQUIVO",
            "log": log_path,
            "relatorio": None,
            "total_registros": 0,
            "total_divergencias": 0,
        }

    try:
        erros, revisao_humana = _coletar_erros(
            df, str(arquivo), logger=logger
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        _log_exception(logger, exc, context="Falha nas regras de negócio")
        fim = now_local()
        log_path = _escrever_log(
            caminho=log,
            inicio=inicio,
            fim=fim,
            arquivo=arquivo,
            total_registros=len(df),
            total_divergencias=0,
            status="ERRO_PROCESSAMENTO",
            hash_md5=hash_md5,
            erro=str(exc),
        )
        return {
            "status_execucao": "ERRO_PROCESSAMENTO",
            "log": log_path,
            "relatorio": None,
            "total_registros": len(df),
            "total_divergencias": 0,
        }
    df_normalizado = normalizar_status(df)
    indices_divergentes = {erro["_indice"] for erro in erros}
    indices_validos = [
        indice for indice in df_normalizado.index if indice not in indices_divergentes
    ]
    lotes_validados = df_normalizado.loc[indices_validos].copy()

    erros_consolidados = _consolidar_erros(erros)
    relatorio = gerar_relatorio_divergencias(
        erros_consolidados,
        saida,
        lotes_validados=lotes_validados,
        revisao_humana=revisao_humana,
    )
    fim = now_local()
    log_path = _escrever_log(
        caminho=log,
        inicio=inicio,
        fim=fim,
        arquivo=arquivo,
        total_registros=len(df),
        total_divergencias=len(erros_consolidados),
        status="SUCESSO",
        hash_md5=hash_md5,
    )
    return {
        "status_execucao": "SUCESSO",
        "log": log_path,
        "relatorio": relatorio,
        "total_registros": len(df),
        "total_divergencias": len(erros_consolidados),
        "total_regras_violadas": len(erros),
        "total_lotes_validados": len(lotes_validados),
        "total_revisao_humana": len(revisao_humana),
    }


def executar_bot_cli(
    argumentos: list[str] | None = None,
    *,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Expõe o fluxo do bot para execução pelo terminal."""
    parser = argparse.ArgumentParser(description="Bot de conferência de lotes")
    parser.add_argument(
        "arquivo",
        nargs="?",
        default=str(ARQUIVO_PADRAO),
        help="Planilha .xlsx de entrada.",
    )
    parser.add_argument(
        "--saida",
        default=str(DIRETORIO_SAIDA_PADRAO),
        help="Diretório dos relatórios e do log.",
    )
    args = parser.parse_args(argumentos)
    return executar_bot(args.arquivo, args.saida, logger=logger)


def main(argumentos: list[str] | None = None) -> int:
    resultado = executar_bot_cli(argumentos)
    print(json.dumps({key: str(value) for key, value in resultado.items()}, ensure_ascii=False))
    return 0 if resultado["status_execucao"] == "SUCESSO" else 1


if __name__ == "__main__":
    # BotCity e Docker invocam "python bot.py". Delegamos para main.main()
    # que configura logging estruturado (execution_id, bot_id) e Maestro
    # antes de chamar executar_bot_cli() de volta.
    from main import main as _main_entrypoint

    raise SystemExit(_main_entrypoint())
