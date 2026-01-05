let ws = null;
let prevPrices = {};   // store previous LTPs

// ==========================
// Load Index & Expiry
// ==========================
async function loadStructure() {
    const res = await fetch("/live/structure");
    const data = await res.json();

    const indexSelect = document.getElementById("indexSelect");
    indexSelect.innerHTML = "";

    Object.keys(data).forEach(index => {
        const opt = document.createElement("option");
        opt.value = index;
        opt.textContent = index;
        indexSelect.appendChild(opt);
    });

    loadExpiries();
}

async function loadExpiries() {
    const index = document.getElementById("indexSelect").value;
    const res = await fetch(`/live/structure/${index}`);
    const data = await res.json();

    const expirySelect = document.getElementById("expirySelect");
    expirySelect.innerHTML = "";

    Object.keys(data).forEach(expiry => {
        const opt = document.createElement("option");
        opt.value = expiry;
        opt.textContent = expiry;
        expirySelect.appendChild(opt);
    });

    connectWebSocket();
}

// ==========================
// WebSocket
// ==========================
function connectWebSocket() {
    if (ws) ws.close();

    prevPrices = {}; // reset on change

    const tbody = document.getElementById("optionTableBody");
    tbody.innerHTML = `
        <tr>
            <td colspan="5" class="text-center text-muted">
                Connecting to live feed...
            </td>
        </tr>
    `;

    const index = document.getElementById("indexSelect").value;
    const expiry = document.getElementById("expirySelect").value;

    ws = new WebSocket(
        `ws://${window.location.host}/ws/options/${index}/${expiry}`
    );

    ws.onmessage = event => {
        const msg = JSON.parse(event.data);
        renderTable(msg.data);
    };

    ws.onclose = () => {
        console.log("WebSocket closed");
    };
}

// ==========================
// Render / Update Table
// ==========================
function renderTable(data) {
    const tbody = document.getElementById("optionTableBody");

    if (!data || Object.keys(data).length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">
                    Waiting for live data...
                </td>
            </tr>
        `;
        return;
    }

    const nowSec = Date.now() / 1000;

    Object.entries(data).forEach(([symbol, info]) => {
        let row = document.getElementById(`row-${symbol}`);

        const prevLtp = prevPrices[symbol];
        const currLtp = info.ltp;

        // --------------------------
        // Detect stale data
        // --------------------------
        let tsText = info.timestamp;
        let tsClass = "";

        if (info.last_update_epoch) {
            const age = nowSec - info.last_update_epoch;

            if (age > 300) { // older than 5 minutes
                tsText += " (stale)";
                tsClass = "text-warning";
            }
        }

        // ==========================
        // CREATE ROW (FIRST TIME)
        // ==========================
        if (!row) {
            row = document.createElement("tr");
            row.id = `row-${symbol}`;

            row.innerHTML = `
                <td>${symbol}</td>
                <td class="ltp">${currLtp}</td>
                <td>${info.oi}</td>
                <td>${info.volume}</td>
                <td class="${tsClass}">${tsText}</td>
            `;

            tbody.appendChild(row);
        }
        // ==========================
        // UPDATE ROW
        // ==========================
        else {
            const ltpCell = row.querySelector(".ltp");

            // Price movement highlight
            if (prevLtp !== undefined) {
                if (currLtp > prevLtp) {
                    row.classList.add("price-up");
                } else if (currLtp < prevLtp) {
                    row.classList.add("price-down");
                }

                setTimeout(() => {
                    row.classList.remove("price-up", "price-down");
                }, 500);
            }

            ltpCell.textContent = currLtp;
            row.children[2].textContent = info.oi;
            row.children[3].textContent = info.volume;
            row.children[4].textContent = tsText;
            row.children[4].className = tsClass;
        }

        prevPrices[symbol] = currLtp;
    });
}

// ==========================
// Events
// ==========================
document.getElementById("indexSelect").addEventListener("change", loadExpiries);
document.getElementById("expirySelect").addEventListener("change", connectWebSocket);

// Init
loadStructure();
