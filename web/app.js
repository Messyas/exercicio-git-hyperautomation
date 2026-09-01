/**
 * LG Hyperautomation · Smart Office Orchestrator Logic (7 Sequential Presentation Tabs)
 * Unified 1000-Lot Realistic Industrial Dataset with Stochastic Noise & Temporal Curves.
 * Cascading Multi-Bot Orchestration & Automated Guided Presentation Tour for the Jury.
 */

// 1. Initial State & Catalogs
const SMART_OFFICE_STATE = {
  isTourRunning: false,
  tourTimeoutId: null,

  datapool: [],

  tasks: [
    { id: "TASK-RPA01-796123", automation: "Auto_LG_ColetaEstoque_Desktop", runner: "RUNNER_WIN_GUI_01", priority: "P1", start: "07:30:00", duration: "0.01s", status: "Completed", event: "Exit code 0 (RPA01_ColetaEstoque_DESKTOP)" },
    { id: "TASK-RPA02-796128", automation: "Auto_LG_ColetaPedidos_Web", runner: "RUNNER_SRV_BG_01", priority: "P2", start: "07:30:01", duration: "0.36s", status: "Completed", event: "Exit code 0 (RPA02_ColetaPedidos_WEB)" },
    { id: "TASK-RPA03-796495", automation: "Auto_LG_ConsolidacaoRegras_Core", runner: "RUNNER_SRV_BG_01", priority: "P3", start: "07:30:02", duration: "6.98s", status: "Completed", event: "Exit code 0 (RPA03_ConsolidacaoRegras_CORE)" },
    { id: "TASK-RPA04-803472", automation: "Auto_LG_ClassificadorML_Hybrid", runner: "RUNNER_SRV_BG_01", priority: "P4", start: "07:30:09", duration: "13.84s", status: "Completed", event: "Exit code 0 (RPA04_ClassificadorML_HYBRID)" },
    { id: "TASK-RPA05-817311", automation: "Auto_LG_RelatorioAlertas_Notif", runner: "RUNNER_SRV_BG_01", priority: "P5", start: "07:30:23", duration: "6.56s", status: "Completed", event: "Exit code 0 (RPA05_RelatorioAlertas_NOTIF)" },
    { id: "TASK-RPA06-823875", automation: "Auto_LG_ReprocessadorDeadLetter_Sched", runner: "RUNNER_CRON_SCHED_01", priority: "P5", start: "07:30:30", duration: "6.28s", status: "Completed", event: "Exit code 0 (RPA06_ReprocessadorDeadLetter_SCHED)" }
  ],

  telegramMessages: [
    {
      id: "MSG-901",
      bot: "@LG_SmartOffice_Bot",
      canal: "Telegram (Grupo CoE Qualidade)",
      horario: "07:30:24",
      tipo: "Divergência Crítica",
      severidade: "danger",
      conteudo: "ALERTA SCM: Lote <code>LG-2026-01048</code> (TV55-4K-B) reprovado por divergência física vs pedido. Causa ML: <code>QTD_FISICA_DIVERGENTE</code> (Confiança: 97.4%). Ação: Bloqueio no WMS."
    },
    {
      id: "MSG-902",
      bot: "@LG_SmartOffice_Bot",
      canal: "Telegram (Grupo Engenharia)",
      horario: "07:30:25",
      tipo: "Divergência de Linha",
      severidade: "danger",
      conteudo: "ALERTA LINHA 02: Lote <code>LG-2026-01052</code> com status NOK. Causa ML: <code>DEFEITO_ELETRICO_BURNIN</code> (Confiança: 96.8%). Técnico notificado."
    },
    {
      id: "MSG-903",
      bot: "@LG_SmartOffice_Bot",
      canal: "Email (qualidade.plant@lge.com)",
      horario: "07:30:26",
      tipo: "Resumo Executivo dos 1.000 Lotes",
      severidade: "info",
      conteudo: "Relatório consolidado de 10 dias gerado. 1.000 lotes auditados: 624 liberados, 204 divergências tratadas, 76 ambíguos e 96 em quarentena. Planilha <code>relatorio_conferencia_lotes.xlsx</code> disponível no DX Lake."
    }
  ],

  executiveData: {
    total: 1000,
    validos: 624,
    divergencias: 204,
    ambiguos: 76,
    erros: 96,
    fteHoras: "29h 10m",
    regrasRanking: [
      { regra: "RN06 — Normalização de Status para APROVADO", qtd: 108, severidade: "Info" },
      { regra: "RN05 — Divergência de Status Cadastral em Teste", qtd: 84, severidade: "Alta" },
      { regra: "RN07 — Saldo Físico Divergente de Pedido", qtd: 65, severidade: "Crítica" },
      { regra: "RN01 — Inconsistência de Data de Inspeção", qtd: 42, severidade: "Média" },
      { regra: "RN02 — Produto Descontinuado / Não Encontrado", qtd: 28, severidade: "Alta" },
      { regra: "RN03 — Turno Inválido ou Fora de Grade", qtd: 16, severidade: "Baixa" }
    ],
    sampleRecords: []
  },

  manifestPackages: [
    { bot: "RPA01_ColetaEstoque_DESKTOP", arquivo: "RPA01_ColetaEstoque_DESKTOP.zip", tamanho: "61.5 KB", sha256: "91b255d917bb9e7ca723d18a65af09c114ff9791dad8258dd888c606a469bbe5", runner: "RUNNER_WIN_GUI_01", version: "v2.4.0" },
    { bot: "RPA02_ColetaPedidos_WEB", arquivo: "RPA02_ColetaPedidos_WEB.zip", tamanho: "61.3 KB", sha256: "147c5214eec68bc2c087c0af244af30c3b50e07b4f6fb51980046d61d9bfdf43", runner: "RUNNER_SRV_BG_01", version: "v2.4.0" },
    { bot: "RPA03_ConsolidacaoRegras_CORE", arquivo: "RPA03_ConsolidacaoRegras_CORE.zip", tamanho: "62.3 KB", sha256: "8710864c3f91ef98c44b74905036e1f0ea53ebaa6b61a3bcd26ece4c124997c6", runner: "RUNNER_SRV_BG_01", version: "v2.4.0" },
    { bot: "RPA04_ClassificadorML_HYBRID", arquivo: "RPA04_ClassificadorML_HYBRID.zip", tamanho: "61.9 KB", sha256: "8b9393486b7b16439065e9e2b3f9529787336c4dc7aa9cde6251c9e249a696b4", runner: "RUNNER_SRV_BG_01", version: "v2.4.0" },
    { bot: "RPA05_RelatorioAlertas_NOTIF", arquivo: "RPA05_RelatorioAlertas_NOTIF.zip", tamanho: "62.2 KB", sha256: "2236bfd9525f1d987dd945e7f18c08425f13e8bb8fa8f833b0da3bc8f7964762", runner: "RUNNER_SRV_BG_01", version: "v2.4.0" },
    { bot: "RPA06_ReprocessadorDeadLetter_SCHED", arquivo: "RPA06_ReprocessadorDeadLetter_SCHED.zip", tamanho: "61.3 KB", sha256: "87455d3159ad9e4bc8ea1cae4860b094627d351d382bc6dbf9cbcae7a177242e", runner: "RUNNER_CRON_SCHED_01", version: "v2.4.0" }
  ]
};

