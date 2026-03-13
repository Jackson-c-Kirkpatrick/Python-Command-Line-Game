# Jackson Kirkpatrick
# Oregon Trail-inspired command-line game written in Python.
# Features inventory management, random events, hunting, rider encounters,
# mountain hazards, and binary save/load functionality.

import random
import time
import struct
from dataclasses import dataclass

SOUTH_PASS_MILEAGE = 950
BLUE_MOUNTAINS_MILEAGE = 1700
OREGON_CITY_MILEAGE = 2040

weekdays = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]

@dataclass
class Status:
    ammo: int = 0
    cash: int = 700
    clothes: int = 0
    food: int = 0
    miles: int = 0
    oxen: int = 0
    supplies: int = 0
    turn: int = 0
    blueMountainsCleared: bool = False
    fortAvailable: bool = False
    haveIllness: bool = False
    haveInjury: bool = False
    isDead: bool = False
    southPassCleared: bool = False
    milesLastTurn: int = 0

@dataclass
class Choices:
    eat: int = 0
    turn: int = 0
    riders: int = 0

status = Status()
choice = Choices()

SAVE_FORMAT = "<9i6?"
SAVE_SIZE = struct.calcsize(SAVE_FORMAT)

chanceEncounterRiders = 4
chanceRuggedMountain = 15
blizzard = False

def addCash(n: int) -> None:
    status.cash += n
    if status.cash < 0:
        status.cash = 0

def addOxen(n: int) -> None:
    status.oxen += n
    if status.oxen < 0:
        status.oxen = 0

def addFood(n: int) -> None:
    status.food += n
    if status.food < 0:
        status.food = 0

def addAmmo(n: int) -> None:
    status.ammo += n
    if status.ammo < 0:
        status.ammo = 0

def addClothes(n: int) -> None:
    status.clothes += n
    if status.clothes < 0:
        status.clothes = 0

def addSupplies(n: int) -> None:
    status.supplies += n
    if status.supplies < 0:
        status.supplies = 0

def addTurn(n: int) -> None:
    status.turn += n

def addMiles(n: int) -> None:
    status.miles += n
    if status.miles < 0:
        status.miles = 0

def recordMileage() -> None:
    status.milesLastTurn = status.miles


def to_upper_manual(text: str) -> str:
    out = []
    for ch in text:
        if 'a' <= ch <= 'z':
            out.append(chr(ord(ch) - 32))
        else:
            out.append(ch)
    return ''.join(out)

def print_inventory() -> None:
    header = f"{'FOOD':15}{'AMMO':15}{'CLOTHING':15}{'MISC. SUPP.':15}{'CASH':12}"
    row    = f"{status.food:15}{status.ammo:15}{status.clothes:15}{status.supplies:15}{status.cash:12}"
    print(header)
    print(row)

def died() -> None:
    print("Due to your unfortunate situation, there are a few formalities we must go through.")
    _ = input("Would you like a minister (Y/N)? ")
    _ = input("Would you like a fancy funeral (Y/N)? ")
    kin = to_upper_manual(input("Would you like us to inform your next of kin (Y/N)? ").strip())
    if kin in ("N", "NO"):
        print("Your Aunt Nellie in St. Louis is anxious to hear")
    print("We thank you for this information and we are sorry you didn't make it to the great territory of Oregon.")
    print("Better luck next time.")
    print("Sincerely, the Oregon City Chamber of Commerce.")
    status.isDead = True

def isGameComplete() -> bool:
    return status.miles >= OREGON_CITY_MILEAGE or status.isDead

def saveFile(filename: str = "trail_save.dat") -> None:
    try:
        data = struct.pack(
            SAVE_FORMAT,
            status.miles,
            status.cash,
            status.ammo,
            status.food,
            status.supplies,
            status.oxen,
            status.clothes,
            status.turn,
            status.milesLastTurn,
            status.fortAvailable,
            status.haveIllness,
            status.haveInjury,
            status.isDead,
            status.blueMountainsCleared,
            status.southPassCleared,
        )
        with open(filename, "wb") as f:
            f.write(data)
    except OSError:
        print("Could not save game file.")

