// content/handlers/events.js
import { getStatus, openApp, readCard, creditBalance } from '../api/client.js';
import { getAppState, setAppState } from '../state/store.js';

export function setupEventHandlers(btnAbrir, btnConsultar, btnAcreditar, resultDisplay) {
    if (!btnAbrir) return;

    const secondaryButtons = [btnConsultar, btnAcreditar];

    function setResult(text, type = 'info') {
        if (!resultDisplay) return;
        resultDisplay.textContent = text;
        resultDisplay.className = 'value ' + type;
    }

    function setButtonState(btn, state, text) {
        if (!btn) return;
        btn.className = 'sube-btn ' + state;
        btn.textContent = text;
    }

    function setButtonsEnabled(enabled) {
        secondaryButtons.forEach(btn => {
            if (btn) btn.disabled = !enabled;
        });
    }

    // Función para consultar el estado actual en la API local
    async function verificarEstadoInicial() {
        try {
            const response = await getStatus();

            if (response.ok) {
                const textData = await response.text();
                let status = textData.trim().toLowerCase();
                
                try {
                    const jsonData = JSON.parse(textData);
                    if (jsonData.status) status = jsonData.status.toLowerCase();
                } catch (e) {}

                if (status === 'open') {
                    setAppState(true);
                    setButtonState(btnAbrir, 'estado-abierto', 'App Abierta');
                    setResult('App SUBE conectada', 'success');
                    setButtonsEnabled(true);
                } else {
                    setAppState(false);
                    setButtonState(btnAbrir, 'estado-inicial', 'Abrir App');
                    setResult('App cerrada (Esperando acción...)', 'info');
                    setButtonsEnabled(false);
                }
            } else {
                throw new Error('API no disponible');
            }
        } catch (error) {
            console.warn('No se pudo verificar el estado inicial con la API local:', error);
            setAppState(false);
            setButtonState(btnAbrir, 'estado-inicial', 'Abrir App');
            setResult('API local desconectada', 'error');
            setButtonsEnabled(false);
        }
    }

    // Ejecutar verificación al aparecer la barra
    verificarEstadoInicial();

    // Evento Abrir App
    btnAbrir.addEventListener('click', async function () {
        if (!getAppState()) {
            setButtonState(this, 'estado-abriendo', 'Abriendo...');
            setResult('Enviando petición a /open...', 'info');
            setButtonsEnabled(false);

            try {
                const responseOpen = await openApp();

                if (responseOpen.ok) {
                    setAppState(true);
                    setButtonState(this, 'estado-abierto', 'App Abierta');
                    setResult('App SUBE abierta correctamente', 'success');
                    setButtonsEnabled(true);
                } else {
                    throw new Error(`Error HTTP al abrir: ${responseOpen.status}`);
                }
            } catch (error) {
                console.error('Error al ejecutar /open:', error);
                setAppState(false);
                setButtonState(this, 'estado-inicial', 'Abrir App');
                setResult('No se pudo abrir la app local', 'error');
                setButtonsEnabled(false);
            }
        } else {
            setResult('La app ya se encuentra abierta', 'success');
        }
    });

    // Evento Consultar ID
    btnConsultar.addEventListener('click', async function () {
        if (!getAppState()) return;
        
        setButtonState(this, 'estado-consultando', 'Consultando...');
        setResult('Escaneando tarjeta SUBE...', 'info');
        btnAbrir.disabled = true;
        btnAcreditar.disabled = true;

        try {
            const data = await readCard();

            if (data.status === 'success') {
                setButtonState(this, 'estado-inicial', `ID: ${data.card_number.slice(0, 4)}...`);
                setResult(`ID: ${data.card_number} | Saldo: $${data.balance}`, 'success');

                // Rellenar input de la página
                const cardInput = document.querySelector('input[placeholder="Nro de Tarjeta"]');
                if (cardInput) {
                    cardInput.value = data.card_number;
                    cardInput.dispatchEvent(new Event('input', { bubbles: true }));
                    cardInput.dispatchEvent(new Event('change', { bubbles: true }));
                } else {
                    console.warn('No se encontró el input de la tarjeta en el DOM');
                }

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

    // Evento Acreditar
    btnAcreditar.addEventListener('click', async function () {
        if (!getAppState()) return;
        
        setButtonState(this, 'estado-acreditando', 'Acreditando...');
        setResult('Procesando acreditación...', 'info');
        btnAbrir.disabled = true;
        btnConsultar.disabled = true;

        try {
            const data = await creditBalance();

            if (data.status === 'success') {
                setButtonState(this, 'estado-inicial', 'Acreditado');
                setResult(`Carga acreditada: $${data.amount_loaded} | Nuevo Saldo: $${data.new_balance}`, 'success');
            } else {
                setButtonState(this, 'estado-inicial', 'Acreditar');
                setResult(data.message || 'Error al acreditar saldo', 'error');
            }
        } catch (error) {
            console.error('Error al conectar con la API para acreditar:', error);
            setButtonState(this, 'estado-inicial', 'Acreditar');
            setResult('Error de conexión con la API local', 'error');
        } finally {
            btnAbrir.disabled = false;
            btnConsultar.disabled = false;
        }
    });

    console.log('SUBE Bar Event Handlers configurados correctamente');
}