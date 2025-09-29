"""Simple labyrinth mini-game built with pygame.

This module is intentionally lightweight: the maze is generated using a fixed
layout so that the game starts instantly.  The :func:`run_labyrinth_game`
function is imported by :mod:`main` and can be wired to a button in the UI.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import List, Tuple

try:
    import pygame
except Exception as exc:  # pragma: no cover - pygame might not be installed
    pygame = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

CELL_SIZE = 48
GRID = [
    "####################",
    "#S   #         #   #",
    "### ### #### # # # #",
    "#     #    # # # # #",
    "# ### #### # # # # #",
    "# #   #    #   #   #",
    "# # ### ####### ###E",
    "# #   #       #   ##",
    "# ### # ##### ###  #",
    "#     #     #     ##",
    "####################",
]
ROWS = len(GRID)
COLS = len(GRID[0])
WINDOW_SIZE = (COLS * CELL_SIZE, ROWS * CELL_SIZE)
BG_COLOR = (30, 30, 40)
WALL_COLOR = (70, 130, 180)
PLAYER_COLOR = (255, 214, 10)
EXIT_COLOR = (120, 230, 130)


@dataclass
class Player:
    position: Tuple[int, int]

    def move(self, dx: int, dy: int) -> None:
        x, y = self.position
        self.position = (x + dx, y + dy)


def _assert_pygame_available() -> None:
    if pygame is None:  # pragma: no cover - environment specific
        raise RuntimeError(
            "pygame is required to launch the labyrinth mini-game."
        ) from _IMPORT_ERROR


def _find_positions() -> Tuple[Tuple[int, int], Tuple[int, int]]:
    start = exit_pos = (1, 1)
    for row_idx, row in enumerate(GRID):
        for col_idx, cell in enumerate(row):
            if cell == "S":
                start = (col_idx, row_idx)
            elif cell == "E":
                exit_pos = (col_idx, row_idx)
    return start, exit_pos


def _is_wall(col: int, row: int) -> bool:
    if 0 <= row < ROWS and 0 <= col < COLS:
        return GRID[row][col] == "#"
    return True


def _draw_grid(screen: "pygame.Surface") -> None:
    for row_idx, row in enumerate(GRID):
        for col_idx, cell in enumerate(row):
            rect = pygame.Rect(col_idx * CELL_SIZE, row_idx * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if cell == "#":
                pygame.draw.rect(screen, WALL_COLOR, rect)
            elif cell == "E":
                pygame.draw.rect(screen, EXIT_COLOR, rect)
            else:
                pygame.draw.rect(screen, BG_COLOR, rect)


def run_labyrinth_game() -> None:
    """Launch the labyrinth mini-game.

    The function returns when the player either reaches the exit or closes the
    window.  In classrooms without pygame installed a helpful error is raised.
    """

    _assert_pygame_available()
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Labyrinth Escape")
    clock = pygame.time.Clock()

    start_pos, exit_pos = _find_positions()
    player = Player(position=start_pos)

    font = pygame.font.SysFont("Arial", 24)
    running = True
    won = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_UP, pygame.K_w):
                    _attempt_move(player, 0, -1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    _attempt_move(player, 0, 1)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    _attempt_move(player, -1, 0)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    _attempt_move(player, 1, 0)

        if player.position == exit_pos:
            won = True
            running = False

        screen.fill(BG_COLOR)
        _draw_grid(screen)
        _draw_player(screen, player)
        pygame.display.flip()
        clock.tick(30)

    _show_outcome(screen, font, won)
    pygame.time.delay(1500)
    pygame.quit()


def _attempt_move(player: Player, dx: int, dy: int) -> None:
    x, y = player.position
    new_x, new_y = x + dx, y + dy
    if not _is_wall(new_x, new_y):
        player.move(dx, dy)


def _draw_player(screen: "pygame.Surface", player: Player) -> None:
    x, y = player.position
    rect = pygame.Rect(x * CELL_SIZE + 10, y * CELL_SIZE + 10, CELL_SIZE - 20, CELL_SIZE - 20)
    pygame.draw.rect(screen, PLAYER_COLOR, rect, border_radius=8)


def _show_outcome(screen: "pygame.Surface", font: "pygame.font.Font", won: bool) -> None:
    if screen is None:
        return
    screen.fill(BG_COLOR)
    message = "You escaped!" if won else "Maybe next time!"
    text = font.render(message, True, (255, 255, 255))
    text_rect = text.get_rect(center=(WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2))
    screen.blit(text, text_rect)
    pygame.display.flip()


if __name__ == "__main__":  # pragma: no cover - manual play helper
    try:
        run_labyrinth_game()
    except RuntimeError as exc:  # pragma: no cover
        sys.stderr.write(f"Failed to run labyrinth game: {exc}\n")
