from enum import Enum


class Action(Enum):
    subscribe = "subscribe"
    unsubscribe = "unsubscribe"
    snapshots = "snapshots"


class Channels(Enum):
    troves_overview = "troves_overview"
    stability_pool = "stability_pool"


class Interval(Enum):
    i15m = 60 * 15
    i1h = 60 * 60
    i4h = 60 * 60 * 4
    i1d = 60 * 60 * 24


class Payload(Enum):
    update = "update"
    snapshot = "snapshot"
