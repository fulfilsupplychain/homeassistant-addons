# Home Assistant Add-ons Repository

[![Deploy Home Assistant Add-ons](https://github.com/fulfilsupplychain/homeassistant-addons/actions/workflows/deploy.yaml/badge.svg)](https://github.com/fulfilsupplychain/homeassistant-addons/actions/workflows/deploy.yaml)

## Installation

1. Open your Home Assistant instance.
2. Navigate to **Settings → Add-ons → Add-on Store**.
3. Click the **⋮** menu (top-right) → **Repositories**.
4. Paste the following URL and click **Add**:

   ```
   https://github.com/fulfilsupplychain/homeassistant-addons
   ```

5. Browse the store for the available add-ons below.

## Add-ons

### 🔧 [My Addon](./my-addon)

A custom Home Assistant add-on template to get you started.

| Key     | Value                              |
| ------- | ---------------------------------- |
| Version | `1.0.0`                            |
| Arch    | amd64, aarch64, armv7, armhf, i386 |
| Stage   | stable                             |

---

## Development

### Repository Structure

```
homeassistant-addons/
├── .github/
│   └── workflows/
│       └── deploy.yaml          # CI/CD pipeline
├── repository.yaml              # Repository metadata
├── README.md                    # This file
└── my-addon/
    ├── config.yaml              # Add-on configuration
    ├── Dockerfile               # Container build
    ├── run.sh                   # Entrypoint script
    ├── README.md                # Add-on documentation
    ├── CHANGELOG.md             # Version history
    ├── icon.png                 # Add-on icon  (128×128)
    └── logo.png                 # Add-on logo  (128×128)
```

### Adding a New Add-on

1. Create a new directory at the repository root (e.g., `my-new-addon/`).
2. Add the required files: `config.yaml`, `Dockerfile`, `run.sh`, `README.md`.
3. Add the new addon slug to the `matrix.addon` list in `.github/workflows/deploy.yaml`.
4. Push to `main` — the CI/CD pipeline will validate, build, tag, and release automatically.

### CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy.yaml`) runs three stages:

| Stage      | Trigger        | What it does                                            |
| ---------- | -------------- | ------------------------------------------------------- |
| **Lint**   | push & PR      | Validates `repository.yaml`, `config.yaml`, Dockerfiles |
| **Build**  | push & PR      | Builds Docker images (no push) to verify correctness    |
| **Deploy** | push to `main` | Creates git tags and GitHub Releases for new versions   |

## License

MIT © Fulfil Supply Chain
