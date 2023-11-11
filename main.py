import os
import json
from scoring import calculateScore
from time import time
from api import getGeneralData, getMapData, submit
from data_keys import (
    MapNames as MN,
    LocationKeys as LK,
    CoordinateKeys as CK,
    ScoringKeys as SK,
    GeneralKeys as GK
)
from dotenv import load_dotenv

load_dotenv()
apiKey = os.environ["apiKey"]
game_folder = "my_games"


def main():

    try:
        apiKey = os.environ["apiKey"]
    except Exception as e:
        raise SystemExit("Did you forget to create a .env file with the apiKey?")

    # User selct a map name
    print(f"1: {MN.stockholm}")
    print(f"2: {MN.goteborg}")
    print(f"3: {MN.malmo}")
    print(f"4: {MN.uppsala}")
    print(f"5: {MN.vasteras}")
    print(f"6: {MN.orebro}")
    print(f"7: {MN.london}")
    print(f"8: {MN.berlin}")
    print(f"9: {MN.linkoping}")
    option_ = input("Select the map you wish to play: ")

    mapName = None
    match option_:
        case "1":
            mapName = MN.stockholm
        case "2":
            mapName = MN.goteborg
        case "3":
            mapName = MN.malmo
        case "4":
            mapName = MN.uppsala
        case "5":
            mapName = MN.vasteras
        case "6":
            mapName = MN.orebro
        case "7":
            mapName = MN.london
        case "8":
            mapName = MN.berlin
        case "9":
            mapName = MN.linkoping
        case _:
            print("Invalid choice.")

    if mapName:

        if not os.path.exists(f"{game_folder}/{mapName}"):
            print(f"Creating folder {game_folder}")
            os.makedirs(f"{game_folder}/{mapName}")

        ##Get map data from Considition endpoint
        mapEntity = getMapData(mapName, apiKey)

        # print(json.dumps(mapEntity, indent=2))
        # with open(f'data/{mapName}', 'w') as f:
        #     f.writelines(json.dumps(mapEntity, indent=2))
        # return

        ##Get non map specific data from Considition endpoint
        generalData = getGeneralData()

        if mapEntity and generalData:
            # ------------------------------------------------------------
            # ----------------Player Algorithm goes here------------------
            # solution = example_solution(mapEntity)
            solution = try_(mapEntity, generalData)
            # ----------------End of player code--------------------------
            # ------------------------------------------------------------

            # Score solution locally
            score = calculateScore(mapName, solution, mapEntity, generalData)

            id_ = score[SK.gameId]
            print(f"Storing  game with id {id_}.")
            print(f"Enter {id_} into visualization.ipynb for local vizualization ")

            # Store solution locally for visualization
            current_time_epoch = time()
            with open(f"{game_folder}/{mapName}/{current_time_epoch}_local_{id_}.json", "w", encoding="utf8") as f:
                json.dump(score, f, indent=4)

            # Submit and and get score from Considition app
            print(f"Submitting solution to Considtion 2023 \n")

            scoredSolution = submit(mapName, solution, apiKey)
            if scoredSolution:
                print("Successfully submitted game")
                print(f"id: {scoredSolution[SK.gameId]}")
                print(f"Score: {scoredSolution[SK.gameScore]}")
            
            with open(f"{game_folder}/{mapName}/{current_time_epoch}_global_{scoredSolution[SK.gameId]}.json", "w", encoding="utf8") as f:
                json.dump(scoredSolution, f, indent=4)



def example_solution(mapEntity):
    solution = {LK.locations: {}}

    for key in mapEntity[LK.locations]:
        location = mapEntity[LK.locations][key]
        name = location[LK.locationName]

        salesVolume = location[LK.salesVolume]
        if salesVolume > 100:
            solution[LK.locations][name] = {
                LK.f9100Count: 0,
                LK.f3100Count: 1,
            }