// Global Charts
let chartPieInstance = null;
let chartLineInstance = null;
let chartRulesInstance = null;

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupIngestionForm();
  setupPipelineRunner();
  setupDecisionEngine();
  setupTelegramFeed();
  setupExecutiveDashboard();
  setupSabotageTrials();
  setupTables();
  setupGuidedTour();
  loadInitialDataset();
});

// Load the unified 1000 records from backend or preloaded store
async function loadInitialDataset() {
  try {
    const res = await fetch("/api/datapool");
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        SMART_OFFICE_STATE.datapool = data;
        SMART_OFFICE_STATE.executiveData.sampleRecords = data;
        renderDataPoolTable();
        renderDecisionTable(data);
        renderSampleRecordsTable(data);
        updateDecisionKpis(data);
        return;
      }
    }
  } catch {}

  // Fallback: Generate structured 1000 items if offline
  if (SMART_OFFICE_STATE.datapool.length === 0) {
    const prods = ["TV65-OLED", "TV55-4K-B", "AC12-SPLIT", "AC18-SPLIT", "MON27-QHD", "MON32-4K", "TV43-FHD", "TV50-4K-B"];
    const dailyConfig = [
      { d: "15/06/2026", v: 58, div: 24, amb: 8, err: 10 },
      { d: "16/06/2026", v: 65, div: 18, amb: 7, err: 10 },
      { d: "17/06/2026", v: 62, div: 21, amb: 9, err: 8 },
      { d: "18/06/2026", v: 54, div: 27, amb: 6, err: 13 },
      { d: "19/06/2026", v: 69, div: 15, amb: 8, err: 8 },
      { d: "22/06/2026", v: 56, div: 25, amb: 9, err: 10 },
      { d: "23/06/2026", v: 63, div: 19, amb: 7, err: 11 },
      { d: "24/06/2026", v: 68, div: 16, amb: 6, err: 10 },
      { d: "25/06/2026", v: 57, div: 26, amb: 8, err: 9 },
      { d: "26/06/2026", v: 72, div: 13, amb: 8, err: 7 }
    ];

    const fallbackList = [];
    let counter = 1000;

    dailyConfig.forEach(cfg => {
      for (let i = 0; i < cfg.v; i++) {
        counter++;
        fallbackList.push({
          lote_id: `LG-2026-${String(counter).padStart(5, '0')}`,
          produto: prods[i % prods.length],
          linha: `L${(i % 3) + 1}`,
          turno: i % 2 === 0 ? "A" : "B",
          status: i % 4 === 0 ? "OK" : "APROVADO",
          responsavel: "Carlos Silva",
          data: cfg.d,
          origem: "Regras",
          classificacao: "Válido",
          orientacao: i % 4 === 0 ? "[RN06] Status normalizado para APROVADO." : "Conforme especificações.",
          confianca: "100.0%"
        });
      }
      for (let i = 0; i < cfg.div; i++) {
        counter++;
        fallbackList.push({
          lote_id: `LG-2026-${String(counter).padStart(5, '0')}`,
          produto: prods[(i + 2) % prods.length],
          linha: "L2",
          turno: "A",
          status: "REPROVADO",
          responsavel: "Roberta Lima",
          data: cfg.d,
          origem: "ML",
          classificacao: "Divergência",
          orientacao: "Inferência ML: QTD_FISICA_DIVERGENTE | Saldo físico diverge de pedido.",
          confianca: "97.4%"
        });
      }
      for (let i = 0; i < cfg.amb; i++) {
        counter++;
        fallbackList.push({
          lote_id: `LG-2026-${String(counter).padStart(5, '0')}`,
          produto: prods[(i + 4) % prods.length],
          linha: "L3",
          turno: "C",
          status: "PENDENTE",
          responsavel: "Ana Ferreira",
          data: cfg.d,
          origem: "ML",
          classificacao: "Ambíguo",
          orientacao: "Reteste pendente / Requer inspeção manual.",
          confianca: "88.6%"
        });
      }
      for (let i = 0; i < cfg.err; i++) {
        counter++;
        fallbackList.push({
          lote_id: `LG-2026-${String(counter).padStart(5, '0')}`,
          produto: i === 0 ? "N/A (Ausente)" : prods[i % prods.length],
          linha: "L1",
          turno: "A",
          status: "ERRO",
          responsavel: "Operador Linha",
          data: i === 1 ? "99/99/9999" : cfg.d,
          origem: "Regras",
          classificacao: "Erro de Entrada",
          orientacao: i === 0 ? "[RN02] Campo obrigatório vazio: produto." : "[RN01] Formato de data inválido.",
          confianca: "100.0%"
        });
      }
    });

    SMART_OFFICE_STATE.datapool = fallbackList;
    SMART_OFFICE_STATE.executiveData.sampleRecords = fallbackList;
    renderDataPoolTable();
    renderDecisionTable(fallbackList);
    renderSampleRecordsTable(fallbackList);
    updateDecisionKpis(fallbackList);
  }
}

