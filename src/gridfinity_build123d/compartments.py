"""Module containing compartment cutters and placement classes."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from build123d import (
    Align,
    Axis,
    BasePartObject,
    Box,
    BuildPart,
    Locations,
    Mode,
    RotationLike,
    fillet,
)

from .constants import gf_bin

if TYPE_CHECKING:
    from .features import CompartmentFeature


class Compartment:
    """Compartment object used as cutter for bins."""

    def __init__(
        self,
        features: CompartmentFeature | list[CompartmentFeature] | None = None,
    ):
        """Create Compartment.

        Args:
            features (CompartmentFeature | list[CompartmentFeature] | None, optional):
                CompartmentFeature or list of CompartmentFeatures. Defaults to None.
        """
        if not features:
            features = []

        self.features: list[CompartmentFeature] = (
            features if isinstance(features, Iterable) else [features]
        )

    def create(
        self,
        size_x: float,
        size_y: float,
        height: float,
        rotation: RotationLike = (0, 0, 0),
        align: Align | tuple[Align, Align, Align] | None = None,
        mode: Mode = Mode.ADD,
    ) -> BasePartObject:
        """Create Compartment object.

        Args:
            size_x (float): Size x.
            size_y (float): Size y.
            height (float): height of compartment.
            rotation (RotationLike, optional): angles to rotate about axes. Defaults to (0, 0, 0).
            align (Union[Align, tuple[Align, Align, Align]], optional): align min, center, or max
                of object. Defaults to None.
            mode (Mode, optional): combination mode. Defaults to Mode.ADD.

        Returns:
            BasePartObject: 3d object.
        """
        with BuildPart() as part:
            _ = Box(
                size_x,
                size_y,
                height,
            )

            for feature in self.features:
                feature.apply(part)

            if not part.part:  # pragma: no cover
                msg = "Part is empty"
                raise RuntimeError(msg)

            bbox = part.part.bounding_box()

            # Select only vertical edges
            fillet_edges = (
                part.edges()
                .filter_by(Axis.Z)
                .filter_by_position(
                    axis=Axis.Z,
                    minimum=bbox.min.Z,
                    maximum=bbox.max.Z - gf_bin.label.thickness,
                    inclusive=(True, False),
                )
            )

            # Round the inner vertical edges (top-down 2D corners)
            _ = fillet(fillet_edges, gf_bin.inner_radius_v)

            # Select the rest of the edges (excluding the top face and lower edge of the label)
            # (Bottom edges and underside of the label)
            fillet_edges = part.edges().filter_by_position(
                axis=Axis.Z,
                minimum=bbox.min.Z,
                maximum=bbox.max.Z - gf_bin.label.thickness,
                inclusive=(True, False),
            )

            _ = fillet(fillet_edges, gf_bin.inner_radius)

        return BasePartObject(part.part, rotation, align, mode)


class Compartments:
    """Compartments collection.

    Creates compartments according to type_list and arranges them according to the grid.

    Example:
        grid = [
            [1,1,2,3,3],
            [1,1,2,4,4]
        ]
        compartment_list = [
            Compartment(),
            Compartment(features=[Scoop()]),
            Compartment(features=[Label()]),
            Compartment(),
        ]
        Will generate 4 compartments.
        One compartment is a square and takes 4 slots. The second
        compartment is a rectangle with a Scoop using two slots in the y-axis direction.The third
        compartment is a rectangle with a Label using 2 slots in the x-axis direction. The fourth
        compartment is a rectangle in the x-axis direction.
        The size of the compartments and exact location is calculated on basis of the total size
        of the grid arrangement
    """

    def __init__(
        self,
        grid: list[list[int]] | None = None,
        compartment_list: Compartment | list[Compartment] | None = None,
        inner_wall: float = 1.2,
        outer_wall: float = 0.95,
    ):
        """Construct grid collection.

        Args:
            grid ( list[list[int]] | None, optional): Configuration for arrangement of compartments.
                Defaults to [[1]].
            compartment_list (Compartment | list[Compartment] | None): Compartment or list of
                compartments. Defaults to None.
            inner_wall (float): Space between arranged compartments. Defaults to 1.2.
            outer_wall (float): Offset outside generated arrangement. Defaults to 0.95.
        """
        if grid is None:
            grid = [[1]]
        if compartment_list is None:
            compartment_list = Compartment()

        self.inner_wall: float = inner_wall
        self.outer_wall: float = outer_wall
        self.grid: list[list[int]] = grid
        self.compartment_list: Compartment | list[Compartment] = compartment_list

    def create(
        self,
        size_x: float,
        size_y: float,
        height: float,
        rotation: RotationLike = (0, 0, 0),
        align: Align | tuple[Align, Align, Align] = Align.CENTER,
        mode: Mode = Mode.ADD,
    ) -> BasePartObject:
        """Create compartments object.

        Args:
            size_x (float): size on the x-axis
            size_y (float): size on the y-axis
            height (float): Height of compartments
            rotation (RotationLike, optional): angles to rotate about axes. Defaults to (0, 0, 0).
            align (Union[Align, tuple[Align, Align, Align]], optional): align min, center, or max
                of object. Defaults to Align.CENTER.
            mode (Mode, optional): combination mode. Defaults to Mode.ADD.

        Returns:
            BasePartObject: 3d object
        """
        distribute_area_x = size_x - self.outer_wall * 2 + self.inner_wall
        distribute_area_y = size_y - self.outer_wall * 2 + self.inner_wall

        size_unit_x = distribute_area_x / len(self.grid[0])
        size_unit_y = distribute_area_y / len(self.grid)

        with BuildPart() as part:
            numbers_processed: list[int] = []
            for r_index, row in enumerate(self.grid):
                for c_index, item in enumerate(row):
                    if item != 0 and item not in numbers_processed:
                        numbers_processed.append(item)

                        units_x = self._count_same_row(c_index, row)
                        units_y = self._count_same_column((r_index, c_index), self.grid)

                        middle_x = (c_index + c_index + units_x) / 2
                        middle_y = (r_index + r_index + units_y) / 2

                        loc_x = self._map_range(
                            middle_x,
                            0,
                            len(self.grid[0]),
                            0,
                            distribute_area_x,
                        )
                        loc_y = (
                            self._map_range(
                                middle_y,
                                0,
                                len(self.grid),
                                0,
                                distribute_area_y,
                            )
                            * -1
                        )

                        with Locations((loc_x, loc_y)):
                            if isinstance(self.compartment_list, Iterable):
                                create_call = self.compartment_list[item - 1].create
                            else:
                                create_call = self.compartment_list.create

                            _ = create_call(
                                size_x=size_unit_x * units_x - self.inner_wall,
                                size_y=size_unit_y * units_y - self.inner_wall,
                                height=height,
                            )

        if not part.part:  # pragma: no cover
            msg = "Part is empty"
            raise RuntimeError(msg)

        return BasePartObject(part=part.part, rotation=rotation, align=align, mode=mode)

    @staticmethod
    def _map_range(
        x: float,
        in_min: float,
        in_max: float,
        out_min: float,
        out_max: float,
    ) -> float:
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    @staticmethod
    def _count_same_row(r_index: int, row: list[int]) -> int:
        number = row[r_index]
        count = 0
        for item in row[r_index:]:
            if number == item:
                count += 1
            else:
                return count

        return count

    @staticmethod
    def _count_same_column(index: tuple[int, int], grid: list[list[int]]) -> int:
        number = grid[index[0]][index[1]]
        count = 0
        for row in grid[index[0] :]:
            if row[index[1]] == number:
                count += 1
            else:
                return count
        return count


class CompartmentsSized:
    """Compartments collection with explicitly sized compartments.

    Unlike Compartments and CompartmentsEqual, which stretch compartments to fill the full
    available area, CompartmentsSized places each compartment at its exact requested size.
    Compartments are arranged side by side along the x-axis and centered as a group, both
    horizontally and vertically, within the available area. Any space left over once every
    compartment is placed is not cut away, it stays solid.

    Example:
        sizes = [(30, 120), (30, 120), (30, 120), (30, 120)]
        Will generate 4 identical 30x120mm compartments, arranged side by side and centered.
    """

    def __init__(
        self,
        sizes: list[tuple[float, float]],
        compartment_list: Compartment | list[Compartment] | None = None,
        inner_wall: float = 1.2,
        outer_wall: float = 0.95,
    ):
        """Construct sized compartment collection.

        Args:
            sizes (list[tuple[float, float]]): size_x, size_y of each compartment, in
                left-to-right placement order.
            compartment_list (Compartment | list[Compartment] | None, optional): Compartment
                or list of compartments, one per entry in sizes when a list is given.
                Defaults to Compartment().
            inner_wall (float, optional): space between compartments. Defaults to 1.2.
            outer_wall (float, optional): minimum required space between the compartments
                and the edge of the available area. Defaults to 0.95.
        """
        if not sizes:
            msg = "sizes can't be empty"
            raise ValueError(msg)
        if compartment_list is None:
            compartment_list = Compartment()

        self.sizes: list[tuple[float, float]] = sizes
        self.compartment_list: Compartment | list[Compartment] = compartment_list
        self.inner_wall: float = inner_wall
        self.outer_wall: float = outer_wall

    def create(
        self,
        size_x: float,
        size_y: float,
        height: float,
        rotation: RotationLike = (0, 0, 0),
        align: Align | tuple[Align, Align, Align] = Align.CENTER,
        mode: Mode = Mode.ADD,
    ) -> BasePartObject:
        """Create sized compartments object.

        Args:
            size_x (float): size of the available area on the x-axis
            size_y (float): size of the available area on the y-axis
            height (float): Height of compartments
            rotation (RotationLike, optional): angles to rotate about axes. Defaults to (0, 0, 0).
            align (Union[Align, tuple[Align, Align, Align]], optional): align min, center, or max
                of object. Defaults to Align.CENTER.
            mode (Mode, optional): combination mode. Defaults to Mode.ADD.

        Returns:
            BasePartObject: 3d object
        """
        total_width = sum(size[0] for size in self.sizes) + self.inner_wall * (len(self.sizes) - 1)

        if total_width + self.outer_wall * 2 > size_x:
            msg = (
                f"compartments require {total_width}mm of width, plus {self.outer_wall}mm "
                f"outer wall on each side, but only {size_x}mm is available"
            )
            raise ValueError(msg)

        for _, comp_size_y in self.sizes:
            if comp_size_y + self.outer_wall * 2 > size_y:
                msg = (
                    f"compartment of size_y={comp_size_y}mm plus {self.outer_wall}mm outer "
                    f"wall on each side doesn't fit within the available {size_y}mm"
                )
                raise ValueError(msg)

        with BuildPart() as part:
            loc_x = -total_width / 2
            for index, (comp_size_x, comp_size_y) in enumerate(self.sizes):
                loc_x += comp_size_x / 2

                if isinstance(self.compartment_list, Iterable):
                    create_call = self.compartment_list[index].create
                else:
                    create_call = self.compartment_list.create

                with Locations((loc_x, 0)):
                    _ = create_call(size_x=comp_size_x, size_y=comp_size_y, height=height)

                loc_x += comp_size_x / 2 + self.inner_wall

        if not part.part:  # pragma: no cover
            msg = "Part is empty"
            raise RuntimeError(msg)

        return BasePartObject(part=part.part, rotation=rotation, align=align, mode=mode)


class CompartmentsEqual(Compartments):
    """Equal spaced compartment collection."""

    def __init__(
        self,
        compartment_list: Compartment | list[Compartment] | None = None,
        div_x: int = 1,
        div_y: int = 1,
        inner_wall: float = 1.2,
        outer_wall: float = 0.95,
    ) -> None:
        """Generate equal spaced compartment collection.

        Args:
            div_x (int): number of compartments in x direction. Defaults to 1.
            div_y (int): number of compartments in y direction. Defaults to 1.
            compartment_list (Compartment | list[Compartment] | None, optional): Compartment or list
                of compartments. Defaults to Compartment().
            inner_wall (float, optional): wall thickness between compartments. Defaults to 1.2.
            outer_wall (float, optional): wall thickness around compartments. Defaults to 0.95.
        """
        if compartment_list is None:
            compartment_list = Compartment()
        grid: list[list[int]] = []
        bin_nr = 1
        for _ in range(div_y):
            row: list[int] = []
            for _ in range(div_x):
                row.append(bin_nr)
                bin_nr += 1
            grid.append(row)
        super().__init__(
            grid=grid,
            compartment_list=compartment_list,
            inner_wall=inner_wall,
            outer_wall=outer_wall,
        )
