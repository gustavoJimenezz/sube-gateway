// content/index.js
import { html } from './ui/bar.js';
import { setupEventHandlers } from './handlers/events.js';
// import { loadInitialState } from './state/store.js';

// ===== CONTROLADOR DE INYECCIÓN DINÁMICA =====
function checkAndInjectBar() {
    const barExists = document.getElementById('sube-bar');
    
    // Heurística para detectar si estamos en el login o fuera de él
    const isLoginPage = window.location.pathname.includes('login') || 
                        document.querySelector('input[type="password"]') !== null || 
                        document.querySelector('form[action*="login"]') !== null;

    if (!isLoginPage && !barExists) {
        // Estamos en la interfaz interna y la barra no está: la inyectamos
        if (document.body) {
            document.body.insertAdjacentHTML('afterbegin', html);
            initApp();
            console.log('SUBE Bar inyectada en la interfaz principal');
        }
    } else if (isLoginPage && barExists) {
        // Si nos redirige al login y la barra sigue visible, la eliminamos
        barExists.remove();
    }
}

// ===== INICIALIZACIÓN DE LA APP =====
async function initApp() {
    const btnAbrir = document.getElementById('btn-abrir');
    const btnConsultar = document.getElementById('btn-consultar');
    const btnAcreditar = document.getElementById('btn-acreditar');
    const resultDisplay = document.getElementById('sube-result');

    if (!btnAbrir) {
        console.warn('Botón Abrir no encontrado, la barra no se inicializó correctamente');
        return;
    }
    
    setupEventHandlers(btnAbrir, btnConsultar, btnAcreditar, resultDisplay);

    console.log('SUBE App inicializada correctamente');
}

// ===== OBSERVADOR DE CAMBIOS (SPA) =====
const observer = new MutationObserver(() => {
    checkAndInjectBar();
});

observer.observe(document.documentElement, {
    childList: true,
    subtree: true
});

// ===== VERIFICACIÓN INICIAL =====
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    checkAndInjectBar();
} else {
    window.addEventListener('DOMContentLoaded', checkAndInjectBar);
}

console.log('SUBE Extension content script cargado');