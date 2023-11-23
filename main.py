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
import math

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
            solution = try_2(mapEntity, generalData, mapName)
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


def try_2(mapEntity, generalData, mapName):
    # goal: salesCapacity close (or >=) to sales volumn as much as possible
    # maxima (salse) revenue, co2_saving, total footfall for all selected locations
    # minima leasing cost

    max_number_of_f9100 = 2  # based on the rule
    max_number_of_f3100 = 2  # based on the rule
    solution = {LK.locations: {}}


    # step 1 - set machine or not
    set_machine_dict = {}
    for curr_location in mapEntity[LK.locations].values():

        big_candidate_list = []
        small_candidate_list = []

        for candidate_location in mapEntity[LK.locations].values():
            distance = distanceBetweenPoint(
                curr_location[CK.latitude],
                curr_location[CK.longitude],
                candidate_location[CK.latitude],
                candidate_location[CK.longitude]
            )
            if distance <= generalData[GK.willingnessToTravelInMeters]:
                if candidate_location[LK.salesVolume] * generalData[GK.refillSalesFactor] < generalData[GK.f3100Data][GK.refillCapacityPerWeek]:
                    small_candidate_list.append(candidate_location[LK.locationName])
                else:
                    big_candidate_list.append(candidate_location[LK.locationName])

        if curr_location[LK.salesVolume] * generalData[GK.refillSalesFactor] < generalData[GK.f3100Data][GK.refillCapacityPerWeek] * 1:

            if len(big_candidate_list) + len(small_candidate_list) == 0:
                set_machine_dict[curr_location[LK.locationName]] = True
            elif len(big_candidate_list) > 0:
                set_machine_dict[curr_location[LK.locationName]] = False
            else:
                small_candidate_list.append(curr_location[LK.locationName])
                sorted_small_candidate_list = sorted(
                    small_candidate_list,
                    key=lambda loc_name: mapEntity[LK.locations][loc_name][LK.footfall],
                    reverse=True
                )
                set_machine_dict[sorted_small_candidate_list[0]] = True

                if sorted_small_candidate_list[0] != curr_location[LK.locationName]:
                    # set_machine_dict[curr_location[LK.locationName]] = set_machine_dict.get(curr_location[LK.locationName], False)
                    set_machine_dict[curr_location[LK.locationName]] = False

        # elif curr_location[LK.salesVolume] * generalData[GK.refillSalesFactor] > generalData[GK.f3100Data][GK.refillCapacityPerWeek] * 1.5:
        #     set_machine_dict[curr_location[LK.locationName]] = True


        else:

            if len(big_candidate_list) + len(small_candidate_list) == 0:
                set_machine_dict[curr_location[LK.locationName]] = True
            elif len(big_candidate_list) > 0:
                big_candidate_list.append(curr_location[LK.locationName])
                sorted_big_candidate_list = sorted(
                    big_candidate_list,
                    key=lambda loc_name: mapEntity[LK.locations][loc_name][LK.footfall],
                    reverse=True
                )
                set_machine_dict[sorted_big_candidate_list[0]] = True

                if sorted_big_candidate_list[0] != curr_location[LK.locationName]:
                    set_machine_dict[curr_location[LK.locationName]] = set_machine_dict.get(curr_location[LK.locationName], False)
                    # set_machine_dict[curr_location[LK.locationName]] = False
            else:
                set_machine_dict[curr_location[LK.locationName]] = True


    # step 2 - re-calculate sales volume
    locationListNoRefillStation = {}
    locationListWithRefillStation = {}
    for key in mapEntity[LK.locations]:
        loc = mapEntity[LK.locations][key]
        if set_machine_dict[key]:
            locationListWithRefillStation[key] = {
                LK.locationName: loc[LK.locationName],
                LK.locationType: loc[LK.locationType],
                CK.latitude: loc[CK.latitude],
                CK.longitude: loc[CK.longitude],
                LK.footfall: loc[LK.footfall],
                LK.footfallScale: loc[LK.footfallScale],
                LK.salesVolume: loc[LK.salesVolume] * generalData[GK.refillSalesFactor]
            }

        else:
            locationListNoRefillStation[key] = {
                LK.locationName: loc[LK.locationName],
                LK.locationType: loc[LK.locationType],
                CK.latitude: loc[CK.latitude],
                CK.longitude: loc[CK.longitude],
                LK.footfall: loc[LK.footfall],
                LK.salesVolume: loc[LK.salesVolume] * generalData[GK.refillSalesFactor],
            }

    locationListWithRefillStation = distributeSales(
        locationListWithRefillStation, locationListNoRefillStation, generalData
    )

    # step 3 - set number of f9100 and f3100
    for key in locationListWithRefillStation:
        loc = locationListWithRefillStation[key]
        sales_volume = loc[LK.salesVolume]

        if loc[LK.salesVolume] < generalData[GK.f3100Data][GK.refillCapacityPerWeek]:
            f9_count_finall = 0
            f3_count_finall = 1
            max_temp_score = calculate_local_score(
                f3_count_finall,
                f9_count_finall,
                generalData,
                sales_volume
            )
        else:

            f9_count = sales_volume // generalData[GK.f9100Data][GK.refillCapacityPerWeek]
            f9_count = max_number_of_f9100 if f9_count > max_number_of_f9100 else f9_count

            rest_volume = sales_volume - f9_count * generalData[GK.f9100Data][GK.refillCapacityPerWeek]

            f3_count = rest_volume // generalData[GK.f3100Data][GK.refillCapacityPerWeek]
            f3_count = max_number_of_f3100 if f3_count > max_number_of_f3100 else f3_count

            max_temp_score = float("inf") * -1
            for f9_c, f3_c in [(f9_count, f3_count), (f9_count, f3_count + 1), (f9_count + 1, 0)]:
                if f9_c > 2 or f3_c > 2:
                    continue
                local_score_exclude_footfall = calculate_local_score(
                    f3_c,
                    f9_c,
                    generalData,
                    sales_volume
                )
                max_temp_score = max(max_temp_score, local_score_exclude_footfall)
                if max_temp_score == local_score_exclude_footfall:
                    f9_count_finall = f9_c
                    f3_count_finall = f3_c

        if max_temp_score < 0 and loc[LK.footfallScale] < 0:
            continue

        # add to solution dict
        solution[LK.locations][key] = {
            LK.f9100Count: int(f9_count_finall),
            LK.f3100Count: int(f3_count_finall),
        }

    return solution