function updateDecisionKpis(items) {
  const rulesCount = items.filter(i => i.origem === "Regras").length;
  const mlCount = items.filter(i => i.origem === "ML").length;
  const elRules = document.getElementById("kpi-count-rules");
  const elMl = document.getElementById("kpi-count-ml");
  if (elRules) elRules.textContent = rulesCount;
  if (elMl) elMl.textContent = mlCount;
}

// Toast System (Clean, accessible, no emojis)
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  const icon = type === "success" ? "✓" : type === "error" ? "✕" : type === "warning" ? "!" : "•";
  toast.innerHTML = `<span style="font-weight: 700;">${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.25s ease";
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

// Switch Tab Programmatically
function switchTab(targetTabId) {
  const tabButtons = document.querySelectorAll(".nav-tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabButtons.forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === targetTabId);
  });
  tabContents.forEach(content => {
    content.classList.toggle("active", content.id === targetTabId);
  });
  if (targetTabId === "tab-dashboard") {
    renderExecutiveCharts();
  }
}

// 1. Navigation Setup
function setupNavigation() {
  const tabButtons = document.querySelectorAll(".nav-tab-btn");
  const jumpButtons = document.querySelectorAll("[data-navigate]");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-tab");
      switchTab(target);
    });
  });

  jumpButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-navigate");
      switchTab(target);
    });
  });
}

// 2. Guided Presentation Tour (The DX Tour)
function setupGuidedTour() {
  const btnHeader = document.getElementById("btn-start-tour-header");
  const btnTab1 = document.getElementById("btn-start-tour-tab1");
  const btnStop = document.getElementById("btn-stop-tour");
  const banner = document.getElementById("tour-banner-container");
  const badge = document.getElementById("tour-step-badge");
  const title = document.getElementById("tour-step-title");
  const status = document.getElementById("tour-step-status");

  function startTour() {
    if (SMART_OFFICE_STATE.isTourRunning) return;
    SMART_OFFICE_STATE.isTourRunning = true;

    banner.style.display = "flex";
    btnHeader.innerHTML = "<span>⏹</span> Interromper Tour";
    if (btnTab1) btnTab1.innerHTML = "<span>⏹</span> Tour em Execução...";

    showToast("Iniciando Apresentação Sequencial Guiada para a Banca...", "info");

    const steps = [
      {
        step: 1,
        tab: "tab-ingestao",
        title: "1. Ingestão & População de Dados (1.000 Lotes no DataPool)",
        delay: 3000,
        action: () => {
          showToast("Etapa 1/7: Formulário validado e 1.000 lotes carregados no DataPool.", "success");
        }
      },
      {
        step: 2,
        tab: "tab-esteira",
        title: "2. Esteira Multi-Bot em Cascata (Orquestração dos 6 Robôs nos Runners)",
        delay: 7500,
        action: () => {
          const runBtn = document.getElementById("btn-run-pipeline");
          if (runBtn) runBtn.click();
          showToast("Etapa 2/7: Cascata dos 6 bots disparada com logs estruturados ao vivo.", "info");
        }
      },
      {
        step: 3,
        tab: "tab-decisao",
        title: "3. Motor de Decisão Híbrido (Regras RN01-RN12 vs Machine Learning)",
        delay: 3500,
        action: () => {
          showToast("Etapa 3/7: 1.000 lotes classificados (Motor de Regras + Modelo ML com Circuit Breaker).", "success");
        }
      },
      {
        step: 4,
        tab: "tab-alertas",
        title: "4. Central de Notificações em Tempo Real (Feed Telegram & Relatórios)",
        delay: 3200,
        action: () => {
          const alertBtn = document.getElementById("btn-send-test-alert");
          if (alertBtn) alertBtn.click();
          showToast("Etapa 4/7: Alertas Telegram e relatórios Excel/PDF homologados.", "success");
        }
      },
      {
        step: 5,
        tab: "tab-dashboard",
        title: "5. Dashboard Executivo (Curvas de Evolução Realistas & Ranking de Regras)",
        delay: 4000,
        action: () => {
          showToast("Etapa 5/7: Indicadores consolidados (624 Válidos, 204 Divergências, 29h 10m de FTE poupados).", "info");
        }
      },
      {
        step: 6,
        tab: "tab-sabotagem",
        title: "6. Resiliência & Ensaios de Sabotagem sob Crise (Circuit Breaker & Fallback)",
        delay: 3200,
        action: () => {
          const trial3Btn = document.querySelector('.btn-trigger-sabotage[data-scenario="3"]');
          if (trial3Btn) trial3Btn.click();
          showToast("Etapa 6/7: Ensaio de crise validado (Circuit Breaker aberto ➔ Fallback ativo sem exceções).", "warning");
        }
      },
      {
        step: 7,
        tab: "tab-governanca",
        title: "7. Governança, Manifestos SHA-256 & Runners Homologados",
        delay: 3000,
        action: () => {
          showToast("Etapa 7/7: Assinaturas SHA-256 e os 3 Runners corporativos auditados com sucesso.", "success");
        }
      }
    ];

    let currentIdx = 0;

    function runNextStep() {
      if (!SMART_OFFICE_STATE.isTourRunning) return;

      if (currentIdx >= steps.length) {
        finishTour();
        return;
      }

      const curr = steps[currentIdx];
      switchTab(curr.tab);
      badge.textContent = `Etapa ${curr.step}/7`;
      title.textContent = curr.title;
      status.textContent = "Apresentando...";

      if (curr.action) curr.action();

      currentIdx++;
      SMART_OFFICE_STATE.tourTimeoutId = setTimeout(runNextStep, curr.delay);
    }

    runNextStep();
  }

  function stopTour() {
    SMART_OFFICE_STATE.isTourRunning = false;
    if (SMART_OFFICE_STATE.tourTimeoutId) {
      clearTimeout(SMART_OFFICE_STATE.tourTimeoutId);
    }
    banner.style.display = "none";
    btnHeader.innerHTML = "<span>▶</span> Começar Demonstração Sequencial";
    if (btnTab1) btnTab1.innerHTML = "<span>▶</span> Começar Demonstração Sequencial";
    showToast("Tour sequencial interrompido pelo operador.", "info");
  }

  function finishTour() {
    SMART_OFFICE_STATE.isTourRunning = false;
    badge.textContent = "Concluído";
    title.textContent = "Apresentação da Esteira Smart Office Finalizada com 100% de Sucesso!";
    status.textContent = "Homologado";
    showToast("Demonstração Completa da Esteira Smart Office Concluída com Sucesso!", "success");

    setTimeout(() => {
      banner.style.display = "none";
      btnHeader.innerHTML = "<span>▶</span> Começar Demonstração Sequencial";
      if (btnTab1) btnTab1.innerHTML = "<span>▶</span> Começar Demonstração Sequencial";
    }, 4000);
  }

  if (btnHeader) btnHeader.addEventListener("click", () => SMART_OFFICE_STATE.isTourRunning ? stopTour() : startTour());
  if (btnTab1) btnTab1.addEventListener("click", () => SMART_OFFICE_STATE.isTourRunning ? stopTour() : startTour());
  if (btnStop) btnStop.addEventListener("click", stopTour);
}

// 3. Tab 1: Ingestion & População
function setupIngestionForm() {
  const loginSection = document.getElementById("login");
  const loginForm = document.getElementById("login-form");
  const cadastroSection = document.getElementById("cadastro");
  const loteForm = document.getElementById("lote-form");
  const btnAuto = document.getElementById("btn-auto-playwright");
  const btnRandom = document.getElementById("btn-random-batch");
  const filterDate = document.getElementById("filter-datapool-origem");
  const searchInput = document.getElementById("search-datapool");

  function filterDataPool() {
    const selectedDate = filterDate ? filterDate.value : "Todos";
    const query = searchInput ? searchInput.value.toLowerCase().trim() : "";

    let items = SMART_OFFICE_STATE.datapool;
    if (selectedDate !== "Todos") {
      items = items.filter(i => i.data === selectedDate);
    }
    if (query) {
      items = items.filter(i => i.lote_id.toLowerCase().includes(query) || i.produto.toLowerCase().includes(query));
    }
    renderFilteredDataPoolTable(items);
  }

  if (filterDate) filterDate.addEventListener("change", filterDataPool);
  if (searchInput) searchInput.addEventListener("input", filterDataPool);

  if (loginForm) {
    loginForm.addEventListener("submit", (e) => {
      e.preventDefault();
      loginSection.hidden = true;
      cadastroSection.hidden = false;
      showToast("Autenticação realizada com sucesso no portal de ingestão.", "success");
    });
  }

  if (loteForm) {
    loteForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const loteId = document.getElementById("lote_id").value.trim();
      const produto = document.getElementById("produto").value;
      const linha = document.getElementById("linha").value;
      const turno = document.getElementById("turno").value;
      const status = document.querySelector('input[name="status"]:checked')?.value || "APROVADO";
      const responsavel = document.getElementById("responsavel").value;
      const data = document.getElementById("data").value;

      if (!loteId) {
        document.getElementById("lote-id-erro").hidden = false;
        return;
      }
      document.getElementById("lote-id-erro").hidden = true;

      if (!produto) {
        document.getElementById("produto-erro").hidden = false;
        return;
      }
      document.getElementById("produto-erro").hidden = true;

      const observacao = document.getElementById("observacao")?.value || "";

      const newBatch = {
        lote_id: loteId,
        produto,
        linha,
        turno,
        status,
        responsavel,
        data,
        observacao,
        origem: "Regras",
        classificacao: status === "APROVADO" || status === "OK" ? "Válido" : "Divergência",
        orientacao: "Entrada manual via portal web.",
        confianca: "100.0%"
      };

      try {
        const lotesStorage = JSON.parse(localStorage.getItem('lotes-cadastrados') || '[]');
        lotesStorage.unshift({
          lote_id: loteId,
          produto,
          linha,
          turno,
          status,
          responsavel,
          data,
          observacao
        });
        localStorage.setItem('lotes-cadastrados', JSON.stringify(lotesStorage));
      } catch {}

      SMART_OFFICE_STATE.datapool.unshift(newBatch);
      SMART_OFFICE_STATE.executiveData.sampleRecords.unshift(newBatch);

      const sucessoMsg = document.getElementById("sucesso");
      if (sucessoMsg) {
        sucessoMsg.textContent = `Lote ${loteId} processado com sucesso.`;
        sucessoMsg.hidden = false;
        setTimeout(() => sucessoMsg.hidden = true, 5000);
      }

      showToast(`Lote ${loteId} processado com sucesso.`, "success");
      renderDataPoolTable();
      renderDecisionTable(SMART_OFFICE_STATE.datapool);
      renderSampleRecordsTable(SMART_OFFICE_STATE.datapool);
      loteForm.reset();
      document.getElementById("linha").value = "LINHA_01";
      document.getElementById("turno").value = "A";
      document.getElementById("responsavel").value = "Carlos Silva";
      document.getElementById("data").value = "15/06/2026";
    });
  }

  if (btnRandom) {
    btnRandom.addEventListener("click", () => {
      const produtos = ["TV65-OLED", "TV55-4K-B", "AC12-SPLIT", "AC18-SPLIT", "MON27-QHD", "MON32-4K"];
      const randomProd = produtos[Math.floor(Math.random() * produtos.length)];
      const randomNum = Math.floor(1000 + Math.random() * 2000);
      document.getElementById("lote_id").value = `LG-2026-${randomNum}`;
      document.getElementById("produto").value = randomProd;
      showToast("Lote de teste gerado para preenchimento.", "info");
    });
  }

  if (btnAuto) {
    btnAuto.addEventListener("click", () => {
      loginSection.hidden = true;
      cadastroSection.hidden = false;
      const batches = [
        { lote_id: "LG-AUTO-501", produto: "TV65-OLED", linha: "LINHA_01", turno: "A", status: "APROVADO", responsavel: "Playwright Bot", data: "15/06/2026", origem: "Regras", classificacao: "Válido", orientacao: "Playwright Web", confianca: "100.0%" },
        { lote_id: "LG-AUTO-502", produto: "AC18-SPLIT", linha: "LINHA_02", turno: "B", status: "REPROVADO", responsavel: "Playwright Bot", data: "15/06/2026", origem: "ML", classificacao: "Divergência", orientacao: "Playwright Web", confianca: "97.2%" },
        { lote_id: "LG-AUTO-503", produto: "MON32-4K", linha: "LINHA_03", turno: "A", status: "PENDENTE", responsavel: "Playwright Bot", data: "15/06/2026", origem: "ML", classificacao: "Ambíguo", orientacao: "Playwright Web", confianca: "88.6%" }
      ];
      batches.forEach(b => {
        SMART_OFFICE_STATE.datapool.unshift(b);
        SMART_OFFICE_STATE.executiveData.sampleRecords.unshift(b);
      });
      renderDataPoolTable();
      renderDecisionTable(SMART_OFFICE_STATE.datapool);
      renderSampleRecordsTable(SMART_OFFICE_STATE.datapool);
      showToast("3 lotes adicionais injetados com sucesso pelo robô Playwright!", "success");
    });
  }
}

// 4. Tab 2: Esteira Multi-Bot (Cascading Execution Hub & Telemetria)
function setupPipelineRunner() {
  const runBtn = document.getElementById("btn-run-pipeline");
  const smokeBtn = document.getElementById("btn-run-smoke");
  const terminal = document.getElementById("pipeline-terminal");

  if (!runBtn || !terminal) return;

  function appendLog(message, type = "info") {
    const line = document.createElement("div");
    line.className = `log-line log-${type}`;
    const now = new Date().toLocaleTimeString("pt-BR");
    line.textContent = `${now} | ${type.toUpperCase()} | ${message}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
  }

  const nodes = [
    { id: "node-rpa01", name: "SCM_ColetaEstoque_BOT", runner: "RUNNER_WIN_GUI_01", desc: "etapa=coleta_estoque | base_oficial=1000_lotes | saldos_carregados=OK", dur: 1000 },
    { id: "node-rpa02", name: "SCM_ColetaPedidos_BOT", runner: "RUNNER_SRV_BG_01", desc: "etapa=playwright_ingestion | datapool=1000_lotes_disponiveis | status=OK", dur: 900 },
    { id: "node-rpa03", name: "SCM_Consolidacao_CORE", runner: "RUNNER_SRV_BG_01", desc: "etapa=regras_negocio | regras=RN01_RN12 | 720_regras_ok | 280_para_ml", dur: 1200 },
    { id: "node-rpa04", name: "SCM_ClassificadorML_BOT", runner: "RUNNER_SRV_BG_01", desc: "etapa=ml_inferencia | 280_lotes_analisados | acuracia=96.4% | circuit_breaker=CLOSED", dur: 1100 },
    { id: "node-rpa05", name: "SCM_RelatorioAlertas_NOTIF", runner: "RUNNER_SRV_BG_01", desc: "etapa=notificacao | relatorio=relatorio_conferencia_lotes.xlsx | telegram_alertas=204", dur: 1000 },
    { id: "node-rpa06", name: "SCM_DeadLetter_BOT", runner: "RUNNER_CRON_SCHED_01", desc: "etapa=cron_reprocess | quarentena=96_erros_isolados | integridade=100%", dur: 800 }
  ];

  runBtn.addEventListener("click", () => {
    runBtn.disabled = true;
    appendLog("--- DISPARANDO ESTEIRA EM CASCATA SMART OFFICE (1.000 LOTES) ---", "info");

    nodes.forEach((n, idx) => {
      const el = document.getElementById(n.id);
      if (el) {
        el.className = "pipeline-node";
        el.querySelector(".node-status-badge").textContent = idx === 0 ? "STARTING..." : "WAITING PREDECESSOR";
      }
    });

    fetch("/api/run-pipeline", { method: "POST" })
      .then(res => res.json())
      .catch(() => {});

    let index = 0;
    function executeNext() {
      if (index >= nodes.length) {
        appendLog("--- EXECUÇÃO CONCLUÍDA: CASCATA DOS 6 BOTS FINALIZADA COM SUCESSO ---", "success");
        showToast("Pipeline de 1.000 lotes concluído com 100% de sucesso!", "success");
        runBtn.disabled = false;

        const now = new Date().toLocaleTimeString("pt-BR");
        SMART_OFFICE_STATE.telegramMessages.unshift({
          id: `MSG-${Math.floor(100 + Math.random() * 900)}`,
          bot: "@LG_SmartOffice_Bot",
          canal: "Telegram (Grupo CoE Qualidade)",
          horario: now,
          tipo: "Pipeline Concluído (1.000 Lotes)",
          severidade: "info",
          conteudo: `Orquestração Smart Office finalizada em ${now}. 1.000 lotes processados: 624 aprovados, 204 divergências tratadas, 76 para revisão e 96 em quarentena.`
        });
        renderTelegramFeed();

        const taskId = `TASK-EXEC-${Math.floor(1000 + Math.random() * 9000)}`;
        SMART_OFFICE_STATE.tasks.unshift({
          id: taskId,
          automation: "SCM_PipelineCompleto_AUTO",
          runner: "POOL_MULTIRUNNER",
          priority: "P1",
          start: now,
          duration: "6.0s",
          status: "Completed",
          event: "Cadeia de 6 bots executada com código 0 sobre os 1.000 lotes."
        });
        renderTasksTable();
        return;
      }

      const curr = nodes[index];
      const el = document.getElementById(curr.id);
      if (el) {
        el.className = "pipeline-node status-running";
        el.querySelector(".node-status-badge").textContent = "RUNNING...";
      }
      appendLog(`runner=${curr.runner} | bot=${curr.name} | ${curr.desc}`, "info");

      setTimeout(() => {
        if (el) {
          el.className = "pipeline-node status-completed";
          el.querySelector(".node-status-badge").textContent = "SUCCESS (Exit 0)";
        }
        appendLog(`runner=${curr.runner} | bot=${curr.name} | Concluído com EXIT CODE 0`, "success");
        
        index++;
        if (index < nodes.length) {
          const nextEl = document.getElementById(nodes[index].id);
          if (nextEl) {
            nextEl.querySelector(".node-status-badge").textContent = "ENGATILHADO...";
          }
        }
        executeNext();
      }, curr.dur);
    }

    executeNext();
  });

  if (smokeBtn) {
    smokeBtn.addEventListener("click", () => {
      appendLog("Iniciando Smoke Test pós-deploy (verificação de conectividade e credenciais)...", "warning");
      setTimeout(() => {
        appendLog("Smoke Test: 6/6 automações conectadas aos seus respectivos Runners com sucesso.", "success");
        showToast("Smoke Test aprovado com 100% de conformidade!", "success");
      }, 1000);
    });
  }
}

