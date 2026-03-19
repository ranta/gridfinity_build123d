"""baseplate.

Module containing classes to create baseplates.
"""

from __future__ import annotations

from collections.abc import Iterable
from math import isclose
from typing import TYPE_CHECKING, Literal

from build123d import (
    Align,
    Axis,
    BasePartObject,
    Box,
    BuildPart,
    Edge,
    Locations,
    Mode,
    Part,
    RotationLike,
    Shape,
    add,
    fillet,
)

from gridfinity_build123d.baseplate_block import BasePlateBlock, BasePlateBlockFrame
from gridfinity_build123d.constants import gridfinity_standard
from gridfinity_build123d.utils import Direction, Utils

if TYPE_CHECKING:
    from gridfinity_build123d.features import Feature


def _normalize_features(features: Feature | list[Feature] | None) -> list[Feature]:
    """Normalize optional feature input into a concrete list."""
    if not features:
        return []

    return features if isinstance(features, Iterable) else [features]


def _round_baseplate_outer_edges(part: BuildPart) -> Part:
    """Apply fillet to outer edges of a baseplate.

    Args:
        part (BuildPart): The BuildPart containing the baseplate to fillet.
    """
    if not part.part:  # pragma: no cover
        msg = "Part is empty"
        raise RuntimeError(msg)

    z_height = part.part.bounding_box().size.Z

    def edge_filter(shape: Shape[Edge]) -> bool:
        inner_edge = shape.edge()
        if not inner_edge:  # pragma: no cover
            m = "Edge is empty"
            raise RuntimeError(m)

        return isclose(inner_edge.length, z_height)

    wires = part.edges().filter_by(Axis.Z).filter_by(edge_filter)

    return fillet(wires, gridfinity_standard.grid.radius)


def _create_equal_grid(size_x: int, size_y: int) -> list[list[bool]]:
    """Create a grid of specified size with all values set to True."""
    return [[True] * size_x for _ in range(size_y)]


class BasePlate(BasePartObject):
    """Baseplate object constructed from grid definition."""

    def __init__(
        self,
        grid: list[list[bool]],
        baseplate_block: BasePlateBlock | None = None,
        features: Feature | list[Feature] | None = None,
        rotation: RotationLike = (0, 0, 0),
        align: Align | tuple[Align, Align, Align] | None = None,
        mode: Mode = Mode.ADD,
    ):
        """ConstructBasePlate.

        Create a baseplate according to grid pattern.

        Args:
            grid (list[list[bool]]): Pattern for creating baseplate.
            baseplate_block (BasePlateBlock | None, optional): Type of BasePlateBlock to construct a
                complete baseplate. Defaults to None.
            rotation (RotationLike): angles to rotate about axes. Defaults to (0, 0, 0).
            features (Feature | list[Feature]): Features applied to the basePlate. Defaults to None.
            align (Union[Align, tuple[Align, Align, Align]], optional): align min, center, or max
                of object. Defaults to (0, 0, 0).
            mode (Mode): combination mode. Defaults to Mode.ADD.
        """
        if baseplate_block is None:
            baseplate_block = BasePlateBlockFrame()

        self.features: list[Feature] = _normalize_features(features)

        with BuildPart() as part:
            _ = Utils.place_by_grid(baseplate_block.create_obj(mode=Mode.PRIVATE), grid)

            _ = _round_baseplate_outer_edges(part)

            for feature in self.features:
                feature.apply(part)

        super().__init__(part.part, rotation, align, mode)


class BasePlateEqual(BasePlate):
    """Rectangular BasePlate."""

    def __init__(
        self,
        size_x: int = 1,
        size_y: int = 1,
        baseplate_block: BasePlateBlock | None = None,
        features: Feature | list[Feature] | None = None,
        rotation: RotationLike = (0, 0, 0),
        align: Align | tuple[Align, Align, Align] | None = None,
        mode: Mode = Mode.ADD,
    ):
        """Construct rectangular BasePlate.

        Create a baseplate according to grid pattern.

        Args:
            size_x (int, optional): x size of baseplate. Defaults to 1.
            size_y (int, optional): y size of baseplate. Defaults to 1.
            baseplate_block (BasePlateBlock | None, optional): Type of BasePlateBlock to construct a
                complete baseplate.
            features (Feature | list[Feature]): Features applied to the basePlate. Defaults to None.
            rotation (RotationLike): angles to rotate about axes. Defaults to (0, 0, 0).
            align (Union[Align, tuple[Align, Align, Align]], optional): align min, center, or max
                of object. Defaults to None.
            mode (Mode): combination mode. Defaults to Mode.ADD.
        """
        if baseplate_block is None:
            baseplate_block = BasePlateBlockFrame()

        grid = _create_equal_grid(size_x, size_y)
        super().__init__(grid, baseplate_block, features, rotation, align, mode)


