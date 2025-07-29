document
  .getElementById("fightForm")
  ?.addEventListener("submit", async function (e) {
    e.preventDefault();
    const fighterA = document.getElementById("fighter_a").value;
    const fighterB = document.getElementById("fighter_b").value;
    const loadingDiv = document.getElementById("loading");
    const resultDiv = document.getElementById("result");
    if (fighterA === fighterB) {
      resultDiv.innerHTML = `<div class="result-card"><p>Pilih fighter beda bro!</p></div>`;
      return;
    }
    loadingDiv.style.display = "block";
    resultDiv.innerHTML = "";
    try {
      const response = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `fighter_a=${encodeURIComponent(
          fighterA
        )}&fighter_b=${encodeURIComponent(fighterB)}`,
      });
      const data = await response.json();
      loadingDiv.style.display = "none";
      if (response.ok) {
        const reasons = data.reason.split(". ").filter((r) => r);
        resultDiv.innerHTML = `
                <div class="result-card">
                    <h3>Winner: ${data.winner}</h3>
                    <p>${
                      data.fighter_a.name
                    }: Score=${data.fighter_a.score.toFixed(2)}${
          data.fighter_a.record ? `, Record=${data.fighter_a.record}` : ""
        }</p>
                    <p>${
                      data.fighter_b.name
                    }: Score=${data.fighter_b.score.toFixed(2)}${
          data.fighter_b.record ? `, Record=${data.fighter_b.record}` : ""
        }</p>
                    ${
                      reasons.length
                        ? `<h3>Alasan:</h3><ul>${reasons
                            .map((r) => `<li>${r}</li>`)
                            .join("")}</ul>`
                        : ""
                    }
                </div>
            `;
      } else {
        resultDiv.innerHTML = `<div class="result-card"><p>${
          data.error || "Error bro, coba lagi!"
        }</p></div>`;
      }
    } catch (error) {
      loadingDiv.style.display = "none";
      resultDiv.innerHTML = `<div class="result-card"><p>Error bro, cek koneksi!</p></div>`;
      console.error("Fetch error:", error);
    }
  });
document
  .getElementById("refreshBtn")
  ?.addEventListener("click", async function () {
    const loadingDiv = document.getElementById("loading");
    const resultDiv = document.getElementById("result");
    loadingDiv.style.display = "block";
    resultDiv.innerHTML = "";
    try {
      const response = await fetch("/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      const data = await response.json();
      loadingDiv.style.display = "none";
      if (data.status === "success") {
        const selectA = document.getElementById("fighter_a");
        const selectB = document.getElementById("fighter_b");
        selectA.innerHTML = `<option value="">-- Pilih Fighter --</option>${data.fighters
          .map((f) => `<option value="${f}">${f}</option>`)
          .join("")}`;
        selectB.innerHTML = `<option value="">-- Pilih Fighter --</option>${data.fighters
          .map((f) => `<option value="${f}">${f}</option>`)
          .join("")}`;
        document.querySelector(
          ".info"
        ).textContent = `Loaded ${data.fighters.length} fighters | Last updated: ${data.last_updated}`;
        resultDiv.innerHTML = `<div class="result-card"><p>Data fighter udah di-refresh, bro!</p></div>`;
      } else {
        resultDiv.innerHTML = `<div class="result-card"><p>${
          data.message || "Gagal refresh data, bro!"
        }</p></div>`;
      }
    } catch (error) {
      loadingDiv.style.display = "none";
      resultDiv.innerHTML = `<div class="result-card"><p>Error bro, cek koneksi!</p></div>`;
      console.error("Refresh error:", error);
    }
  });