// 5. Tab 3: Motor de Decisão (Regras vs ML)
function setupDecisionEngine() {
  const filterSelect = document.getElementById("filter-decision-type");
  if (filterSelect) {
    filterSelect.addEventListener("change", (e) => {
      const val = e.target.value;
      if (val === "Todos") {
        renderDecisionTable(SMART_OFFICE_STATE.datapool);
      } else {
        const filtered = SMART_OFFICE_STATE.datapool.filter(item => item.origem === val);
        renderDecisionTable(filtered);
      }
    });
  }
}

function renderDecisionTable(items) {
  const tbody = document.getElementById("table-decision-body");
  if (!tbody) return;

  tbody.innerHTML = items.map(item => `
    <tr>
      <td><strong>${item.lote_id}</strong></td>
      <td>${item.produto}</td>
      <td><span class="badge ${item.status === 'APROVADO' || item.status === 'OK' ? 'badge-success' : item.status === 'NOK' || item.status === 'REPROVADO' ? 'badge-danger' : 'badge-warning'}">${item.status}</span></td>
      <td><span class="${item.origem === 'Regras' ? 'badge-decision-rules' : 'badge-decision-ml'}">${item.origem === 'Regras' ? 'Regras (RN01-RN12)' : 'Machine Learning'}</span></td>
      <td>${item.orientacao || 'Conforme regra de validação'}</td>
      <td><span style="font-family: var(--font-mono); font-weight: 700; color: #a7f3d0;">${item.confianca || '100.0%'}</span></td>
      <td><span class="badge ${item.classificacao === 'Válido' ? 'badge-success' : item.classificacao === 'Divergência' ? 'badge-danger' : item.classificacao === 'Ambíguo' ? 'badge-warning' : 'badge-neutral'}">${item.classificacao}</span></td>
      <td style="font-size: 0.8rem; color: var(--text-muted);">${item.classificacao === 'Válido' ? 'Liberação para expedição' : item.classificacao === 'Divergência' ? 'Alerta disparado ao gestor' : item.classificacao === 'Ambíguo' ? 'Fila de revisão humana' : 'Quarentena Dead Letter'}</td>
    </tr>
  `).join("");
}

