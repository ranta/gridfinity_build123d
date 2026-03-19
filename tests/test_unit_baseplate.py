from unittest.mock import ANY, MagicMock, patch

from build123d import BuildPart

from gridfinity_build123d.baseplate import (
    BasePlate,
    BasePlateEqual,
    BasePlateSized,
)
from gridfinity_build123d.baseplate_block import (
    BasePlateBlock,
    BasePlateBlockFrame,
    BasePlateBlockFull,
)
from gridfinity_build123d.features import Feature
from gridfinity_build123d.utils import Direction
from tests import mocks, testutils


@patch("gridfinity_build123d.baseplate.Utils.place_by_grid", autospec=True)
class BasePlateTest(testutils.UtilTestCase):
    def test_base_plate(self, place_mock: MagicMock) -> None:
        place_box = mocks.BoxAsMock(10, 10, 10)
        place_mock.side_effect = place_box.create

        grid = MagicMock()
        with BuildPart() as part:
            BasePlate(grid)

        place_mock.assert_called_once_with(ANY, grid)

        bbox = part.part.bounding_box()
        self.assertVectorAlmostEqual((10, 10, 10), bbox.size)
        self.assertAlmostEqual(862.6548245743672, part.part.volume)

    def test_base_plate_bpblock(self, place_mock: MagicMock) -> None:
        place_box = mocks.BoxAsMock(10, 10, 10)
        place_mock.side_effect = place_box.create

        baseplate_block = MagicMock(spec=BasePlateBlock)
        bp_block_box = mocks.BoxAsMock(1, 1, 1)
        baseplate_block.create_obj.side_effect = bp_block_box.create

        grid = MagicMock()
        with BuildPart() as part:
            BasePlate(grid, baseplate_block)

        baseplate_block.create_obj.assert_called_once()
        place_mock.assert_called_once_with(bp_block_box.created_objects[0], grid)

        bbox = part.part.bounding_box()
        self.assertVectorAlmostEqual((10, 10, 10), bbox.size)
        self.assertAlmostEqual(862.6548245743672, part.part.volume)

    def test_base_plate_features(self, place_mock: MagicMock) -> None:
        place_box = mocks.BoxAsMock(10, 10, 10)
        place_mock.side_effect = place_box.create
        feature = MagicMock(spec=Feature)

        grid = MagicMock()
        with BuildPart() as part:
            BasePlate(grid, features=feature)

        feature.apply.assert_called_once()

        bbox = part.part.bounding_box()
        self.assertVectorAlmostEqual((10, 10, 10), bbox.size)
        self.assertAlmostEqual(862.6548245743672, part.part.volume)


@patch("gridfinity_build123d.baseplate.BasePlate.__init__")
class BasePlateEqualTest(testutils.UtilTestCase):
    @patch("gridfinity_build123d.baseplate.BasePlateBlockFrame", autospec=True)
    def test_base_plate_equal(
        self,
        bplateblock_mock: MagicMock,
        bplate_mock: MagicMock,
    ) -> None:
        features = MagicMock(spec=Feature)

        BasePlateEqual(size_x=2, size_y=3, features=features)

        bplate_mock.assert_called_once_with(
            [[True, True], [True, True], [True, True]],
            bplateblock_mock.return_value,
            features,
            ANY,
            ANY,
            ANY,
        )

    def test_base_plate_equal_block(
        self,
        bplate_mock: MagicMock,
    ) -> None:
        block_mock = MagicMock(spec=BasePlateBlock)
        features = MagicMock(spec=Feature)

        BasePlateEqual(
            size_x=2,
            size_y=3,
            baseplate_block=block_mock,
            features=features,
        )

        bplate_mock.assert_called_once_with(
            [[True, True], [True, True], [True, True]],
            block_mock,
            features,
            ANY,
            ANY,
            ANY,
        )


class BasePlateSizedTest(testutils.UtilTestCase):
    def test_base_plate_sized_requires_at_least_one_grid_cell(self) -> None:
        with self.assertRaises(ValueError):
            BasePlateSized(41.9, 42)

        with self.assertRaises(ValueError):
            BasePlateSized(42, 41.9)

    def test_base_plate_sized_rejects_invalid_grid_align_x(self) -> None:
        with self.assertRaises(ValueError):
            BasePlateSized(50, 50, grid_align_x=Direction.FRONT)

    def test_base_plate_sized_rejects_invalid_grid_align_y(self) -> None:
        with self.assertRaises(ValueError):
            BasePlateSized(50, 50, grid_align_y=Direction.LEFT)

    def test_base_plate_sized_accepts_exact_single_cell_size(self) -> None:
        """Verify minimum accepted size (42 mm = 1 grid cell)."""
        base_plate = BasePlateSized(42, 42)
        bbox = base_plate.bounding_box()
        self.assertVectorAlmostEqual((42, 42, 4.649), bbox.size)

    def test_base_plate_sized_floors_dimensions_to_full_cells(self) -> None:
        """Verify that non-multiples of 42 are accepted and creates a valid baseplate."""
        base_plate = BasePlateSized(83, 85)
        bbox = base_plate.bounding_box()

        # Outer dimensions should match the requested size
        self.assertAlmostEqual(83, bbox.size.X, places=2)
        self.assertAlmostEqual(85, bbox.size.Y, places=2)

        # Should have reasonable geometry
        self.assertAlmostEqual(base_plate.volume, 18916.080061292214)
        self.assertAlmostEqual(base_plate.area, 11237.060313619717)

    def test_base_plate_sized_custom_block_full(self) -> None:
        """Verify custom block produces different geometry than frame."""
        base_plate_frame = BasePlateSized(50, 50, baseplate_block=BasePlateBlockFrame())
        base_plate_full = BasePlateSized(50, 50, baseplate_block=BasePlateBlockFull())

        bbox_frame = base_plate_frame.bounding_box()
        bbox_full = base_plate_full.bounding_box()

        # Full block should be taller
        self.assertLess(bbox_frame.size.Z, bbox_full.size.Z)
        # Full block should have more volume
        self.assertLess(base_plate_frame.volume, base_plate_full.volume)
