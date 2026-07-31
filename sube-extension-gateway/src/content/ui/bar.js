// HTML y SVG
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

// const imageUrl = chrome.runtime.getURL('icon-sube.jpg');
// const imageUrl = chrome.runtime.getURL("dist/icon-sube.jpg");
const imageUrl = chrome.runtime.getURL("src/public/icon-sube.jpg");
const html = `
    <div id="sube-bar">
        
        <div class="sube-section-left">
            <div id="sube-logo">
                <img src="${imageUrl}" alt="SUBE">
            </div>
            <button id="btn-abrir" class="sube-btn estado-inicial">Abrir App</button>
        </div>
        <div class="sube-section-center">
            <button id="btn-consultar" class="sube-btn estado-inicial" disabled>Consultar ID</button>
            <button id="btn-acreditar" class="sube-btn estado-inicial" disabled>Acreditar</button>
        </div>
        <div class="sube-section-right">
            <div id="sube-output">
                <span class="value info" id="sube-result"></span>
            </div>
        </div>
    </div>
`;


export { svgIcon, html };