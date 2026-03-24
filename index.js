// index.js

const net = require('net');

const SERVER_PORT = 65432;
const SERVER_ADDR = "192.168.0.138";

// ─── Persistent TCP connection ───────────────────────────────────────────────
let socket = null;
let recvBuf = "";

function connect() {
    socket = net.createConnection({ port: SERVER_PORT, host: SERVER_ADDR }, () => {
        console.log('Connected to server');
        document.getElementById("status").textContent = "● Connected";
        document.getElementById("status").style.color = "green";
        // Start polling for stats once connected
        setInterval(() => sendCommand("ping"), 300);
    });

    socket.on('data', (data) => {
        recvBuf += data.toString();
        // Responses are newline-terminated JSON
        while (recvBuf.includes("\n")) {
            const idx = recvBuf.indexOf("\n");
            const line = recvBuf.slice(0, idx).trim();
            recvBuf = recvBuf.slice(idx + 1);
            if (line) {
                try {
                    updateUI(JSON.parse(line));
                } catch(e) {
                    console.error("Bad JSON:", line);
                }
            }
        }
    });

    socket.on('error', (err) => {
        console.error("Socket error:", err.message);
        document.getElementById("status").textContent = "⚠ Disconnected";
        document.getElementById("status").style.color = "red";
        socket = null;
        // Retry after 2 seconds
        setTimeout(connect, 2000);
    });

    socket.on('end', () => {
        console.log('Server closed connection');
        document.getElementById("status").textContent = "⚠ Disconnected";
        document.getElementById("status").style.color = "red";
        socket = null;
        setTimeout(connect, 2000);
    });
}

function sendCommand(cmd) {
    if (socket && !socket.destroyed) {
        socket.write(cmd + "\n");
    }
}

// ─── UI update ───────────────────────────────────────────────────────────────
function updateUI(s) {
    document.getElementById("direction").textContent  = s.direction    ?? "–";
    document.getElementById("speed").textContent      = s.speed        ?? "0";
    document.getElementById("distance").textContent   = s.distance     ?? "0.0";
    document.getElementById("temperature").textContent= s.temperature  ?? "0.0";
    document.getElementById("obstacle").textContent   = s.obstacle_dist?? "0.0";
}

// ─── Keyboard control ────────────────────────────────────────────────────────
const KEY_CMD = {
    87: "forward",   // W
    83: "backward",  // S
    65: "left",      // A
    68: "right",     // D
};
const ARROW_IDS = {
    87: "upArrow",
    83: "downArrow",
    65: "leftArrow",
    68: "rightArrow",
};

let heldKey = null;

document.addEventListener("keydown", (e) => {
    if (heldKey === e.keyCode) return; // already held
    if (!KEY_CMD[e.keyCode]) return;
    heldKey = e.keyCode;
    document.getElementById(ARROW_IDS[e.keyCode]).style.color = "green";
    sendCommand(KEY_CMD[e.keyCode]);
});

document.addEventListener("keyup", (e) => {
    if (!KEY_CMD[e.keyCode]) return;
    heldKey = null;
    document.getElementById(ARROW_IDS[e.keyCode]).style.color = "grey";
    sendCommand("stop");
});

// ─── Init ─────────────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", connect);