import av
import numpy as np
import face_alignment
import os

class Video:
    """
    handles the computation of HR from video file
    """
    def __init__(self, filename):
        self.filename = filename
        self.container = None
        self.landmarks = None
        self.patch_positions = []
        self.patch_size = None
        self.series = []

    def process_video(self):
        """
        launches computation and returns time series
        """
        self.open_videofile()
        self.compute_landmarks()
        self.positions_from_landmarks()
        self.compute_signal()
        return self.series



    def open_videofile(self):
        """
        Opens and returns the video file at path specified
        upon class initialization;
        saves av.container
        """
        if os.path.isfile(self.filename):
            self.container = av.open(self.filename)
        else:
            raise IOError('Cannot open file {}'.format(self.filename))


    def compute_landmarks(self):
        """
        Compute the landmarks on the first frame of the container
        container: av.container
        returns 68x2 ndarray 
        """
        if self.container is None:
            raise IOError('Video container has not been initialized')


        first_frame = next(self.container.decode(video=0))
        first_frame_np = first_frame.to_ndarray(format='rgb24')
        fa = face_alignment.FaceAlignment(face_alignment.LandmarksType._2D,
            flip_input=False, device='cpu')

        self.landmarks = fa.get_landmarks(first_frame_np)[0]

    @staticmethod
    def convert_positions(positions):
        """
        converts the positions list of tuples to integer values
        """
        return [(int(x), int(y)) for (x, y) in positions] 

    def positions_from_landmarks(self):
        """
        Compute and saves boxes and box size for PPG from landmarks
        landmarks: 68x2 ndarray
        """
        if self.landmarks is None:
            raise IOError('Landmarks have not been computed')
        if len(self.patch_positions) != 0:
            raise IOError('Patch positions have already been computed')

        positions = []
        top_left_brow = self.landmarks[19]
        top_right_brow = self.landmarks[24]
        left_eye = self.landmarks[37]
        brow_eye_distance = np.linalg.norm(top_left_brow - left_eye)
        f_param = 4
        size = int(brow_eye_distance / f_param)
        positions.append((top_left_brow[0] , top_left_brow[1] - size*2))
        positions.append((top_right_brow[0] , top_right_brow[1] -size*2))
        positions.append((top_left_brow[0] , top_left_brow[1] - size*4))
        positions.append((top_right_brow[0] , top_right_brow[1] -size*4))
        positions.append(tuple(np.mean([positions[0], positions[1]], axis=0)))
        positions.append(tuple(np.mean([positions[2], positions[3]], axis=0)))
        
        self.patch_positions = self.convert_positions(positions)
        self.patch_size = int(size)

    def compute_signal(self):
        """
        computes univariate signal from video container and positions list
        """
        if len(self.patch_positions) == 0:
            raise IOError('Patch positions have not been computed')
        if len(self.series) != 0:
            raise IOError('Series has already been computed')

        result = []

        for frame in self.container.decode(video=0):
            frame_results = []
            np_frame = frame.to_ndarray(format='rgb24')
            for x, y in self.patch_positions:
                frame = np_frame[y:(y+self.patch_size), x:(x+self.patch_size), 1]
                frame_results.append(np.mean(frame))

            result.append(frame_results)

        self.series = np.array(result)
