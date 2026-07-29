import { useEffect, useState } from "react";

const API_STATES = {
  checking: {
    label: "Verificando backend",
    className: "status status--checking",
  },
  online: {
    label: "Backend disponível",
    className: "status status--online",
  },
  offline: {
    label: "Backend indisponível",
    className: "status status--offline",
  },
};

function App() {
  const [apiState, setApiState] = useState("checking");

  useEffect(() => {
    const controller = new AbortController();

    async function checkApi() {
      try {
        const response = await fetch("/api/health", {
          signal: controller.signal,
        });
        const data = await response.json();

        setApiState(response.ok && data.status === "ok" ? "online" : "offline");
      } catch (error) {
        if (error.name !== "AbortError") {
          setApiState("offline");
        }
      }
    }

    checkApi();

    return () => controller.abort();
  }, []);

  const currentState = API_STATES[apiState];

  return (
    <main className="page">
      <section className="hero">
        <div className="brand-mark" aria-hidden="true">
          O
        </div>

        <div>
          <p className="eyebrow">MikroTik Field Assistant</p>
          <h1>ORION</h1>
          <p className="tagline">Configure. Monitore. Valide.</p>
        </div>
      </section>

      <section className="card" aria-labelledby="initial-stage-title">
        <div>
          <p className="card-kicker">ORION Field V1</p>
          <h2 id="initial-stage-title">Estrutura inicial pronta</h2>
          <p>
            O próximo passo será conectar a um MikroTik e identificar o
            equipamento pela API do RouterOS.
          </p>
        </div>

        <div className={currentState.className} role="status">
          <span className="status-dot" aria-hidden="true" />
          {currentState.label}
        </div>
      </section>
    </main>
  );
}

export default App;
