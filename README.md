# hass-pyscript-hue_assistant
Adds helpful Hue functionality to Home Assistant via Pyscript

Hue Assistant adds lists for Hue Bridge-stored scenes and Hue Essentials effects/animations stored in the Bridge

You can activate the selected scene/effect by calling `pyscript.activate_scene` or `pyscript.activate_effect`

You can also supply room_scene or room_effect, respectively, formatted as `"<Room Name> - <Scene/Effect Name>`

Hue Assistant also requires configuration of the bridge host/IP and an API username. If you're uncertain of how to do so, the Philips Hue developer site [has a helpful guide](https://developers.meethue.com/develop/get-started-2/#so-lets-get-started). From there, add it to your Pyscript config in Home Assistant:

```
pyscript:
  allow_all_imports: true
  apps:
    hue_assistant:
      hostname: Philips-hue.local
      username: !secret hue_user
```

It's recommended to use the `secrets.yaml` file for adding the username, as shown above. Additionally a static IP for your bridge, configured as a static DHCP assignment in your router, is recommended, but you may also use the mDNS name "Philips-hue.local" if your bridge is named such for resolution.