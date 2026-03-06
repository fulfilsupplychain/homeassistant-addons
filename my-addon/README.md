# My Addon

A custom Home Assistant add-on.

## About

This add-on provides a starting template for developing your own Home Assistant add-ons. It demonstrates the basic structure including configuration options, logging, and the Home Assistant API integration.

## Installation

1. Navigate to **Settings → Add-ons → Add-on Store** in your Home Assistant instance.
2. Click the **⋮** menu (top right) → **Repositories**.
3. Add this repository URL:
   ```
   https://github.com/YOUR_GITHUB_USERNAME/homeassistant-addons
   ```
4. Find **My Addon** in the store and click **Install**.

## Configuration

| Option      | Description                        | Default                |
| ----------- | ---------------------------------- | ---------------------- |
| `message`   | A custom message logged at startup | `Hello from My Addon!` |
| `log_level` | Logging verbosity                  | `info`                 |

### Example configuration

```yaml
message: "Hello World!"
log_level: info
```

## Support

- Open an issue on the [GitHub repository](https://github.com/YOUR_GITHUB_USERNAME/homeassistant-addons/issues).
