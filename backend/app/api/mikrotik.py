from fastapi import APIRouter, HTTPException, status

from app.models.mikrotik import DeviceSummary, MikroTikConnection
from app.services.routeros import (
    MikroTikAuthenticationError,
    MikroTikConnectionError,
    MikroTikResponseError,
    MikroTikTimeoutError,
    MikroTikTLSVerificationError,
    discover_device,
)


router = APIRouter(prefix="/api/mikrotik", tags=["mikrotik"])


@router.post("/discover", response_model=DeviceSummary)
def discover_mikrotik(connection: MikroTikConnection) -> DeviceSummary:
    """Connect to one MikroTik and return its basic identity."""
    try:
        return discover_device(connection)
    except MikroTikAuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha não foram aceitos pelo MikroTik.",
        ) from error
    except MikroTikTimeoutError as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="O MikroTik demorou demais para responder. Verifique o IP, a porta e a rede.",
        ) from error
    except MikroTikTLSVerificationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Não foi possível validar o certificado TLS do MikroTik. "
                "Confira o certificado ou desative a validação somente em uma rede confiável."
            ),
        ) from error
    except MikroTikResponseError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "A conexão foi estabelecida, mas o MikroTik não retornou "
                "os dados básicos esperados."
            ),
        ) from error
    except MikroTikConnectionError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Não foi possível conectar ao MikroTik. Confirme se a API está "
                "habilitada e se o IP e a porta estão corretos."
            ),
        ) from error

