"""Testes unitários para a camada pura de indicadores operacionais (Aula 24)."""

import pytest
from dashboard.servico_validacao import RegistroValidado
from src.operational_indicators import (
    CATALOGO_REGRAS,
    OperationalIndicators,
    RankedRule,
    _percentual,
    calcular_indicadores,
)


@pytest.mark.unit
def test_percentual_calculo_basico():
    assert _percentual(25, 100) == 25.0
    assert _percentual(1, 0) == 0.0
    assert _percentual(0, 0) == 0.0


@pytest.mark.unit
def test_calcular_indicadores_lista_vazia():
    indicadores = calcular_indicadores([])
    assert indicadores.total_registros == 0
    assert indicadores.registros_validos == 0
    assert indicadores.percentual_validos == 0.0
    assert indicadores.divergencias == 0
    assert indicadores.percentual_divergencias == 0.0
    assert indicadores.ambiguos == 0
    assert indicadores.percentual_ambiguos == 0.0
    assert indicadores.erros_entrada == 0
    assert indicadores.percentual_erros_entrada == 0.0
    assert indicadores.regra_mais_acionada is None
    assert indicadores.taxa_qualidade_entrada == 0.0
    assert indicadores.taxa_revisao_humana == 0.0
    assert indicadores.taxa_retrabalho == 0.0
    assert indicadores.ganho_estimado_minutos == 0.0
    assert indicadores.ranking_regras == ()


@pytest.mark.unit
@pytest.mark.parametrize(
    "classificacao, campo_esperado",
    [
        ("Válido", "registros_validos"),
        ("Divergência", "divergencias"),
        ("Ambíguo", "ambiguos"),
        ("Erro de Entrada", "erros_entrada"),
    ],
)
def test_classificacoes_individuais(classificacao, campo_esperado):
    reg = RegistroValidado(
        lote_id="L01",
        produto="P01",
        linha="L1",
        turno="T1",
        status="APROVADO",
        responsavel="R1",
        data="01/08/2026",
        observacao="",
        data_referencia="01/08/2026",
        classificacao=classificacao,
    )
    indicadores = calcular_indicadores([reg])
    assert getattr(indicadores, campo_esperado) == 1
    assert indicadores.total_registros == 1


@pytest.mark.unit
def test_classificacao_desconhecida_gera_value_error():
    reg = RegistroValidado(
        lote_id="L01",
        produto="P01",
        linha="L1",
        turno="T1",
        status="APROVADO",
        responsavel="R1",
        data="01/08/2026",
        observacao="",
        data_referencia="01/08/2026",
        classificacao="Desconhecido",
    )
    with pytest.raises(ValueError, match="Desconhecido"):
        calcular_indicadores([reg])


@pytest.mark.unit
def test_validacao_tempos_invalidos():
    reg = RegistroValidado(
        lote_id="L01",
        produto="P01",
        linha="L1",
        turno="T1",
        status="APROVADO",
        responsavel="R1",
        data="01/08/2026",
        observacao="",
        data_referencia="01/08/2026",
    )
    with pytest.raises(ValueError, match="negativos"):
        calcular_indicadores([reg], tempo_manual_minutos=-1.0)

    with pytest.raises(ValueError, match="negativos"):
        calcular_indicadores([reg], tempo_automatizado_minutos=-0.5)

    with pytest.raises(ValueError, match="superior"):
        calcular_indicadores(
            [reg], tempo_manual_minutos=1.0, tempo_automatizado_minutos=2.0
        )


@pytest.mark.unit
def test_ranking_ordem_decrescente_e_regra_principal():
    r1 = RegistroValidado(
        lote_id="L01",
        produto="P01",
        linha="L1",
        turno="T1",
        status="APROVADO",
        responsavel="R1",
        data="01/08/2026",
        observacao="",
        data_referencia="01/08/2026",
        regras_aplicadas=["RN06", "RN10"],
        classificacao="Divergência",
    )
    r2 = RegistroValidado(
        lote_id="L02",
        produto="P01",
        linha="L1",
        turno="T1",
        status="APROVADO",
        responsavel="R1",
        data="01/08/2026",
        observacao="",
        data_referencia="01/08/2026",
        regras_aplicadas=["RN06"],
        classificacao="Válido",
    )
    indicadores = calcular_indicadores([r1, r2])

    assert indicadores.regra_mais_acionada is not None
    assert indicadores.regra_mais_acionada.codigo == "RN06"
    assert indicadores.regra_mais_acionada.ocorrencias == 2
    assert indicadores.regra_mais_acionada.percentual_total == 100.0

    ranking = indicadores.ranking_regras
    assert len(ranking) == 2
    assert ranking[0].codigo == "RN06"
    assert ranking[0].ocorrencias == 2
    assert ranking[1].codigo == "RN10"
    assert ranking[1].ocorrencias == 1
    assert ranking[1].percentual_total == 50.0


