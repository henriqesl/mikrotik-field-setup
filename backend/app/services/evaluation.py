from app.models.mikrotik import MetricAssessment


def _assessment(
    status: str,
    label: str,
    explanation: str,
) -> MetricAssessment:
    return MetricAssessment(
        status=status,
        label=label,
        explanation=explanation,
    )


def assess_signal(signal_dbm: int | None) -> MetricAssessment:
    if signal_dbm is None:
        return _assessment(
            "unavailable",
            "Indisponível",
            "O equipamento não informou o nível de sinal.",
        )
    if signal_dbm >= -65:
        return _assessment(
            "excellent",
            "Muito bom",
            "Há boa margem de sinal para o enlace.",
        )
    if signal_dbm >= -72:
        return _assessment(
            "good",
            "Bom",
            "O nível de sinal está adequado.",
        )
    if signal_dbm >= -79:
        return _assessment(
            "attention",
            "Atenção",
            "O sinal tem margem reduzida; valide perda e latência.",
        )
    if signal_dbm >= -86:
        return _assessment(
            "weak",
            "Fraco",
            "O enlace pode funcionar, mas tem pouca margem.",
        )
    return _assessment(
        "critical",
        "Muito fraco",
        "O sinal exige alinhamento e validação do desempenho.",
    )


def assess_association(authorized: bool | None) -> MetricAssessment:
    if authorized is True:
        return _assessment(
            "good",
            "Autorizado",
            "O peer concluiu a autenticação.",
        )
    if authorized is False:
        return _assessment(
            "critical",
            "Não autorizado",
            "O peer aparece na tabela, mas não concluiu a autenticação.",
        )
    return _assessment(
        "informational",
        "Registrado",
        "A pilha Wireless não informou a autorização separadamente.",
    )


def assess_packet_loss(packet_loss_percent: float) -> MetricAssessment:
    if packet_loss_percent == 0:
        return _assessment(
            "excellent",
            "Excelente",
            "Todos os pacotes receberam resposta.",
        )
    if packet_loss_percent <= 1:
        return _assessment(
            "good",
            "Muito baixa",
            "A perda foi pequena, mas merece observação.",
        )
    if packet_loss_percent <= 5:
        return _assessment(
            "attention",
            "Atenção",
            "Há perda de pacotes; repita o teste para confirmar.",
        )
    if packet_loss_percent <= 20:
        return _assessment(
            "weak",
            "Instável",
            "A perda compromete a estabilidade; repita e investigue.",
        )
    return _assessment(
        "critical",
        "Crítica",
        "A perda é alta e compromete a comunicação.",
    )


def assess_average_latency(latency_ms: float | None) -> MetricAssessment:
    if latency_ms is None:
        return _assessment(
            "unavailable",
            "Sem resposta",
            "Não houve resposta suficiente para medir a média.",
        )
    if latency_ms <= 5:
        return _assessment(
            "excellent",
            "Excelente",
            "A latência média está muito baixa.",
        )
    if latency_ms <= 20:
        return _assessment(
            "good",
            "Boa",
            "A latência média está adequada.",
        )
    if latency_ms <= 50:
        return _assessment(
            "attention",
            "Atenção",
            "A latência média está acima do ideal para um enlace local.",
        )
    if latency_ms <= 100:
        return _assessment(
            "weak",
            "Alta",
            "A latência média pode afetar o uso do enlace.",
        )
    return _assessment(
        "critical",
        "Muito alta",
        "A latência média indica uma comunicação degradada.",
    )


def assess_maximum_latency(latency_ms: float | None) -> MetricAssessment:
    if latency_ms is None:
        return _assessment(
            "unavailable",
            "Sem resposta",
            "Não houve resposta suficiente para medir o pico.",
        )
    if latency_ms <= 10:
        return _assessment(
            "excellent",
            "Excelente",
            "Não foram observados picos relevantes.",
        )
    if latency_ms <= 50:
        return _assessment(
            "good",
            "Bom",
            "O maior tempo de resposta permanece aceitável.",
        )
    if latency_ms <= 100:
        return _assessment(
            "attention",
            "Atenção",
            "Foi observado um pico de latência.",
        )
    if latency_ms <= 200:
        return _assessment(
            "weak",
            "Alto",
            "O pico pode indicar interferência ou congestionamento.",
        )
    return _assessment(
        "critical",
        "Muito alto",
        "O pico de latência indica instabilidade importante.",
    )

