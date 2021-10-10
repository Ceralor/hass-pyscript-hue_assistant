#!/usr/bin/env python3

## Hue Assistant for Pyscript
## MIT License 2021
## Adds lists for Hue Bridge-stored scenes and Hue Essentials effects/animations stored in the Bridge
## This requires two Input Select helpers: Hue Animations and Hue Scenes
## This also requires an input_text named hue_user that has a valid Hue username, preferably the one your HA app uses
## It also needs the bridge's IP; I use a rate accelerator to pull this but you can manually plug it below.
## You can activate the selected scene/effect by calling pyscript.activate_scene or pyscript.activate_effect
## You can also supply room_scene or room_effect, respectively, formatted as "<Room Name> - <Scene/Effect Name>"
import requests, json, re

bridge_host = pyscript.app_config["bridge_ip"]
hue_user = pyscript.app_config["hue_user"]
hue_api_url = f"http://{bridge_host}/api/{hue_user}"

@time_trigger('startup')
def init_pyscript_huelists():
    pyscript.hue_lists = "ATTRIB"
    state.set("binary_sensor.hue_sync", state=False, \
        new_attributes={"device_class":"connectivity", \
            "friendly_name":"Hue Sync Status"})

@time_trigger('startup','cron(0 * * * *)')
@service
def update_effects():
    groupsearch = re.compile("/groups/\d+")
    sensors = task.executor(requests.get,hue_api_url+'/sensors').json()
    groups = task.executor(requests.get,hue_api_url+'/groups').json()
    resourcelinks = task.executor(requests.get,hue_api_url+'/resourcelinks').json()
    hue_essentials_sensors = [x for x in sensors.keys() if sensors[x]['type'] == 'CLIPGenericStatus']
    hue_effects_sensors = [x for x in hue_essentials_sensors if sensors[x]['modelid'] == 'HueEssentialsEffect_State']
    hue_effects = {}
    for effect_sensor in hue_effects_sensors:
        resourcelink = [resourcelinks[x] for x in resourcelinks.keys() if f"/sensors/{effect_sensor}" in resourcelinks[x]['links']][0]
        group_path = list(filter(groupsearch.match,resourcelink['links']))[0]
        group_id = re.search("(\d+)",group_path).group(1)
        group = groups[group_id]
        effect_display_name = group['name'] + " - " + resourcelink['name']
        log.debug(f"Storing info for effect {effect_display_name}")
        hue_effects[effect_display_name] = effect_sensor
    state.setattr('pyscript.hue_lists.effects_json', json.dumps(hue_effects))
    input_select.set_options(options=list(hue_effects.keys()),entity_id="input_select.hue_animations")

@time_trigger('startup','cron(0 * * * *)')
@service
def update_scenes():
    groups = task.executor(requests.get,hue_api_url+'/groups').json()
    scenes = task.executor(requests.get,hue_api_url+'/scenes').json()
    hue_scenes = {}
    for scene_id in scenes.keys():
        scene = scenes[scene_id]
        if scene['name'] == 'HueEssentialsEffect':
            continue
        group = groups[scene['group']]
        scene_display_name = f"{group['name']} - {scene['name']}"
        log.debug(f"Storing info for scene {scene_display_name}")
        hue_scenes[scene_display_name] = {'scene_name':scene['name'],'scene_id':scene_id,'group_name':group['name'],'group_id':scene['group']}
    state.setattr('pyscript.hue_lists.scenes_json',json.dumps(hue_scenes))
    input_select.set_options(options=list(hue_scenes.keys()),entity_id="input_select.hue_scenes")

@service
def activate_scene(room_scene=None):
    if room_scene == None:
        room_scene = input_select.hue_scenes
    scenes = json.loads(state.getattr('pyscript.hue_lists')['scenes_json'])
    if room_scene not in scenes.keys():
        update_scenes()
        scenes = json.loads(state.getattr('pyscript.hue_lists')['scenes_json'])
        if room_scene not in scenes.keys():
            log.error(f"{room_scene} not found in Hue Bridge")
            return False
    scene_info = scenes[room_scene]
    log.debug(f"Activating '{scene_info['scene_name']}'' in '{scene_info['group_name']}'")
    hue.hue_activate_scene(group_name=scene_info['group_name'],scene_name=scene_info['scene_name'])

def send_sensor_state(sensor_id=None,state_name=None,state_value=None):
    body = {state_name: state_value}
    r = task.executor(requests.put,hue_api_url+f"/sensors/{sensor_id}/state",json=body)
    if r.status_code == 200:
        log.debug(f"Successfully set {state_name} to {state_value} on sensor ID {sensor_id}")
    else:
        log.error(r.text)
        return False

@service
def activate_effect(room_effect=None):
    if room_effect == None:
        room_effect = input_select.hue_animations
    effects = json.loads(state.getattr('pyscript.hue_lists')['effects_json'])
    if room_effect not in effects.keys():
        update_effects()
        effects = json.loads(state.getattr('pyscript.hue_lists')['effects_json'])
        if room_effect not in effects.keys():
            log.error(f"{room_effect} not found in Hue Bridge")
            return False
    effect_sensor_id = effects[room_effect]
    deactivate_effects()
    send_sensor_state(effect_sensor_id,'status',1)

@service
def deactivate_effects():
    effects = json.loads(state.getattr('pyscript.hue_lists')['effects_json'])
    for effect_id in effects.values():
        send_sensor_state(effect_id,'status',0)

@time_trigger("period(now, 5s)")
def sync_status():
    groups = task.executor(requests.get,hue_api_url+f"/groups").json()
    states = [ x["stream"]["active"] for x in groups.values() if x['type'] == "Entertainment" ]
    sync_active = "on" if True in states else "off"
    state.set("binary_sensor.hue_sync", sync_active)    
