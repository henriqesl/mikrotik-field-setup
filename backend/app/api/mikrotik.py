from fastapi import APIRouter, HTTPException, status

from app.models.mikrotik import (
    DeviceSummary,
    MikroTikConnection,
    PingRequest,
    PingResult,
)
from app.services.routeros import (
    MikroTikAuthenticationError,
    MikroTikError,
    MikroTikResponseError,
    MikroTikTimeoutError,
    MikroTikTLSVerificationError,
    discover_device,
    ping_device,
)


router = APIRouter(prefix="/api/mikrotik", tags=["mikrotik"])


def _friendly_http_error(error: MikroTikError) -> HTTPException:
    if isinstance(error, MikroTikAuthenticationError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha não foram aceitos pelo MikroTik.",
        )
    if isinstance(error, MikroTikTimeoutError):
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=(
                "O MikroTik demorou demais para responder. "
                "Verifique o IP, a porta e a rede."
            ),
        )
    if isinstance(error, MikroTikTLSVerificationError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Não foi possível validar o certificado TLS do MikroTik. "
                "Confira o certificado ou desative a validação somente em uma rede confiável."
            ),
        )
    if isinstance(error, MikroTikResponseError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "O MikroTik respondeu, mas o ORION não conseguiu interpretar "
                "todos os dados recebidos."
            ),
        )

    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=(
            "Não foi possível conectar ao MikroTik. Confirme se a API está "
            "habilitada e se o IP e a porta estão corretos."
        ),
    )


@router.post("/discover", response_model=DeviceSummary)
def discover_mikrotik(connection: MikroTikConnection) -> DeviceSummary:
    """Connect to one MikroTik and return its basic identity."""
    try:
        return discover_device(connection)
    except MikroTikError as error:
        raise _friendly_http_error(error) from error


@router.post(
    "/ping",
    response_model=PingResult,
    response_model_exclude_none=True,
)
def ping_from_mikrotik(request: PingRequest) -> PingResult:
    """Run a short ICMP test from the connected MikroTik."""
    try:
        return ping_device(request)
    except MikroTikError as error:
        raise _friendly_http_error(error) from error
