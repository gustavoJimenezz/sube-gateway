// ===== HTML DE LA BARRA =====
// const svgIcon = `
//     <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
//         <rect x="8" y="22" width="84" height="52" rx="10" fill="#00AEEF" />
//         <path d="M 8 50 L 92 50 L 92 64 C 92 69.5 87.5 74 82 74 L 18 74 C 12.5 74 8 69.5 8 64 Z" fill="#0047AB" />
//         <rect x="18" y="32" width="16" height="11" rx="2" fill="#FFD700" stroke="#DAA520" stroke-width="0.8"/>
//         <line x1="26" y1="32" x2="26" y2="43" stroke="#DAA520" stroke-width="0.6"/>
//         <line x1="18" y1="37.5" x2="34" y2="37.5" stroke="#DAA520" stroke-width="0.6"/>
//         <path d="M 75 32 A 8 8 0 0 1 75 44" stroke="white" stroke-width="2" stroke-linecap="round"/>
//         <path d="M 78 29 A 12 12 0 0 1 78 47" stroke="white" stroke-width="1.8" stroke-linecap="round" opacity="0.7"/>
//         <circle cx="72" cy="38" r="1.5" fill="white"/>
//         <text x="20" y="65" font-family="Arial, sans-serif" font-size="14" font-weight="900" fill="white" letter-spacing="1.5">SUBE</text>
//     </svg>
// `;

const svgIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 150 150">
  <!-- Fondo -->
  <rect width="150" height="150" fill="#0079B8"/>

  <!-- Texto SUBE -->
  <g font-family="Arial, Helvetica, sans-serif" font-weight="700" font-size="52">
    <text x="8" y="65" fill="#ffffff">S</text>

    <!-- U blanca -->
    <text x="42" y="65" fill="#ffffff">U</text>

    <!-- Flecha verde -->
    <polygon points="64,10 84,30 76,30 76,65 52,65 52,30 44,30"
             fill="#9EB64B"/>

    <text x="77" y="65" fill="#ffffff">B</text>
    <text x="112" y="65" fill="#ffffff">E</text>
  </g>

  <!-- Iconos inferiores -->
  <g fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">

    <!-- Autobús -->
    <g transform="translate(12,95)">
      <rect x="5" y="10" width="26" height="28" rx="5"/>
      <line x1="10" y1="17" x2="26" y2="17"/>
      <circle cx="11" cy="42" r="2"/>
      <circle cx="25" cy="42" r="2"/>
      <line x1="18" y1="5" x2="18" y2="10"/>
      <line x1="13" y1="5" x2="13" y2="10"/>
      <line x1="23" y1="5" x2="23" y2="10"/>
    </g>

    <!-- Metro -->
    <g transform="translate(57,95)">
      <rect x="5" y="10" width="26" height="28" rx="6"/>
      <line x1="10" y1="17" x2="26" y2="17"/>
      <circle cx="11" cy="42" r="2"/>
      <circle cx="25" cy="42" r="2"/>
      <line x1="2" y1="25" x2="5" y2="25"/>
      <line x1="31" y1="25" x2="34" y2="25"/>
    </g>

    <!-- Tren -->
    <g transform="translate(102,95)">
      <rect x="5" y="10" width="26" height="28" rx="4"/>
      <line x1="18" y1="5" x2="18" y2="10"/>
      <line x1="13" y1="5" x2="13" y2="10"/>
      <line x1="23" y1="5" x2="23" y2="10"/>
      <circle cx="11" cy="42" r="2"/>
      <circle cx="25" cy="42" r="2"/>
      <line x1="12" y1="38" x2="24" y2="38"/>
    </g>

  </g>
</svg>`;

const html = `
    <div id="sube-bar">
        <div class="sube-section-left">
            <div id="sube-logo">
                ${svgIcon}
            </div>
        </div>
        <div class="sube-section-center">
            <button id="btn-abrir" class="sube-btn estado-inicial">Abrir App</button>
            <button id="btn-consultar" class="sube-btn estado-inicial" disabled>Consultar ID</button>
            <button id="btn-acreditar" class="sube-btn estado-inicial" disabled>Acreditar</button>
        </div>
        <div class="sube-section-right">
            <div id="sube-output">
                <span class="value info" id="sube-result">Verificando estado...</span>
            </div>
        </div>
    </div>
