import scipy
import warnings
import numpy as np
from .video import Video

class Euler:
    def __init__(self, signals=None):
        self.signals = None

    def get_signals(self, filename):
        """
        Extracts eulerian signals from video
        """
        if self.signals is not None:
            raise IOError("Signal has already been computed")

        video = Video(filename)
        self.signals = video.process_video()


    def simple_average(self, lo_hr=50, hi_hr=200):
        """
        Averages the signal and performs simple frequency analysis
        to extract hr
        returns: hr
        """
        ms = np.mean(self.signals, axis=1)

        if len(ms) < 30*20:
            warnings.warn("Your video is shorter than 30 seconds. Resolution of HR detection may be too low")

        freq, power = scipy.signal.welch(ms - ms[0], fs=30, nperseg=len(ms))

        # poor man's filter:
        mask = ((freq * 60 > lo_hr) &  (freq * 60 < hi_hr))
        power[~mask] = 0 
        hr = freq[np.argmax(power)]*60

        return hr