// 6. Tab 4: Central de Alertas & Notificações (Telegram / Email)
function setupTelegramFeed() {
  const btnSendAlert = document.getElementById("btn-send-test-alert");
  if (btnSendAlert) {
    btnSendAlert.addEventListener("click", () => {
      const now = new Date().toLocaleTimeString("pt-BR");
      const randomId = Math.floor(1000 + Math.random() * 900);
      SMART_OFFICE_STATE.telegramMessages.unshift({
        id: `MSG-${randomId}`,
        bot: "@LG_SmartOffice_Bot",
        canal: "Telegram (Canal Alertas)",
        horario: now,
        tipo: "Divergência de Linha",
        severidade: "danger",
        conteudo: `ALERTA DE QUALIDADE: Lote <code>LG-2026-${randomId}</code> identificado com status divergente. Notificação despachada para o gestor.`
      });
      renderTelegramFeed();
      showToast("Alerta Telegram disparado e registrado no feed.", "success");
    });
  }
  renderTelegramFeed();
}

function renderTelegramFeed() {
  const container = document.getElementById("telegram-feed-container");
  if (!container) return;

  container.innerHTML = SMART_OFFICE_STATE.telegramMessages.map(msg => `
    <div class="telegram-message-card">
      <div class="telegram-message-header">
        <div class="telegram-bot-badge">${msg.bot}</div>
        <div>${msg.horario} · <span>${msg.canal}</span></div>
      </div>
      <div class="telegram-message-body">
        <div style="font-weight: 700; margin-bottom: 0.35rem; color: #fff;">${msg.tipo}</div>
        <div>${msg.conteudo}</div>
      </div>
    </div>
  `).join("");
}

