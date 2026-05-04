# ARW-25 Puzzle Game

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![PyGame](https://img.shields.io/badge/PyGame-2.x-green.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand%20Tracking-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

A hand-tracking puzzle game for La Salle Computer Society's Annual Recruitment Week 2025. Players use camera-based hand gestures or mouse to drag and drop symbols into the correct order within 60 seconds.

## Game Description

**Given**: A random reference key containing an ordered sequence of items (gears and rubies).

**Goal**: Using hand gestures (pinch to grab) or mouse, drag and drop the items into the correct slots at the bottom of the screen to match the reference key order.

**Controls**:
- Make an **OK hand sign** (pinch thumb and index) for accurate hand tracking
- Use **index finger + thumb pinch** to grab items
- Press **M** to toggle between camera and mouse mode
- Press **D** to toggle debug mode (shows hand skeleton)
- Press **R** to restart the game
- Press **ESC** to quit

## Technology Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.12** | Programming language |
| **PyGame** | Game rendering and UI |
| **OpenCV** | Camera capture and image processing |
| **MediaPipe** | Hand tracking and gesture detection |
| **NumPy** | Numerical operations |
| **PyInstaller** | Standalone executable build |

## Project Structure

```
arw-25-puzzle-game/
├── main.py                    # Main entry point, game loop, input handling
├── requirements.txt           # Python dependencies
├── config/
│   ├── config.py              # Display settings, colors, game constants
│   └── camera.py              # HandTracker class (MediaPipe integration)
├── game/
│   └── logic.py               # GameLogic class (game mechanics, state)
├── assets/                    # Game item images (gears, rubies)
├── dist/                      # Built executables
└── *.spec                     # PyInstaller configuration files
```

## Getting Started

### Prerequisites

- Python 3.12+
- Webcam (for hand tracking mode)
- Assets folder with game item images

### Installation

1. Clone the repository:
```bash
git clone https://github.com/dlsu-lscs/arw-25-puzzle-game
cd arw-25-puzzle-game
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Game

```bash
python main.py
```

### Building an Executable

```bash
pyinstaller main.spec
```

## Game Mechanics

### Hand Tracking
- Uses MediaPipe Hands to detect hand landmarks
- Pinch detection: thumb (landmark 4) and index fingertip (landmark 8)
- Normalized pinch threshold: 0.18 (adjusted by hand bounding box size)
- Supports mouse fallback when camera is unavailable

### Drag and Drop
- **Grab**: Click mouse OR pinch thumb+index together
- **Drag**: Move hand/cursor while holding
- **Drop**: Release mouse OR unpinch
  - If near a slot (within 70px): object snaps to slot center
  - Otherwise: object returns to random position in spawn area

### Slots
- 5 slots arranged horizontally at y=500
- Visual feedback: green border = filled, gray border = empty
- Objects snap to slot center when placed

### Win/Lose Conditions
- **Win**: All 5 slots contain the correct symbol in the correct order
- **Lose**: 60-second timer expires before winning

## Configuration

| Setting | Value | Location |
|---------|-------|----------|
| Display Resolution | 1280x720 | config.py |
| Target FPS | 60 | config.py |
| Game Timer | 60 seconds | config.py, logic.py |
| Object Collision Radius | 40px | logic.py |
| Slot Snap Radius | 70px | logic.py |
| Spawn Area | (100, 100, 400, 300) | logic.py |
| Slot Positions | x=300,400,500,600,700 at y=500 | logic.py |
| Pinch Threshold | 0.18 (normalized) | camera.py |
| Max Hands | 1 | camera.py |
| Detection Confidence | 0.6 | camera.py |
| Tracking Confidence | 0.5 | camera.py |

## Asset Requirements

Place images in the `assets/` folder with these naming conventions:
- Files containing `ruby` → treated as ruby items
- Files containing `gear`, `nut`, `bolt`, or `steel` → treated as gear items
- Supported formats: `.png`, `.webp`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│  (Game Loop, Input Handling, Asset Loading, Display)         │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
┌──────────────────┐               ┌──────────────────────────┐
│   config/        │               │        game/             │
│  ├─ config.py   │               │  └─ logic.py             │
│  └─ camera.py   │               │     (GameLogic)          │
│  (HandTracker)   │               │  - Object management     │
└──────────────────┘               │  - Slot collision        │
                                   │  - Win condition         │
                                   └──────────────────────────┘
```

### Data Flow
1. OpenCV captures webcam frame at 1280x720
2. Frame is flipped horizontally for mirror effect
3. HandTracker processes frame via MediaPipe
4. GameLogic handles object positions and collision detection
5. Frame is rendered with game elements overlaid
6. Converted to PyGame surface for display at 60 FPS

## License

MIT License - Copyright (c) 2025 La Salle Computer Society

See [LICENSE](LICENSE) for full details.