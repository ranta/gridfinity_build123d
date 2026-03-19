from unittest.mock import MagicMock

from build123d import BuildPart

from gridfinity_build123d import BasePlateBlockFrame, BasePlateBlockFull, BasePlateBlockSkeleton
from gridfinity_build123d.features import Feature
from tests import testutils


class BasePlateBlockFrameTest(testutils.UtilTestCase):
    def test_base_plate_block_frame(self) -> None:
        with BuildPart() as part:
            BasePlateBlockFrame().create_obj()
        bbox = part.part.bounding_box()
        self.assertVectorAlmostEqual((42, 42, 4.649), bbox.size)
        self.assertAlmostEqual(1291.4544166737892, part.part.volume)

    def test_base_plate_block_frame_feature(self) -> None:
        feature = MagicMock(spec=Feature)

        with BuildPart() as part:
            BasePlateBlockFrame(features=feature).create_obj()

        feature.apply.assert_called_once()

        bbox = part.part.bounding_box()
        self.assertVectorAlmostEqual((42, 42, 4.649), bbox.size)
        self.assertAlmostEqual(1291.4544166737892, part.part.volume)

    def test_base_plate_block_frame_height(self) -> None:
        with BuildPart() as part:
            BasePlateBlockFrame(bottom_height=10).create_obj()

        bbox = part.part.bounding_box()
        self.assertVectorAlmostEqual((42, 42, 14.649), bbox.size)
        self.assertAlmostEqual(5765.90685383006, part.part.volume)


class BasePlateBlockFullTest(testutils.UtilTestCase):
    def test_base_plate_block_frame(self) -> None:
        with BuildPart() as part:
            BasePlateBlockFull().create_obj()
        bbox = part.part.bounding_box()
        self.assertVectorAlmostEqual((42, 42, 11.049), bbox.size)
        self.assertAlmostEqual(12581.054416673793, part.part.volume)

    def test_base_plate_block_frame_height(self) -> None:
        with BuildPart() as part:
            BasePlateBlockFull(bottom_height=10).create_obj()
        bbox = part.part.bounding_box()
        self.assertVectorAlmostEqual((42, 42, 14.649), bbox.size)
        self.assertAlmostEqual(18931.45441667379, part.part.volume)

    def test_base_plate_block_frame_feature(self) -> None:
        feature = MagicMock(spec=Feature)

        with BuildPart() as part:
            BasePlateBlockFull(features=feature).create_obj()

        feature.apply.assert_called_once()

        bbox = part.part.bounding_box()
        self.assertVectorAlmostEqual((42, 42, 11.049), bbox.size)
        self.assertAlmostEqual(12581.054416673793, part.part.volume)


class BasePlateBlockSkeletonTest(testutils.UtilTestCase):
    def test_baseplateblockskeleton(self) -> None:
        part = BasePlateBlockSkeleton().create_obj()

        bbox = part.bounding_box()
        self.assertVectorAlmostEqual((42, 42, 11.049), bbox.size)
        self.assertAlmostEqual(6310.622527428775, part.volume)
