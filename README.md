
# Platformer-Python-Game

Platformer-Python-Game is a 2D platformer game built using Python and Pygame. The player can jump, collect fruits, avoid fire traps, and reach checkpoints to complete levels.

## Features

- **Player Character**: A customizable character that can move left, right, and jump.
- **Fruits**: Various fruits that can be collected to increase the score.
- **Fire Traps**: Fire obstacles that can harm the player.
- **Checkpoints**: Checkpoints that the player can activate to complete levels.
- **Scrolling Background**: A scrolling background to create a seamless gaming experience.

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/Adridiior/Platformer-Python-Game.git
   cd Platformer-Python-Game
   ```

2. Install the required dependencies:
   ```sh
   pip install pygame
   ```

3. Run the game:
   ```sh
   python main.py
   ```

## Usage

- **Move Left**: Press the left arrow key.
- **Move Right**: Press the right arrow key.
- **Jump**: Press the space bar (double jump is supported).

## Game Mechanics

- **Gravity**: The player is affected by gravity, which pulls them down.
- **Health**: The player starts with a health of 5. Colliding with fire traps reduces health.
- **Score**: The player can collect fruits to increase their score.
- **Checkpoints**: Activating checkpoints allows the player to complete the level.

## File Structure

- **main.py**: The main game file.
- **assets/**: Directory containing all game assets (sprites, images, etc.).
- **Player Class**: Handles player movement, jumping, and interactions.
- **Object Classes**: Includes `Block`, `Fire`, `Fruit`, and `Checkpoint` classes for different game objects.

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Credits

- Developed by Adriano Di Iorio
- Built with [Pygame](https://www.pygame.org/)
