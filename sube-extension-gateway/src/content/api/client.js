const API_BASE = 'http://127.0.0.1:8000';
let currentController = null;

function getSignal() {
  if (currentController) {
    currentController.abort();
  }
  currentController = new AbortController();
  return currentController.signal;
}

export async function getStatus() {
  const response = await fetch(`${API_BASE}/status`);
  return response;
}

export async function openApp() {
  const response = await fetch(`${API_BASE}/open`, {
    method: 'POST',
    headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }
  });
  return response;
}

export async function closeApp() {
  const response = await fetch(`${API_BASE}/close`, {
    method: 'POST',
    headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }
  });
  return response;
}

export async function readCard() {
  const signal = getSignal()
  const response = await fetch(`${API_BASE}/read`, {
    method: 'POST',
    headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }
  }, signal);

  currentController = null;
  return response.json();
}

export async function creditBalance() {
  const signal = getSignal()
  const response = await fetch(`${API_BASE}/credit-balance`, {
    method: 'POST',
    headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, signal);
  });
  currentController = null;
  return response.json();
}

export async function restart() {
  if (currentController) {
    currentController.abort();
    currentController = null;
    console.log("Petición activa abortada en el cliente.");
  }

  const response = await fetch(`${API_BASE}/restart`, {
    method: 'POST',
    headers: { 
      'Accept': 'application/json', 
      'Content-Type': 'application/json' 
    }
  });
  if (!response.ok) {
    throw new Error(`Error en el servidor: ${response.status}`);
  }
  const data = await response.json();
  return data;
}