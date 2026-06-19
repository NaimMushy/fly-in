*This project has been created as part of the 42 curriculum by ibady.*


# ==== FLY-IN ====

## Table of contents

  1. [Description](#description)
  2. [Instructions](#instructions)
  3. [Resources](#resources)
  4. [Algorithm](#algorithm)
  5. [Visual Representation](#visual-representation)<br><br>



### Description


  ____
  
  **General description**:

  This project has for goal to execute a simulation of drone routing through a specific map with zones and connections between them.<br>
  To do so, a pathfinding algorithm is used to find the best route possible for each of the drones.<br>
  In addition, there are certain constraints to mind when directing the drones.<br>
  Movement between zones has a specific cost depending on the zones' type, and the capacity of the zones varies.<br>
  During a turn, a drone can either move to another zone, pass through a connection or wait.<br>
  The simulation stops when all the drones have reached the end zone, all the while trying to achieve a minimal number of turns.<br><br>
  A visualization of the simulation is provided via the Arcade Python library, offering user interaction through commands, as well as a terminal menu.<br>
  



### Instructions


  ____

  **1. Execution:**

  + Makefile rules:<br><br>
  ``make`` -> installs dependencies and runs the program<br>
  ``make run`` -> runs the program<br>
  ``make install`` -> installs dependencies<br>
  ``make clean`` -> removes the __pycache__ files<br>
  ``make lint`` -> checks for mypy and flake8 errors<br>
  ``make lint-strict`` -> checks for mypy --strict and flake8 errors<br>
  ``make debug`` -> runs the program with a debugger<br><br>
  If you wish to specifiy a map file from the start, define the MAP variable as so:<br>
  ``make run MAP="<file_path>"``<br><br>
  + Direct execution:<br><br>
  You can also simply run the program with the following:<br>
  ``poetry run python3 fly_in.py <file_path>``<br>
  with file_path being the optional path to the file containing the map data.

  **2. Input File Example:**

  ```
  nb_drones: 2

  start_hub: start 0 0 [color=green]
  hub: waypoint1 1 0 [color=blue]
  hub: waypoint2 2 0 [color=blue]
  end_hub: goal 3 0 [color=red]

  connection: start-waypoint1
  connection: waypoint1-waypoint2
  connection: waypoint2-goal
  ```

  **3. Output Example:**

  ```
  D1-waypoint2 D2-waypoint1
  ```

  **4. Simulation Options:**

  + Start Menu:<br>

    When the program is run, a start menu is presented, with multiple options:<br>
      - select new map -> change the drone map used for the simulation<br>
      - launch the drones -> start the simulation using the map selected<br>
      - toggle graphic mode -> turn on and off the graphic mode, which provides a visual representation via the arcade library (on by default)<br>
      - display map paths -> show a list of all available paths for the drone maps included in the subject (for tests)<br>
      - quit the program -> exit<br><br>
    
    If the map given to parse is invalid or cannot be opened, the appropriate error message is displayed and the user has to change maps to be able to run the simulation.<br>
    Otherwise, the simulation should run without an issue.<br><br>


### Resources


  ____

  **Links:**

   Arcade display:<br><br>
    - [Arcade documentation for basic methods](https://api.arcade.academy/en/stable/example_code/index.html)<br>
    - [Arcade documentation for function definition and parameters](https://api.arcade.academy/en/2.6.1/arcade.html)<br>
    - [Blinking dots animation](https://stackoverflow.com/questions/58212749/triple-dots-animation-while-program-is-loading-in-terminal)<br><br>

  Algorithm:<br><br>
    - [Geeksforgeeks Python documentation on heapq](https://www.geeksforgeeks.org/python/heap-queue-or-heapq-in-python/)<br>
    - [Geeksforgeeks Dijkstra explanation](https://www.geeksforgeeks.org/dsa/dijkstras-shortest-path-algorithm-greedy-algo-7/)<br>
    - [Wikipedia page for Dijkstra algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)<br>
    - [Wikipedia page for Yen's K algorithm](https://en.wikipedia.org/wiki/Yen%27s_algorithm)<br><br>

  **AI Usage:**
  
  I asked ChatGPT for some help mainly for debugging, especially for the terminal display that I ended up not using.<br>


  ### Algorithm


  ____

  **Pathfinding Algorithm:**

  I used a combination of Dijkstra algorithm and Yen's K shortest path algorithm.<br>
  The Dijkstra algorithm searches for the lowest cost path it can find (just like a BFS but with a priority queue implemented), while the Yen's K algorithm repeats the Dijkstra until K best paths are obtained or no more paths are found.<br><br>
  The Dijkstra algorithm starts from a given zone, with a priority queue containing only that zone.<br>
  Then, it iteratively takes the path with the lowest cost in the stack and the zone associated with it and explores all neighboring zones of the current zone, adding them to the stack with the corresponding path (if they were not already in the stack with a lower path cost).<br>
  When the destination is found or there are no more zones in the stack (no path available), the algorithm returns the best path it found.<br>
  I used heapq instead of lists because it ensures my paths are stored and retrieved by cost instead of arrival.<br><br>
  For Yen's K shortest path algorithm, the main idea is to build a list of the best paths found so far, and a set of potential paths.<br>
  Initially, the best paths contain only the absolute shortest path.<br>
  For each iteration (from 1 to K), I examine each path and generate new potential paths by deviating from the current path at each node except the destination.<br>
  The deviation is done by establishing a root path (the current path until the current node) and computing the shortest path from that node to the destination while temporarily removing zones that would cause a loop or duplicate a previously found path.<br><br>
  Using the two in tandem allows me to find at most the 5 (default) best alternatives for each drone, so that they can follow the proper path, but without having to calculate **every** path that exists (that makes the program too slow).<br><br>
  

  **Drone Routing:**

  Instead of assigning a specific path to every drone at the beginning of the simulation and then letting them move following their path,
  I reevaluate which paths are available starting from the drone's current position and then determine the best one to follow.<br>
  In most cases, the first path that a drone follows does not change throughout the simulation, but I preferred to be rigorous and eliminate potential losses of efficiency.<br><br>



### Visual Representation


  ____

  **Terminal Display:**

At first I wanted to try and make a visual representation in the terminal. I made something that worked pretty well and I was happy with the way it looked.<br>
Unfortunately this kind of display is too easily broken by a miscalculation or an unexpected edge case (as I discovered in my first retry of the project).<br>
That's why I switched to the Arcade library and made a simple and uncomplicated display that wouldn't crash because of a small bug. Although I kept the terminal menu I used in the old version for user interaction and choice.<br>
The Arcade library for Python is relatively easy to understand and use, and I have to admit I didn't go very far to see if I could do a more elaborate display as this project has been going on for a while now and I would like to pass it.<br>
I used very basic methods such as draw_line, draw_text and draw_rect, and I added some user commands to make it more interesting.<br>
The simulation runs by default on auto, and the user can imcrease or decrease the speed, go step by step, pause and exit.<br>
On the right side I also display the drone movements during the current turn.<br>
To make it a little prettier I added a drone image instead of a simple dot, and I changed the font for a pixel-style font (free license).<br>
The graphic mode can be disabled or enabled in the main menu, so that the user can choose to have only the terminal logs.<br><br>