@pytest.mark.unit
def test_ranking_empate_preserva_primeira_ocorrencia():
    r1 = RegistroValidado(
        lote_id="L01",
        produto="P01",
        linha="L1",
        turno="T1",
        status="APROVADO",
        responsavel="R1",
        data="01/08/2026",
        observacao="",
        data_referencia="01/08/2026",
        regras_aplicadas=["RN04", "RN05"],
        classificacao="Divergência",
    )
    indicadores = calcular_indicadores([r1])
    ranking = indicadores.ranking_regras
    assert len(ranking) == 2
    assert ranking[0].codigo == "RN04"
    assert ranking[1].codigo == "RN05"


@pytest.mark.unit
def test_um_registro_multiplas_regras():
    r1 = RegistroValidado(
        lote_id="",
        produto="",
        linha="",
        turno="",
        status="",
        responsavel="",
        data="",
        observacao="",
        data_referencia="01/08/2026",
        regras_aplicadas=["RN01", "RN02", "RN03", "RN04"],
        classificacao="Erro de Entrada",
    )
    indicadores = calcular_indicadores([r1])
    assert len(indicadores.ranking_regras) == 4
    for item in indicadores.ranking_regras:
        assert item.ocorrencias == 1
        assert item.percentual_total == 100.0


@pytest.mark.unit
def test_cenario_completo_10_indicadores():
    # Simulando um conjunto representativo
    registros = []
    # 60 Válidos (com RN06 em 10)
    for i in range(60):
        regras = ["RN06"] if i < 10 else []
        registros.append(
            RegistroValidado(
                lote_id=f"V{i}",
                produto="P1",
                linha="L1",
                turno="T1",
                status="APROVADO",
                responsavel="R1",
                data="01/08/2026",
                observacao="",
                data_referencia="01/08/2026",
                regras_aplicadas=regras,
                classificacao="Válido",
            )
        )
    # 20 Divergências (RN05 em 15, RN10 em 5)
    for i in range(20):
        regras = ["RN05"] if i < 15 else ["RN10"]
        registros.append(
            RegistroValidado(
                lote_id=f"D{i}",
                produto="P1",
                linha="L1",
                turno="T1",
                status="REPROVADO",
                responsavel="R1",
                data="01/08/2026",
                observacao="",
                data_referencia="01/08/2026",
                regras_aplicadas=regras,
                classificacao="Divergência",
            )
        )
    # 8 Ambíguos (RN09)
    for i in range(8):
        registros.append(
            RegistroValidado(
                lote_id=f"A{i}",
                produto="P1",
                linha="L1",
                turno="T1",
                status="ANALISANDO",
                responsavel="R1",
                data="01/08/2026",
                observacao="",
                data_referencia="01/08/2026",
                regras_aplicadas=["RN09"],
                classificacao="Ambíguo",
            )
        )
    # 12 Erros de Entrada (RN01)
    for i in range(12):
        registros.append(
            RegistroValidado(
                lote_id=f"E{i}",
                produto="P1",
                linha="L1",
                turno="T1",
                status="APROVADO",
                responsavel="R1",
                data="01/08/2026",
                observacao="",
                data_referencia="01/08/2026",
                regras_aplicadas=["RN01"],
                classificacao="Erro de Entrada",
            )
        )

    # Total = 100
    indicadores = calcular_indicadores(
        registros, tempo_manual_minutos=2.0, tempo_automatizado_minutos=0.25
    )

    assert indicadores.total_registros == 100
    assert indicadores.registros_validos == 60
    assert indicadores.percentual_validos == 60.0
    assert indicadores.divergencias == 20
    assert indicadores.percentual_divergencias == 20.0
    assert indicadores.ambiguos == 8
    assert indicadores.percentual_ambiguos == 8.0
    assert indicadores.erros_entrada == 12
    assert indicadores.percentual_erros_entrada == 12.0
    assert indicadores.taxa_qualidade_entrada == 88.0
    assert indicadores.taxa_revisao_humana == 8.0
    assert indicadores.taxa_retrabalho == 20.0

    # Ganho: 100 * (2.0 - 0.25) = 175.0 minutos
    assert indicadores.tempo_manual_minutos == 2.0
    assert indicadores.tempo_automatizado_minutos == 0.25
    assert indicadores.ganho_estimado_minutos == 175.0

    # Regra mais acionada: RN05 com 15 ocorrências
    assert indicadores.regra_mais_acionada is not None
    assert indicadores.regra_mais_acionada.codigo == "RN05"
    assert indicadores.regra_mais_acionada.ocorrencias == 15
    assert indicadores.regra_mais_acionada.percentual_total == 15.0
    assert (
        indicadores.regra_mais_acionada.nome
        == CATALOGO_REGRAS["RN05"]
    )
