def validar_observacao_reprovado(registro: dict) -> dict:
    """
    RN07 - Observação Obrigatória para Reprovados

    Avalia a coluna 'observacao' de um registro. Se o 'status'
    for 'REPROVADO', a observação não pode estar vazia.

    Args:
        registro (dict): Dicionário representando uma linha da planilha.
                         Deve conter as chaves 'status' e 'observacao'.

    Returns:
        dict: O registro atualizado. Se a regra for violada, adiciona
              os detalhes do erro na chave 'divergencia_rn07'.
    """
    # Extrai os valores removendo espaços em branco extras e garantindo o formato
    status = str(registro.get("status", "")).strip().upper()
    observacao = str(registro.get("observacao", "")).strip()

    # Cria a chave como uma lista vazia caso o registro ainda não tenha passado por outros erros
    if "divergencias" not in registro:
        registro["divergencias"] = []

    # Aplica a regra RN07
    if status == "REPROVADO" and not observacao:
        registro["divergencias"].append({
            "regra_violada": "RN07",
            "descricao": "Status REPROVADO exige preenchimento da observação.",
            "acao_recomendada": "Encaminhar ao analista para preenchimento",
            "severidade": "Alta"
        })

    return registro