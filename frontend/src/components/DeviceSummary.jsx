const DEVICE_FIELDS = [
  ["Identidade", "identity"],
  ["Modelo", "model"],
  ["RouterOS", "routeros_version"],
  ["Arquitetura", "architecture"],
];

const STACK_LABELS = {
  wifi: "WiFi moderno",
  wifiwave2: "WiFiWave2",
  wireless: "Wireless legado",
  not_detected: "Não detectado",
};

function interfaceStatus(wifiInterface) {
  if (wifiInterface.disabled === true) {
    return "Desativada";
  }

  if (wifiInterface.running === true) {
    return "Ativa";
  }

  if (wifiInterface.running === false) {
    return "Sem enlace";
  }

  return "Estado não informado";
}

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

      <div className="wifi-heading">
        <div>
          <p className="card-kicker">Rádio</p>
          <h3>Interfaces Wi-Fi</h3>
        </div>
        <div className="wifi-meta">
          <span>{STACK_LABELS[device.wifi_stack]}</span>
          <span>{device.wifi_package || "Pacote não informado"}</span>
        </div>
      </div>

      {device.wifi_interfaces.length > 0 ? (
        <div className="interface-list">
          {device.wifi_interfaces.map((wifiInterface, index) => (
            <article
              className="interface-card"
              key={wifiInterface.name || wifiInterface.mac_address || index}
            >
              <div>
                <strong>{wifiInterface.name || "Interface sem nome"}</strong>
                <span>{wifiInterface.mac_address || "MAC não informado"}</span>
              </div>
              <span
                className={
                  wifiInterface.running && !wifiInterface.disabled
                    ? "interface-state interface-state--active"
                    : "interface-state"
                }
              >
                {interfaceStatus(wifiInterface)}
              </span>
            </article>
          ))}
        </div>
      ) : (
        <p className="empty-state">
          Nenhuma interface Wi-Fi foi informada pelo equipamento.
        </p>
      )}
    </section>
  );
}

export default DeviceSummary;
