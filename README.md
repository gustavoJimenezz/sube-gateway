# SUBE Gateway

SUBE Gateway is composed of two independent modules that work together to
provide browser-based interaction with the official SUBE desktop application.

The solution consists of:

- **sube-local-gateway/** – A local REST API server responsible for controlling
  the SUBE desktop application through Windows automation. It exposes endpoints
  used to open the application, read card information, and credit pending
  balance.

- **sube-extension-gateway/** – A browser extension that injects a toolbar into
  supported webpages and communicates with the Local Gateway through its REST
  API, providing an easy-to-use interface for end users.

## Project Structure

```
.
├── sube-local-gateway/
└── sube-extension-gateway/
```

Each module is self-contained and includes its own documentation covering:

- Installation
- Development
- Build process
- Project structure
- Configuration
- Usage
- Known issues (when applicable)

For implementation details, refer to the README file inside each project
directory.