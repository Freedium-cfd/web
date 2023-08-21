import cProfile
import logging
import os
import pstats
from io import StringIO


def profiler_enable():
    profile = cProfile.Profile()
    profile.enable()
    return profile


def profiler_disable(profile):
    profile.disable()


PROFILE_LIMIT = int(os.environ.get("PROFILE_LIMIT", 30))


def profiler_summary(profile):
    s = StringIO()
    pid = os.getpid()
    ps = pstats.Stats(profile, stream=s).sort_stats("time", "cumulative")
    ps.print_stats(PROFILE_LIMIT)

    # logging.error("\n[%d] [INFO] [%s] URI %s" % (os.pid, req.method, req.uri))
    logging.error("[%d] [INFO] %s" % (pid, s.getvalue()))
