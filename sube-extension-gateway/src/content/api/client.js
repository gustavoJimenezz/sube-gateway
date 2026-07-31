const API_BASE = 'http://127.0.0.1:8000';

export async function getStatus() {
  const response = await fetch(`${API_BASE}/status`);
  console.log("Respuesta")
  console.log(response)
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
  const response = await fetch(`${API_BASE}/read`, {
    method: 'POST',
    headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }
  });
  return response.json();
}

export async function creditBalance() {
  const response = await fetch(`${API_BASE}/credit-balance`, {
    method: 'POST',
    headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }
  });
  return response.json();
}