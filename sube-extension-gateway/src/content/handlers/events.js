// content/handlers/events.js
import { getStatus, openApp, readCard, creditBalance, closeApp } from '../api/client.js';
// import { getAppState } from '../state/store.js';


export async function isAppOpen() {
    try {
        const res = await getStatus();
        const data = await res.json();

        return data.status === "open";
    } catch (err) {
        console.error(err);
        return false;
    }
}

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

    setButtonsEnabled(isAppOpen())

    btnAbrir.addEventListener('click', async function () {
        const appEstaAbierta = await isAppOpen();
        if (!appEstaAbierta) {
            setButtonState(this, 'estado-abriendo', 'Abriendo...');
            setResult('Iniciando programa', 'info');

            try {
                const responseOpen = await openApp();

                if (responseOpen.ok) {
                    setButtonState(this, 'estado-cerrado', 'Cerrar programa');
                    setResult('App SUBE abierta', 'success');
                    setButtonsEnabled(true);
                }

            } catch (error) {
                console.error('Error al ejecutar /open:', error);
                setButtonState(this, 'estado-inicial', 'Abrir App');
                setResult('No se pudo abrir la app local', 'error');
                setButtonsEnabled(false);
            }
        } else {
            setButtonState(this, 'estado-cerrando', 'Cerrando...');
            setResult('Cerrando programa', 'info');

            try {
                const responseClose = await closeApp();

                if (responseClose.ok) {
                    setButtonState(this, 'estado-inicial', 'Abrir App');
                    setResult('App SUBE cerrada', 'success');
                    setButtonsEnabled(false);
                }

            } catch (error) {
                console.error('Error al ejecutar /close:', error);
                setButtonState(this, 'estado-cerrado', 'Cerrar programa');
                setResult('No se pudo cerrar la app local', 'error');
                setButtonsEnabled(true);
            }
        }
    });

    btnConsultar.addEventListener('click', async function () {
        const appEstaAbierta = await isAppOpen();
        if (!appEstaAbierta) return;

        setButtonState(this, 'estado-consultando', 'Consultando ..');
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
        // if (!getAppState()) return;

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