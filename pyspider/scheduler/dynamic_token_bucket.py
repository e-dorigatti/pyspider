
from .token_bucket import Bucket
from scipy import stats
import numpy as np
from datetime import datetime
import pytz
import random


class DynamicBucket(Bucket):
    """ Token-bucket algorithm with time varying rate and unlimited burst
    If burst is set to a negative number the bucket fill rate is a bimodal
    distribution obtained by summing two student's t distribution.
    If burst is positive then the standart token-bucket algorithm is used.
    """
    def __init__(self, rate=1, burst=None, timezone=None,
                 dist1=(11, 1, 2),    # (center, degrees of freedom, scale)
                 dist2=(16, 1, 3)):   # (center, degrees of freedom, scale)
        super(DynamicBucket, self).__init__(rate, burst)
        self.timezone = timezone or pytz.timezone(random.choice(pytz.common_timezones))

        xs = np.arange(0, 24, 1/60.)
        self.rate_time = map(sum, zip(self._make_t(xs, *dist1), self._make_t(xs, *dist2)))
        self.ymax = max(self.rate_time)
        self._real_rate = rate
        self._real_burst = burst

    def _make_t(self, xs, center, deg, scale):
        return [stats.t.pdf(x, deg, center, scale) for x in xs]

    @property
    def rate(self):
        if self._real_burst < 0.0:
            now = datetime.now(self.timezone)
            x = now.hour * 60 + now.minute
            return self.rate_time[x] * self._real_rate / self.ymax
        else:
            return self._real_rate

    @rate.setter
    def rate(self, value):
        self._real_rate = value

    @property
    def burst(self):
        return -self._real_burst if self._real_burst < 0.0 else self._real_burst

    @burst.setter
    def burst(self, value):
        self._real_burst = value

    def get(self):
        return super(DynamicBucket, self).get()
