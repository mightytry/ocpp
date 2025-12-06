[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![codecov](https://codecov.io/gh/lbbrhzn/ocpp/branch/main/graph/badge.svg?token=3FRJIF5KRW)](https://codecov.io/gh/lbbrhzn/ocpp)
[![Documentation Status](https://readthedocs.org/projects/home-assistant-ocpp/badge/?version=latest)](https://home-assistant-ocpp.readthedocs.io/en/latest/?badge=latest)
[![hacs_downloads](https://img.shields.io/github/downloads/lbbrhzn/ocpp/latest/total)](https://github.com/lbbrhzn/ocpp/releases/latest)

![OCPP](https://github.com/home-assistant/brands/raw/master/custom_integrations/ocpp/icon.png)

This is a Home Assistant integration for Electric Vehicle chargers that support the following Open Charge Point Protocols 1.6j, 2.0.1 and 2.1 (experimental).

* based on the [Python OCPP Package](https://github.com/mobilityhouse/ocpp).
* HACS compliant repository 

Documentation can be found here [home-assistant-ocpp.readthedocs.io](https://home-assistant-ocpp.readthedocs.io)

**💡 Tip:** If you like this project consider buying me a coffee or a cocktail:

<a href="https://www.buymeacoffee.com/lbbrhzn" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/default-black.png" alt="Buy Me A Coffee" width="150px">
</a>

## Configuration

### Remote Id Tag

The integration allows you to configure a **Remote Id Tag** for each charger that is used for remote start transactions. This can be set during charger setup.

- **Maximum Length**: 32 characters
- **Default Behavior**: If not specified, a random 20-character uppercase alphanumeric tag is generated for each charger
- **Configuration**: 
  - Set during charger configuration when a charger connects for the first time
  - Each charger can have its own unique Remote Id Tag

The Remote Id Tag is validated during configuration and will be rejected if it exceeds 32 characters. For defensive purposes, if an overlong tag is provided from another source, it will be truncated to 32 characters with a warning logged.
