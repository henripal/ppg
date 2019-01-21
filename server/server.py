import argparse
import asyncio
import json
import logging
import os
import time
import aiohttp_cors

import cv2
from aiohttp import web
from av import VideoFrame

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder

ROOT = os.path.dirname(__file__)


class VideoTransformTrack(VideoStreamTrack):
    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.counter = 0
        self.track = track
        # self.transform = transform

    async def recv(self):
        frame = await self.track.recv()
        self.counter += 1

        # if self.transform == 'edges':
        #     # perform edge detection
        #     img = frame.to_ndarray(format='bgr24')
        #     img = cv2.cvtColor(cv2.Canny(img, 100, 200), cv2.COLOR_GRAY2BGR)

        #     # rebuild a VideoFrame, preserving timing information
        #     new_frame = VideoFrame.from_ndarray(img, format='bgr24')
        #     new_frame.pts = frame.pts
        #     new_frame.time_base = frame.time_base
        #     return new_frame
        # elif self.transform == 'rotate':
        #     # rotate image
        #     img = frame.to_ndarray(format='bgr24')
        #     rows, cols, _ = img.shape
        #     M = cv2.getRotationMatrix2D((cols / 2, rows / 2), frame.time * 45, 1)
        #     img = cv2.warpAffine(img, M, (cols, rows))

        #     # rebuild a VideoFrame, preserving timing information
        #     new_frame = VideoFrame.from_ndarray(img, format='bgr24')
        #     new_frame.pts = frame.pts
        #     new_frame.time_base = frame.time_base
        #     return new_frame
        # else:
        return frame



async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(
        sdp=params['sdp'],
        type=params['type'])


    pc = RTCPeerConnection()
    pcs.add(pc)


    @pc.on('datachannel')
    def on_datachannel(channel):
        @channel.on('message')
        def on_message(message):
            channel.send('pong')

    @pc.on('iceconnectionstatechange')
    async def on_iceconnectionstatechange():
        print('ICE connection state is %s' % pc.iceConnectionState)
        if pc.iceConnectionState == 'failed':
            await pc.close()
            pcs.discard(pc)

    @pc.on('track')
    def on_track(track):
        print('Track %s received' % track.kind)

        if track.kind == 'video':
            local_video = VideoTransformTrack(track)
            pc.addTrack(local_video)

        @track.on('ended')
        async def on_ended():
            print('Track %s ended' % track.kind)

    # handle offer
    await pc.setRemoteDescription(offer)

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type='application/json',
        text=json.dumps({
            'sdp': pc.localDescription.sdp,
            'type': pc.localDescription.type
        }))


pcs = set()


async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WebRTC audio / video / data-channels demo')
    parser.add_argument('--port', type=int, default=8080,
                        help='Port for HTTP server (default: 8080)')
    parser.add_argument('--verbose', '-v', action='count')
    parser.add_argument('--write-audio', help='Write received audio to a file')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    app = web.Application()
    cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    app.on_shutdown.append(on_shutdown)
    app.router.add_post('/offer', offer)
    for route in list(app.router.routes()):
        print('adding route')
        cors.add(route)
    web.run_app(app, port=args.port)
