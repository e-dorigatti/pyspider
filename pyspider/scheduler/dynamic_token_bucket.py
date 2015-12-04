
from .token_bucket import Bucket
import math
from datetime import datetime
import pytz
import random


class DynamicBucket(Bucket):
    """ Token-bucket algorithm with time varying rate and unlimited burst
    If burst is set to a negative number the bucket fill rate is a bimodal
    distribution obtained by summing two independent normal random variables.
    If burst is positive then the standart token-bucket algorithm is used.
    """
    def __init__(self, rate=1, burst=None, timezone=None,
                 dist1=(10, 2, 1),     # mu, sigma, scaling
                 dist2=(16, 2, 0.7)):  # mu, sigma, scaling
        super(DynamicBucket, self).__init__(rate, burst)
        self.timezone = timezone or pytz.timezone(random.choice(pytz.common_timezones))

        xs = [x / 60. for x in range(0, 24 * 60)]
        self.rate_time = map(sum, zip(self.compute_distribution(xs, *dist1),
                                      self.compute_distribution(xs, *dist2)))
        self.ymax = max(self.rate_time)
        self._real_rate = rate
        self._real_burst = burst

    def compute_distribution(self, xs, mu, sigma, scale):
        def pdf(x):
            return math.exp(-(x-mu)**2/(2*sigma**2))/math.sqrt(2*math.pi*sigma)
        return [pdf(x) * scale for x in xs]

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
