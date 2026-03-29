// frontend/charts.js
let revenueChart, incomeChart, scenarioChart;

function buildCharts(model, profile) {
  const years     = model.projection_years;
  const scenarios = model.scenarios;
  const histYears = profile.revenue_dates || [];
  const histRev   = profile.revenue       || [];

  const allYears  = [...histYears, ...years];

  // Colours
  const BLUE   = "#2563eb";
  const GREEN  = "#16a34a";
  const RED    = "#dc2626";
  const MUTED  = "#6b6b68";
  const GRID   = "#e5e4e0";

    const baseOpts = {
    responsive: true,
    maintainAspectRatio: true,
    layout: {
        padding: { left: 10, right: 10, top: 10, bottom: 10 }
    },
    plugins: {
        legend: { position: "top", labels: { font: { size: 12 }, boxWidth: 14 } },
        tooltip: {
        callbacks: {
            label: ctx => `$${(ctx.raw / 1e9).toFixed(1)}B`
        }
        }
    },
    scales: {
        x: { grid: { color: GRID }, ticks: { font: { size: 11 } } },
        y: {
        grid: { color: GRID },
        ticks: { font: { size: 11 }, callback: v => `$${(v/1e9).toFixed(0)}B` }
        }
    }
    };

  // ── Revenue projection ────────────────────────────────────────────────
  const histPad  = new Array(histYears.length).fill(null);
  const projPad  = new Array(histYears.length - 1).fill(null);
  const bridgeRev = histRev[histRev.length - 1];

  revenueChart = new Chart(
    document.getElementById("chartRevenue"),
    {
      type: "line",
      data: {
        labels: allYears,
        datasets: [
          {
            label: "Historical",
            data: [...histRev, null],
            borderColor: MUTED, backgroundColor: "transparent",
            borderWidth: 2, pointRadius: 3, tension: 0.3,
          },
          {
            label: "Base case",
            data: [...projPad, bridgeRev, ...scenarios.base.revenue],
            borderColor: BLUE, backgroundColor: BLUE + "18",
            borderWidth: 2, pointRadius: 2, tension: 0.3, fill: false,
          },
          {
            label: "Upside",
            data: [...projPad, bridgeRev, ...scenarios.upside.revenue],
            borderColor: GREEN, backgroundColor: "transparent",
            borderWidth: 1.5, borderDash: [5,3], pointRadius: 2, tension: 0.3,
          },
          {
            label: "Downside",
            data: [...projPad, bridgeRev, ...scenarios.downside.revenue],
            borderColor: RED, backgroundColor: "transparent",
            borderWidth: 1.5, borderDash: [5,3], pointRadius: 2, tension: 0.3,
          },
        ]
      },
      options: baseOpts
    }
  );

  // ── Net income ────────────────────────────────────────────────────────
  const histInc    = profile.net_income || [];
  const bridgeInc  = histInc[histInc.length - 1];
  const projPadInc = new Array(histInc.length - 1).fill(null);

  incomeChart = new Chart(
    document.getElementById("chartIncome"),
    {
      type: "bar",
      data: {
        labels: allYears,
        datasets: [
          {
            label: "Historical net income",
            data: [...histInc, ...new Array(years.length).fill(null)],
            backgroundColor: MUTED + "55", borderColor: MUTED,
            borderWidth: 1,
          },
          {
            label: "Base projected income",
            data: [...new Array(histInc.length).fill(null), ...scenarios.base.net_income],
            backgroundColor: BLUE + "55", borderColor: BLUE, borderWidth: 1,
          },
        ]
      },
      options: { ...baseOpts, scales: { ...baseOpts.scales } }
    }
  );

  // ── Scenario comparison (Y5 bar) ──────────────────────────────────────
  scenarioChart = new Chart(
    document.getElementById("chartScenarios"),
    {
      type: "bar",
      data: {
        labels: ["Base case", "Upside", "Downside"],
        datasets: [{
          label: `Revenue in ${years[years.length-1]}`,
          data: [
            scenarios.base.revenue[years.length-1],
            scenarios.upside.revenue[years.length-1],
            scenarios.downside.revenue[years.length-1],
          ],
          backgroundColor: [BLUE + "88", GREEN + "88", RED + "88"],
          borderColor:     [BLUE, GREEN, RED],
          borderWidth: 1.5, borderRadius: 4,
        }]
      },
      options: {
        ...baseOpts,
        plugins: {
            legend: { display: false },
            tooltip: {
            callbacks: {
                label: ctx => `$${(ctx.raw / 1e9).toFixed(1)}B`
            }
            }
        },
        scales: {
            ...baseOpts.scales,
            y: {
            ...baseOpts.scales.y,
            min: 0,
            }
        }
    }
    }
  );
}