from build123d import Axis, BuildPart, CenterOf, Vector
from parameterized import parameterized

from gridfinity_build123d import (
    BasePlateBlockFrame,
    BasePlateBlockFull,
    BasePlateBottomSideRound,
    BasePlateEqual,
    BasePlateSized,
    BottomCorners,
    BottomMiddle,
    Direction,
    MagnetHole,
    ScrewHoleCountersink,
    TopCorners,
    Weighted,
)
from tests import testutils


class BasePlateTest(testutils.UtilTestCase):
    def test_base_plate_frame(self) -> None:
        with BuildPart() as part:
            BasePlateEqual(size_x=2, size_y=3, baseplate_block=BasePlateBlockFrame())
        bbox = part.part.bounding_box()
        self.assertVectorAlmostEqual((84, 126, 4.649), bbox.size)
        self.assertAlmostEqual(9934.358783084768, part.part.area)
        self.assertAlmostEqual(7684.874727987361, part.part.volume)

    def test_base_plate_weighted(self) -> None:
        with BuildPart() as part:
            BasePlateEqual(
                size_x=3,
                size_y=2,
                baseplate_block=BasePlateBlockFull(
                    features=[
                        MagnetHole(TopCorners()),
                        ScrewHoleCountersink(BottomCorners()),
                        Weighted(BottomMiddle()),
                    ],
                ),
            )
        bbox = part.part.bounding_box()
        self.assertVectorAlmostEqual((126.0, 84.0, 11.049), bbox.size)
        self.assertAlmostEqual(32628.56878916578, part.part.area)
        self.assertAlmostEqual(57020.89197927, part.part.volume)

    def test_base_plate_bottom_side_round_direction(self) -> None:
        base_plate = BasePlateEqual(size_x=2, size_y=2)
        base_plate_rounded = BasePlateEqual(
            size_x=2,
            size_y=2,
            features=BasePlateBottomSideRound(
                radius=1,
                direction=[
                    Direction.FRONT,
                    Direction.BACK,
                    Direction.LEFT,
                    Direction.RIGHT,
                ],
            ),
        )
        base_plate_side_rounded = BasePlateEqual(
            size_x=2,
            size_y=2,
            features=BasePlateBottomSideRound(radius=1, direction=Direction.FRONT),
        )

        bbox = base_plate.bounding_box()
        bbox_rounded = base_plate_rounded.bounding_box()
        self.assertVectorAlmostEqual(
            (bbox.size.X, bbox.size.Y, bbox.size.Z),
            bbox_rounded.size,
            places=6,
        )

        self.assertLess(base_plate_side_rounded.volume, base_plate.volume)
        self.assertLess(base_plate_rounded.volume, base_plate_side_rounded.volume)

    def test_base_plate_bottom_side_round_front_only_does_not_change_back(self) -> None:
        """Make sure when we round only the front, the back face area is unchanged."""
        base_plate = BasePlateEqual(size_x=2, size_y=2)
        front_rounded = BasePlateEqual(
            size_x=2,
            size_y=2,
            features=BasePlateBottomSideRound(radius=1, direction=Direction.FRONT),
        )

        base_faces_y = base_plate.faces().filter_by(Axis.Y).sort_by(Axis.Y)
        rounded_faces_y = front_rounded.faces().filter_by(Axis.Y).sort_by(Axis.Y)

        # FRONT is min-Y, BACK is max-Y.
        self.assertLess(rounded_faces_y[0].area, base_faces_y[0].area)
        self.assertAlmostEqual(rounded_faces_y[-1].area, base_faces_y[-1].area, places=6)


class BasePlateSizedTest(testutils.UtilTestCase):
    @parameterized.expand(  # type: ignore[untyped-decorator]
        [
            # centered
            ({}, Vector(0.0, 0.0, 2.3245)),
            # left_front
            (
                {"grid_align_x": Direction.LEFT, "grid_align_y": Direction.FRONT},
                Vector(-4.0, -4.0, 2.3245),
            ),
            # right_back
            (
                {"grid_align_x": Direction.RIGHT, "grid_align_y": Direction.BACK},
                Vector(4.0, 4.0, 2.3245),
            ),
            # left_back
            (
                {"grid_align_x": Direction.LEFT, "grid_align_y": Direction.BACK},
                Vector(-4.0, 4.0, 2.3245),
            ),
            # left_center
            (
                {"grid_align_x": Direction.LEFT},
                Vector(-4.0, 0, 2.3245),
            ),
        ]
    )
    def test_base_plate_sized_aligns_top_opening_from_requested_anchor(
        self,
        kwargs: dict[str, Direction],
        expected_center: Vector,
    ) -> None:
        base_plate = BasePlateSized(50, 50, **kwargs)

        top_face = base_plate.faces().sort_by(Axis.Z)[-1]
        top_inner_wire_centers = [
            wire.center(CenterOf.BOUNDING_BOX) for wire in top_face.inner_wires()
        ]
        self.assertEqual(1, len(top_inner_wire_centers))

        self.assertVectorAlmostEqual(
            (expected_center.X, expected_center.Y, expected_center.Z),
            top_inner_wire_centers[0],
            places=6,
        )
        self.assertVectorAlmostEqual((50, 50, 4.649), base_plate.bounding_box().size)