def loadFile(filename: str = "trail_save.dat") -> None:
    try:
        with open(filename, "rb") as f:
            data = f.read()

        if len(data) != SAVE_SIZE:
            raise OSError("Save file wrong size")

        unpacked = struct.unpack(SAVE_FORMAT, data)
        (
            miles,
            cash,
            ammo,
            food,
            supplies,
            oxen,
            clothes,
            turn,
            milesLastTurn,
            fortAvailable,
            haveIllness,
            haveInjury,
            isDead,
            blueCleared,
            southCleared,
        ) = unpacked

        status.miles = miles
        status.cash = cash
        status.ammo = ammo
        status.food = food
        status.supplies = supplies
        status.oxen = oxen
        status.clothes = clothes
        status.turn = turn
        status.milesLastTurn = milesLastTurn
        status.fortAvailable = bool(fortAvailable)
        status.haveIllness = bool(haveIllness)
        status.haveInjury = bool(haveInjury)
        status.isDead = bool(isDead)
        status.blueMountainsCleared = bool(blueCleared)
        status.southPassCleared = bool(southCleared)

        print("Previous game loaded from binary file.")
    except (OSError, struct.error):
        print("No valid save file found. Starting new game.")

dates = [
    "March 29", "April 12", "April 26", "May 10",
    "May 24", "June 7", "June 21", "July 5",
    "July 19", "August 2", "August 16", "August 31",
    "September 13", "September 27", "October 11", "October 25",
    "November 8", "November 22",
]

def announce_date() -> None:
    if 1 <= status.turn <= len(dates):
        print(f"Monday, {dates[status.turn - 1]}, 1847")
    else:
        print("Monday, (date unknown), 1847")

choiceTurnResponses = ["Stopping at the fort", "Hunting", "Continuing the trail", "Quit"]
choiceEatResponses = ["Eating poorly", "Eating moderately", "Eating well"]
choiceRidersResponses = ["Running", "Attacking", "Continuing the trail", "Circling the wagons"]

events = [
    "Wagon breaks down -- lose time and supplies fixing it.",
    "Ox injures leg -- slows you down rest of trip",
    "Bad luck -- your daughter broke her arm.",
    "Ox wanders off -- spend time looking for it.",
    "Your son gets lost -- spend half the day looking for him.",
    "Unsafe water -- lose time looking for clean spring.",
    "Heavy rains -- time and supplies lost.",
    "Bandits attack",
    "There was a fire in your wagon -- food and supplies damaged.",
    "Lose your way in heavy fog -- time is lost.",
    "You killed a poisonous snake after it bit you.",
    "Wagon gets swamped fording river -- lose food and clothes.",
    "Wild animals attack!",
    "Cold weather -- BRRRRRR!",
    "Hail storm -- supplies damaged",
    "Helpful Indians show you where to find more food.",
]

def ask_menu(prompt: str, valid_numbers: set[int]) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            x = int(raw)
        except ValueError:
            print(f"Please enter a number: {', '.join(map(str, sorted(valid_numbers)))}.")
            continue
        if x in valid_numbers:
            return x
        print(f"Please enter one of: {', '.join(map(str, sorted(valid_numbers)))}.")

def getRandom(low: int, high: int) -> int:
    return random.randint(low, high)

def distanceCurve(eventType: int) -> int:
    miles_scaled = (status.miles / 100.0) - eventType
    numerator = (miles_scaled ** 2) + 72
    denominator = (miles_scaled ** 2) + 12
    return int(numerator / denominator)

def ask_int(prompt: str) -> int:
    while True:
        s = input(prompt).strip()
        try:
            return int(s)
        except ValueError:
            print("Please enter a whole number with no $ or decimals.")

def getSick() -> bool:
    print("You became sick.")

    if status.supplies > 0:
        print("You use some medical supplies and eventually recover.")
        addSupplies(-5)
        if status.supplies < 0:
            status.supplies = 0 
        return True
    else:
        print("You have no medical supplies. Your condition worsens.")
        status.haveIllness = True
        return False

