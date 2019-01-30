

var pc = new RTCPeerConnection();
var landmarks = null

// // get DOM elements
// var dataChannelLog = document.getElementById('data-channel'),
//     iceConnectionLog = document.getElementById('ice-connection-state'),
//     iceGatheringLog = document.getElementById('ice-gathering-state'),
//     signalingLog = document.getElementById('signaling-state');

// // register some listeners to help debugging
// pc.addEventListener('icegatheringstatechange', function() {
//     iceGatheringLog.textContent += ' -> ' + pc.iceGatheringState;
// }, false);
// iceGatheringLog.textContent = pc.iceGatheringState;

// pc.addEventListener('iceconnectionstatechange', function() {
//     iceConnectionLog.textContent += ' -> ' + pc.iceConnectionState;
// }, false);
// iceConnectionLog.textContent = pc.iceConnectionState;

// pc.addEventListener('signalingstatechange', function() {
//     signalingLog.textContent += ' -> ' + pc.signalingState;
// }, false);
// signalingLog.textContent = pc.signalingState;

// connect audio / video
pc.addEventListener('track', function(evt) {
    document.getElementById('video').srcObject = evt.streams[0];
});

// data channel
var dc = null, dcInterval = null;

function negotiate() {
    return pc.createOffer().then(function(offer) {
        return pc.setLocalDescription(offer);
    }).then(function() {
        // wait for ICE gathering to complete
        return new Promise(function(resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(function() {
        var offer = pc.localDescription;
        // var codec = document.getElementById('video-codec').value;
        // if (codec !== 'default') {
        var _ = sdpFilterCodec("VP8/90000", offer.sdp);
        // }

        // document.getElementById('offer-sdp').textContent = offer.sdp;
        return fetch('http://localhost:8080/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
                // video_transform: document.getElementById('video-transform').value
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then(function(response) {
        return response.json();
    }).then(function(answer) {
        // document.getElementById('answer-sdp').textContent = answer.sdp;
        return pc.setRemoteDescription(answer);
    }).catch(function(e) {
        alert(e);
    });
}

function startDataChannel() {
    dc = pc.createDataChannel('chat');
    dc.onclose = function() {
        clearInterval(dcInterval);
        // dataChannelLog.textContent += '- close\n';
    };
    dc.onopen = function() {
        // dataChannelLog.textContent += '- open\n';
        dcInterval = setInterval(function() {
            var message = 'ping';
            // dataChannelLog.textContent += '> ' + message + '\n';
            dc.send(message);
        }, 1000);
    };
    dc.onmessage = function(evt) {
        // dataChannelLog.textContent += '< ' + evt.data + '\n';
    };
}

async function startVideo() {
    await faceapi.loadSsdMobilenetv1Model('/models')
    await faceapi.loadFaceLandmarkModel('/models')
    await console.log("starting video")
    var constraints = {
        audio: false,
        video: {
            width: 800,
            height: 600
        }
    };


    await navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
        stream.getTracks().forEach(function(track) {
            pc.addTrack(track, stream);
        });
        negotiate();
    }, function(err) {
        alert('Could not acquire media: ' + err);
    });



    const input = await document.getElementById('video')
    await setTimeout(() => detectLoop(input), 2000);
    await setTimeout(() => monitorLoop(input), 8000);

}

async function monitorLoop(input) {
    if (landmarks) {
       var position = landmarks.positions[0]
       console.log(position)
        
        const targetCanvas = await document.getElementById("screencapCanvas")
        const video = await document.getElementById('video')
        // const photo = await document.getElementById("photo")
        var targetContext = targetCanvas.getContext('2d');
        var size = 60
        targetCanvas.width = size
        targetCanvas.height = size
        // canvas.width = video.offsetWidth
        // canvas.height = video.offsetHeight
        targetContext.drawImage(video, position.x, position.y, size, size, 0, 0, size, size);
        // var data = canvas.toDataURL('image/png');
        // photo.setAttribute('src', data);
        // context.fillStyle = "#AAA";
        // context.fillRect(0, 0, canvas.width, canvas.height);
    }
    setTimeout(() => monitorLoop(), 500);
}

async function detectLoop(input) {

    const detectionsWithLandmarks = await faceapi
        .detectSingleFace(input)
        .withFaceLandmarks()


    if (!detectionsWithLandmarks) {
        setTimeout(() => detectLoop(input), 1000)
    }


    const detectionsWithLandmarksForSize = await faceapi.resizeResults(detectionsWithLandmarks,
        { width: input.offsetWidth, height: input.offsetHeight})


    const canvas = await document.getElementById('overlay')
    canvas.width = input.offsetWidth
    canvas.height = input.offsetHeight
    if (detectionsWithLandmarksForSize) {
        faceapi.drawLandmarks(canvas, detectionsWithLandmarksForSize.landmarks, { drawLines: true })
        landmarks = detectionsWithLandmarksForSize.landmarks
    }

    setTimeout(() => detectLoop(input));
}

function start() {
    startDataChannel();
    startVideo();

}

function stop() {
    if (dc) {
        dc.close();
    }

    if (pc.getTransceivers) {
        pc.getTransceivers().forEach(function(transceiver) {
            transceiver.stop();
        });
    }

    // close local audio / video
    pc.getSenders().forEach(function(sender) {
        sender.track.stop();
    });

    // close peer connection
    setTimeout(function() {
        pc.close();
    }, 500);
}

function sdpFilterCodec(codec, realSpd){
    var allowed = []
    var codecRegex = new RegExp('a=rtpmap:([0-9]+) '+escapeRegExp(codec))
    var videoRegex = new RegExp('(m=video .*?)( ([0-9]+))*\\s*$')
    
    var lines = realSpd.split('\n');

    var isVideo = false;
    for(var i = 0; i < lines.length; i++){
        if (lines[i].startsWith('m=video ')) {
            isVideo = true;
        } else if (lines[i].startsWith('m=')) {
            isVideo = false;
        }

        if (isVideo) {
            var match = lines[i].match(codecRegex)
            if (match) {
                allowed.push(parseInt(match[1]))
            }
        }
    }

    var skipRegex = 'a=(fmtp|rtcp-fb|rtpmap):([0-9]+)'
    var sdp = ""

    var isVideo = false;
    for(var i = 0; i < lines.length; i++){
        if (lines[i].startsWith('m=video ')) {
            isVideo = true;
        } else if (lines[i].startsWith('m=')) {
            isVideo = false;
        }

        if (isVideo) {
            var skipMatch = lines[i].match(skipRegex);
            if (skipMatch && !allowed.includes(parseInt(skipMatch[2]))) {
                continue;
            } else if (lines[i].match(videoRegex)) {
                sdp+=lines[i].replace(videoRegex, '$1 '+allowed.join(' ')) + '\n'
            } else {
                sdp += lines[i] + '\n'
            }
        } else {
            sdp += lines[i] + '\n'
        }
    }

    return sdp;
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
}
