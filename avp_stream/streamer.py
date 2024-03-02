import grpc
from avp_stream.grpc_msg import * 
from threading import Thread
from avp_stream.utils import * 
import time 
import numpy as np 


YUP2ZUP = np.array([[[1, 0, 0, 0], 
                    [0, 0, -1, 0], 
                    [0, 1, 0, 0],
                    [0, 0, 0, 1]]], dtype = np.float64)


class VisionProStreamer:

    def __init__(self, ip, record = True, axis_up = 'Y'): 

        # Vision Pro IP 
        self.ip = ip
        self.record = record 
        self.recording = [] 
        self.latest = None 
        if axis_up == 'Z': 
            self.axis_transform = YUP2ZUP
        else:
            self.axis_transform = np.expand_dims(np.eye(4), axis = 0)
        self.start_streaming()


    def start_streaming(self): 

        stream_thread = Thread(target = self.stream)
        stream_thread.start() 
        while self.latest is None: 
            pass 
        print(' == DATA IS FLOWING IN! ==')
        print('Ready to start streaming.') 


    def stream(self): 

        request = handtracking_pb2.HandUpdate()
        try:
            with grpc.insecure_channel(f"{self.ip}:12345") as channel:
                stub = handtracking_pb2_grpc.HandTrackingServiceStub(channel)
                responses = stub.StreamHandUpdates(request)
                for response in responses:
                    transformations = {
                        "left_wrist": self.axis_transform @  process_matrix(response.left_hand.wristMatrix),
                        "right_wrist": self.axis_transform @  process_matrix(response.right_hand.wristMatrix),
                        "left_fingers": self.axis_transform @  process_matrices(response.left_hand.skeleton.jointMatrices),
                        "right_fingers": self.axis_transform @  process_matrices(response.right_hand.skeleton.jointMatrices),
                        "head": self.axis_transform @  process_matrix(response.Head), 
                        # "rgb": response.rgb, # TODO: should figure out how to get the rgb image from vision pro 
                    }
                    if self.record: 
                        self.recording.append(transformations)
                    self.latest = transformations 

        except Exception as e:
            print(f"An error occurred: {e}")
            pass 

    def get_latest(self): 
        return self.latest
        
    def get_recording(self): 
        return self.recording
    

if __name__ == "__main__": 

    streamer = VisionProStreamer(ip = '10.29.230.57')
    while True: 

        latest = streamer.get_latest()
        print(latest)