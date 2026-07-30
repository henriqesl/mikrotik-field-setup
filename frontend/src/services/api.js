export async function discoverDevice(connection) {
  let response;

  try {
    response = await fetch("/api/mikrotik/discover", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(connection),
    });
  } catch {
    throw new Error(
      "O backend do ORION não está disponível. Inicie o FastAPI e tente novamente.",
    );
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.detail ||
        "Não foi possível concluir a comunicação com o backend do ORION.",
    );
  }

  return data;
}
