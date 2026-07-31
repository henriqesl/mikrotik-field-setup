import { useState } from "react";

import { runPing } from "../services/api.js";

function formatLatency(value) {
  return value === null ? "Sem resposta" : `${value} ms`;
}

function PingTest({ connection }) {
  const [target, setTarget] = useState("");
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setIsLoading(true);
    setErrorMessage("");
    setResult(null);

    try {
      setResult(await runPing(connection, target));
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="diagnostic-card" aria-labelledby="ping-title">
      <div className="section-heading">
        <div>
          <p className="card-kicker">Diagnóstico básico</p>
          <h2 id="ping-title">Testar comunicação</h2>
          <p className="section-description">
            O teste parte do MikroTik conectado e envia cinco pacotes.
          </p>
        </div>
        <span className="step-label">Ping</span>
      </div>

      <form className="ping-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>IP do destino</span>
          <input
            inputMode="decimal"
            onChange={(event) => setTarget(event.target.value)}
            placeholder="Outro rádio, gateway ou internet"
            required
            value={target}
          />
        </label>
        <button className="primary-button" disabled={isLoading} type="submit">
          {isLoading ? "Testando…" : "Testar conexão"}
        </button>
      </form>

      {errorMessage && (
        <div className="inline-error" role="alert">
          {errorMessage}
        </div>
      )}

      {result && (
        <div className="ping-result" aria-live="polite">
          <header>
            <div>
              <span>Destino testado</span>
              <strong>{result.target}</strong>
            </div>
            <span
              className={
                result.received > 0
                  ? "ping-state ping-state--reachable"
                  : "ping-state"
              }
            >
              {result.received > 0 ? "Acessível" : "Sem resposta"}
            </span>
          </header>

          <dl className="ping-metrics">
            <div>
              <dt>Perda</dt>
              <dd>{result.packet_loss_percent}%</dd>
            </div>
            <div>
              <dt>Latência média</dt>
              <dd>{formatLatency(result.average_latency_ms)}</dd>
            </div>
            <div>
              <dt>Latência máxima</dt>
              <dd>{formatLatency(result.maximum_latency_ms)}</dd>
            </div>
            <div>
              <dt>Respostas</dt>
              <dd>
                {result.received}/{result.sent}
              </dd>
            </div>
          </dl>

          <p className="measurement-source">
            {result.measurement_source === "routeros_summary"
              ? "Métricas fornecidas pelo RouterOS."
              : "Métricas calculadas pelo ORION a partir das respostas."}
          </p>
        </div>
      )}
    </section>
  );
}

export default PingTest;

