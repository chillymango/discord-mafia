"""
We should be able to start a game from here or something like that
"""
from engine.game import Game


def main(game: Game = None) -> None:
    if game is None:
        # i don't know what the point of creating a game with zero players is but whatever
        game = Game()

    # if we have a game we should start doing role assignments according to config


if __name__ == "__main__":
    main()
