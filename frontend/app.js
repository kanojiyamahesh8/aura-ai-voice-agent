// ============================================================
// AURA AI — FRONTEND LOGIC
// ============================================================

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
// 6. Receive live conversation transcript
// 7. Display AI agent state
// 8. End the call
// 9. Update the UI state
// 10. Load test orders dynamically
//
// ============================================================


// ------------------------------------------------------------
// Global state
// ------------------------------------------------------------

let room = null;
let transcriptMessages = [];


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

        // Reset transcript for the new call
        transcriptMessages = [];

        document.getElementById("transcript").innerHTML =
            "<p>No conversation yet.</p>";

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


        // ----------------------------------------------------
        // Listen for audio tracks from the AI agent
        // ----------------------------------------------------

        room.on(
            LivekitClient.RoomEvent.TrackSubscribed,
            handleTrackSubscribed
        );


        // ----------------------------------------------------
        // Listen for conversation transcript
        // ----------------------------------------------------

        room.on(
            LivekitClient.RoomEvent.TranscriptionReceived,
            handleTranscription
        );


        // ----------------------------------------------------
        // Listen for AI agent state changes
        // ----------------------------------------------------

        room.on(
            LivekitClient.RoomEvent.ParticipantAttributesChanged,
            handleParticipantAttributesChanged
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
// Handle LiveKit transcription
// ------------------------------------------------------------

function handleTranscription(segments, participant) {

    for (const segment of segments) {

        // We only display completed transcript segments.
        if (!segment.final || !segment.text.trim()) {
            continue;
        }


        // Identify who is speaking.
        const speaker = participant?.isAgent
            ? "Aura"
            : "You";


        addTranscriptMessage(
            speaker,
            segment.text
        );
    }
}


// ------------------------------------------------------------
// Add message to transcript UI
// ------------------------------------------------------------

function addTranscriptMessage(speaker, text) {

    const transcript = document.getElementById("transcript");


    // Remove the initial placeholder.
    if (transcriptMessages.length === 0) {
        transcript.innerHTML = "";
    }


    transcriptMessages.push({
        speaker: speaker,
        text: text
    });


    const message = document.createElement("p");


    message.innerHTML = `
        <strong>${speaker}:</strong> ${text}
    `;


    transcript.appendChild(message);


    // Keep the latest message visible.
    transcript.scrollTop = transcript.scrollHeight;
}


// ------------------------------------------------------------
// Handle AI agent state changes
// ------------------------------------------------------------

function handleParticipantAttributesChanged(
    changedAttributes,
    participant
) {

    // We only care about the AI agent.
    if (!participant.isAgent) {
        return;
    }


    const state = changedAttributes["lk.agent.state"];


    if (!state) {
        return;
    }


    const statusMessages = {

        initializing: "Connecting...",

        idle: "Ready",

        listening: "Listening",

        thinking: "Thinking",

        speaking: "Speaking"

    };


    updateStatus(
        statusMessages[state] || state
    );
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


// ------------------------------------------------------------
// Create order card
// ------------------------------------------------------------

function createOrderCard(orderId, order) {

    const orderCard = document.createElement("div");

    orderCard.className = "order-card";


    orderCard.innerHTML = `
        <h3>${orderId}</h3>

        <p>
            <strong>Customer:</strong>
            ${order.customer}
        </p>

        <p>
            <strong>Product:</strong>
            ${order.product}
        </p>

        <p>
            <strong>Value:</strong>
            ₹${order.value}
        </p>

        <p>
            <strong>Status:</strong>
            ${order.status}
        </p>
    `;


    return orderCard;
}


// ------------------------------------------------------------
// Load and display Aura Skincare orders
// ------------------------------------------------------------

async function loadOrders() {

    try {

        const response = await fetch("/orders");


        if (!response.ok) {
            throw new Error("Could not load orders.");
        }


        const orders = await response.json();


        const ordersContainer =
            document.getElementById("orders-container");


        ordersContainer.innerHTML = "";


        // Dynamically create cards for every order.
        for (const [orderId, order] of Object.entries(orders)) {

            ordersContainer.appendChild(
                createOrderCard(orderId, order)
            );

        }

    }


    catch (error) {

        console.error(
            "Order loading error:",
            error
        );


        document.getElementById(
            "orders-container"
        ).textContent =
            "Unable to load test orders.";

    }
}


// ------------------------------------------------------------
// Load orders when page starts
// ------------------------------------------------------------

loadOrders();