def getInitialPurchase() -> None:
    print("\nLet's outfit your wagon. You have $700 to spend.")
    while True:
        spendOx = ask_int("How much do you want to spend on OXEN? $")
        if 200 <= spendOx <= 300: break
        print("YOU MUST SPEND BETWEEN $200 AND $300 ON YOUR TEAM OF OXEN.")
    while True:
        spendFood = ask_int("How much do you want to spend on FOOD? $")
        if spendFood >= 0: break
        print("YOU MUST SPEND A NON-NEGATIVE AMOUNT.")
    while True:
        spendAmmo = ask_int("How much do you want to spend on AMMUNITION? $")
        if spendAmmo >= 0: break
        print("YOU MUST SPEND A NON-NEGATIVE AMOUNT.")
    while True:
        spendClothes = ask_int("How much do you want to spend on CLOTHING? $")
        if spendClothes >= 0: break
        print("YOU MUST SPEND A NON-NEGATIVE AMOUNT.")
    while True:
        spendMisc = ask_int("How much do you want to spend on MISCELLANEOUS? $")
        if spendMisc >= 0: break
        print("YOU MUST SPEND A NON-NEGATIVE AMOUNT.")
    addOxen(spendOx)
    addFood(spendFood)
    addAmmo(spendAmmo * 50)
    addClothes(spendClothes)
    addSupplies(spendMisc)
    total_spent = spendOx + spendFood + spendAmmo + spendClothes + spendMisc
    addCash(-total_spent)
    status.cash = max(0, status.cash)
    status.food = max(0, status.food)
    status.ammo = max(0, status.ammo)
    status.supplies = max(0, status.supplies)
    status.clothes = max(0, status.clothes)
    print(f"\nAFTER ALL YOUR PURCHASES, YOU NOW HAVE ${status.cash} DOLLARS LEFT.")
    print_inventory()

def visit_fort() -> None:
    print("\nWELCOME TO THE FORT")
    print("You can buy supplies here.")
    print(f"Current cash: ${status.cash}")

    buy_food = ask_int("How much do you want to spend on FOOD? $")
    buy_ammo = ask_int("How much do you want to spend on AMMO? $")
    buy_clothes = ask_int("How much do you want to spend on CLOTHING? $")
    buy_supplies = ask_int("How much do you want to spend on SUPPLIES? $")

    total = buy_food + buy_ammo + buy_clothes + buy_supplies

    if total > status.cash:
        print("You don't have that much cash. Leaving the fort.")
        return

    addCash(-total)
    addFood(buy_food)
    addAmmo(buy_ammo * 50)
    addClothes(buy_clothes)
    addSupplies(buy_supplies)

    print("You finish shopping at the fort.")
    print_inventory()

def caughtInBlizzard() -> None:
    global blizzard
    print("BLIZZARD IN MOUNTAIN PASS--TIME AND SUPPLIES LOST")
    blizzard = True
    addFood(-25)
    addSupplies(-10)
    addAmmo(-300)
    addMiles(-getRandom(30, 40))
    if status.clothes < getRandom(18, 20):
        _ = getSick()

def reachMountains() -> None:
    if status.miles >= SOUTH_PASS_MILEAGE:
        if getRandom(0, 10) < 9 - distanceCurve(chanceRuggedMountain):
            print("RUGGED MOUNTAINS")
            if getRandom(0, 100) < 10:
                if getRandom(0, 100) < 11:
                    print("THE GOING GETS SLOW")
                    addMiles(-getRandom(45, 90))
                else:
                    print("WAGON DAMAGED! -- LOSE TIME AND SUPPLIES")
                    addSupplies(-5)
                    addAmmo(-200)
                    addMiles(-getRandom(20, 30))
            else:
                print("YOU GOT LOST -- LOSE VALUABLE TIME TRYING TO FIND THE TRAIL!")
                addMiles(-60)

        if not status.southPassCleared:
            status.southPassCleared = True
            if getRandom(0, 100) < 80:
                caughtInBlizzard()
            else:
                print("YOU MADE IT SAFELY THROUGH THE SOUTH PASS -- NO SNOW")
        else:
     
            if status.miles >= BLUE_MOUNTAINS_MILEAGE:
                if not status.blueMountainsCleared:
                    status.blueMountainsCleared = True
                    if getRandom(0, 100) < 70:
                        caughtInBlizzard()

