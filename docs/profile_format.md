# Profile Format

Profiles are JSON files stored in:

`%APPDATA%\OpenLaunchDeck\profiles`

Each profile contains:

- `name`
- `id`
- `default_page`
- `settings`
- `pages`

Each page contains a `buttons` object keyed by A1-H8. Missing buttons are filled as blank buttons at load time.

```json
{
  "name": "Basic PC",
  "id": "basic_pc",
  "default_page": "main",
  "pages": [
    {
      "name": "Main",
      "id": "main",
      "buttons": {
        "A1": {
          "label": "Browser",
          "color": "green",
          "enabled": true,
          "dangerous": false,
          "action": {
            "type": "open_url",
            "config": {
              "url": "https://www.google.com"
            }
          }
        }
      }
    }
  ]
}
```

Button definitions can also store notes, icon fields, press behavior, release behavior, active color, success color, and error color.