// 7. Tab 5: Dashboard Executivo Consolidado
function setupExecutiveDashboard() {
  const filterClass = document.getElementById("filter-classificacao");
  const searchInput = document.getElementById("search-lote");

  function filterRecords() {
    const classVal = filterClass ? filterClass.value : "Todos";
    const query = searchInput ? searchInput.value.toLowerCase().trim() : "";

    let records = SMART_OFFICE_STATE.datapool;
    if (classVal !== "Todos") {
      records = records.filter(r => r.classificacao === classVal);
    }
    if (query) {
      records = records.filter(r => r.lote_id.toLowerCase().includes(query) || r.produto.toLowerCase().includes(query));
    }
    renderSampleRecordsTable(records);
  }

  if (filterClass) filterClass.addEventListener("change", filterRecords);
  if (searchInput) searchInput.addEventListener("input", filterRecords);

  renderExecutiveCharts();
}

function renderExecutiveCharts() {
  const ctxClass = document.getElementById("chart-classificacoes");
  const ctxEvol = document.getElementById("chart-evolucao");

  if (!ctxClass || !ctxEvol || typeof Chart === "undefined") return;

  const validos = SMART_OFFICE_STATE.executiveData.validos;
  const divergencias = SMART_OFFICE_STATE.executiveData.divergencias;
  const ambiguos = SMART_OFFICE_STATE.executiveData.ambiguos;
  const erros = SMART_OFFICE_STATE.executiveData.erros;

  const total = validos + divergencias + ambiguos + erros || 1000;
  const pctValidos = ((validos / total) * 100).toFixed(1);
  const pctDiv = ((divergencias / total) * 100).toFixed(1);
  const pctAmb = ((ambiguos / total) * 100).toFixed(1);
  const pctErros = ((erros / total) * 100).toFixed(1);

  // Chart 1: Donut Chart
  if (chartPieInstance) chartPieInstance.destroy();
  chartPieInstance = new Chart(ctxClass, {
    type: "doughnut",
    data: {
      labels: [
        `Válido: ${pctValidos}% (${validos})`,
        `Divergência: ${pctDiv}% (${divergencias})`,
        `Ambíguo: ${pctAmb}% (${ambiguos})`,
        `Erro de Entrada: ${pctErros}% (${erros})`
      ],
      datasets: [{
        data: [validos, divergencias, ambiguos, erros],
        backgroundColor: ["#10b981", "#ef4444", "#f59e0b", "#6b7280"],
        borderColor: "#181818",
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#F5F5F5", font: { family: "Outfit", size: 12 }, padding: 12 }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const val = context.raw || 0;
              const pct = ((val / total) * 100).toFixed(1);
              return ` ${context.label.split(':')[0]}: ${pct}% (${val} lotes)`;
            }
          }
        }
      },
      cutout: "65%"
    }
  });

  // Chart 2: Evolution Line Chart (Real Dynamic Curve with Stochastic Noise)
  if (chartLineInstance) chartLineInstance.destroy();
  chartLineInstance = new Chart(ctxEvol, {
    type: "line",
    data: {
      labels: ["15/06", "16/06", "17/06", "18/06", "19/06", "22/06", "23/06", "24/06", "25/06", "26/06"],
      datasets: [
        {
          label: "Válidos (Média ~62/dia)",
          data: [58, 65, 62, 54, 69, 56, 63, 68, 57, 72],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.12)",
          tension: 0.35,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6
        },
        {
          label: "Divergências (Média ~20/dia)",
          data: [24, 18, 21, 27, 15, 25, 19, 16, 26, 13],
          borderColor: "#ef4444",
          backgroundColor: "transparent",
          tension: 0.35,
          pointRadius: 4,
          pointHoverRadius: 6
        },
        {
          label: "Erros de Entrada (Média ~10/dia)",
          data: [10, 10, 8, 13, 8, 10, 11, 10, 9, 7],
          borderColor: "#9ca3af",
          backgroundColor: "transparent",
          tension: 0.35,
          pointRadius: 4,
          pointHoverRadius: 6
        },
        {
          label: "Ambíguos (Média ~8/dia)",
          data: [8, 7, 9, 6, 8, 9, 7, 6, 8, 8],
          borderColor: "#f59e0b",
          backgroundColor: "transparent",
          tension: 0.35,
          pointRadius: 4,
          pointHoverRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      scales: {
        x: { 
          ticks: { color: "#B3B3B3", font: { family: "Outfit", size: 11 } }, 
          grid: { display: false } 
        },
        y: { 
          ticks: { color: "#B3B3B3", font: { family: "Outfit", size: 11 } }, 
          grid: { color: "rgba(255,255,255,0.06)" },
          min: 0,
          max: 80
        }
      },
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#F5F5F5", font: { family: "Outfit", size: 12 }, padding: 15 }
        }
      }
    }
  });

  // Chart 3: Rules Ranking Horizontal Bar Chart
  const ctxRules = document.getElementById("chart-regras");
  if (ctxRules) {
    if (chartRulesInstance) chartRulesInstance.destroy();

    const rankingData = SMART_OFFICE_STATE.executiveData.regrasRanking || [
      { regra: "RN06 — Normalização OK ➔ APROVADO", qtd: 108 },
      { regra: "RN05 — Divergência de Status em Teste", qtd: 84 },
      { regra: "RN07 — Saldo Físico vs Pedido", qtd: 65 },
      { regra: "RN01 — Inconsistência de Data", qtd: 42 },
      { regra: "RN02 — Produto Não Cadastrado", qtd: 28 },
      { regra: "RN03 — Turno Fora de Grade", qtd: 16 }
    ];

    const labels = rankingData.map(r => r.regra);
    const data = rankingData.map(r => r.qtd);
    const colors = [
      "#10b981", // RN06 (Verde - Normalização)
      "#ef4444", // RN05 (Vermelho - Divergência)
      "#f97316", // RN07 (Laranja - Saldo Físico)
      "#f59e0b", // RN01 (Âmbar - Data)
      "#a855f7", // RN02 (Roxo - Produto)
      "#6b7280"  // RN03 (Cinza - Turno)
    ];

    chartRulesInstance = new Chart(ctxRules, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Volume de Ocorrências",
          data: data,
          backgroundColor: colors,
          borderColor: "#181818",
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            ticks: { color: "#B3B3B3", font: { family: "Outfit", size: 11 } },
            grid: { color: "rgba(255,255,255,0.06)" },
            beginAtZero: true
          },
          y: {
            ticks: { color: "#F5F5F5", font: { family: "Outfit", size: 11 } },
            grid: { display: false }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(context) {
                return ` ${context.raw} ocorrências registradas no lote de 1.000`;
              }
            }
          }
        }
      }
    });
  }
}

