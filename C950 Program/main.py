# Bryan Huynh - Student ID: 011920597

import csv
import datetime


# ------------------------------
#       Hash Map
# ------------------------------

class HashMap:
    def __init__(self):
        self.size = 40
        self.map = [None] * self.size

    def _get_hash(self, key):
        hash = 0
        for char in str(key):
            hash += ord(char)
        return hash % self.size

    def add(self, key, value):
        key_hash = self._get_hash(key)
        key_value = [key, value]

        if self.map[key_hash] is None:
            self.map[key_hash] = list([key_value])
            return True
        else:
            for pair in self.map[key_hash]:
                if pair[0] == key:
                    pair[1] = value
                    return True
            self.map[key_hash].append(key_value)
            return True

    def get(self, key):
        key_hash = self._get_hash(key)
        if self.map[key_hash] is not None:
            for pair in self.map[key_hash]:
                if pair[0] == key:
                    return pair[1]
        return None

    def get_all(self):
        # Returns all stored values
        items = []
        for bucket in self.map:
            if bucket:
                for pair in bucket:
                    items.append(pair[1])
        return items

    def delete(self, key):
        key_hash = self._get_hash(key)

        if self.map[key_hash] is None:
            return False
        for i in range (0, len(self.map[key_hash])):
            if self.map[key_hash][i][0] == key:
                self.map[key_hash].pop(i)
                return True

    def print(self):
        print('---PACKAGES----')
        for item in self.map:
            if item is not None:
                print(str(item))


# ------------------------------
#       Package Class
# ------------------------------

class Package:
    def __init__(self, package_id, address, city, state, zip_code, deadline, weight):
        self.package_id = int(package_id)
        self.address = address
        self.corrected_address = None
        self.corrected_city = None
        self.corrected_state = None
        self.corrected_zip = None
        self.address_corrected_time = None
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.deadline = deadline
        self.weight = weight

        self.status = "Arriving to depot (ETA: 9:05 AM)."
        self.status = "At hub"
        self.departure_time = None
        self.delivery_time = None
        self.truck_id = None

    def status_at_time(self, query_time):
        if self.delivery_time and query_time >= self.delivery_time:
            return f"Delivered at {self.delivery_time} (Truck {self.truck_id})"
        elif self.departure_time and query_time >= self.departure_time:
            return f"En route (Truck {self.truck_id})"
        elif self.package_id in DELAYED_PACKAGES and query_time < datetime.timedelta(hours=9, minutes=6):
            return "Arriving to depot (ETA 9:05 AM)."
        else:
            return "At hub"

    def __str__(self):
        return (f"Package {self.package_id} | {self.address} | "
                f"Deadline: {self.deadline} | Status: {self.status}")

# ------------------------------
#       Truck Class
# ------------------------------

class Truck:
    SPEED_MPH = 18

    # This will be used to track trucks' mileage at any given time
    def mileage_at_time(self, query_time):
        if self.start_driving_time is None or query_time <= self.start_driving_time:
            return 0.0

        elapsed_time = query_time - self.start_driving_time
        elapsed_hours = elapsed_time.total_seconds() / 3600
        miles_driven = elapsed_hours * self.SPEED_MPH

        return min(miles_driven, self.miles)

    def __init__(self, truck_id, departure_time):
        self.truck_id = truck_id
        self.departure_time = departure_time
        self.start_driving_time = None
        self.packages = []
        self.miles = 0.0
        self.current_location = 0
        self.time = datetime.timedelta(hours=8)

    def load_package(self, package):
        if len(self.packages) >= 16:
            raise ValueError(f"Truck {self.truck_id} cannot carry more than 16 packages")
        self.packages.append(package)

    def deliver_package(self, package, distance, destination):
        self.miles += distance
        self.time += datetime.timedelta(hours=distance / 18)
        package.status = "Delivered"
        package.delivery_time = self.time
        self.current_location = get_address_index(destination)

    def return_to_hub(self):
        hub_index = 0
        distance = get_distance(self.current_location, hub_index)
        self.miles += distance
        self.time += datetime.timedelta(hours=distance / 18)
        self.current_location = hub_index

# ------------------------------
#       CSV File Loaders
# ------------------------------

def load_package(filename, hash_table):
    # Loads package data into the hash table
    with open(filename, newline ='') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            package = Package(
                int(row[0]),
                normalize_address(row[1]),
                row[2],
                row[3],
                row[4],
                row[5],
                row[6]
            )
            hash_table.add(package.package_id, package)

