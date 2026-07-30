import { useEffect, useState } from "react";

import ConnectionForm from "./components/ConnectionForm.jsx";
import DeviceSummary from "./components/DeviceSummary.jsx";
import { discoverDevice } from "./services/api.js";

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
  const [device, setDevice] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

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

  async function handleConnect(connection) {
    setIsLoading(true);
    setErrorMessage("");
    setDevice(null);

    try {
      const discoveredDevice = await discoverDevice(connection);
      setDevice(discoveredDevice);
      return true;
    } catch (error) {
      setErrorMessage(error.message);
      return false;
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="page">
      <header className="app-header">
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

        <div className={currentState.className} role="status">
          <span className="status-dot" aria-hidden="true" />
          {currentState.label}
        </div>
      </header>

      <section className="workspace">
        <ConnectionForm isLoading={isLoading} onConnect={handleConnect} />

        {errorMessage && (
          <div className="error-message" role="alert">
            <strong>Conexão não concluída</strong>
            <span>{errorMessage}</span>
          </div>
        )}

        {device && <DeviceSummary device={device} />}
      </section>
    </main>
  );
}

export default App;
