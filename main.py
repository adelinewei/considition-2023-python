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
    GeneralKeys as GK,
    HotspotKeys as HK,
    GeneralKeys as GK,
    CoordinateKeys as CK,
)
from dotenv import load_dotenv

load_dotenv()
apiKey = os.environ["apiKey"]
game_folder = "my_games"


def main():

    try:
        apiKey = os.environ["apiKey"]
    except Exception:
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
    print(f"10: {MN.sSandbox}")
    print(f"11: {MN.gSandbox}")
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
        case "10":
            mapName = MN.sSandbox
        case "11":
            mapName = MN.gSandbox
        case _:
            print("Invalid choice.")

    if mapName:

        if not os.path.exists(f"{game_folder}/{mapName}"):
            print(f"Creating folder {game_folder}")
            os.makedirs(f"{game_folder}/{mapName}")

        # Get map data from Considition endpoint
        mapEntity = getMapData(mapName, apiKey)
        # with open(f'data/{mapName}', 'w') as f:
        #     f.writelines(json.dumps(mapEntity, indent=2))

        # Get non map specific data from Considition endpoint
        generalData = getGeneralData()
        # with open(f'data/generalData', 'w') as f:
        #     f.writelines(json.dumps(generalData, indent=2))

        if mapEntity and generalData:
            # ------------------------------------------------------------
            # ----------------Player Algorithm goes here------------------
            # solution = example_solution(mapEntity, generalData, mapName)
            solution = try_1(mapEntity, generalData, mapName)
            # ----------------End of player code--------------------------
            # ------------------------------------------------------------

            print("\n===== Score solution locally =====")
            score = calculateScore(mapName, solution, mapEntity, generalData)

            id_ = score[SK.gameId]
            print(f"Local id: {score[SK.gameId]}")
            print(f"Local score: {score[SK.gameScore]}")

            # Store solution locally for visualization
            current_time_epoch = time()
            with open(f"{game_folder}/{mapName}/{current_time_epoch}_local_{id_}.json", "w", encoding="utf8") as f:
                json.dump(score, f, indent=4)

            print("\n===== Submit and and get score from Considition app =====")
            print("Submitting solution to Considtion 2023")

            scoredSolution = submit(mapName, solution, apiKey)
            if scoredSolution:
                print("Successfully submitted game")
                print(f"id: {scoredSolution[SK.gameId]}")
                print(f"Score: {scoredSolution[SK.gameScore]}")
                with open(f"{game_folder}/{mapName}/{current_time_epoch}_global_{scoredSolution[SK.gameId]}.json", "w", encoding="utf8") as f:
                    json.dump(scoredSolution, f, indent=4)


def example_solution(mapEntity, generalData, mapName):
    solution = {LK.locations: {}}

    if mapName not in [MN.sSandbox, MN.gSandbox]:
        for key in mapEntity[LK.locations]:
            location = mapEntity[LK.locations][key]
            name = location[LK.locationName]

            salesVolume = location[LK.salesVolume]
            if salesVolume > 100:
                solution[LK.locations][name] = {
                    LK.f9100Count: 1,
                    LK.f3100Count: 0,
                }
    else:
        print("======== Sandbox ========")
        hotspot1 = mapEntity[HK.hotspots][0]
        hotspot2 = mapEntity[HK.hotspots][1]

        solution[LK.locations]["location1"] = {
            LK.f9100Count: 1,
            LK.f3100Count: 0,
            LK.locationType: generalData[GK.locationTypes][
                GK.groceryStoreLarge
            ][GK.type_],
            CK.longitude: hotspot1[CK.longitude],
            CK.latitude: hotspot1[CK.latitude],
        }

        solution[LK.locations]["location2"] = {
            LK.f9100Count: 0,
            LK.f3100Count: 1,
            LK.locationType: generalData[GK.locationTypes][GK.groceryStore][
                GK.type_
            ],
            CK.longitude: hotspot2[CK.longitude],
            CK.latitude: hotspot2[CK.latitude],
        }
    return solution


