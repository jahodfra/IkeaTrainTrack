# IkeaTrainTrack
Solver for closed tracks for IKEA Lillabo. This program constructs all enclosed tracks with the prescribed set of segments.

![Original set](http://www.ikea.com/us/en/images/products/lillabo-piece-basic-train-set-assorted-colors__65510_PE176881_S4.JPG)

## Example image:
![Schematic track](docs/example.png?raw=true)

## Installation
```bash
sudo pip3 install Cython
python3 setup.py build_ext --inplace
```

## Usage
To print all enclosed tracks:
```bash
python3 solver.py --turns=12 --straight=4 --ups=2 --downs=2 --pillars=4 >tracks
cat tracks
```

To display all enclosed tracks:
```bash
python3 tohtml.py <tracks
```
Then open ./report/index.html in a browser.

To filter out tracks which can be constructed simply by extending existing tracks:
```bash
python3 simplify.py <tracks
```

To display one track:
```bash
python3 track.py RRRRRRRR
```

## Limitations
The program takes into account only pieces in basic set (Left and right turn, Straight segment and Up and Down segment). Since then Ikea introduced lot more pieces e.g. crossroads, short turns, short straight segments, depos and so on which are not represented in the program.

In real world the pieces do not strictly fit together and it is possible to use mechanical tolerance to create tracks which are not found by the search.

The collision detection is simplified and doesn't take into account width of the track.

The search is basically [Breadth first search](https://en.wikipedia.org/wiki/Breadth-first_search) with heuristic to prune paths, which cannot be enclosed. The running time complexity and and memory complexity is exponential (estimated) in the number of pieces. Also the number of solutions grows exponentially (estimated) even if we use simplify.py on the output.

## Possible improvements
1. Due to memory complexity it would be reasonable to search only with half of the number of pieces and then to combine found states to find enclosed paths. Still it means that I would able to search tracks with around 3 sets.
2. I can try to generate random path and use [Hill Climbing](https://en.wikipedia.org/wiki/Hill_climbing) to find enclosed path. That would allow much more pieces.
3. I can try to create an editor which would allow human guided creation and sharing of the tracks.