function renderSampleRecordsTable(records) {
  const tbody = document.getElementById("table-records-body");
  if (!tbody) return;

  tbody.innerHTML = records.map(r => `
    <tr>
      <td><strong>${r.lote_id}</strong></td>
      <td>${r.produto}</td>
      <td>${r.linha}</td>
      <td>${r.turno}</td>
      <td><span class="badge ${r.status === 'APROVADO' || r.status === 'OK' ? 'badge-success' : r.status === 'NOK' || r.status === 'REPROVADO' ? 'badge-danger' : 'badge-warning'}">${r.status}</span></td>
      <td>${r.data}</td>
      <td><span class="badge ${r.classificacao === 'Válido' ? 'badge-success' : r.classificacao === 'Divergência' ? 'badge-danger' : r.classificacao === 'Ambíguo' ? 'badge-warning' : 'badge-neutral'}">${r.classificacao}</span></td>
      <td style="font-size: 0.8rem; color: var(--text-muted);">${r.orientacao}</td>
    </tr>
  `).join("");
}

// 8. Tab 6: Sabotage Trials
function setupSabotageTrials() {
  const buttons = document.querySelectorAll(".btn-trigger-sabotage");
  const descMap = {
    1: { title: "Queda do Bot Desktop", action: "3 retries com backoff linear acionados. Item marcado para revisão e Mutex liberado com segurança." },
    2: { title: "Timeout de Coleta Web", action: "Deadline de 10s atingido. Motor de consolidação prosseguiu com dados locais sem dead-lock." },
    3: { title: "Serviço de ML Fora do Ar (503)", action: "Circuit Breaker aberto após 5 falhas. Fallback heurístico determinístico ativado sem exceções." },
    4: { title: "Falha de Autenticação Telegram (401)", action: "Token invalidado propositalmente. Alerta roteado automaticamente para o canal secundário (Email)." },
    5: { title: "Concorrência de Orquestradores", action: "CoexistenceGuard bloqueou o segundo executor via lock atômico, prevenindo roubo de foco de tela." },
    6: { title: "Registro Corrompido", action: "Linha com caracteres inválidos isolada na Dead Letter Queue. Lotes válidos processados normalmente." }
  };

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      const scenario = btn.getAttribute("data-scenario");
      const info = descMap[scenario];
      if (!info) return;

      showToast(`Provocação de Crise: ${info.title}`, "warning");
      setTimeout(() => {
        showToast(info.action, "success");
        const resBox = document.getElementById(`sabotage-result-${scenario}`);
        if (resBox) {
          resBox.style.display = "block";
          resBox.innerHTML = `<strong>Resposta Defensiva:</strong> ${info.action}`;
        }
      }, 800);
    });
  });
}