def shoot() -> int:
    start_seconds = time.perf_counter()
    player_text = input("TYPE BANG ")
    elapsed_seconds = time.perf_counter() - start_seconds
    if to_upper_manual(player_text) == "BANG":
        return int(elapsed_seconds)
    return 7

def hunt() -> None:
    addMiles(-45)
    spd = shoot()
    if spd <= 1:
        print("RIGHT BETWEEN THE EYES--YOU GOT A BIG ONE!!!!")
        addFood(52 + getRandom(0, 6))
        addAmmo(-(10 + getRandom(0, 4)))
    else:
        r = getRandom(0, 100)
        if r > spd * 13:
            print("NICE SHOT--RIGHT THROUGH THE NECK--FEAST TONIGHT!!")
            addFood(max(0, 48 - spd * 2))
            addAmmo(-(10 + spd * 3))
        else:
            print("SORRY---NO LUCK TODAY")

def process_riders_choice(riders_are_hostile: bool, player_choice: int) -> None:
    if riders_are_hostile:
        if player_choice == 1:
            print("Running")
            addMiles(20)
            addSupplies(-15)
            addAmmo(-150)
            addOxen(-40)
        elif player_choice == 2:
            print("Attacking")
            shoot_speed = shoot()
            addAmmo(-(shoot_speed * 4 + 80))
        elif player_choice == 3:
            print("Continuing the trail")
            if getRandom(1, 100) <= 20:
                print("They did not attack")
            else:
                addAmmo(-150)
                addSupplies(-15)
        elif player_choice == 4:
            shoot_speed = shoot()
            addAmmo(-(shoot_speed * 30 + 80))
            addMiles(-25)
    else:
        if player_choice == 1:
            print("Running")
            addMiles(15)
            addOxen(-10)
        elif player_choice == 2:
            print("Attacking")
            addMiles(-5)
            addAmmo(-100)
        elif player_choice == 3:
            print("Continuing the trail")
        elif player_choice == 4:
            print("Circling the wagons")
            addMiles(-20)
    if status.ammo <= 0:
        print("You ran out of bullets and got massacred by the riders")
        died()

def apply_event_effects(event_index: int) -> None:
    idx = event_index + 1
    if idx == 1:
        addMiles(-getRandom(15, 20))
        addSupplies(-8)
    elif idx == 2:
        addMiles(-25)
        addOxen(-20)
    elif idx == 3:
        addMiles(-getRandom(5, 9))
        addSupplies(-getRandom(2, 5))
    elif idx == 4:
        addMiles(-17)
    elif idx == 5:
        addMiles(-10)
    elif idx == 6:
        addMiles(-getRandom(10, 12))
    elif idx == 7:
        if status.miles < 950:
            addFood(-10)
            addAmmo(-500)
            addSupplies(-15)
            addMiles(-getRandom(10, 15))
    elif idx == 8:
        print("Bandit attack")
        shoot_speed = shoot()
        addAmmo(-(20 * shoot_speed))
        if status.ammo < 1:
            print("You ran out of bullets -- they get lots of cash")
            two_thirds = (status.cash * 2) // 3
            addCash(-two_thirds)
        elif shoot_speed <= 1:
            print("Quickest draw outside of Dodge City!!! You got 'em!")
        else:
            print("You got shot in the leg and they took one of your oxen. Better have a doctor look at your wound.")
            status.haveInjury = True
            addSupplies(-5)
            addOxen(-20)
    elif idx == 9:
        addFood(-40)
        addAmmo(-400)
        addMiles(-15)
        addSupplies(-getRandom(3, 11))
    elif idx == 10:
        addMiles(-getRandom(10, 15))
    elif idx == 11:
        addAmmo(-10)
        addSupplies(-5)
        if status.supplies <= 0:
            print("You died of snakebite since you have no medicine")
            died()
    elif idx == 12:
        addFood(-30)
        addAmmo(-20)
        addMiles(-getRandom(20, 40))
    elif idx == 13:
        print("Wild animals attack!")
        if status.ammo < 40:
            print("You were too low on bullets. The wolves overpowered you")
            status.haveInjury = True
            died()
        else:
            shoot_speed = shoot()
            if shoot_speed <= 2:
                print("Nice shooting pardner -- They didn't get much")
            else:
                print("Slow on the draw -- They got at your food and clothes")
            addAmmo(-(20 + shoot_speed))
            addClothes(-(4 * shoot_speed))
            addFood(-(8 * shoot_speed))
    elif idx == 14:
        threshold = getRandom(22, 26)
        if status.clothes < threshold:
            print("You don't have enough clothing to keep warm.")
            status.haveIllness = True
            _ = getSick()
        else:
            print("You have enough clothing to keep warm.")
    elif idx == 15:
        addMiles(-getRandom(5, 15))
        addAmmo(-200)
        addSupplies(-getRandom(4, 7))
    elif idx == 16:
        addFood(14)

