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
  A visualization of the simulation step by step is provided with a terminal display, offering user interaction through small menus and commands.<br>
  



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
  If you wish to specifiy a map file from the start, define the ARGS as so:<br>
  ``make run ARGS="<file_path>"``<br><br>
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
  [map display]

  ==== DRONE MOVEMENTS ====

   -> D1-waypoint2 D2-waypoint1
  ```

  **4. Simulation Options:**

  + Start Menu:<br>

    When the program is run, a start menu is presented, with multiple options:<br>
      - select new map -> change the drone map used for the simulation<br>
      - launch the drones -> start the simulation using the map selected<br>
      - toggle info mode -> turn on and off the information mode, which provides additional information throughout the simulation<br>
      - display map paths -> show a list of all available paths for the drone maps included in the subject (for tests)<br>
      - quit the program -> exit<br><br>
    
    If the map given to parse is invalid or cannot be opened, the appropriate error message is displayed and the user has to change maps to be able to run the simulation.<br>
    Otherwise, the simulation should run without an issue.<br><br>

  + Step by step Menu:<br>

    When the simulation starts, the beginnning state of the drone map is displayed, followed by an option menu:<br>
      - next step -> move forward to the next step in the simulation<br>
      - previous step -> go back to the previous step in the simulation<br>
      - return to the main menu -> stop the simulation and go back to the start menu<br><br>
  
    If the current state of the simulation is the last one, meaning all the drones have been delivered, going to the next step of the simulation will end the simulation and return to the start menu.<br>


### Resources


  ____

  **Links:**

  Terminal display:<br><br>
    - [Rich colors documentation](https://rich.readthedocs.io/en/stable/appendix/colors.html)<br>
    - [Rich text documentation](https://rich.readthedocs.io/en/stable/text.html)<br>
    - [Blinking dots animation](https://stackoverflow.com/questions/58212749/triple-dots-animation-while-program-is-loading-in-terminal)<br><br>

  Algorithm:<br><br>
    - [Geeksforgeeks Python documentation on heapq](https://www.geeksforgeeks.org/python/heap-queue-or-heapq-in-python/)<br>
    - [Geeksforgeeks Dijkstra explanation](https://www.geeksforgeeks.org/dsa/dijkstras-shortest-path-algorithm-greedy-algo-7/)<br>
    - [Wikipedia page for Dijkstra algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)<br>
    - [Wikipedia page for Yen's K algorithm](https://en.wikipedia.org/wiki/Yen%27s_algorithm)<br><br>

  **AI Usage:**
  
  I asked ChatGPT for some help regarding some issues with the terminal display as well as for debugging.<br>


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

  **Display Connections:**

  I also used an A* pathfinding algorithm for the display of the connections between zones.<br>
  At first, I struggled to form lines that seemed okay, then I decided to calculate a path of coordinates using a simple and efficient algorithm I was familiar with.<br>
  The result is pretty acceptable, becoming a bit jumbled when there are too many connections as they can overlap each other, but I didn't find a better way to do it in the terminal interface.<br><br>


### Visual Representation


  ____

  **Terminal Display:**

  I decided to try to achieve a correct visual representation using the terminal interface.<br>
  It proved to be quite a challenge, as I could not simply write a character at a certain position in the terminal.<br>
  What I did was construct each vertical line of the terminal with the appropriate characters, store them in a grid and then print them one by one.<br>
  I used the rich library for python to add more color options (if you wish to see all the colors available, go see the Resources section).<br><br>
  To avoid having to calculate again if the same map is launched more than once, I defined State objects that contain all the information relevant to a certain simulation and each of its steps.<br>
  That way, I can simply display the required states for the simulation if they have already been created.<br><br>
  What's more, with the information mode enabled, the type of the zone is displayed on the top border, and additional information regarding the drones and zones is printed at the end of a turn.<br><br>