def calculate_local_score(f3_count, f9_count, generalData, sales_volume):
    # calculate earnings
    sales_capacity = \
        f3_count * generalData[GK.f3100Data][GK.refillCapacityPerWeek] + \
        f9_count * generalData[GK.f9100Data][GK.refillCapacityPerWeek]
    sales = min(round(sales_volume, 0), sales_capacity)

    revenue = sales * generalData[GK.refillUnitData][GK.profitPerUnit]
    leasing_cost = \
        f3_count * generalData[GK.f3100Data][GK.leasingCostPerWeek] + \
        f9_count * generalData[GK.f9100Data][GK.leasingCostPerWeek]

    earnings = (revenue - leasing_cost) / 1000

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


def distanceBetweenPoint(lat_1, long_1, lat_2, long_2) -> int:
    R = 6371e3
    φ1 = lat_1 * math.pi / 180  #  φ, λ in radians
    φ2 = lat_2 * math.pi / 180
    Δφ = (lat_2 - lat_1) * math.pi / 180
    Δλ = (long_2 - long_1) * math.pi / 180

    a = math.sin(Δφ / 2) * math.sin(Δφ / 2) + math.cos(φ1) * math.cos(φ2) * math.sin(
        Δλ / 2
    ) * math.sin(Δλ / 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    d = R * c

    return round(d, 0)


def distributeSales(with_, without, generalData):
    for key_without in without:
        distributeSalesTo = {}
        loc_without = without[key_without]

        for key_with_ in with_:
            distance = distanceBetweenPoint(
                loc_without[CK.latitude],
                loc_without[CK.longitude],
                with_[key_with_][CK.latitude],
                with_[key_with_][CK.longitude],
            )
            if distance < generalData[GK.willingnessToTravelInMeters]:
                distributeSalesTo[with_[key_with_][LK.locationName]] = distance

        total = 0
        if distributeSalesTo:
            for key_temp in distributeSalesTo:
                distributeSalesTo[key_temp] = (
                    math.pow(
                        generalData[GK.constantExpDistributionFunction],
                        generalData[GK.willingnessToTravelInMeters]
                        - distributeSalesTo[key_temp],
                    )
                    - 1
                )
                total += distributeSalesTo[key_temp]

            for key_temp in distributeSalesTo:
                with_[key_temp][LK.salesVolume] += (
                    distributeSalesTo[key_temp]
                    / total
                    * generalData[GK.refillDistributionRate]
                    * loc_without[LK.salesVolume]
                )

    return with_


if __name__ == "__main__":
    main()
