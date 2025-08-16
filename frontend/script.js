const startAndstopBtn = document.getElementById("startAndstopBtn");
const recordedAudio = document.getElementById("recordedAudio");
const loading = document.getElementById("loading");
const successMessage = document.getElementById("successMessage");

let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let stream;

// Generate a persistent session_id for memory
const sessionId = crypto.randomUUID();

async function endtoendAudioWithMemory(formdata) {
    try {
        const response = await fetch(`/agent/chat/${sessionId}`, {
            method: "POST",
            body: formdata
        });

        if (!response.ok) {
            throw new Error("Failed to generate audio");
        }

        const data = await response.json();
        console.log("Server reply:", data);
        return data;
    } catch (error) {
        console.error("Error from transcribe to audio:", error.message);
        alert("An error occurred while generating the voice.");
    }
}

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then((mediaStream) => {
            stream = mediaStream;
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                loading.style.display = "block";
                successMessage.classList.remove("show");
                recordedAudio.style.display = "none";

                const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
                let formdata = new FormData();
                formdata.append("file", audioBlob);

                const { audio_url } = await endtoendAudioWithMemory(formdata);

                loading.style.display = "none";
                successMessage.classList.add("show");
                recordedAudio.src = audio_url;
                recordedAudio.style.display = "block";
                recordedAudio.play();

                // Automatically start recording again after playback
                recordedAudio.onended = () => {
                    startRecording();
                };

                setTimeout(() => {
                    successMessage.classList.remove("show");
                }, 3000);
            };

            mediaRecorder.start();
            isRecording = true;
            startAndstopBtn.textContent = "Stop Recording";
            startAndstopBtn.classList.add("stillRecording");
        })
        .catch((err) => {
            alert("Microphone access denied or unavailable.");
            console.error(err);
        });
}

startAndstopBtn.addEventListener("click", (e) => {
    e.preventDefault();

    if (!isRecording) {
        startRecording();
    } else {
        mediaRecorder.stop();
        stream.getTracks().forEach((track) => track.stop());
        isRecording = false;
        startAndstopBtn.textContent = "Start Recording";
        startAndstopBtn.classList.remove("stillRecording");
    }
});
