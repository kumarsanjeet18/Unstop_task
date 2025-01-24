from flask import Flask, request, jsonify, render_template
import random
from itertools import combinations

app = Flask(__name__)

# Define hotel structure
HOTEL_STRUCTURE = {
    floor: [f"{floor}0{room}" if room < 10 else f"{floor}{room}" for room in range(1, 11)]
    for floor in range(1, 10)
}
HOTEL_STRUCTURE[10] = [f"100{room}" for room in range(1, 8)]


# Initial room statuses
rooms_status = {
    room: "available"
    for floor, rooms in HOTEL_STRUCTURE.items()
    for room in rooms
}

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint to get the room statuses
@app.route('/rooms', methods=['GET'])
def get_rooms():
    return jsonify(rooms_status)

# Endpoint to reset room statuses
@app.route('/reset', methods=['POST'])
def reset_rooms():
    global rooms_status
    rooms_status = {
        room: "available"
        for floor, rooms in HOTEL_STRUCTURE.items()
        for room in rooms
    }
    return jsonify({"message": "Room statuses reset successfully."})

# Endpoint to generate random occupancy
@app.route('/generate', methods=['POST'])
def generate_random_occupancy():
    global rooms_status
    for room in rooms_status.keys():
        rooms_status[room] = "occupied" if random.choice([True, False]) else "available"
    return jsonify({"message": "Random occupancy generated."})

# Helper function to calculate travel time
def calculate_travel_time(rooms):
    floors = {int(room[:-2]) for room in rooms}
    if len(floors) == 1:
        # Same floor: horizontal travel time
        horizontal_distance = max(int(room[-2:]) for room in rooms) - min(int(room[-2:]) for room in rooms)
        return horizontal_distance
    else:
        # Different floors: vertical and horizontal travel time
        vertical_distance = (max(floors) - min(floors)) * 2
        horizontal_distance = len(rooms)  # One minute per adjacent room
        return vertical_distance + horizontal_distance

# Helper function to generate combinations of rooms
def combinations_of_rooms(available_rooms, num_rooms):
    return list(combinations(available_rooms, num_rooms))

# Endpoint to book rooms
@app.route('/book', methods=['POST'])
def book_rooms():
    global rooms_status
    try:
        data = request.json
        num_rooms = data.get('num_rooms', 0)

        if num_rooms < 1 or num_rooms > 5:
            return jsonify({"error": "You can book between 1 and 5 rooms only."}), 400

        available_rooms = [room for room, status in rooms_status.items() if status == "available"]
        if len(available_rooms) < num_rooms:
            return jsonify({"error": "Not enough rooms available."}), 400

        # Group available rooms by floor
        floor_rooms = {}
        for room in available_rooms:
            floor = int(room[:-2])
            floor_rooms.setdefault(floor, []).append(room)

        selected_rooms = []
        # Try to book rooms on the same floor first
        for floor, rooms in floor_rooms.items():
            if len(rooms) >= num_rooms:
                selected_rooms = rooms[:num_rooms]
                break

        # If not enough rooms on the same floor, select across floors minimizing travel time
        if not selected_rooms:
            all_combinations = []
            for floor, rooms in floor_rooms.items():
                # Check all combinations of rooms across floors
                combinations = combinations_of_rooms(available_rooms, num_rooms)
                for combination in combinations:
                    travel_time = calculate_travel_time(combination)
                    all_combinations.append((combination, travel_time))

            # Select the combination with the minimum travel time
            selected_rooms, travel_time = min(all_combinations, key=lambda x: x[1])

        # Update room statuses
        for room in selected_rooms:
            rooms_status[room] = "booked"

        return jsonify({
            "booked_rooms": selected_rooms,
            "total_travel_time": travel_time
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
