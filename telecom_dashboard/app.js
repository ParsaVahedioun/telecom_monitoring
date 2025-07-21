const API_BASE = "http://127.0.0.1:8000/api";
let chart;

window.addEventListener("DOMContentLoaded", () => {
  loadUsers();
  document.getElementById("rangeSelect").addEventListener("change", toggleCustomRange);
});

async function loadUsers() {
  const res = await fetch(`${API_BASE}/users`);
  const data = await res.json();

  if (!Array.isArray(data)) {
    console.error("❌ API response is not an array:", data);
    return;
  }

  const select = document.getElementById("userSelect");
  select.innerHTML = '<option value="">انتخاب کنید</option>';
  data.forEach(user => {
    const option = document.createElement("option");
    option.value = user.id;
    option.textContent = `${user.name} (${user.ip_address})`;
    select.appendChild(option);
  });
}

function toggleCustomRange() {
  const val = document.getElementById("rangeSelect").value;
  document.getElementById("customFromDiv").style.display = val === "custom" ? "block" : "none";
}

async function fetchLogs() {
  const userId = document.getElementById("userSelect").value;
  const range = document.getElementById("rangeSelect").value;
  let fromTime = "";

  if (!userId) return alert("لطفاً کاربر را انتخاب کنید.");

  if (range === "custom") {
    fromTime = document.getElementById("fromDate").value;
  } else {
    const now = new Date();
    let diffMs = {
      "1h": 3600000,
      "24h": 86400000,
      "7d": 604800000,
      "30d": 2592000000,
    }[range];
    const fromDate = new Date(now - diffMs);
    fromTime = fromDate.toISOString();
  }

  const url = new URL(`${API_BASE}/users/${userId}/traffic`);
  // در تابع fetchLogs
  url.searchParams.append("from", fromTime);
  url.searchParams.append("to", new Date().toISOString()); // اضافه کردن پارامتر to
  const res = await fetch(url);
  const logs = await res.json();

  updateTable(logs);
  updateChart(logs);
}

function updateTable(logs) {
  const table = document.getElementById("logTable");
  table.innerHTML = "";
  if (logs.length === 0) {
    table.innerHTML = '<tr><td colspan="4" class="text-center">داده‌ای یافت نشد.</td></tr>';
    return;
  }

  logs.forEach(log => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${new Date(log.timestamp).toLocaleString("fa-IR")}</td>
      <td>${log.interface_name}</td>
      <td>${log.rx_bytes.toLocaleString()}</td>
      <td>${log.tx_bytes.toLocaleString()}</td>
    `;
    table.appendChild(row);
  });
}

function updateChart(logs) {
  const ctx = document.getElementById("usageChart").getContext("2d");
  const labels = logs.map(log => new Date(log.timestamp).toLocaleTimeString("fa-IR"));
  const rxData = logs.map(log => log.rx_bytes);
  const txData = logs.map(log => log.tx_bytes);

  if (chart) chart.destroy();

  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: '⬇ RX',
          data: rxData,
          borderColor: 'rgb(54, 162, 235)',
          tension: 0.4,
          fill: false
        },
        {
          label: '⬆ TX',
          data: txData,
          borderColor: 'rgb(255, 99, 132)',
          tension: 0.4,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        title: { display: true, text: 'نمودار مصرف داده' }
      },
      interaction: {
        intersect: false,
        mode: 'index',
      },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'بایت (Bytes)' }
        },
        x: {
          title: { display: true, text: 'زمان' }
        }
      }
    }
  });
}

async function addUser(e) {
  e.preventDefault();

  const name = document.getElementById("newName").value.trim();
  const ip = document.getElementById("newIP").value.trim();
  if (!name || !ip) return;

  const res = await fetch(`${API_BASE}/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, ip_address: ip })
  });

  if (res.ok) {
    alert("✅ کاربر با موفقیت اضافه شد");
    loadUsers();
    document.getElementById("newName").value = "";
    document.getElementById("newIP").value = "";
  } else {
    const err = await res.json();
    alert(`❌ خطا: ${err.detail || "افزودن ناموفق بود"}`);
  }
}