def load_addresses(filename):
    #Loads address list to return addresses as array
    addresses = []
    address_lookup = {}

    with open(filename, newline='') as file:
        reader = csv.reader(file)
        for index, row in enumerate(reader):
            address = normalize_address(row[2])
            addresses.append(address)
            address_lookup[address] = index
    return addresses, address_lookup

def load_distances(filename):
    distance = []
    with open(filename, newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            distance.append(row)
    return distance

# ------------------------------
#       Distance Utilities
# ------------------------------

def normalize_address(address):
    return address.replace(" South", " S") \
                  .replace(" North", " N") \
                  .replace(" East", " E") \
                  .replace(" West", " W") \
                  .replace(".", "") \
                  .strip()

def get_address_index(address):
    # Returns the index of an address from the lookup table
    try:
        return ADDRESS_LOOKUP[address.strip()]
    except KeyError:
        raise ValueError(f"Address not found in distance table: {address}")

def get_distance(i, j):
    # Both directions need to be checked

    distance = DISTANCE_TABLE[max(i, j)][min(i, j)]
    return float(distance) if distance else float(DISTANCE_TABLE[min(i, j)][max(i, j)])

# ------------------------------
#   Nearest Neighbor Algorithm
# ------------------------------
def deliver_truck(truck):

    if any(p.package_id in DELAYED_PACKAGES for p in truck.packages):
        truck.time = max(truck.time, DELAYED_TIME)

    truck.start_driving_time = truck.time

    for package in truck.packages:
        package.departure_time = truck.time

    while truck.packages:

        # Split packages by deadline
        early_deadline = [p for p in truck.packages if p.deadline != "EOD"]
        eod_packages = [p for p in truck.packages if p.deadline == "EOD"]

        # Always prioritize early deadlines first
        candidate_list = early_deadline if early_deadline else eod_packages

        nearest_distance = float("inf")
        nearest_package = None
        nearest_address = None

        for package in candidate_list:

            destination = package.address

            if package.corrected_address and truck.time >= package.address_corrected_time:
                destination = package.corrected_address

            address_index = get_address_index(destination)
            distance = get_distance(truck.current_location, address_index)

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_package = package
                nearest_address = destination

        # Drive to the nearest selected package
        truck.miles += nearest_distance
        truck.time += datetime.timedelta(hours=nearest_distance / Truck.SPEED_MPH)
        truck.current_location = get_address_index(nearest_address)

        delivered = []

        # Deliver ALL packages at that address
        for package in truck.packages:

            destination = package.address
            if package.corrected_address and truck.time >= package.address_corrected_time:
                destination = package.corrected_address

            if destination == nearest_address:
                package.status = "Delivered"
                package.delivery_time = truck.time
                delivered.append(package)

        for package in delivered:
            truck.packages.remove(package)

def parse_time(time_str):
    try:
        hours, minutes = map(int, time_str.split(":"))
        if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
            raise ValueError(f"Invalid time format: {time_str}")
        return datetime.timedelta(hours=hours, minutes=minutes)
    except ValueError:
        return None

def get_full_address(package, query_time=None):
    if query_time and package.corrected_address and query_time >= package.address_corrected_time:
        return f"{package.corrected_address}, {package.corrected_city}, {package.corrected_state}, {package.corrected_zip}"
    return f"{package.address}, {package.city}, {package.state}, {package.zip_code}"

def lookup_package_by_id(package_table, package_id, query_time=None):
    package = package_table.get(package_id)

    if not package:
        print(f"Package ID {package_id} not found.")
        return
    if query_time:
        status = package.status_at_time(query_time)
    else:
        status = package.status
        if package.delivery_time:
            status += f" at {package.delivery_time}"

    print(f"\n----------- PACKAGE {package_id} INFORMATION -----------")
    print(f"{"Package ID":<20}{package.package_id}")
    address = package.address
    city = package.city
    state = package.state
    zip_code = package.zip_code

    if query_time and package.corrected_address and query_time >= package.address_corrected_time:
        address = package.corrected_address
        city = package.corrected_city
        state = package.corrected_state
        zip_code = package.corrected_zip

    print(f"{'Address':<20}{address}")
    print(f"{'City':<20}{city}")
    print(f"{'State':<20}{state}")
    print(f"{'Zip Code':<20}{zip_code}")
    print(f"{"Deadline":<20}{package.deadline}")
    print(f"{"Weight":<20}{package.weight}")
    print(f"{"Truck ID":<20}{package.truck_id}")
    print(f"{"Delivery Status":<20}{status}")

# ------------------------------
#      Main Program Flow
# ------------------------------

# Manually setting packages with specific constraints
TRUCK_2_ONLY = {3, 18, 36, 38}
DELAYED_PACKAGES = {6, 25, 28, 32}
early_deadline_packages = {1, 6, 13, 14, 15, 16, 20, 25, 29, 30, 31, 34, 40}
DELAYED_TIME = datetime.timedelta(hours=9, minutes=6)

if __name__ == "__main__":
    package_table = HashMap()
    load_package("WGUPSPackages.csv", package_table)
    ADDRESS_LIST, ADDRESS_LOOKUP = load_addresses("WGUPSAddresses.csv")
    DISTANCE_TABLE = load_distances("WGUPSDistances.csv")
    all_packages = package_table.get_all()

    # Initialize trucks
    truck1 = Truck(1, datetime.timedelta(hours=8, minutes=0))
    truck2 = Truck(2, datetime.timedelta(hours=8, minutes=0))
    truck3 = Truck(3, None)

    # Explicit truck assignments
    # early deadline + specific delivery grouped packages
    truck1_ids = {13, 14, 15, 16, 19, 20, 1, 4, 5, 7, 8, 10, 11, 12, 30}
    # TRUCK_2_ONLY + delayed + early deadline
    truck2_ids = {2, 3, 6, 18, 25, 29, 30, 31, 36, 38}
    # delayed
    truck3_ids = {9, 26, 27, 28, 32, 33, 35}

    assigned_ids = truck1_ids | truck2_ids | truck3_ids

    for package in all_packages:
        pid = package.package_id

        if pid in truck1_ids:
            package.truck_id = 1
            truck1.load_package(package)

        elif pid in truck2_ids:
            package.truck_id = 2
            truck2.load_package(package)

        elif pid in truck3_ids:
            package.truck_id = 3
            truck3.load_package(package)

    for package in package_table.get_all():
        if package.package_id not in assigned_ids:
            # Load remaining packages on Truck 1 if space allows
            if len(truck1.packages) < 16:
                truck1.load_package(package)
                package.truck_id = 1
            elif len(truck2.packages) < 16:
                truck2.load_package(package)
                package.truck_id = 2
            else:
                truck3.load_package(package)
                package.truck_id = 3

    # Package 9 cannot be loaded before address correction at 10:20
    package_9 = package_table.get(9)
    package_9.corrected_address = normalize_address("410 S State St")
    package_9.corrected_city = "Salt Lake City"
    package_9.corrected_state = "UT"
    package_9.corrected_zip = "84111"
    package_9.address_corrected_time = datetime.timedelta(hours=10, minutes=20)

    if any(p.package_id in DELAYED_PACKAGES for p in truck1.packages):
        truck1.time = DELAYED_TIME

    deliver_truck(truck1)
    truck1.return_to_hub()

    deliver_truck(truck2)
    truck2.return_to_hub()

    truck3.time = min(truck1.time, truck2.time)
    deliver_truck(truck3)
    truck3.return_to_hub()

    # Used to see which truck returns to hub first for driver to take truck 3 for remaining packages
    print(f"\nTruck 1 finished at {truck1.time}, miles: {truck1.miles:.2f}")
    print(f"Truck 2 finished at {truck2.time}, miles: {truck2.miles:.2f}")
    print(f"Truck 3 started at {truck3.time}")

# Used for debugging to quickly identify any packages that have not met delivery deadlines
def validate_deadlines(package_table):
    print("\nDeadline Validation")
    print("-" * 40)
    missed = False
    for package in package_table.get_all():
        if package.deadline == "EOD":
            continue
        deadline_td = parse_deadline(package.deadline)
        if package.delivery_time and package.delivery_time > deadline_td:
            print(
                f"Package {package.package_id} missed deadline: "
                f"Delivered at {package.delivery_time}, Deadline {package.deadline}"
            )
            missed = True
    if not missed:
        print("All packages met their deadlines.")

def parse_deadline(deadline_str):
    import datetime
    dt = datetime.datetime.strptime(deadline_str, "%I:%M %p")
    return datetime.timedelta(hours=dt.hour, minutes=dt.minute)

validate_deadlines(package_table)

def user_interface(package_table, truck1, truck2, truck3):
    # Interactive UI by using integrated CLI
    while True:
        print("\nWGUPS Package Tracking System")
        print("1. View package status at a specific time")
        print("2. View total mileage")
        print("3  View package info by ID")
        print("4. Exit\n")

        choice = input("Enter choice: ")

        if choice == "1":
            time_input = input("Enter time (24h format: HH:MM): ")
            query_time = parse_time(time_input)

            if query_time is None:
                print("Invalid time format. Please enter time as HH:MM")
                continue

            print(f"\nPackage Statuses at {query_time}:")
            print("-" * 140)
            print(f"{'ID':<5}{'Weight':<8}{'Delivery Address':<70}{'Status':<45}{'Deadline':<10}")
            print("-" * 140)

            for package in sorted(package_table.get_all(), key=lambda p: p.package_id):
                status = package.status_at_time(query_time)

                address = package.address
                city = package.city
                state = package.state
                zip_code = package.zip_code

                if (
                    package.package_id == 9
                    and package.corrected_address
                    and query_time >= package.address_corrected_time
                ):
                    address = package.corrected_address
                    city = package.corrected_city
                    state = package.corrected_state
                    zip_code = package.corrected_zip

                full_address = f"{address}, {city}, {state} {zip_code}"

                print(
                    f"{package.package_id:<5}"
                    f"{package.weight:<8}"
                    f"{full_address:<70}"
                    f"{status:<45}"
                    f"{package.deadline:<10}"
                )

            print(f"\nTruck mileage at {query_time}")
            print("-" * 30)
            print(f"{'Truck 1 mileage:':<15} {truck1.mileage_at_time(query_time):>8.2f} miles")
            print(f"{'Truck 2 mileage:':<15} {truck2.mileage_at_time(query_time):>8.2f} miles")
            print(f"{'Truck 3 mileage:':<15} {truck3.mileage_at_time(query_time):>8.2f} miles")
            print(f"{"Total mileage:":<16} {truck1.mileage_at_time(query_time) + truck2.mileage_at_time(query_time) + truck3.mileage_at_time(query_time):>8.2f} miles")

        elif choice == "2":
            total_miles = truck1.miles + truck2.miles + truck3.miles
            print("\nMileage Summary")
            print("-" * 30)
            print(f"{'Truck 1:':<15} {truck1.miles:>8.2f} miles")
            print(f"{'Truck 2:':<15} {truck2.miles:>8.2f} miles")
            print(f"{'Truck 3:':<15} {truck3.miles:>8.2f} miles")
            print("-" * 30)
            print(f"{'Total':<15} {total_miles:>8.2f} miles\n")

        elif choice == "3":
            pid = int(input("Enter package ID: "))
            time_input = input("Enter time (24h format: HH:MM): ")
            if time_input:
                query_time = parse_time(time_input)
                if query_time is None:
                    print("Invalid time format. Please enter time as HH:MM.")
                    continue
                lookup_package_by_id(package_table, pid, query_time)
            else:
                lookup_package_by_id(package_table, pid)

        elif choice == "4":
            print("Closing program.")
            break

        else:
            print("Invalid input. Please try again.")

    # Final output after exiting program
    total_miles = truck1.miles + truck2.miles + truck3.miles
    print("\nMileage Summary")
    print("-" * 30)
    print(f"{'Truck 1:':<15} {truck1.miles:>8.2f} miles")
    print(f"{'Truck 2:':<15} {truck2.miles:>8.2f} miles")
    print(f"{'Truck 3:':<15} {truck3.miles:>8.2f} miles")
    print("-" * 30)
    print(f"{'Total':<15} {total_miles:>8.2f} miles\n")

    print("\nPackage Summary")
    print(f"{'ID':<5}{'Weight':<8}{'Delivery Address':<70}{'Delivery Time':<30}{'Deadline':<10}")
    print("-" * 123)

    for package in sorted(package_table.get_all(), key=lambda p: p.package_id):

        address = package.address
        city = package.city
        state = package.state
        zip_code = package.zip_code

        # Updates package 9 with corrected address
        if (
            package.corrected_address
            and package.delivery_time
            and package.delivery_time >= package.address_corrected_time
        ):
            address = package.corrected_address
            city = package.corrected_city
            state = package.corrected_state
            zip_code = package.corrected_zip

        full_address = f"{address}, {city}, {state} {zip_code}"

        if package.delivery_time:
            delivery_time_str = f"{package.delivery_time} (Truck {package.truck_id})"
        else:
            delivery_time_str = "Not delivered"

        print(
            f"{package.package_id:<5}"
            f"{package.weight:<8}"
            f"{full_address:<70}"
            f"{delivery_time_str:<30}"
            f"{package.deadline:<10}"
        )

user_interface(package_table, truck1, truck2, truck3)
