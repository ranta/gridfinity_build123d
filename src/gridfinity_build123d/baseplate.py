"""baseplate.

Module containing classes to create baseplates.
"""

from __future__ import annotations

from collections.abc import Iterable
from math import isclose
from typing import TYPE_CHECKING

from build123d import (
    Align,
    Axis,
    BasePartObject,
    BuildPart,
    Edge,
    Mode,
    Part,
    RotationLike,
    Shape,
    fillet,
)

from gridfinity_build123d.baseplate_block import BasePlateBlockFrame
from gridfinity_build123d.constants import gridfinity_standard
from gridfinity_build123d.utils import Utils

if TYPE_CHECKING:
    from gridfinity_build123d.baseplate_block import BasePlateBlock
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