`;

// Inyectar HTML cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    document.body.insertAdjacentHTML('afterbegin', html);
    initSubeApp();
});

// Por si el script corre cuando el DOM ya cargó
if (document.readyState === 'interactive' || document.readyState === 'complete') {
    document.body.insertAdjacentHTML('afterbegin', html);
    initSubeApp();
}

// ===== LÓGICA DE LA APLICACIÓN =====
function initSubeApp() {
    const btnAbrir = document.getElementById('btn-abrir');
    const btnConsultar = document.getElementById('btn-consultar');
    const btnAcreditar = document.getElementById('btn-acreditar');
    const resultDisplay = document.getElementById('sube-result');
    const secondaryButtons = [btnConsultar, btnAcreditar];

    if (!btnAbrir) return; // Evitar doble ejecución

    function setResult(text, type = 'info') {
        resultDisplay.textContent = text;
        resultDisplay.className = 'value ' + type;
    }

    function setButtonState(btn, state, text) {
        btn.className = 'sube-btn ' + state;
        btn.textContent = text;
    }

    function setButtonsEnabled(enabled) {
        secondaryButtons.forEach(btn => btn.disabled = !enabled);
    }

    let appAbierta = false;

    // Función para consultar el estado actual en la API local
    async function verificarEstadoInicial() {
        try {
            const response = await fetch('http://127.0.0.1:8000/status', {
                method: 'GET',
                headers: { 'Accept': 'application/json' }
            });

            if (response.ok) {
                // Intentamos leer como texto plano o JSON según responda tu API
                const textData = await response.text();
                let status = textData.trim().toLowerCase();
                
                // Si la API devuelve JSON, intentamos parsearlo de forma segura
                try {
                    const jsonData = JSON.parse(textData);
                    if (jsonData.status) status = jsonData.status.toLowerCase();
                } catch (e) {
                    // Si no es JSON, se queda con el texto plano recibido
                }

                if (status === 'open') {
                    appAbierta = true;
                    setButtonState(btnAbrir, 'estado-abierto', 'App Abierta');
                    setResult('App SUBE conectada', 'success');
                    setButtonsEnabled(true);
                } else {
                    appAbierta = false;
                    setButtonState(btnAbrir, 'estado-inicial', 'Abrir App');
                    setResult('App cerrada (Esperando acción...)', 'info');
                    setButtonsEnabled(false);
                }
            } else {
                throw new Error('API no disponible');
            }
        } catch (error) {
            console.warn('No se pudo verificar el estado inicial con la API local:', error);
            appAbierta = false;
            setButtonState(btnAbrir, 'estado-inicial', 'Abrir App');
            setResult('API local desconectada', 'error');
            setButtonsEnabled(false);
        }
    }

    // Ejecutar verificación al cargar la extensión
    verificarEstadoInicial();

    // Evento Abrir App / Gestionar Apertura
    btnAbrir.addEventListener('click', async function () {
        if (!appAbierta) {
            setButtonState(this, 'estado-abriendo', 'Abriendo...');
            setResult('Enviando petición a /open...', 'info');
            setButtonsEnabled(false);

            try {
                // Llamada al endpoint /open para iniciar la app
                const responseOpen = await fetch('http://127.0.0.1:8000/open', {
                    method: 'POST',
                    headers: { 
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                });

                if (responseOpen.ok) {
                    appAbierta = true;
                    setButtonState(this, 'estado-abierto', 'App Abierta');
                    setResult('App SUBE abierta correctamente', 'success');
                    setButtonsEnabled(true);
                } else {
                    throw new Error(`Error HTTP al abrir: ${responseOpen.status}`);
                }
            } catch (error) {
                console.error('Error al ejecutar /open:', error);
                appAbierta = false;
                setButtonState(this, 'estado-inicial', 'Abrir App');
                setResult('No se pudo abrir la app local', 'error');
                setButtonsEnabled(false);
            }
        } else {
            // Comportamiento opcional si ya está abierta y deseas cerrarla o refrescar
            setResult('La app ya se encuentra abierta', 'success');
        }
    });


    btnConsultar.addEventListener('click', async function () {
        if (!appAbierta) return;
        setButtonState(this, 'estado-consultando', 'Consultando...');
        setResult('Escaneando tarjeta SUBE...', 'info');
        btnAbrir.disabled = true;
        btnAcreditar.disabled = true;

        try {
            const response = await fetch('http://127.0.0.1:8000/read', {
                method: 'POST',
                headers: { 
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                setButtonState(this, 'estado-inicial', `ID: ${data.card_number.slice(0, 4)}...`);
                setResult(`ID: ${data.card_number} | Saldo: $${data.balance}`, 'success');
            } else {
                setButtonState(this, 'estado-inicial', 'Consultar ID');
                setResult(data.message || 'Error al leer la tarjeta', 'error');
            }
        } catch (error) {
            console.error('Error al conectar con la API para leer tarjeta:', error);
            setButtonState(this, 'estado-inicial', 'Consultar ID');
            setResult('Error de conexión con la API local', 'error');
        } finally {
            btnAbrir.disabled = false;
            btnAcreditar.disabled = false;
        }
    });

    // btnConsultar.addEventListener('click', function () {
    //     if (!appAbierta) return;
    //     setButtonState(this, 'estado-consultando', 'Consultando...');
    //     setResult('Escaneando tarjeta SUBE...', 'info');
    //     btnAbrir.disabled = true;
    //     btnAcreditar.disabled = true;

    //     setTimeout(() => {
    //         setButtonState(this, 'estado-inicial', 'ID: 1234...');
    //         setResult('ID: 1234-5678-9012 | Saldo: $1.250', 'success');
    //         btnAbrir.disabled = false;
    //         btnAcreditar.disabled = false;
    //     }, 1800);
    // });

    btnAcreditar.addEventListener('click', function () {
        if (!appAbierta) return;
        setButtonState(this, 'estado-acreditando', 'Acreditar...');
        setResult('Procesando acreditación...', 'info');
        btnAbrir.disabled = true;
        btnConsultar.disabled = true;

        setTimeout(() => {
            setButtonState(this, 'estado-inicial', 'Acreditado');
            setResult('Carga acreditada: $1.500', 'success');
            btnAbrir.disabled = false;
            btnConsultar.disabled = false;
        }, 2200);
    });

    console.log('SUBE Bar Extension cargada correctamente');
}