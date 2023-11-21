import os
import math
import json
from scoring import calculateScore, distanceBetweenPoint
from api import getGeneralData, getMapData, submit
from data_keys import (
    MapNames as MN,
    LocationKeys as LK,
    ScoringKeys as SK,
    HotspotKeys as HK,
    GeneralKeys as GK,
    CoordinateKeys as CK,
)
from dotenv import load_dotenv

load_dotenv()
apiKey = os.environ["apiKey"]
game_folder = "my_games"


def main():
    if not os.path.exists("my_games"):
        print(f"Creating folder {game_folder}")
        os.makedirs(game_folder)

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
        ##Get map data from Considition endpoint
        data_file_name = f"data/map_{mapName}.json"
        if not os.path.isfile(data_file_name):
            mapEntity = getMapData(mapName, apiKey)
            with open(data_file_name, "w", encoding="utf8") as f:
                json.dump(mapEntity, f, indent=4)
        else:
            with open(data_file_name, "r", encoding="utf8") as f:
                mapEntity = json.load(f)

        ##Get non map specific data from Considition endpoint
        genderal_file_name = "data/general.json"
        if not os.path.isfile(genderal_file_name):
            generalData = getGeneralData()
            with open(genderal_file_name, "w", encoding="utf8") as f:
                json.dump(generalData, f, indent=4)
        else:
            with open(genderal_file_name, "r", encoding="utf8") as f:
                generalData = json.load(f)

        if mapEntity and generalData:
            # ------------------------------------------------------------
            # ----------------Player Algorithm goes here------------------
            solution = calulate_solution(mapEntity, generalData)
            # solution = {LK.locations: {}}
            # if mapName not in [MN.sSandbox, MN.gSandbox]:
            #     for key in mapEntity[LK.locations]:
            #         location = mapEntity[LK.locations][key]
            #         name = location[LK.locationName]

            #         salesVolume = location[LK.salesVolume]
            #         if salesVolume > 100:
            #             solution[LK.locations][name] = {
            #                 LK.f9100Count: 1,
            #                 LK.f3100Count: 0,
            #             }
            # else:
            #     hotspot1 = mapEntity[HK.hotspots][0]
            #     hotspot2 = mapEntity[HK.hotspots][1]

            #     solution[LK.locations]["location1"] = {
            #         LK.f9100Count: 1,
            #         LK.f3100Count: 0,
            #         LK.locationType: generalData[GK.locationTypes][
            #             GK.groceryStoreLarge
            #         ][GK.type_],
            #         CK.longitude: hotspot1[CK.longitude],
            #         CK.latitude: hotspot1[CK.latitude],
            #     }

            #     solution[LK.locations]["location2"] = {
            #         LK.f9100Count: 0,
            #         LK.f3100Count: 1,
            #         LK.locationType: generalData[GK.locationTypes][GK.groceryStore][
            #             GK.type_
            #         ],
            #         CK.longitude: hotspot2[CK.longitude],
            #         CK.latitude: hotspot2[CK.latitude],
            #     }
            # ----------------End of player code--------------------------
            # ------------------------------------------------------------

            # Score solution locally
            score = calculateScore(mapName, solution, mapEntity, generalData)

            print(f"Score: {score[SK.gameScore]}")
            # id_ = score[SK.gameId]
            # print(f"Storing game with id {id_}.")
            # print(f"Enter {id_} into visualization.ipynb for local vizualization ")

            # # Store solution locally for visualization
            # with open(f"{game_folder}/{id_}.json", "w", encoding="utf8") as f:
            #     json.dump(score, f, indent=4)

            # # Submit and and get score from Considition app
            # print(f"Submitting solution to Considtion 2023 \n")

            # scoredSolution = submit(mapName, solution, apiKey)
            # if scoredSolution:
            #     print("Successfully submitted game")
            #     print(f"id: {scoredSolution[SK.gameId]}")
            #     print(f"Score: {scoredSolution[SK.gameScore]}")


