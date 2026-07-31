import pytest

from app.services.evaluation import (
    assess_association,
    assess_average_latency,
    assess_maximum_latency,
    assess_packet_loss,
    assess_signal,
)


@pytest.mark.parametrize(
    ("value", "label"),
    [
        (-61, "Muito bom"),
        (-68, "Bom"),
        (-75, "Atenção"),
        (-84, "Fraco"),
        (-90, "Muito fraco"),
        (None, "Indisponível"),
    ],
)
def test_signal_assessment_ranges(value, label) -> None:
    assert assess_signal(value).label == label


@pytest.mark.parametrize(
    ("value", "label"),
    [
        (0, "Excelente"),
        (1, "Muito baixa"),
        (5, "Atenção"),
        (20, "Instável"),
        (40, "Crítica"),
    ],
)
def test_packet_loss_assessment_ranges(value, label) -> None:
    assert assess_packet_loss(value).label == label


def test_latency_assessments_keep_average_and_peak_independent() -> None:
    assert assess_average_latency(3).label == "Excelente"
    assert assess_maximum_latency(52).label == "Atenção"


def test_association_does_not_infer_legacy_authorization() -> None:
    assessment = assess_association(None)

    assert assessment.status == "informational"
    assert assessment.label == "Registrado"
