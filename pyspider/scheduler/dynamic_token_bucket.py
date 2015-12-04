
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

    # amplitude is further scaled based on weekdays
    weekday_scaling = [1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.3]

    def __init__(self, rate=1, burst=None, timezone=None,
                 dist1=(10, 2, 1),     # mu, sigma, scaling
                 dist2=(16, 2, 0.7)):  # mu, sigma, scaling
        super(DynamicBucket, self).__init__(rate, burst)
        self.timezone = timezone or pytz.timezone(random.choice(pytz.common_timezones))

        self._real_rate = rate
        self._real_burst = burst
        self.dist1, self.dist2 = dist1, dist2

    def daily_random_noise(self, now, x, noise_mu=0, noise_sigma=0.1):
        """ Alter x by a small, random, normally-distributed amount (the same each day)
        """
        old = random.getstate()
        random.seed(now.year * 365 + now.month * 31 + now.day)
        val = x + random.normalvariate(noise_mu, noise_sigma)
        random.setstate(old)
        return val

    def probability_density_function(self, x, mu, sigma, scale):
        now = datetime.now(self.timezone)
        mu = self.daily_random_noise(now, mu, 0, mu * 0.1)
        sigma = max(0.1, self.daily_random_noise(now, sigma, 0, sigma * 0.1))
        normal = math.exp(-(x-mu)**2/(2*sigma**2))/math.sqrt(2*math.pi*sigma)
        return scale * normal * self.weekday_scaling[now.weekday()]

    @property
    def rate(self):
        if self._real_burst < 0.0:
            now = datetime.now(self.timezone)
            x = now.hour + now.minute / 60.
            y1 = self.probability_density_function(x, *self.dist1)
            y2 = self.probability_density_function(x, *self.dist2)
            ymax = max(self.dist1[2] / math.sqrt(2 * math.pi),
                       self.dist2[2] / math.sqrt(2 * math.pi))
            return (y1 + y2) * self._real_rate / ymax
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