def calulate_solution(mapEntity, generalData):

    solution = {LK.locations: {}}

    for key in mapEntity[LK.locations]:
        location = mapEntity[LK.locations][key]

        name = location[LK.locationName]

        if location["locationType"] == "Grocery-store-large":
            solution[LK.locations][name] = {
                LK.f9100Count: 1,
                LK.f3100Count: 0,
            }
            continue

        # if location["locationType"] == "Grocery-store":
        #     solution[LK.locations][name] = {
        #         LK.f9100Count: 0,
        #         LK.f3100Count: 1,
        #     }
        #     continue

        salesVolume = location[LK.salesVolume] * generalData[GK.refillSalesFactor]
        f3100_capacity = generalData[GK.f3100Data][GK.refillCapacityPerWeek]
        f9100_capacity = generalData[GK.f9100Data][GK.refillCapacityPerWeek]

        f3100_leasing_cost = generalData[GK.f3100Data][GK.leasingCostPerWeek]
        f9100_leasing_cost = generalData[GK.f9100Data][GK.leasingCostPerWeek]

        sales = salesVolume
        if abs(f9100_capacity-salesVolume) > abs(f3100_capacity-salesVolume):
            if f3100_capacity < salesVolume:
                sales = f3100_capacity

            revenue = sales * generalData[GK.refillUnitData][GK.profitPerUnit]

            if revenue - f3100_leasing_cost > 0:
                solution[LK.locations][name] = {
                    LK.f9100Count: 0,
                    LK.f3100Count: 1,
                }
        else:
            if f9100_capacity < salesVolume:
                sales = f9100_capacity
            revenue = sales * generalData[GK.refillUnitData][GK.profitPerUnit]

            if revenue - f9100_leasing_cost > 0:
                solution[LK.locations][name] = {
                    LK.f9100Count: 1,
                    LK.f3100Count: 0,
                }

    # ============================================================
    # Check if distance smaller than 200 meters between two locations
    in_willing_travel_range = {}

    loc = mapEntity["locations"]
    for central_location in solution["locations"].keys():
        in_willing_travel_range[central_location] = {}
        remain_location_list = list(solution["locations"].keys())
        remain_location_list.remove(central_location)
        for remain_location in remain_location_list:
            distance = distanceBetweenPoint(
                loc[central_location][CK.latitude],
                loc[central_location][CK.longitude],
                loc[remain_location][CK.latitude],
                loc[remain_location][CK.longitude],
            )
            if distance < (generalData[GK.willingnessToTravelInMeters]):
                in_willing_travel_range[central_location][remain_location] = distance

        if len(in_willing_travel_range[central_location]) == 0:
            in_willing_travel_range.pop(central_location)

    del_location = []
    calcualted = []
    for i, location in enumerate(in_willing_travel_range):
        # print(location)
        # print(in_willing_travel_range[location])
        if (location in del_location) or (location in calcualted):
            continue

        # print(location, in_willing_travel_range[location])

        # 只有兩個點
        if len(in_willing_travel_range[location]) == 1:
            neighbor_location = list(in_willing_travel_range[location].keys())[0]
            if len(in_willing_travel_range[neighbor_location]) > 1:
                continue
            if (loc[location]["salesVolume"] > loc[neighbor_location]["salesVolume"]) or \
                (loc[location]["salesVolume"] == loc[neighbor_location]["salesVolume"] and loc[location]["footfall"] > loc[neighbor_location]["footfall"]):
                sales_volume = loc[location]["salesVolume"] + \
                    loc[neighbor_location]["salesVolume"]*generalData[GK.refillDistributionRate]
                if sales_volume*generalData[GK.refillSalesFactor] > 70 and sales_volume*generalData[GK.refillSalesFactor] < 140:
                    solution["locations"][location]["freestyle3100Count"] += 1
                
                if sales_volume*generalData[GK.refillSalesFactor] > 140 and sales_volume*generalData[GK.refillSalesFactor] < 438:
                    if solution["locations"][location]["freestyle9100Count"] == 0:
                        solution["locations"][location]["freestyle9100Count"] += 1
                        solution["locations"][location]["freestyle3100Count"] -= 1

                if sales_volume*generalData[GK.refillSalesFactor] > 438  and sales_volume*generalData[GK.refillSalesFactor] < (438+70):
                    solution["locations"][location]["freestyle3100Count"] += 1

                del_location.append(neighbor_location)
                calcualted.append(location)

            else:
                sales_volume = loc[neighbor_location]["salesVolume"] + \
                    loc[location]["salesVolume"]*generalData[GK.refillDistributionRate]
                # if sales_volume*generalData[GK.refillSalesFactor] > 70  and sales_volume*generalData[GK.refillSalesFactor] < 140:
                #     solution["locations"][neighbor_location]["freestyle3100Count"] += 1
                if sales_volume*generalData[GK.refillSalesFactor] > 72 and sales_volume*generalData[GK.refillSalesFactor] < 140:
                    solution["locations"][neighbor_location]["freestyle3100Count"] += 1
                
                if sales_volume*generalData[GK.refillSalesFactor] > 140 and sales_volume*generalData[GK.refillSalesFactor] < 438:
                    if solution["locations"][neighbor_location]["freestyle9100Count"] == 0:
                        solution["locations"][neighbor_location]["freestyle9100Count"] += 1
                        solution["locations"][neighbor_location]["freestyle3100Count"] -= 1

                if sales_volume*generalData[GK.refillSalesFactor] > 438  and sales_volume*generalData[GK.refillSalesFactor] < (438+70):
                    solution["locations"][neighbor_location]["freestyle3100Count"] += 1

                del_location.append(location)
                calcualted.append(neighbor_location)
            
            # print(del_location)

        # 兩個點以上，且所有點都包含在一起
        if len(in_willing_travel_range[location]) > 1:

            neighbor_location = list(in_willing_travel_range[location].keys())
            # count = 0
            # for i in neighbor_location:
            #     if len(in_willing_travel_range[i]) == (len(neighbor_location)+1):
            #         count += 1
            # if count != len(neighbor_location):
            #     continue

            # next_location = False
            # for i in neighbor_location:
            #     if len(in_willing_travel_range[i]) != (len(neighbor_location)+1):
            #         next_location = True
            #         break
            # if next_location:
            #     continue
            # print(location)
            # print(in_willing_travel_range[location])

            # # 取 footfall 最大的 location 或是 salesVolume 最大的點
            # max_footfall = loc[location]["footfall"]
            # max_sales_volume = loc[location]["salesVolume"]
            # for i in neighbor_location:
            #     max_sales_volume = max(max_sales_volume, loc[i]["salesVolume"])
            #     max_footfall = max(max_footfall, loc[i]["footfall"])

            # if mapEntity["locationTypeCount"]["total"] > 100:
            #     if loc[location]["footfall"] != max_footfall:
            #         continue
            # else:
            #     if loc[location]["salesVolume"] != max_sales_volume:
            #         continue

            salesVolume_list = [loc[location]["salesVolume"]]
            footfall_list = [loc[location]["footfall"]]
            for i in neighbor_location:
                salesVolume_list.append(loc[i]["salesVolume"])
                footfall_list.append(loc[i]["footfall"])
            max_sales_volume = max(salesVolume_list)
            max_footfall = max(footfall_list)
            
            # 如果全部的 salesVolume 都一樣，取 footfall 最大的點
            # if all(salesVolume_list) == max_sales_volume:
            if salesVolume_list.count(max_sales_volume) == len(salesVolume_list):
                if loc[location]["footfall"] != max_footfall:
                    continue
            # 如果 salesVolume 不是最大，跳過
            if loc[location]["salesVolume"] != max_sales_volume:
                continue
            # salesVolume 的值最大，但並非和其他 location 一樣
            else:
                # 找出同樣 salesVolume 值的最大 footfall 值
                max_sales_volume_footfall = max([footfall_list[i] for i, ele in enumerate(salesVolume_list) if ele == max_sales_volume])
                if loc[location]["footfall"] != max_sales_volume_footfall:
                    continue

            sum_sales_volume = loc[location]["salesVolume"]
            for i in neighbor_location:
                # print(i)
                sum_sales_volume += loc[i]["salesVolume"]*generalData[GK.refillDistributionRate]
                del_location.append(i)

            # print(sum_sales_volume*generalData[GK.refillSalesFactor])
            if sum_sales_volume*generalData[GK.refillSalesFactor] > 438:
                solution["locations"][location]["freestyle9100Count"] += 1
            elif sum_sales_volume*generalData[GK.refillSalesFactor] > 140 and solution["locations"][location]["freestyle9100Count"] == 0:
                solution["locations"][location]["freestyle9100Count"] += 1
                if solution["locations"][location]["freestyle3100Count"] == 1:
                    solution["locations"][location]["freestyle3100Count"] -= 1
            elif sum_sales_volume*generalData[GK.refillSalesFactor] > 70:
                solution["locations"][location]["freestyle3100Count"] += 1

        # del_location.append("location39")

        # # 兩個 location 以上，但可能被包含在不同的圈圈裡
        # for willing_travel_location in in_willing_travel_range:
        #     # 刪除只有兩個 location 的圈圈
        #     if len(in_willing_travel_range[willing_travel_location]) == 1:
        #         continue
        #     # 在 willing travel 的距離，還沒被刪掉
        #     if willing_travel_location in del_location:
        #         continue
            
        #     # print(willing_travel_location, in_willing_travel_range[willing_travel_location])
        #     # 紀錄該 location 在不同圈圈出現的次數
        #     appear_times = {}

        #     # print(in_willing_travel_range[location])
        #     for l in in_willing_travel_range[willing_travel_location]:
        #         print(l)
        #         if not appear_times.get(l):
        #             appear_times[l] = 1
        #         else:
        #             appear_times[l] += 1
        #         print(l, in_willing_travel_range[willing_travel_location][l])
        #         print(in_willing_travel_range[l])
        #         for j in in_willing_travel_range[l]:
        #             # print(j)
        #             if not appear_times.get(j):
        #                 appear_times[j] = 1
        #             else:
        #                 appear_times[j] += 1

        #     # 不考慮全部的 location 都包含在一起
        #     appear_times_list = list(appear_times.values())
        #     if appear_times_list.count(appear_times_list[0]) == len(appear_times_list):
        #         continue
            
        #     # print(willing_travel_location, in_willing_travel_range[willing_travel_location])
        #     # print(appear_times)
        #     # for a in appear_times:
        #     #     print(mapEntity["locations"][a])
        #     #     if mapEntity["locations"][a]["footfallScale"] == 0:
        #     #         del_location.append(a)
        #     # print("-----"*20)

            
        #     appear_times_key_list = list(appear_times)
        #     # print(appear_times_key_list)
        #     idx = appear_times_list.index(min(appear_times_list))
        #     pop_location = appear_times_key_list[idx]

        #     del_location.append(pop_location)
        #     # print(idx, pop_location)
        #     # print(appear_times_key_list)
            
            # appear_times_key_list.remove(pop_location)
            # # print(appear_times_key_list)
            # del_location.extend(appear_times_key_list)

            # print("========"*10)

            # print("="*50)
    # print(del_location)

    for i in set(del_location):
        # print(i)
        solution["locations"].pop(i)

    
    sales_volume_total = {}
    # 沒有設機器的 location
    for key_without in mapEntity["locations"]:
        if key_without in solution["locations"]:
            continue

        distributeSalesTo = {}
        loc_without = mapEntity["locations"][key_without]

        # 有設機器的 location
        for key_with_ in solution["locations"]:
            # 計算有設機器與沒設機器的 location 的距離，留下 200 公尺的 location
            distance = distanceBetweenPoint(
                loc_without[CK.latitude],
                loc_without[CK.longitude],
                mapEntity["locations"][key_with_][CK.latitude],
                mapEntity["locations"][key_with_][CK.longitude],
            )
            if distance < generalData[GK.willingnessToTravelInMeters]:
                distributeSalesTo[mapEntity["locations"][key_with_][LK.locationName]] = distance
        
        total = 0
        if distributeSalesTo:
            # 有設機器的 location
            for key_temp in distributeSalesTo:
                distributeSalesTo[key_temp] = (
                    # constantExpDistributionFunction = 1.03
                    # willingnessToTravelInMeters = 200
                    # 1.03^(200-distance_diff) - 1
                    # 距離越近，分數越高
                    math.pow(
                        generalData[GK.constantExpDistributionFunction],
                        generalData[GK.willingnessToTravelInMeters]
                        - distributeSalesTo[key_temp],
                    )
                    - 1
                )
                total += distributeSalesTo[key_temp]
            # 有設機器的 location 會去分攤沒設機器的 location 的 sales volume
            for key_temp in distributeSalesTo:
                if sales_volume_total.get(key_temp) == None:
                    sales_volume_total[key_temp] = (mapEntity["locations"][key_temp][LK.salesVolume] * generalData[GK.refillSalesFactor]) + (
                    distributeSalesTo[key_temp]
                    / total
                    * generalData[GK.refillDistributionRate]
                    * loc_without[LK.salesVolume]
                     * generalData[GK.refillSalesFactor]
                )
                else:
                    sales_volume_total[key_temp] += (
                    distributeSalesTo[key_temp]
                    / total
                    * generalData[GK.refillDistributionRate]
                    * loc_without[LK.salesVolume]
                     * generalData[GK.refillSalesFactor]
                )

    # print(sales_volume_total)

    for location in sales_volume_total:
        if sales_volume_total[location] < (solution["locations"][location]["freestyle3100Count"]*70 + solution["locations"][location]["freestyle9100Count"]*438):
            if (sales_volume_total[location] < (solution["locations"][location]["freestyle9100Count"]*438)) and \
                (solution["locations"][location]["freestyle9100Count"]*438 < (solution["locations"][location]["freestyle3100Count"]*70 + solution["locations"][location]["freestyle9100Count"]*438)):
                solution["locations"][location]["freestyle3100Count"] -= 1
                continue
            else:
                continue
        # print(location, sales_volume_total[location])
        # print(solution["locations"][location])
        if sales_volume_total[location] > 438:
            solution["locations"][location]["freestyle9100Count"] += 1
        elif sales_volume_total[location] > 140 and solution["locations"][location]["freestyle9100Count"] == 0:
            solution["locations"][location]["freestyle9100Count"] += 1
            if solution["locations"][location]["freestyle3100Count"] == 1:
                solution["locations"][location]["freestyle3100Count"] -= 1
        elif sales_volume_total[location] > 73:
            solution["locations"][location]["freestyle3100Count"] += 1

        # print(solution["locations"][location])
    
    # print(solution)
    
    return solution


if __name__ == "__main__":
    main()
