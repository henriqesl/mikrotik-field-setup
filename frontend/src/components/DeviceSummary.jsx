const DEVICE_FIELDS = [
  ["Identidade", "identity"],
  ["Modelo", "model"],
  ["RouterOS", "routeros_version"],
  ["Arquitetura", "architecture"],
];

function DeviceSummary({ device }) {
  return (
    <section className="device-card" aria-labelledby="device-title">
      <div className="section-heading">
        <div>
          <p className="card-kicker">Dados reais do RouterOS</p>
          <h2 id="device-title">Equipamento identificado</h2>
        </div>
        <span className="success-badge">Conectado</span>
      </div>

      <dl className="device-grid">
        {DEVICE_FIELDS.map(([label, key]) => (
          <div className="device-field" key={key}>
            <dt>{label}</dt>
            <dd>{device[key] || "Não informado pelo equipamento"}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export default DeviceSummary;

