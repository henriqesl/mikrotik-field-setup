# ORION — MikroTik Field Assistant

O ORION simplifica a leitura, o monitoramento e o diagnóstico de equipamentos MikroTik para equipes de campo. Ele não substitui o RouterOS, WinBox ou WebFig: apresenta os dados mais importantes do enlace com explicações diretas.

> Configure. Monitore. Valide.

## ORION Field V1

A V1 conecta diretamente ao RouterOS e oferece:

- identificação de modelo, versão, arquitetura e pacote Wi-Fi;
- suporte às pilhas `wifi`, `wifiwave2` e `wireless`;
- leitura de interfaces, modo AP/Station, SSID, canal e bridge;
- registration table, sinal, taxas TX/RX e tempo de associação;
- monitoramento automático e modo rápido de alinhamento;
- ping com perda e latências média e máxima;
- avaliação individual das métricas e saúde ponderada do enlace;
- diagnóstico estrutural de bridge, portas e IP de gerenciamento;
- validação manual de gateway, ARP e acesso externo por ICMP.

Os dados são lidos da API do RouterOS. Interpretações e valores calculados são apresentados separadamente. Não existe banco de dados e as credenciais permanecem somente na memória durante a conexão.

## Tecnologias

- React 19 e Vite no frontend;
- FastAPI no backend;
- `routeros-py` para a API binária do RouterOS;
- pytest para os testes do backend.

## Executar localmente

Requisitos: Node.js, Python 3.11 ou superior e um MikroTik com o serviço API habilitado.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

O backend fica disponível em `http://127.0.0.1:8000`.

### Frontend

Em outro terminal:

```powershell
cd frontend
npm ci
npm run dev
```

O frontend usa `http://localhost:5174`. A porta foi fixada com `strictPort`, portanto o Vite avisará claramente caso ela também esteja ocupada.

## Testes e build

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

```powershell
cd frontend
npm run build
npm audit --audit-level=high
```

## Modo offline

O arquivo `mikrotik-generator.html` continua sendo o ORION Setup offline. Ele gera scripts `.rsc` para enlace, rede básica e Gateway LoRa sem depender do backend.

## Limites conhecidos da V1

- conexão somente por IPv4 e RouterOS API;
- sem descoberta ou comunicação por MAC;
- sem configuração direta, reset ou alterações no equipamento;
- sem banco de dados, histórico, relatórios ou autenticação de usuários;
- ICMP pode ser bloqueado, portanto um teste externo sem resposta não prova sozinho que a internet está indisponível;
- validação final em equipamentos físicos ainda é necessária antes de uso operacional.

## Evolução planejada

A V2 poderá adicionar configuração direta e assistida de enlaces, com pré-visualização, backup e validação antes de aplicar mudanças. C++ não faz parte da V1 e somente deverá entrar futuramente se houver uma necessidade concreta de desempenho, sockets ou diagnóstico avançado.