def try_1(mapEntity, generalData, mapName):
    # goal: salesCapacity close (or >=) to sales volumn as much as possible
    # maxima (salse) revenue, co2_saving, total footfall for all selected locations
    # minima leasing cost

    max_number_of_f9100 = 2  # based on the rule
    max_number_of_f3100 = 2  # based on the rule

    solution = {LK.locations: {}}

    for key in mapEntity[LK.locations]:
        loc = mapEntity[LK.locations][key]

        distribute_scales = 0  # TODO add distributeScales, should be large
        sales_volume = (loc[LK.salesVolume] + distribute_scales) * generalData[GK.refillSalesFactor]

        if sales_volume < generalData[GK.f3100Data][GK.refillCapacityPerWeek]:
            f3_count = 1
            f9_count = 0
        else:
            f9_count = sales_volume // generalData[GK.f9100Data][GK.refillCapacityPerWeek]
            f9_count = max_number_of_f9100 if f9_count > max_number_of_f9100 else f9_count

            rest_volume = sales_volume - f9_count * generalData[GK.f9100Data][GK.refillCapacityPerWeek]

            f3_count = rest_volume // generalData[GK.f3100Data][GK.refillCapacityPerWeek]
            f3_count = max_number_of_f3100 if f3_count > max_number_of_f3100 else f3_count

            # if f9_count < 2 and f3_count == 2:
            #     f9_count += 1
            #     f3_count = 0
            if f9_count < max_number_of_f9100:
                # if replace n f3s by 1 f9
                temp_score_f9 = calculate_local_score(
                    f3_count=0,
                    f9_count=1,
                    generalData=generalData,
                    sales_volume=rest_volume)

                # if keep setting n f3s (n <= max_number_of_f3100)
                rest_volume = min(round(rest_volume, 4), (f3_count * generalData[GK.f3100Data][GK.refillCapacityPerWeek]))
                temp_score_f3 = calculate_local_score(
                    f3_count=f3_count,
                    f9_count=0,
                    generalData=generalData,
                    sales_volume=rest_volume)

                # replace n f3s by 1 f9 if it increase the local score
                if temp_score_f9 > temp_score_f3:
                    f9_count += 1
                    f3_count = 0

        # validation
        local_score_exclude_footfall = calculate_local_score(f3_count, f9_count, generalData, sales_volume)

        if f3_count + f9_count < 1 or (local_score_exclude_footfall < 0):
            continue

        # add to solution dict
        solution[LK.locations][key] = {
            LK.f9100Count: int(f9_count),
            LK.f3100Count: int(f3_count),
        }

    return solution


def calculate_local_score(f3_count, f9_count, generalData, sales_volume):
    # calculate earnings
    sales_capacity = \
        f3_count * generalData[GK.f3100Data][GK.refillCapacityPerWeek] + \
        f9_count * generalData[GK.f9100Data][GK.refillCapacityPerWeek]
    sales = min(round(sales_volume, 4), sales_capacity)

    revenue = sales * generalData[GK.refillUnitData][GK.profitPerUnit]
    leasing_cost = \
        f3_count * generalData[GK.f3100Data][GK.leasingCostPerWeek] + \
        f9_count * generalData[GK.f9100Data][GK.leasingCostPerWeek]

    earnings = revenue - leasing_cost

    # calculate co2 saving price
    co2_savings = \
        sales * (generalData[GK.classicUnitData][GK.co2PerUnitInGrams] - generalData[GK.refillUnitData][GK.co2PerUnitInGrams])
    co2_cost = \
        f3_count * generalData[GK.f3100Data][GK.staticCo2] + \
        f9_count * generalData[GK.f9100Data][GK.staticCo2]

    co2_savings_balance = co2_savings - co2_cost
    co2_savings_price = (co2_savings_balance / 1000) * generalData[GK.co2PricePerKiloInSek]

    # calculate local score (exclude footfall)
    local_score_exclude_footfall = co2_savings_price + earnings

    return local_score_exclude_footfall


if __name__ == "__main__":
    main()