def show_instructions():
   print (""" This program simulates a trip over the Oregon Trail from
    Independence, Missouri to Oregon City, Oregon in 1847.
    Your family of five will cover the 2000 mile Oregon Trail
    in 5-6 months --- if you make it alive.

    You had saved $900 to spend for the trip, and you've just
        paid $200 for a wagon.
    You will need to spend the rest of your money on the
        following items:

        Oxen - You can spend $200 to $300 on your team.
            The more you spend, the faster you'll go
            because you'll have better oxen

        Food - The more you have, the less chance there
            is of getting sick

        Ammunition - $1 buys a belt of 50 bullets.
            You will need bullets for attacks by animals
            and bandits, and for hunting food

        Clothing - This is especially important for the cold
            weather you will encounter when crossing
            the mountains

        Miscellaneous supplies - This includes medicine and
            other things you will need for sickness
            and emergency repairs

    You can spend all your money before you start your trip
        or you can save some of your cash to spend at forts along
        the way when you run low. However, items cost more at
        the forts. You can also go hunting along the way to get
        more food.

    Whenever you have to use your trusty rifle along the way,
        you will see the words: TYPE BANG. The faster you type
        in the word 'BANG' and hit the 'RETURN' key, the better
        luck you'll have with your gun.
        When asked to enter money amounts, don't use a '$'.

    Good luck!!!""")

def arrived() -> None:
    if status.isDead:
        return

    print("YOU FINALLY ARRIVED AT OREGON CITY")
    print(f"AFTER {OREGON_CITY_MILEAGE} LONG MILES -- HOORAY!!")
    print()

    
    if status.miles == status.milesLastTurn:
        miles_fraction = 1.0
    else:
        miles_fraction = (OREGON_CITY_MILEAGE - status.milesLastTurn) / (
            status.miles - status.milesLastTurn
        )

    
    miles_fraction = max(0.0, min(1.0, miles_fraction))

    
    food_per_turn = 8 + 5 * choice.eat
    food_to_give_back = (1 - miles_fraction) * food_per_turn
    addFood(int(round(food_to_give_back)))

    
    last_turn_days = miles_fraction * 14.0

    
    days_traveled = int(status.turn * 14 + last_turn_days)

    
    day_of_week_index = int((last_turn_days + 6) % 7)
    print(weekdays[day_of_week_index])

    
    d = days_traveled
    if d < 125:
        d -= 93
        month = "JULY"
    elif d < 156:
        d -= 124
        month = "AUGUST"
    elif d < 186:
        d -= 155
        month = "SEPTEMBER"
    elif d < 217:
        d -= 185
        month = "OCTOBER"
    else:
        d -= 216
        month = "NOVEMBER"

    print(f"{month} {d} 1847")

    print_inventory()
    print()
    print("PRESIDENT JAMES K. POLK SENDS YOU HIS")
    print("      HEARTIEST CONGRATULATIONS")
    print()
    print("           AND WISHES YOU A PROSPEROUS LIFE AHEAD")
    print()
    print("                      AT YOUR NEW HOME")

