import json
import os
from api import getGeneralData, getMapData
from data_keys import MapNames as MN

##Get map data from Considition endpoint
apiKey = os.environ["apiKey"]

def get_maps():
    map_names = [
        MN.stockholm,
        MN.goteborg,
        MN.malmo,
        MN.uppsala,
        MN.vasteras,
        MN.orebro,
        MN.london,
        MN.berlin,
        MN.linkoping,
        MN.sSandbox,
        MN.gSandbox
    ]
    for map_name in map_names:
        try:
            map_entity = getMapData(map_name, apiKey)
            if map_entity:
                with open(f'map_entities/{map_name}.json', 'w') as w:
                    json.dump(map_entity, w, indent=4)
        except:
            pass


def get_general_data():
    try:
        general_data = getGeneralData()
        if general_data:
            with open(f'general_data.json', 'w') as w:
                json.dump(general_data, w, indent=4)
    except:
        pass

##Get non map specific data from Considition endpoint
# generalData = getGeneralData()
if __name__ == '__main__':
    # get_maps()
    get_general_data()