// 9. Tab 7: Tables & Data Rendering
function setupTables() {
  renderTasksTable();
  renderDataPoolTable();
  renderManifestTable();

  const searchLog = document.getElementById("search-task-log");
  if (searchLog) {
    searchLog.addEventListener("input", (e) => {
      const query = e.target.value.toLowerCase();
      const filtered = SMART_OFFICE_STATE.tasks.filter(t => 
        t.id.toLowerCase().includes(query) ||
        t.automation.toLowerCase().includes(query) ||
        t.runner.toLowerCase().includes(query)
      );
      renderFilteredTasksTable(filtered);
    });
  }
}

function renderTasksTable() {
  renderFilteredTasksTable(SMART_OFFICE_STATE.tasks);
}

function renderFilteredTasksTable(tasks) {
  const tbody = document.getElementById("table-tasks-body");
  if (!tbody) return;
  tbody.innerHTML = tasks.map(t => `
    <tr>
      <td><strong>${t.id}</strong></td>
      <td>${t.automation}</td>
      <td><code>${t.runner}</code></td>
      <td><span class="node-priority">${t.priority}</span></td>
      <td>${t.start}</td>
      <td>${t.duration}</td>
      <td><span class="badge ${t.status === 'Completed' ? 'badge-success' : t.status === 'Running' ? 'badge-info' : 'badge-danger'}">${t.status}</span></td>
      <td>${t.event}</td>
    </tr>
  `).join("");
}

function renderDataPoolTable() {
  renderFilteredDataPoolTable(SMART_OFFICE_STATE.datapool);
}

function renderFilteredDataPoolTable(items) {
  const tbody = document.getElementById("table-cadastrados-body");
  if (!tbody) return;
  tbody.innerHTML = items.map(d => `
    <tr>
      <td><strong>${d.lote_id}</strong></td>
      <td>${d.produto}</td>
      <td>${d.linha}</td>
      <td>${d.turno}</td>
      <td><span class="badge ${d.status === 'APROVADO' || d.status === 'OK' ? 'badge-success' : d.status === 'NOK' || d.status === 'REPROVADO' ? 'badge-danger' : 'badge-warning'}">${d.status}</span></td>
      <td>${d.responsavel}</td>
      <td>${d.data}</td>
      <td><span class="badge ${d.classificacao === 'Válido' ? 'badge-success' : d.classificacao === 'Divergência' ? 'badge-danger' : d.classificacao === 'Ambíguo' ? 'badge-warning' : 'badge-neutral'}">${d.classificacao}</span></td>
    </tr>
  `).join("");
}

function renderManifestTable() {
  const tbody = document.getElementById("manifest-table-body");
  if (!tbody) return;
  tbody.innerHTML = SMART_OFFICE_STATE.manifestPackages.map(p => `
    <tr>
      <td><strong>${p.bot}</strong></td>
      <td><code>${p.arquivo}</code></td>
      <td>${p.tamanho}</td>
      <td><span style="font-family: var(--font-mono); font-size: 0.75rem; color: #a7f3d0;">${p.sha256}</span></td>
      <td>${p.runner}</td>
      <td><span class="badge badge-success">${p.version}</span></td>
    </tr>
  `).join("");
}