def main():
    load_answer = to_upper_manual(input("Do you want to load your saved game? (Y/N) ").strip())
    if load_answer in ("Y", "YES"):
        loadFile("trail_save.dat")
        print("Save loaded.")
    else:
        print("Starting a new game...")

    resp = to_upper_manual(input("Would you like instructions? (Y/Yes or N/No) "))
    if resp in ("Y", "YES"):
        show_instructions()
    else:
        print("Ok, lets move on then")

    if status.turn == 0 and status.miles == 0:
        getInitialPurchase()

    while True:
        addTurn(1)
        announce_date()
        print_inventory()
        status.fortAvailable = not status.fortAvailable

        riders_roll_value = getRandom(0, 10)
        riders_threshold_value = max(0, distanceCurve(chanceEncounterRiders) - 1)
        encountered_riders = riders_roll_value < riders_threshold_value
        riders_are_hostile = False
        if encountered_riders:
            riders_are_hostile = (getRandom(1, 100) <= 80)
            print("Riders spotted - " + ("hostile!" if riders_are_hostile else "friendly."))

        event_index = getRandom(0, 15)
        print(events[event_index])
        apply_event_effects(event_index)
        if status.isDead:
            break

        if status.fortAvailable:
            choice.turn = ask_menu("DO YOU WANT TO (1) STOP AT THE FORT, (2) HUNT, (3) CONTINUE, (4) QUIT? ", {1, 2, 3, 4})
            if choice.turn == 1:
                visit_fort()
            if choice.turn == 2:
                hunt()
                print_inventory()
            if choice.turn == 4:
                print("Quitting the game...")
                saveFile()
                break
        else:
            choice.turn = ask_menu("DO YOU WANT TO (1) HUNT, (2) CONTINUE, (3) QUIT? ", {1, 2, 3})
            mapped = [1, 2, 3][choice.turn - 1]
            print(choiceTurnResponses[mapped])
            if choice.turn == 1:
                hunt()
                print_inventory()
            if choice.turn == 3:
                print("Quitting the game...")
                saveFile()
                break

        while True:
            if status.food < 13:
                print("YOU DON'T HAVE ENOUGH FOOD TO FEED YOUR PARTY.")
                print("YOU RAN OUT OF FOOD AND YOUR PARTY STARVED.")
                died()
                break

            choice.eat = ask_menu("DO YOU WANT TO EAT (1) POORLY, (2) MODERATELY, (3) WELL? ", {1, 2, 3})
            needed = 8 + 5 * choice.eat

            if status.food - needed < 0:
                print("YOU CAN'T EAT THAT WELL")
                continue

            addFood(-needed)
            print(choiceEatResponses[choice.eat - 1])
            break

        if status.isDead:
            break
            

        if choice.eat == 1:
            status.haveIllness = (random.random() < 0.40)
        elif choice.eat == 2:
            status.haveIllness = (random.random() < 0.25)
        elif choice.eat == 3:
            status.haveIllness = (random.random() < 0.10)
        if status.haveIllness:
            print("You have become ill.")
            _ = getSick()
            status.haveIllness = False

        recordMileage()

        addMiles(200 + (status.oxen - 220) // 5 + random.randint(0, 10))
        print(f"Current mileage: {status.miles} miles")

       
        reachMountains()

        if encountered_riders:
            choice.riders = ask_menu(
                "RIDERS AHEAD. (1) RUN, (2) ATTACK, (3) CONTINUE, (4) CIRCLE? ",
                {1, 2, 3, 4}
            )
            print(choiceRidersResponses[choice.riders - 1])
            process_riders_choice(riders_are_hostile, choice.riders)
            if status.isDead:
                break

        if isGameComplete():
            if status.isDead:
                print("Game over.")
            else:
                arrived()
            break

        saveFile()

if __name__ == "__main__":
    main()