class BasePlateSized(BasePartObject):
    """BasePlate constructed from direct millimeter dimensions.

    Create a baseplate with direct millimeter dimensions. Any space not occupied
    by full gridfinity grid cells is filled with solid material.

    Grid alignment can be controlled independently in X and Y to anchor the grid
    to left/right and front/back when dimensions are not exact grid multiples.
    """

    def __init__(
        self,
        width: float,
        depth: float,
        baseplate_block: BasePlateBlock | None = None,
        features: Feature | list[Feature] | None = None,
        grid_align_x: Literal[Direction.LEFT, Direction.RIGHT] | None = None,
        grid_align_y: Literal[Direction.FRONT, Direction.BACK] | None = None,
        rotation: RotationLike = (0, 0, 0),
        align: Align | tuple[Align, Align, Align] | None = None,
        mode: Mode = Mode.ADD,
    ):
        """Construct BasePlateSized.

        Args:
            width (float): Total width of the baseplate in mm (x-direction).
            depth (float): Total depth of the baseplate in mm (y-direction).
            baseplate_block (BasePlateBlock | None, optional): Type of BasePlateBlock to use.
                Defaults to BasePlateBlockFrame.
            features (Feature | list[Feature] | None, optional): Features applied to the
                baseplate. Defaults to None.
            grid_align_x (Literal[Direction.LEFT, Direction.RIGHT] | None, optional):
                Horizontal alignment of the grid area within the base width.
                Use Direction.LEFT or Direction.RIGHT; None centers the grid.
            grid_align_y (Literal[Direction.FRONT, Direction.BACK] | None, optional):
                Depth alignment of the grid area within the base depth.
                Use Direction.FRONT or Direction.BACK; None centers the grid.
            rotation (RotationLike): Angles to rotate about axes. Defaults to (0, 0, 0).
            align (Union[Align, tuple[Align, Align, Align]], optional): Alignment of the
                object. Defaults to None.
            mode (Mode): Combination mode. Defaults to Mode.ADD.

        Raises:
            ValueError: If width or depth is smaller than one gridfinity grid cell (42 mm).
        """
        if baseplate_block is None:
            baseplate_block = BasePlateBlockFrame()

        self.features: list[Feature] = _normalize_features(features)

        baseplate_grid = self._create_baseplate_grid(width, depth, baseplate_block)
        grid_bbox = baseplate_grid.bounding_box()

        with BuildPart() as part:
            # Create a large base
            _ = Box(width, depth, grid_bbox.size.Z)

            offset_multiplier = self._get_offset_location_multiplier(grid_align_x, grid_align_y)
            offset_x = (width - grid_bbox.size.X) / 2 * offset_multiplier[0]
            offset_y = (depth - grid_bbox.size.Y) / 2 * offset_multiplier[1]
            with Locations((offset_x, offset_y, 0)):
                # Cut a hole in the base for the grid and fill it with the grid.
                _ = Box(
                    grid_bbox.size.X,
                    grid_bbox.size.Y,
                    grid_bbox.size.Z,
                    mode=Mode.SUBTRACT,
                )
                _ = add(baseplate_grid, mode=Mode.ADD)

            _ = _round_baseplate_outer_edges(part)

            for feature in self.features:
                feature.apply(part)

        if not part.part:  # pragma: no cover
            msg = "Part is empty"
            raise RuntimeError(msg)

        super().__init__(part.part, rotation, align, mode)

    def _create_baseplate_grid(
        self, width: float, depth: float, baseplate_block: BasePlateBlock
    ) -> Part:
        grid_size_x = int(width // gridfinity_standard.grid.size)
        grid_size_y = int(depth // gridfinity_standard.grid.size)
        if grid_size_x < 1 or grid_size_y < 1:
            msg = (
                f"width ({width} mm) and depth ({depth} mm) must each be at least "
                f"{gridfinity_standard.grid.size} mm to fit one gridfinity grid cell."
            )
            raise ValueError(msg)

        grid = _create_equal_grid(grid_size_x, grid_size_y)
        return Utils.place_by_grid(baseplate_block.create_obj(mode=Mode.PRIVATE), grid)

    def _get_offset_location_multiplier(
        self,
        grid_align_x: Literal[Direction.LEFT, Direction.RIGHT] | None = None,
        grid_align_y: Literal[Direction.FRONT, Direction.BACK] | None = None,
    ) -> tuple[int, int]:
        """Calculate multipliers for offsetting the grid placement based on alignment settings."""
        if grid_align_x is None:
            x_multiplier = 0
        elif grid_align_x in (Direction.LEFT, Direction.RIGHT):
            x_multiplier = Direction.to_tuple(grid_align_x)[0]
        else:
            msg = "grid_align_x must be Direction.LEFT, Direction.RIGHT, or None"
            raise ValueError(msg)

        if grid_align_y is None:
            y_multiplier = 0
        elif grid_align_y in (Direction.FRONT, Direction.BACK):
            y_multiplier = Direction.to_tuple(grid_align_y)[1]
        else:
            msg = "grid_align_y must be Direction.FRONT, Direction.BACK, or None"
            raise ValueError(msg)

        return x_multiplier, y_multiplier
