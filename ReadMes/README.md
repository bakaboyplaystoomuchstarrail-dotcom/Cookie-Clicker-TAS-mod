# Cookie-Clicker-Optimizer
My goal is simple. To destroy cookie clicker by finding the definitive fastest way to 100% the game. I've decided to tackle this process in steps. I figured that the first thing we should focus on is the fundamental game loop of cookie clicker, that being the actual generation of cookies. This will act as a framework to show us the fastest paths to being able to afford certain purchases and reach certain achievement milestones and ascension requirements. Programming the code necessary to achieve the non baking related achievements shouldn't be too difficult since that isn't where the complexity of the game lies, it's in the interconnectedness between the features and this issue is resolved by us establishing a good foundation. 

The program works by having us input a cookies baked end goal, upon which a BFS program will launch that utilises the game state logic to correctly calculate all possible options that we cannot guarantee are mathematically inefficient, this allows for our program to find the definitive best path as unlike a heuristic program it doesn't rule out possible options purely because they don't immediately seem optimal. 

By using a BFS or Breadth First Search program we further optimise the entire program as the pattern used to explore the possible branches of the simulation is methodical, we clear out our queue of game states that need exploring on each and every level before moving onto the next one meaning that the first solution we find is always guaranteed to be the shortest one we'll find and as such we can terminate the BFS without having to search further. 

Once the BFS program finds an optimal path I can verify whether it does in fact reach the end goal with the same amount of time passed and buildings owned as projected by the BFS by manually executing the actions the BFS data export contains using a TAS mod I've developed for the browser verison of Cookie Clicker. 

The BFS program runs on a milisecond to milisecond basis as it turns out that all 

Features:
- BFS search algorithm in 'main.py' that runs on a milisecond to milisecond basis
- Game state logic is accurately mimicked as the 20ms click throttling 
- Visualization capability using manim. 
- Auto-clean of Manim outputs: previous renders (including partial_movie_files) are deleted whenever a visualization is launched.

## Setup
- Python 3.9+ recommended.
- Install Manim Community Edition:
  ```bash path=null start=null
  pip install manim
  ```

This project’s scenes avoid LaTeX by using `Text`, so a TeX distribution isn’t required for the provided examples.

## Usage
- Optimizer + verification page:
  ```bash path=null start=null
  python main.py
  ```
  After solving, it opens `Automated Verification/auto_verification.html`.

- Visualizations (renders video to `media/`):
  ```bash path=null start=null
  manim -pqh pure_click_timeline.py PureClickTimeline100
  manim -pqh pure_click_timeline.py AllPathsTo20Cookies
  ```
  Flags: `-p` preview, `-q` quality (e.g., `h` high, `m` medium, `l` low).

## Auto-clean behavior (new)
To prevent files piling up, `pure_click_timeline.py` automatically deletes prior visualization outputs when Manim imports the module. The following directories (if present) under the project root are removed before each render:
- `media/` (videos, images, partial_movie_files, caches, Tex, raster images)
- `renders/`, `output/`, `outputs/`

If you need to keep old renders, comment out the `clean_visualization_outputs()` call at the top of `pure_click_timeline.py`.

## Notes
- The verification page shows simulated vs expected time, frames, and building counts.
- Manim output paths and quality can be customized via CLI flags or `manim.cfg` if you add one.
