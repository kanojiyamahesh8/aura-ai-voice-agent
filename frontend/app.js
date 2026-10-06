// ============================================================
// AURA AI — FRONTEND LOGIC
// ============================================================
//
// This file contains the browser-side logic for the Aura
// Skincare AI voice agent.
//
// Responsibilities:
//
// 1. Start the voice call
// 2. Get a LiveKit token from the backend
// 3. Connect the browser to LiveKit
// 4. Enable the customer's microphone
// 5. Receive audio from the AI agent
// 6. End the call
// 7. Update the UI state
//
// ============================================================


// ------------------------------------------------------------
// Global state
// ------------------------------------------------------------

let room = null;


// ------------------------------------------------------------
// DOM elements
// ------------------------------------------------------------

const startCallButton = document.getElementById("startCall");
const endCallButton = document.getElementById("endCall");
const statusElement = document.getElementById("status");


// ------------------------------------------------------------
// Event listeners
// ------------------------------------------------------------

startCallButton.addEventListener("click", startCall);
endCallButton.addEventListener("click", endCall);


// ------------------------------------------------------------
// Start voice call
// ------------------------------------------------------------

async function startCall() {

    try {

        updateStatus("Connecting...");

        // Ask our FastAPI backend for a temporary
        // LiveKit access token.
        const response = await fetch("/token");

        if (!response.ok) {
            throw new Error("Could not get LiveKit token.");
        }

        const data = await response.json();


        // Create a LiveKit room.
        room = new LivekitClient.Room();


        // Listen for audio tracks from the AI agent
        // before connecting to the room.
        room.on(
            LivekitClient.RoomEvent.TrackSubscribed,
            handleTrackSubscribed
        );


        // Connect the browser to LiveKit Cloud.
        await room.connect(
            data.url,
            data.token
        );


        // Allow audio playback in the browser.
        await room.startAudio();


        // Enable the customer's microphone.
        await room.localParticipant.setMicrophoneEnabled(true);


        updateStatus("Connected — Listening");


        // Update buttons.
        startCallButton.disabled = true;
        endCallButton.disabled = false;

    }

    catch (error) {

        console.error("Call connection error:", error);

        updateStatus("Connection failed");

        alert(error.message);

    }
}


// ------------------------------------------------------------
// Handle audio received from AI agent
// ------------------------------------------------------------

function handleTrackSubscribed(track) {

    if (track.kind === "audio") {

        const audioElement = track.attach();

        document.body.appendChild(audioElement);

    }
}


// ------------------------------------------------------------
// End voice call
// ------------------------------------------------------------

async function endCall() {

    if (room) {

        await room.disconnect();

        room = null;

    }

    updateStatus("Disconnected");

    startCallButton.disabled = false;
    endCallButton.disabled = true;
}


// ------------------------------------------------------------
// Update status shown in UI
// ------------------------------------------------------------

function updateStatus(message) {

    statusElement.textContent = message;

}