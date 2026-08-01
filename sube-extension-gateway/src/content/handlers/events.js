import { getStatus, openApp, readCard, creditBalance, closeApp, restart } from '../api/client.js';

export async function isAppOpen() {
    try {
        const res = await getStatus();
        const data = await res.json();
        
        return data.status === "open";
    } catch (err) {
        return false;
    }
}

function setButtonState(btn, state, text) {
    if (!btn) return;
    btn.className = 'sube-btn ' + state;
    btn.textContent = text;
}

function setButtonsEnabled(enabled, secondaryButtons) {
    secondaryButtons.forEach(btn => {
        if (btn) btn.disabled = !enabled;
    });
}

function interpretarAcreditacion(arrayDatos) {
    if (!arrayDatos || arrayDatos.length === 0) {
        return { estado: 'error', mensaje: 'El lector no devolvió información.' };
    }

    const textoCompleto = arrayDatos.join(' ').replace(/\s+/g, ' ').toLowerCase();

    if (textoCompleto.includes('no se detecto') || textoCompleto.includes('ninguna tarjeta')) {
        return { estado: 'error', mensaje: 'No se detectó ninguna tarjeta en el lector.' };
    }

    if (textoCompleto.includes('no tiene cargas') || textoCompleto.includes('cargas pendientes')) {
        const matchSaldo = textoCompleto.match(/\$\s*(\d+[.,]\d+)/); 
        const saldoActual = matchSaldo ? matchSaldo[1] : 'Desconocido';
        
        return { 
            estado: 'info', 
            mensaje: `La tarjeta no tiene cargas pendientes. Saldo actual: $${saldoActual}` 
        };
    }

    const indexImporte = arrayDatos.findIndex(item => item.toLowerCase().includes('importe cargado'));
    const indexSaldo = arrayDatos.findIndex(item => item.toLowerCase().includes('saldo:'));

    if (indexImporte !== -1 && indexSaldo !== -1) {
        const mitad = arrayDatos.length / 2;
        return {
            estado: 'success',
            montoCargado: arrayDatos[indexImporte + mitad],
            nuevoSaldo: arrayDatos[indexSaldo + mitad]
        };
    }

    

    return { estado: 'error', mensaje: 'El lector devolvió un resultado desconocido.' };
}

function encontrarInputSube() {
    let input = null;
    input = document.querySelector('input[name="133"]');
    if (input) return input;

    input = document.querySelector('input[placeholder*="Tarjeta"][maxlength="16"]');
    if (input) return input;

    const labels = Array.from(document.querySelectorAll('label.control-label'));
    const labelDestino = labels.find(label => label.textContent.trim() === 'Destino');
    if (labelDestino) {
        input = labelDestino.parentElement.querySelector('input');
        if (input) return input;
    }

    return null;
}

export function initialButtonsSet(isOpen, btnConsultar, btnAcreditar, btnAbrir) {
        secondaryButtons = [btnConsultar, btnAcreditar]
        if (isOpen) {
            setButtonState(btnAbrir, 'estado-cerrado', 'Cerrar programa');
            setButtonsEnabled(true, secondaryButtons);

        } else {
            setButtonState(btnAbrir, 'estado-inicial', 'Abrir App');
            setButtonsEnabled(false, secondaryButtons);
        }
}

export function setupEventHandlers(btnAbrir, btnConsultar, btnAcreditar, resultDisplay, btnReiniciar) {
    if (!btnAbrir) return;

    const secondaryButtons = [btnConsultar, btnAcreditar];

    function setResult(text, type = 'info') {
        if (!resultDisplay) return;
        resultDisplay.textContent = text;
        resultDisplay.className = 'value ' + type;
    }

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
                    setButtonsEnabled(true, secondaryButtons);
                }

            } catch (error) {
                console.error('Error al ejecutar /open:', error);
                setButtonState(this, 'estado-inicial', 'Abrir App');
                setResult('No se pudo abrir la app local', 'error');
                setButtonsEnabled(false, secondaryButtons);
            }
        } else {
            setButtonState(this, 'estado-cerrando', 'Cerrando...');
            setResult('Cerrando programa', 'info');

            try {
                const responseClose = await closeApp();

                if (responseClose.ok) {
                    setButtonState(this, 'estado-inicial', 'Abrir App');
                    setResult('App SUBE cerrada', 'success');
                    setButtonsEnabled(false, secondaryButtons);
                }

            } catch (error) {
                console.error('Error al ejecutar /close:', error);
                setButtonState(this, 'estado-cerrado', 'Cerrar programa');
                setResult('No se pudo cerrar la app local', 'error');
                setButtonsEnabled(true, secondaryButtons);
            }
        }
    });

    btnConsultar.addEventListener('click', async function () {
        setResult('Escaneando tarjeta SUBE ...', 'info');
        setButtonsEnabled(false, secondaryButtons);

        try {
            const data = await readCard();
            console.log("Data: ", data.data)

            if (data.status === 'success') {

                if (!data.data || data.data.length === 0) {
                    throw new Error('La API no devolvió datos de la tarjeta');
                }
                
                const saldoConSigno = data.data.find(str => str.startsWith('$')) || '$0';
                const numeroTarjeta = data.data.find(str => {
                    const limpio = str.replaceAll(' ', '');
                    return /^\d+$/.test(limpio);
                }) || '';

                const balance = saldoConSigno.replace('$', '').trim();
                const card_number = numeroTarjeta.replaceAll(' ', '');

                setResult(`ID: ${card_number} | Saldo: $${balance}`, 'success');

                const cardInput = encontrarInputSube();

                if (cardInput) {
                    cardInput.value = card_number;
                    cardInput.dispatchEvent(new Event('input', { bubbles: true }));
                    cardInput.dispatchEvent(new Event('change', { bubbles: true }));
                } else {
                    console.log('No se encontró el input.');
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
            setButtonsEnabled(true, secondaryButtons);

        }
    });

    btnAcreditar.addEventListener('click', async function () {
        setResult('Procesando acreditación...', 'info');
        setButtonsEnabled(true, secondaryButtons);

        try {
            const data = await creditBalance();
            console.log("respuesta: ", data)
            console.log("Data ",data.data)

            if (data.status === 'success') {
                
                const resultado = interpretarAcreditacion(data.data);

                if (resultado.estado === 'success') {
                    setResult(`Carga acreditada: ${resultado.montoCargado} | Nuevo Saldo: ${resultado.nuevoSaldo}`, 'success');
                    setButtonState(this, 'estado-inicial', 'Acreditar');
                
                } else if (resultado.estado === 'info') {
                    setResult(resultado.mensaje, 'info'); 
                    setButtonState(this, 'estado-inicial', 'Acreditar');
                
                } else {
                    setResult(resultado.mensaje, 'error');
                    setButtonState(this, 'estado-inicial', 'Acreditar');
                }
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

    btnReiniciar.addEventListener('click', async function () {
        setResult('Cancelando operaciones y reiniciando programa...', 'info');

        try {
            const data = await restart(); 
            if (data.status === 'success') {
                setButtonState(this, 'estado-inicial', 'Reiniciar');
                setResult('Programa reiniciado con éxito', 'success');

            } else {
                setButtonState(this, 'estado-inicial', 'Reiniciar');
                setResult(data.message || 'No se pudo reiniciar la aplicación', 'error');
            }

        } catch (error) {
            console.error('Error al conectar con la API para reiniciar:', error);
            setButtonState(this, 'estado-inicial', 'Reiniciar');
            setResult('Error de conexión al intentar reiniciar la app local', 'error');
        }
    });
        
    console.log('SUBE Bar Event Handlers configurados correctamente');
}