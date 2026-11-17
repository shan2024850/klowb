"""P1-UNIT-009: feed-quality invariants on observations."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from libs.domain.enums import FeedQuality, weakest_feed_quality
from libs.schemas.system import FEED_QUALITY_LEGEND
from tests import factories

NOT_DELAYED = [q for q in FeedQuality if q is not FeedQuality.DELAYED]


def test_p1_unit_009_delayed_requires_a_positive_delay() -> None:
    with pytest.raises(ValidationError, match="delay_seconds"):
        factories.trade(feed_quality=FeedQuality.DELAYED, delay_seconds=0)
    delayed = factories.trade(feed_quality=FeedQuality.DELAYED, delay_seconds=900)
    assert delayed.delay_seconds == 900


@pytest.mark.parametrize("quality", NOT_DELAYED)
def test_p1_unit_009_a_delay_is_only_valid_for_delayed_data(quality: FeedQuality) -> None:
    with pytest.raises(ValidationError, match="delay_seconds"):
        factories.trade(feed_quality=quality, delay_seconds=900)
    assert factories.trade(feed_quality=quality).delay_seconds == 0


@pytest.mark.parametrize("quality", list(FeedQuality))
def test_p1_unit_009_redistribution_defaults_to_false_for_every_quality(
    quality: FeedQuality,
) -> None:
    delay = 900 if quality is FeedQuality.DELAYED else 0
    observation = factories.trade(feed_quality=quality, delay_seconds=delay)
    assert observation.redistribution_allowed is False


def test_p1_unit_009_unofficial_data_can_never_be_redistributable() -> None:
    with pytest.raises(ValidationError, match="UNOFFICIAL"):
        factories.trade(feed_quality=FeedQuality.UNOFFICIAL, redistribution_allowed=True)


def test_p1_unit_009_weakest_quality_wins_and_is_never_upgraded() -> None:
    assert (
        weakest_feed_quality(FeedQuality.REALTIME_CONSOLIDATED, FeedQuality.REALTIME_SINGLE_VENUE)
        is FeedQuality.REALTIME_SINGLE_VENUE
    )
    assert (
        weakest_feed_quality(FeedQuality.REALTIME_SINGLE_VENUE, FeedQuality.DELAYED)
        is FeedQuality.DELAYED
    )
    assert weakest_feed_quality(FeedQuality.EOD, FeedQuality.UNOFFICIAL) is FeedQuality.UNOFFICIAL
    assert weakest_feed_quality(*FeedQuality) is FeedQuality.SIMULATED
    assert weakest_feed_quality(FeedQuality.DELAYED) is FeedQuality.DELAYED
    with pytest.raises(ValueError, match="at least one"):
        weakest_feed_quality()


def test_p1_unit_009_ranks_are_a_strict_total_order() -> None:
    ranks = [q.rank for q in FeedQuality]
    assert len(set(ranks)) == len(ranks)
    assert max(FeedQuality, key=lambda q: q.rank) is FeedQuality.REALTIME_CONSOLIDATED


def test_p1_unit_009_only_realtime_classes_are_realtime_or_execution_eligible() -> None:
    realtime = {q for q in FeedQuality if q.is_realtime}
    assert realtime == {
        FeedQuality.REALTIME_CONSOLIDATED,
        FeedQuality.REALTIME_EXCHANGE,
        FeedQuality.REALTIME_SINGLE_VENUE,
    }
    legend = {entry.value: entry for entry in FEED_QUALITY_LEGEND}
    assert set(legend) == set(FeedQuality), "legend must describe every feed quality"
    for quality, entry in legend.items():
        assert entry.realtime is quality.is_realtime
        assert entry.execution_eligible is quality.is_realtime
        assert entry.rank == quality.rank


def test_p1_unit_009_only_the_consolidated_feed_is_described_as_consolidated() -> None:
    for entry in FEED_QUALITY_LEGEND:
        mentions = "consolidated" in entry.label.lower()
        assert mentions is (entry.value is FeedQuality.REALTIME_CONSOLIDATED), entry.label
    labels = [entry.label for entry in FEED_QUALITY_LEGEND]
    assert len(set(labels)) == len(labels), "labels must be distinct"
