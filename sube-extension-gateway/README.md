# SUBE Extension Gateway

Browser extension that injects a horizontal control bar at the bottom of any
supported webpage. It provides a simple interface to communicate with the
**SUBE Local Gateway** through JavaScript, allowing users to open the SUBE
desktop application, read the card ID, and load pending balance directly from
the browser.

---

## Project Structure

```text
sube-extension/
├── src/
│   ├── content/
│   │   ├── index.js
│   │   ├── ui/
│   │   │   └── bar.js
│   │   ├── api/
│   │   │   └── client.js
│   │   ├── state/
│   │   │   └── store.js
│   │   └── handlers/
│   │       └── events.js
│   └── public/
│       ├── icon-sube.jpg
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
├── manifest.json
├── styles.css
├── index.html
├── package.json
└── vite.config.js
```

## Features

- Injects a bottom toolbar into supported webpages.
- Communicates with the SUBE Local Gateway through its REST API.
- Opens the SUBE desktop application.
- Reads the SUBE card identifier.
- Credits pending balance to the card.
- Displays connection status and operation results.
- Uses a lightweight JavaScript implementation without frontend frameworks.

---

## Development

### Installation

```bash
npm install
```

### Development Server

```bash
npm run dev
```

### Build

```bash
npm run build
```

The compiled extension files are generated in the `dist/` directory.

### Watch Mode

```bash
npm run watch
```

### Preview

```bash
npm run preview
```

---

## Loading the Extension

The project is intended to be used as a Chromium-based browser extension.

After building:

1. Open the browser extensions page.
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select the project folder (or the generated extension directory, depending on your build configuration).
5. The extension will be available immediately.

The extension behavior is defined in `manifest.json`.

---

## User Interface

The injected toolbar contains:

- **SUBE logo**
- **Open App** button
- **Read Card ID** button
- **Credit Balance** button
- **Status and operation messages**

The toolbar is automatically positioned at the bottom of the page.

---

## Main Components

| Component | Description |
|-----------|-------------|
| `content/index.js` | Extension entry point. |
| `ui/bar.js` | Creates and injects the toolbar HTML. |
| `api/client.js` | REST client for the Local Gateway. |
| `state/store.js` | Shared application state. |
| `handlers/events.js` | Button events and UI logic. |

---

## Assets

The extension includes the following resources:

- SUBE logo
- Extension icons (16x16, 48x48, 128x128)

These assets are packaged and accessed through the Chrome Extension API.

---

## Requirements

- Chromium-based browser (Google Chrome, Microsoft Edge, Brave, etc.)
- SUBE Local Gateway running locally.
- JavaScript enabled.