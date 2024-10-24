import random
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
from skimage import io

from fireball_detection.tiling.included import (SQUARE_SIZE,
                                         retrieve_included_coordinates)
from object_detection.dataset import GFO_JPEGS, GFO_PICKINGS, GFO_THUMB_EXT


MIN_BB_DIM_SIZE = 20
MIN_POINTS_IN_TILE = 3

included_coordinates = retrieve_included_coordinates()


@dataclass
class FireballTile:
    position: pd.DataFrame
    points: list[float] = None
    bb_centre: tuple[float] = tuple()
    bb_dim: tuple[int] = tuple()
    image: np.ndarray = None


class SplitTilesFireball:

    fireball_name: str
    fireball_tiles: list[FireballTile]
    negative_tiles: list[FireballTile]

    def __init__(self, fireball_name: str) -> None:
        self.fireball_name = fireball_name

        self.fireball_tiles = []
        self.negative_tiles = []

        fireball_image = io.imread(Path(GFO_JPEGS, fireball_name + GFO_THUMB_EXT))
        points = pd.read_csv(Path(GFO_PICKINGS, self.fireball_name + ".csv"))
        # Check if tile contains points
        for tile_pos in included_coordinates:
            points_in_tile = []

            for point in points.itertuples(False, None):
                if (
                    tile_pos[0] <= point[0] and point[0] < tile_pos[0] + SQUARE_SIZE and \
                    tile_pos[1] <= point[1] and point[1] < tile_pos[1] + SQUARE_SIZE
                ):
                    points_in_tile.append(point)
            
            if len(points_in_tile) == 0:
                self.negative_tiles.append(FireballTile(tile_pos))
            elif len(points_in_tile) >= MIN_POINTS_IN_TILE:
                self.fireball_tiles.append(
                    FireballTile(
                        tile_pos,
                        pd.DataFrame(points_in_tile, columns=["x", "y"])
                    )
                )
        
        # Create bounding boxes for each tile
        for tile in self.fireball_tiles:
            pp_min_x = tile.points['x'].min()
            pp_max_x = tile.points['x'].max()
            pp_min_y = tile.points['y'].min()
            pp_max_y = tile.points['y'].max()

            points_dim = (pp_max_x - pp_min_x, pp_max_y - pp_min_y)
            padding = 0.05

            bb_min_x = max(pp_min_x - (points_dim[0] * padding), tile.position[0])
            bb_max_x = min(pp_max_x + (points_dim[0] * padding), tile.position[0] + SQUARE_SIZE)

            bb_min_y = max(pp_min_y - (points_dim[1] * padding), tile.position[1])
            bb_max_y = min(pp_max_y + (points_dim[1] * padding), tile.position[1] + SQUARE_SIZE)

            bb_centre_x = (bb_min_x + bb_max_x) / 2
            bb_centre_y = (bb_min_y + bb_max_y) / 2

            bb_width = max(bb_max_x - bb_min_x, MIN_BB_DIM_SIZE)
            bb_height = max(bb_max_y - bb_min_y, MIN_BB_DIM_SIZE)

            norm_bb_centre_x = min((bb_centre_x - tile.position[0]) / SQUARE_SIZE, 1.0)
            norm_bb_centre_y = min((bb_centre_y - tile.position[1]) / SQUARE_SIZE, 1.0)

            norm_bb_width = min(bb_width / SQUARE_SIZE, 1.0)
            norm_bb_height = min(bb_height / SQUARE_SIZE, 1.0)

            tile.bb_centre = (norm_bb_centre_x, norm_bb_centre_y)
            tile.bb_dim = (norm_bb_width, norm_bb_height)

            tile.image = fireball_image[tile.position[1] : tile.position[1] + SQUARE_SIZE, tile.position[0] : tile.position[0] + SQUARE_SIZE]
        
        # Assign images to negative tiles
        if len(self.fireball_tiles) * 10 > len(self.negative_tiles):
            print("fireball_tiles * 10 > negative_tiles", fireball_name)
            sample_size = len(self.negative_tiles)
        else:
            sample_size = len(self.fireball_tiles) * 10
        self.negative_tiles = random.sample(self.negative_tiles, sample_size)
        for tile in self.negative_tiles:
            tile.image = fireball_image[tile.position[1] : tile.position[1] + SQUARE_SIZE, tile.position[0] : tile.position[0] + SQUARE_SIZE]


    def save_images(self, folder: str) -> None:
        for i, tile in enumerate(self.fireball_tiles):
            io.imsave(
                Path(folder, f"{self.fireball_name}_{i}.jpg"),
                tile.image,
                check_contrast=False
            )
        for i, tile in enumerate(self.negative_tiles):
            io.imsave(
                Path(folder, f"{self.fireball_name}_negative_{i}.jpg"),
                tile.image,
                check_contrast=False
            )


    def save_labels(self, folder: str) -> None:
        for i, tile in enumerate(self.fireball_tiles):
            label = (0, tile.bb_centre[0], tile.bb_centre[1], tile.bb_dim[0], tile.bb_dim[1])
            with open(Path(folder, f"{self.fireball_name}_{i}.txt"), 'x') as label_file:
                label_file.write(" ".join(str(item) for item in label))
        for i in range(len(self.negative_tiles)):
            open(Path(folder, f"{self.fireball_name}_negative_{i}.txt"), 'x').close()


def main():
    fireball = SplitTilesFireball("03_2020-07-20_041559_K_DSC_9695")
    for i, tile in enumerate(fireball.fireball_tiles):
        plot_fireball_tile(fireball.fireball_name, i, tile)


def plot_fireball_tile(fireball_name: str, i: int, tile: FireballTile):
    # Unpack tile attributes
    image = tile.image
    points = np.array(tile.points)
    position = tile.position
    bb_centre = tile.bb_centre
    bb_dim = tile.bb_dim

    # Adjust points to be relative to the tile's position
    relative_points = points - position

    # Calculate bounding box corners (xyxy format)
    bb_min_x = (bb_centre[0] - (bb_dim[0] / 2)) * SQUARE_SIZE
    bb_min_y = (bb_centre[1] - (bb_dim[1] / 2)) * SQUARE_SIZE

    bb_width = bb_dim[0] * SQUARE_SIZE
    bb_height = bb_dim[1] * SQUARE_SIZE

    # Create a plot
    _, ax = plt.subplots(1)
    ax.imshow(image)

    # Plot the points on the image
    if relative_points.any():
        ax.scatter(relative_points[:, 0], relative_points[:, 1], c='red', label='Points', s=12)

    # Add a rectangle for the bounding box
    rect = patches.Rectangle((bb_min_x, bb_min_y), bb_width, bb_height, linewidth=5, edgecolor='red', facecolor='none')
    ax.add_patch(rect)

    # Add a legend and show the plot
    ax.set_title(f"{fireball_name}_{i}.jpg")
    ax.axis('off')
    plt.show()


if __name__ == "__main__":
    main()