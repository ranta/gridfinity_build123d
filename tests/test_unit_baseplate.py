from unittest.mock import ANY, MagicMock, patch

from build123d import BuildPart

from gridfinity_build123d.baseplate import (
    BasePlate,
    BasePlateEqual,
)
from gridfinity_build123d.baseplate_block import BasePlateBlock
from gridfinity_build123d.features import Feature
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