def try_(mapEntity, generalData):

    solution = {LK.locations: {}}
    not_in_solution = {LK.locations: {}}

    for key in mapEntity[LK.locations]:
        loc = mapEntity[LK.locations][key]

        # solution logic TODO
        # TODO check relation between salse volumn and 1f9 capacity for each locqtions. 
        # TODO check relation between local footfall and sales local volumn - > might effect the solution logic
        # TODO if a location has little salse volume but a lot footfall, it's still a good locaton to set the f machines
        # goal: salesCapacity close (>=?, depends on leasing cost) to sales volumn as much as possible
        # maxima (salse) revenue, co2_saving total footfall for all selected locations
        # minima leasing cost

        distribute_scales = 0  # TODO add distributeScales, should be large
        footfall = loc[LK.footfall]  # TODO total footfall for all selected locations should be large

        sales_volume = (loc[LK.salesVolume] + distribute_scales) * generalData[GK.refillSalesFactor]

        # dummy solution TODO replace it
        # a x + b y = z
        # a: f3_count = z - by / x
        # b: f9_count, b < -(y - z) /y ?
        # z: sales_volume
        # x: f3_cap, y: f9_cap
        # TODO should use sales_volume, not loc[LK.salesVolume]
        if sales_volume < generalData[GK.f3100Data][GK.refillCapacityPerWeek]:
            if footfall > 0:
                f3_count = 1
                f9_count = 0
            else:
                f3_count = 0
                f9_count = 0
        else:
            f9_count = sales_volume // generalData[GK.f9100Data][GK.refillCapacityPerWeek]
            f3_count = (sales_volume % generalData[GK.f9100Data][GK.refillCapacityPerWeek]) // generalData[GK.f3100Data][GK.refillCapacityPerWeek]

        # validation
        sales_capacity = \
            f3_count * generalData[GK.f3100Data][GK.refillCapacityPerWeek] \
            + f9_count * generalData[GK.f9100Data][GK.refillCapacityPerWeek]

        sales = min(round(sales_volume, 0), sales_capacity)
        revenue = sales * generalData[GK.refillUnitData][GK.profitPerUnit]
        leasing_cost = \
            f3_count * generalData[GK.f3100Data][GK.leasingCostPerWeek] \
            + f9_count * generalData[GK.f9100Data][GK.leasingCostPerWeek]
        earnings = revenue - leasing_cost
        co2_savings = sales \
            * (
                generalData[GK.classicUnitData][GK.co2PerUnitInGrams]
                - generalData[GK.refillUnitData][GK.co2PerUnitInGrams]
            ) / 1000
        co2_savings_rating = co2_savings - \
            f3_count * generalData[GK.f3100Data][GK.staticCo2] / 1000 \
            - f9_count * generalData[GK.f9100Data][GK.staticCo2] / 1000

        co2_savings_price = co2_savings_rating * generalData[GK.co2PricePerKiloInSek]

        local_score_exclude_footfall = co2_savings_price + earnings

        if f3_count + f9_count < 1 or ((local_score_exclude_footfall < 0 and footfall < 0.0)):

            not_in_solution[key] = {
                LK.locationName: loc[LK.locationName],
                LK.locationType: loc[LK.locationType],
                CK.latitude: loc[CK.latitude],
                CK.longitude: loc[CK.longitude],
                LK.footfall: loc[LK.footfall],
                LK.salesVolume: loc[LK.salesVolume] * generalData[GK.refillSalesFactor],
            }
            continue

        # print("key----------------------------", key)
        # print(f"#f9: {f9_count}, #f3: {f3_count}")
        # print("local_score_exclude_footfall:", local_score_exclude_footfall)
        # print("co2_savings_price:", co2_savings_price)
        # print("earnings", earnings)

        # add to solution dict
        solution[LK.locations][key] = {
            LK.f9100Count: int(f9_count),
            LK.f3100Count: int(f3_count),
        }

    return solution


if __name__ == "__main__":
    main()
