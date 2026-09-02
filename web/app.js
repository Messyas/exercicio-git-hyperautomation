/**
 * LG Hyperautomation · Smart Office Orchestrator Logic (7 Sequential Presentation Tabs)
 * Unified 1000-Lot Realistic Industrial Dataset with Stochastic Noise & Temporal Curves.
 * Cascading Multi-Bot Orchestration & Automated Guided Presentation Tour for the Jury.
 */

// 1. Initial State & Catalogs
const SMART_OFFICE_STATE = {
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

// Pagination State (Frontend 10-item paging for all tables)
const TABLE_PAGINATION = {
  datapool: { page: 1, pageSize: 10 },
  tasks: { page: 1, pageSize: 10 },
  decision: { page: 1, pageSize: 10 },
  records: { page: 1, pageSize: 10 },
  excel: { page: 1, pageSize: 10 }
};

function renderPaginationBar(containerId, totalItems, currentPage, pageSize, onPageChange) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!totalItems || totalItems === 0) {
    container.style.display = "none";
    return;
  }
  container.style.display = "flex";

  const totalPages = Math.ceil(totalItems / pageSize) || 1;
  const validPage = Math.min(Math.max(1, currentPage), totalPages);

  const start = (validPage - 1) * pageSize + 1;
  const end = Math.min(validPage * pageSize, totalItems);

  container.innerHTML = `
    <div class="pagination-info">
      Exibindo <strong>${start.toLocaleString("pt-BR")}</strong>–<strong>${end.toLocaleString("pt-BR")}</strong> de <strong>${totalItems.toLocaleString("pt-BR")}</strong> itens
    </div>
    <div class="pagination-controls">
      <button type="button" class="pagination-btn btn-prev" ${validPage <= 1 ? "disabled" : ""}>Anterior</button>
      <span class="pagination-page-indicator">Página ${validPage} de ${totalPages}</span>
      <button type="button" class="pagination-btn btn-next" ${validPage >= totalPages ? "disabled" : ""}>Próxima</button>
    </div>
  `;

  const btnPrev = container.querySelector(".btn-prev");
  const btnNext = container.querySelector(".btn-next");

  if (btnPrev && validPage > 1) {
    btnPrev.addEventListener("click", (e) => {
      e.preventDefault();
      onPageChange(validPage - 1);
    });
  }
  if (btnNext && validPage < totalPages) {
    btnNext.addEventListener("click", (e) => {
      e.preventDefault();
      onPageChange(validPage + 1);
    });
  }
}

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupIngestionForm();
  setupDesktopGuiControls();
  setupPipelineRunner();
  setupDecisionEngine();
  setupTelegramFeed();
  setupExecutiveDashboard();
  setupSabotageTrials();
  setupTables();
  setupReportModal();
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
        SMART_OFFICE_STATE.officialDatapool = [...data];
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
    SMART_OFFICE_STATE.officialDatapool = [...fallbackList];
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

// 2. Tab 1: Ingestion & População
// 2. Tab 1: Ingestion & População (Playwright Live Simulator & DataPool)
let isBotIngesting = false;

async function simulateRobotIngestionStepByStep() {
  if (isBotIngesting) {
    showToast("Robô Playwright já está executando a ingestão!", "warning");
    return;
  }
  isBotIngesting = true;

  const botPanel = document.getElementById("bot-sim-panel");
  const botBadge = document.getElementById("bot-status-badge");
  const btnAuto = document.getElementById("btn-auto-playwright");
  const btnAutoInner = document.getElementById("btn-auto-playwright-inner");
  const loginSection = document.getElementById("login");
  const cadastroSection = document.getElementById("cadastro");

  if (btnAuto) btnAuto.disabled = true;
  if (btnAutoInner) btnAutoInner.disabled = true;

  if (botPanel) botPanel.classList.add("bot-active");
  if (botBadge) {
    botBadge.className = "badge bot-badge-running";
    botBadge.textContent = "AUTENTICANDO...";
  }

  const terminal = document.getElementById("pipeline-terminal");
  function appendTerminalLog(msg, type = "info") {
    if (!terminal) return;
    const line = document.createElement("div");
    line.className = `log-line log-${type}`;
    const now = new Date().toLocaleTimeString("pt-BR");
    line.textContent = `${now} | ${type.toUpperCase()} | ${msg}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
  }

  // Auto login if on login screen
  if (loginSection && !loginSection.hidden) {
    appendTerminalLog("[RPA02 · Playwright] Navegando para tela de login e inserindo credenciais...", "info");
    const userInp = document.getElementById("login-usuario");
    const passInp = document.getElementById("login-senha");
    if (userInp) {
      userInp.classList.add("bot-typing-focus");
      await new Promise(r => setTimeout(r, 120));
      userInp.classList.remove("bot-typing-focus");
    }
    if (passInp) {
      passInp.classList.add("bot-typing-focus");
      await new Promise(r => setTimeout(r, 120));
      passInp.classList.remove("bot-typing-focus");
    }
    loginSection.hidden = true;
    if (cadastroSection) cadastroSection.hidden = false;
    appendTerminalLog("[RPA02 · Playwright] Login realizado com sucesso como operador.qualidade.", "success");
  }

  const randomSuffix = Math.floor(600 + Math.random() * 300);
  const botBatches = [
    {
      lote_id: `LG-AUTO-${randomSuffix}`,
      produto: "TV65-OLED",
      linha: "LINHA_01",
      turno: "A",
      status: "APROVADO",
      responsavel: "Robô Playwright (RPA02)",
      data: "15/06/2026",
      observacao: "Inspeção óptica de painel OLED 4K concluída sem anomalias pelo robô.",
      origem: "Regras",
      classificacao: "Válido",
      orientacao: "Playwright Web",
      confianca: "100.0%",
      _isNew: true
    },
    {
      lote_id: `LG-AUTO-${randomSuffix + 1}`,
      produto: "AC18-SPLIT",
      linha: "LINHA_02",
      turno: "B",
      status: "REPROVADO",
      responsavel: "Robô Playwright (RPA02)",
      data: "15/06/2026",
      observacao: "Pressão de ciclo térmico fora de conformidade nominal (Divergência detectada).",
      origem: "ML",
      classificacao: "Divergência",
      orientacao: "Playwright Web",
      confianca: "97.2%",
      _isNew: true
    },
    {
      lote_id: `LG-AUTO-${randomSuffix + 2}`,
      produto: "MON27-QHD",
      linha: "LINHA_03",
      turno: "A",
      status: "APROVADO",
      responsavel: "Robô Playwright (RPA02)",
      data: "15/06/2026",
      observacao: "Calibração de gama DCI-P3 e taxa de atualização de 144Hz validadas com sucesso.",
      origem: "Regras",
      classificacao: "Válido",
      orientacao: "Playwright Web",
      confianca: "100.0%",
      _isNew: true
    },
    {
      lote_id: `LG-AUTO-${randomSuffix + 3}`,
      produto: "TV55-4K-B",
      linha: "LINHA_01",
      turno: "C",
      status: "PENDENTE",
      responsavel: "Robô Playwright (RPA02)",
      data: "15/06/2026",
      observacao: "Inspeção de retroiluminação LED com variação luminosa marginal sob análise.",
      origem: "ML",
      classificacao: "Ambíguo",
      orientacao: "Playwright Web",
      confianca: "88.4%",
      _isNew: true
    },
    {
      lote_id: `LG-AUTO-${randomSuffix + 4}`,
      produto: "AC12-SPLIT",
      linha: "LINHA_02",
      turno: "A",
      status: "APROVADO",
      responsavel: "Robô Playwright (RPA02)",
      data: "15/06/2026",
      observacao: "Teste de estanqueidade gás R32 e isolamento elétrico validados com êxito.",
      origem: "Regras",
      classificacao: "Válido",
      orientacao: "Playwright Web",
      confianca: "100.0%",
      _isNew: true
    },
    {
      lote_id: `LG-AUTO-${randomSuffix + 5}`,
      produto: "MON32-4K",
      linha: "LINHA_03",
      turno: "B",
      status: "REPROVADO",
      responsavel: "Robô Playwright (RPA02)",
      data: "15/06/2026",
      observacao: "Detecção de pixel inoperante no quadrante B3 por visão computacional.",
      origem: "ML",
      classificacao: "Divergência",
      orientacao: "Playwright Web",
      confianca: "98.1%",
      _isNew: true
    },
    {
      lote_id: `LG-AUTO-${randomSuffix + 6}`,
      produto: "TV43-FHD",
      linha: "LINHA_01",
      turno: "B",
      status: "APROVADO",
      responsavel: "Robô Playwright (RPA02)",
      data: "15/06/2026",
      observacao: "Conexão de chicote elétrico e placa T-Con conferida conforme diagrama industrial.",
      origem: "Regras",
      classificacao: "Válido",
      orientacao: "Playwright Web",
      confianca: "100.0%",
      _isNew: true
    },
    {
      lote_id: `LG-AUTO-${randomSuffix + 7}`,
      produto: "TV50-4K-B",
      linha: "LINHA_01",
      turno: "A",
      status: "APROVADO",
      responsavel: "Robô Playwright (RPA02)",
      data: "15/06/2026",
      observacao: "Gravação de firmware LG webOS 2026 e teste acústico dos alto-falantes concluídos.",
      origem: "Regras",
      classificacao: "Válido",
      orientacao: "Playwright Web",
      confianca: "100.0%",
      _isNew: true
    }
  ];

  appendTerminalLog(`[RPA02 · Playwright] Iniciando preenchimento sequencial de ${botBatches.length} lotes de inspeção na interface Web...`, "info");

  for (let i = 0; i < botBatches.length; i++) {
    const b = botBatches[i];
    if (botBadge) {
      botBadge.className = "badge bot-badge-running";
      botBadge.textContent = `DIGITANDO LOTE (${i + 1}/${botBatches.length})`;
    }

    const inpLote = document.getElementById("lote_id");
    const selProd = document.getElementById("produto");
    const inpLinha = document.getElementById("linha");
    const inpTurno = document.getElementById("turno");
    const inpResp = document.getElementById("responsavel");
    const inpData = document.getElementById("data");
    const txtObs = document.getElementById("observacao");
    const submitBtn = document.getElementById("btn-processar-lote");

    if (inpLote) {
      inpLote.classList.add("bot-typing-focus");
      inpLote.value = b.lote_id;
      await new Promise(r => setTimeout(r, 60));
      inpLote.classList.remove("bot-typing-focus");
    }

    if (selProd) {
      selProd.classList.add("bot-typing-focus");
      selProd.value = b.produto;
      await new Promise(r => setTimeout(r, 50));
      selProd.classList.remove("bot-typing-focus");
    }

    if (inpLinha) inpLinha.value = b.linha;
    if (inpTurno) inpTurno.value = b.turno;

    const radio = document.querySelector(`input[name="status"][value="${b.status}"]`);
    if (radio) {
      radio.checked = true;
      radio.parentElement.classList.add("bot-typing-focus");
      await new Promise(r => setTimeout(r, 40));
      radio.parentElement.classList.remove("bot-typing-focus");
    }

    if (inpResp) inpResp.value = b.responsavel;
    if (inpData) inpData.value = b.data;

    if (txtObs) {
      txtObs.classList.add("bot-typing-focus");
      txtObs.value = b.observacao;
      await new Promise(r => setTimeout(r, 60));
      txtObs.classList.remove("bot-typing-focus");
    }

    // Submit button pulse
    if (submitBtn) {
      submitBtn.classList.add("bot-submit-pulse");
      await new Promise(r => setTimeout(r, 90));
      submitBtn.classList.remove("bot-submit-pulse");
    }

    // Insert into state
    SMART_OFFICE_STATE.datapool.unshift(b);
    SMART_OFFICE_STATE.executiveData.sampleRecords.unshift(b);

    // Re-render DataPool table & downstream pipeline tables
    renderDataPoolTable();
    renderDecisionTable(SMART_OFFICE_STATE.datapool);
    renderSampleRecordsTable(SMART_OFFICE_STATE.datapool);

    appendTerminalLog(`[RPA02 · Playwright] Lote ${b.lote_id} (${b.produto}) cadastrado! Fila atualizada para ${SMART_OFFICE_STATE.datapool.length} lotes.`, "success");
    showToast(`Lote ${b.lote_id} cadastrado e disponível no DataPool!`, "success");

    await new Promise(r => setTimeout(r, 80));
  }

  // Carga massiva do robô: garante que os 1.000 lotes oficiais estejam integrados no DataPool
  if (SMART_OFFICE_STATE.datapool.length < 1000) {
    if (botBadge) {
      botBadge.className = "badge bot-badge-running";
      botBadge.textContent = "INGESTÃO EM LOTE (1.000 LOTES)...";
    }
    appendTerminalLog("[RPA02 · Playwright] Carga massiva ativada: sincronizando os 1.000 lotes oficiais da fábrica no DataPool...", "info");
    await new Promise(r => setTimeout(r, 400));

    if (SMART_OFFICE_STATE.officialDatapool && SMART_OFFICE_STATE.officialDatapool.length > 0) {
      SMART_OFFICE_STATE.datapool = [...SMART_OFFICE_STATE.officialDatapool];
    } else {
      await loadInitialDataset();
    }

    // Mantém os lotes recém-digitados no topo para demonstração visual
    botBatches.forEach(b => {
      if (!SMART_OFFICE_STATE.datapool.some(d => d.lote_id === b.lote_id)) {
        SMART_OFFICE_STATE.datapool.unshift(b);
      }
    });

    renderDataPoolTable();
    renderDecisionTable(SMART_OFFICE_STATE.datapool);
    renderSampleRecordsTable(SMART_OFFICE_STATE.datapool);
    appendTerminalLog(`[RPA02 · Playwright] Ingestão concluída com sucesso: ${SMART_OFFICE_STATE.datapool.length.toLocaleString("pt-BR")} lotes prontos para a esteira multi-bot.`, "success");
  }

  if (botBadge) {
    botBadge.className = "badge badge-success";
    botBadge.textContent = `CONCLUÍDO (${SMART_OFFICE_STATE.datapool.length.toLocaleString("pt-BR")} LOTES)`;
  }
  if (botPanel) botPanel.classList.remove("bot-active");
  if (btnAuto) btnAuto.disabled = false;
  if (btnAutoInner) btnAutoInner.disabled = false;

  const btnClear = document.getElementById("btn-clear-datapool");
  const btnRestore = document.getElementById("btn-restore-datapool");
  if (btnClear) btnClear.style.display = "inline-flex";
  if (btnRestore) btnRestore.style.display = "none";

  const sucessoDiv = document.getElementById("sucesso");
  if (sucessoDiv) {
    sucessoDiv.textContent = `${SMART_OFFICE_STATE.datapool.length.toLocaleString("pt-BR")} lotes processados e disponíveis no DataPool para as próximas etapas.`;
    sucessoDiv.hidden = false;
  }

  showToast(`${SMART_OFFICE_STATE.datapool.length.toLocaleString("pt-BR")} lotes integrados no DataPool pelo robô Playwright!`, "success");
  isBotIngesting = false;
}

function setupIngestionForm() {
  const loginSection = document.getElementById("login");
  const loginForm = document.getElementById("login-form");
  const cadastroSection = document.getElementById("cadastro");
  const loteForm = document.getElementById("lote-form");
  const btnAuto = document.getElementById("btn-auto-playwright");
  const btnAutoInner = document.getElementById("btn-auto-playwright-inner");
  const btnRandom = document.getElementById("btn-random-batch");
  const filterDate = document.getElementById("filter-datapool-origem");
  const searchInput = document.getElementById("search-datapool");

  function filterDataPool() {
    TABLE_PAGINATION.datapool.page = 1;
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
        confianca: "100.0%",
        _isNew: true
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
      }

      showToast(`Lote ${loteId} processado e inserido no DataPool!`, "success");
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
      simulateRobotIngestionStepByStep();
    });
  }

  if (btnAutoInner) {
    btnAutoInner.addEventListener("click", () => {
      simulateRobotIngestionStepByStep();
    });
  }

  const btnClear = document.getElementById("btn-clear-datapool");
  const btnRestore = document.getElementById("btn-restore-datapool");

  if (btnClear) {
    btnClear.addEventListener("click", () => {
      SMART_OFFICE_STATE.datapool = [];
      renderDataPoolTable();
      renderDecisionTable([]);
      renderSampleRecordsTable([]);
      btnClear.style.display = "none";
      if (btnRestore) btnRestore.style.display = "inline-flex";
      showToast("DataPool zerado com sucesso! A fila está vazia para demonstrar a ingestão do zero.", "info");

      const terminal = document.getElementById("pipeline-terminal");
      if (terminal) {
        const line = document.createElement("div");
        line.className = "log-line log-warning";
        const now = new Date().toLocaleTimeString("pt-BR");
        line.textContent = `${now} | WARN | DataPool zerado pelo operador para demonstração do fluxo limpo do zero.`;
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
      }
    });
  }

  if (btnRestore) {
    btnRestore.addEventListener("click", () => {
      if (SMART_OFFICE_STATE.officialDatapool && SMART_OFFICE_STATE.officialDatapool.length > 0) {
        SMART_OFFICE_STATE.datapool = [...SMART_OFFICE_STATE.officialDatapool];
      } else {
        loadInitialDataset();
      }
      renderDataPoolTable();
      renderDecisionTable(SMART_OFFICE_STATE.datapool);
      renderSampleRecordsTable(SMART_OFFICE_STATE.datapool);
      btnRestore.style.display = "none";
      if (btnClear) btnClear.style.display = "inline-flex";
      showToast("Base oficial de lotes restaurada com sucesso!", "success");

      const terminal = document.getElementById("pipeline-terminal");
      if (terminal) {
        const line = document.createElement("div");
        line.className = "log-line log-info";
        const now = new Date().toLocaleTimeString("pt-BR");
        line.textContent = `${now} | INFO | Base oficial restaurada: ${SMART_OFFICE_STATE.datapool.length} lotes disponíveis no DataPool.`;
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
      }
    });
  }
}

// =========================================================================
// 4. Sistema Desktop Legado (RPA01 · RUNNER_WIN_GUI_01)
// =========================================================================
const ESTOQUE_DESKTOP_DB = {
  "LOTE-001": { produto: "TV 55 OLED", saldo: 150, doca: "DOCA-01", status: "LIBERADO", turno: "A" },
  "LOTE-002": { produto: "LAVADORA 12KG", saldo: 80, doca: "DOCA-02", status: "LIBERADO", turno: "B" },
  "LOTE-003": { produto: "GELADEIRA FROST", saldo: 45, doca: "DOCA-01", status: "INSPECAO", turno: "A" },
  "LOTE-004": { produto: "AR CONDICIONADO", saldo: 200, doca: "DOCA-03", status: "LIBERADO", turno: "C" },
  "LOTE-005": { produto: "MICROONDAS 30L", saldo: 0, doca: "DOCA-02", status: "ESGOTADO", turno: "B" },
  "LOTE-006": { produto: "SOUNDBAR LG", saldo: 95, doca: "DOCA-01", status: "LIBERADO", turno: "A" },
  "LOTE-007": { produto: "MONITOR ULTRA", saldo: 120, doca: "DOCA-04", status: "LIBERADO", turno: "C" }
};

function consultarLoteDesktopVisual(lote) {
  const inputLote = document.getElementById("gui-lote-input");
  const banner = document.getElementById("gui-resultado-banner");
  const tbody = document.getElementById("desktop-stock-tbody");

  if (inputLote) inputLote.value = lote;

  const data = ESTOQUE_DESKTOP_DB[lote];
  if (data) {
    if (banner) {
      banner.style.background = "rgba(16, 185, 129, 0.15)";
      banner.style.borderColor = "#10b981";
      banner.style.color = "#34d399";
      banner.innerHTML = `<span>Produto: <strong>${data.produto}</strong> | Saldo: <strong>${data.saldo} un</strong> | Local: <strong>${data.doca}</strong> | Status: <strong>${data.status}</strong></span>`;
    }
  } else {
    if (banner) {
      banner.style.background = "rgba(239, 68, 68, 0.15)";
      banner.style.borderColor = "#ef4444";
      banner.style.color = "#f87171";
      banner.innerHTML = `<span>Lote <strong>${lote}</strong> não localizado na base de estoque físico.</span>`;
    }
  }

  if (tbody) {
    const rows = tbody.querySelectorAll("tr");
    rows.forEach(r => {
      if (r.getAttribute("data-lote") === lote) {
        r.classList.add("active-row");
        r.scrollIntoView({ block: "nearest", behavior: "smooth" });
      } else {
        r.classList.remove("active-row");
      }
    });
  }
}

async function simulateDesktopStockExtraction() {
  const win = document.getElementById("desktop-gui-window");
  const mutexBadge = document.getElementById("gui-mutex-badge");
  const statusbarText = document.getElementById("gui-statusbar-text");
  const banner = document.getElementById("gui-resultado-banner");
  const terminal = document.getElementById("pipeline-terminal");

  function appendTerminalLog(msg, type = "info") {
    if (!terminal) return;
    const line = document.createElement("div");
    line.className = `log-line log-${type}`;
    const now = new Date().toLocaleTimeString("pt-BR");
    line.textContent = `${now} | ${type.toUpperCase()} | ${msg}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
  }

  if (win) {
    win.style.display = "flex";
    win.classList.remove("minimized");
  }

  if (mutexBadge) {
    mutexBadge.className = "badge badge-error";
    mutexBadge.textContent = "MUTEX ADQUIRIDO (RUNNER_WIN_GUI_01)";
  }
  if (statusbarText) {
    statusbarText.textContent = "Sessão Gráfica: RUNNER_WIN_GUI_01 | Coleta RPA01 em Andamento...";
  }

  appendTerminalLog("[RPA01 · Desktop] Conectado à sessão gráfica RUNNER_WIN_GUI_01 com Mutex exclusivo (CoexistenceGuard).", "info");

  const lotesParaConsultar = ["LOTE-001", "LOTE-002", "LOTE-003", "LOTE-004", "LOTE-006", "LOTE-007"];
  for (const lote of lotesParaConsultar) {
    consultarLoteDesktopVisual(lote);
    const item = ESTOQUE_DESKTOP_DB[lote];
    if (item) {
      appendTerminalLog(`[RPA01 · Desktop] ${lote} (${item.produto}): Saldo = ${item.saldo} un [${item.doca} | ${item.status}] extraído via tela desktop.`, "info");
    }
    await new Promise(r => setTimeout(r, 400));
  }

  if (banner) {
    banner.style.background = "rgba(16, 185, 129, 0.2)";
    banner.style.borderColor = "#10b981";
    banner.style.color = "#34d399";
    banner.innerHTML = `<span><strong>Coleta de Estoque Finalizada</strong>: 1.000 saldos físicos consolidados no DataPool.</span>`;
  }
  if (mutexBadge) {
    mutexBadge.className = "badge badge-success";
    mutexBadge.textContent = "MUTEX LIBERADO (EXIT 0)";
  }
  if (statusbarText) {
    statusbarText.textContent = "Sessão Gráfica Dedicada: RUNNER_WIN_GUI_01 | Status: ONLINE | Mutex Liberado";
  }

  appendTerminalLog("[RPA01 · Desktop] 1.000 posições de estoque mapeadas e salvas em 'data/datapool/coleta_desktop_estoque.json'.", "success");
  showToast("RPA01 Desktop: Posições de estoque extraídas com sucesso!", "success");
}

function setupDesktopGuiControls() {
  const win = document.getElementById("desktop-gui-window");
  const btnToggle = document.getElementById("btn-toggle-desktop-gui");
  const btnClose = document.getElementById("btn-close-desktop-gui");
  const btnMinimize = document.getElementById("btn-minimize-desktop-gui");
  const btnBuscar = document.getElementById("gui-btn-buscar");
  const inputLote = document.getElementById("gui-lote-input");

  if (!win) return;

  if (btnToggle) {
    btnToggle.addEventListener("click", () => {
      if (win.style.display === "none" || !win.style.display) {
        win.style.display = "flex";
        win.classList.remove("minimized");
        fetch("/api/open-desktop-gui", { method: "POST" }).catch(() => {});
        showToast("Janela do Sistema Desktop Legado (RPA01) aberta!", "info");
      } else {
        win.style.display = "none";
      }
    });
  }

  if (btnClose) {
    btnClose.addEventListener("click", () => {
      win.style.display = "none";
    });
  }

  if (btnMinimize) {
    btnMinimize.addEventListener("click", () => {
      win.classList.toggle("minimized");
    });
  }

  if (btnBuscar && inputLote) {
    btnBuscar.addEventListener("click", () => {
      const lote = inputLote.value.trim().toUpperCase() || "LOTE-001";
      consultarLoteDesktopVisual(lote);
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
    { id: "node-rpa02", name: "SCM_ColetaPedidos_BOT", runner: "RUNNER_SRV_BG_01", desc: "etapa=playwright_ingestion | datapool=lotes_disponiveis | status=OK", dur: 1800 },
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

    // Dispara pipeline no backend e abre a GUI do cliente Desktop nativo em primeiro plano
    fetch("/api/open-desktop-gui", { method: "POST" }).catch(() => {});
    fetch("/api/run-pipeline", { method: "POST" })
      .then(res => res.json())
      .catch(() => {});

    let index = 0;
    async function executeNext() {
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

      if (curr.id === "node-rpa01") {
        await simulateDesktopStockExtraction();
      } else if (curr.id === "node-rpa02") {
        await simulateRobotIngestionStepByStep();
      } else {
        await new Promise(r => setTimeout(r, curr.dur));
      }

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
      TABLE_PAGINATION.decision.page = 1;
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

  if (!items || items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-dim); padding: 2rem;">Nenhum registro encontrado no motor de decisão.</td></tr>`;
    renderPaginationBar("pagination-decision", 0, 1, 10, () => {});
    return;
  }

  const { page, pageSize } = TABLE_PAGINATION.decision;
  const totalPages = Math.ceil(items.length / pageSize) || 1;
  const safePage = Math.min(Math.max(1, page), totalPages);
  TABLE_PAGINATION.decision.page = safePage;

  const pageItems = items.slice((safePage - 1) * pageSize, safePage * pageSize);

  tbody.innerHTML = pageItems.map(item => `
    <tr>
      <td><strong>${item.lote_id}</strong></td>
      <td>${item.produto}</td>
      <td><span class="badge ${item.status === 'APROVADO' || item.status === 'OK' ? 'badge-success' : item.status === 'NOK' || item.status === 'REPROVADO' ? 'badge-danger' : 'badge-warning'}">${item.status}</span></td>
      <td><span class="${item.origem === 'Regras' ? 'badge-decision-rules' : 'badge-decision-ml'}">${item.origem === 'Regras' ? 'Regras (RN01–RN12)' : 'Machine Learning'}</span></td>
      <td>${item.orientacao || 'Conforme regra de validação'}</td>
      <td><span style="font-family: var(--font-mono); font-weight: 700; color: #a7f3d0;">${item.confianca || '100.0%'}</span></td>
      <td><span class="badge ${item.classificacao === 'Válido' ? 'badge-success' : item.classificacao === 'Divergência' ? 'badge-danger' : item.classificacao === 'Ambíguo' ? 'badge-warning' : 'badge-neutral'}">${item.classificacao}</span></td>
      <td style="font-size: 0.8rem; color: var(--text-muted);">${item.classificacao === 'Válido' ? 'Liberação para expedição' : item.classificacao === 'Divergência' ? 'Alerta disparado ao gestor' : item.classificacao === 'Ambíguo' ? 'Fila de revisão humana' : 'Quarentena Dead Letter'}</td>
    </tr>
  `).join("");

  renderPaginationBar("pagination-decision", items.length, safePage, pageSize, (newPage) => {
    TABLE_PAGINATION.decision.page = newPage;
    renderDecisionTable(items);
  });
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
    TABLE_PAGINATION.records.page = 1;
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
      "#8b5cf6", // RN07 (Violeta - Saldo Físico)
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

  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-dim); padding: 2rem;">Nenhum registro encontrado.</td></tr>`;
    renderPaginationBar("pagination-records", 0, 1, 10, () => {});
    return;
  }

  const { page, pageSize } = TABLE_PAGINATION.records;
  const totalPages = Math.ceil(records.length / pageSize) || 1;
  const safePage = Math.min(Math.max(1, page), totalPages);
  TABLE_PAGINATION.records.page = safePage;

  const pageRecords = records.slice((safePage - 1) * pageSize, safePage * pageSize);

  tbody.innerHTML = pageRecords.map(r => `
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

  renderPaginationBar("pagination-records", records.length, safePage, pageSize, (newPage) => {
    TABLE_PAGINATION.records.page = newPage;
    renderSampleRecordsTable(records);
  });
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
      TABLE_PAGINATION.tasks.page = 1;
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

  if (!tasks || tasks.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-dim); padding: 1.5rem;">Nenhuma task registrada.</td></tr>`;
    renderPaginationBar("pagination-tasks", 0, 1, 10, () => {});
    return;
  }

  const { page, pageSize } = TABLE_PAGINATION.tasks;
  const totalPages = Math.ceil(tasks.length / pageSize) || 1;
  const safePage = Math.min(Math.max(1, page), totalPages);
  TABLE_PAGINATION.tasks.page = safePage;

  const pageTasks = tasks.slice((safePage - 1) * pageSize, safePage * pageSize);

  tbody.innerHTML = pageTasks.map(t => `
    <tr>
      <td style="white-space: nowrap;"><strong style="font-family: var(--font-mono); font-size: 0.8125rem;">${t.id}</strong></td>
      <td style="white-space: nowrap;">${t.automation}</td>
      <td style="white-space: nowrap;"><code>${t.runner}</code></td>
      <td><span class="node-priority">${t.priority}</span></td>
      <td style="white-space: nowrap;">${t.start}</td>
      <td style="white-space: nowrap;">${t.duration}</td>
      <td><span class="badge ${t.status === 'Completed' ? 'badge-success' : t.status === 'Running' ? 'badge-info' : 'badge-danger'}">${t.status}</span></td>
      <td>${t.event}</td>
    </tr>
  `).join("");

  renderPaginationBar("pagination-tasks", tasks.length, safePage, pageSize, (newPage) => {
    TABLE_PAGINATION.tasks.page = newPage;
    renderFilteredTasksTable(tasks);
  });
}

function updateDataPoolCounter() {
  const counter = document.getElementById("datapool-count-text");
  if (counter) {
    const total = SMART_OFFICE_STATE.datapool.length;
    counter.textContent = `${total.toLocaleString("pt-BR")} lotes prontos para a esteira`;
  }
}

function renderDataPoolTable() {
  updateDataPoolCounter();
  renderFilteredDataPoolTable(SMART_OFFICE_STATE.datapool);
}

function renderFilteredDataPoolTable(items) {
  const tbody = document.getElementById("table-cadastrados-body");
  if (!tbody) return;
  if (!items || items.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; padding: 2.8rem 1rem; color: var(--text-dim);">
          <div style="font-size: 1.25rem; font-weight: 600; color: var(--text-muted); margin-bottom: 0.5rem;">Fila do DataPool Zerada (0 Lotes)</div>
          <p style="font-size: 0.875rem; max-width: 520px; margin: 0 auto 1.25rem; line-height: 1.5;">
            A fila de entrada está limpa. Clique em <strong>Executar Ingestão ao Vivo</strong> no painel do Robô Playwright acima para cadastrar lotes ou recarregue a base oficial a qualquer momento.
          </p>
          <button type="button" class="btn btn-sm btn-primary" onclick="document.getElementById('btn-restore-datapool')?.click();">
            Restaurar Base Oficial do DataPool
          </button>
        </td>
      </tr>
    `;
    renderPaginationBar("pagination-datapool", 0, 1, 10, () => {});
    return;
  }

  const { page, pageSize } = TABLE_PAGINATION.datapool;
  const totalPages = Math.ceil(items.length / pageSize) || 1;
  const safePage = Math.min(Math.max(1, page), totalPages);
  TABLE_PAGINATION.datapool.page = safePage;

  const pageItems = items.slice((safePage - 1) * pageSize, safePage * pageSize);

  tbody.innerHTML = pageItems.map(d => `
    <tr class="${d._isNew ? 'row-newly-added' : ''}">
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

  renderPaginationBar("pagination-datapool", items.length, safePage, pageSize, (newPage) => {
    TABLE_PAGINATION.datapool.page = newPage;
    renderFilteredDataPoolTable(items);
  });
}

function renderManifestTable() {
  const tbody = document.getElementById("manifest-table-body");
  if (!tbody) return;
  tbody.innerHTML = SMART_OFFICE_STATE.manifestPackages.map(p => `
    <tr>
      <td><strong>${p.bot}</strong></td>
      <td><code>${p.arquivo}</code></td>
      <td>${p.tamanho}</td>
      <td>
        <span class="sha256-badge" title="SHA-256: ${p.sha256} (Clique para copiar)" onclick="navigator.clipboard.writeText('${p.sha256}'); showToast('Hash SHA-256 copiado para a área de transferência!', 'info');">
          <code>${p.sha256.substring(0, 10)}...${p.sha256.substring(56)}</code>
          <span class="copy-icon" style="font-size: 0.72rem; color: #94a3b8;">copiar</span>
        </span>
      </td>
      <td><code>${p.runner}</code></td>
      <td><span class="badge badge-success">${p.version}</span></td>
    </tr>
  `).join("");
}

// =========================================================================
// 10. Report Modal Controller (Quick-view popup for presentation & jury)
// =========================================================================

const EXCEL_PREVIEW_FALLBACK = {
  sheet_names: [
    "Resumo", "Todos", "Válidos", "Divergências", "Ambíguos", 
    "Erros de Entrada", "Ranking de Regras", "Dicionário", "Decisões de ML"
  ],
  sheets: {
    "Resumo": [
      ["Indicador Operacional", "Valor Consolidado", "Meta / Observação"],
      ["Total de Lotes Auditados", "1.000 lotes", "100% da amostragem consolidada de 10 dias"],
      ["Lotes Válidos (Conformes)", "624 lotes (62.4%)", "Liberados imediatamente para expedição"],
      ["Divergências Físico x Pedido", "204 lotes (20.4%)", "Tratadas com causa provável via ML"],
      ["Registros Ambíguos", "76 lotes (7.6%)", "Encaminhados para revisão humana"],
      ["Erros de Entrada", "96 lotes (9.6%)", "Retidos na Dead Letter Queue"],
      ["Taxa de Qualidade da Entrada", "90.4%", "Meta corporativa > 80.0% (Conforme)"],
      ["Taxa de Revisão Humana", "7.6%", "Meta corporativa < 15.0% (Conforme)"],
      ["Taxa de Retrabalho", "20.4%", "Meta corporativa < 6.0% (Atenção)"],
      ["Ganho Estimado de Tempo (FTE)", "29h 10m (1.750 min)", "Estimativa: 2.0 min manual vs 0.25 min bot"],
      ["Regra Mais Acionada", "RN06 (Normalização OK ➔ APROVADO)", "108 ocorrências (sem falhas de sistema)"]
    ],
    "Todos": [
      ["Lote ID", "Produto", "Linha", "Turno", "Status Original", "Classificação", "Regras Aplicadas"],
      ["LG-2026-00101", "TV55-4K-B", "LINHA_01", "A", "OK", "Válido", "RN06"],
      ["LG-2026-00102", "AC12-SPLIT", "LINHA_02", "B", "APROVADO", "Válido", "Nenhuma"],
      ["LG-2026-00103", "TV65-OLED", "LINHA_01", "A", "NOK", "Divergência", "RN05, RN07"],
      ["LG-2026-00104", "MON27-QHD", "LINHA_03", "C", "APROVADO", "Válido", "Nenhuma"],
      ["LG-2026-00105", "TV50-4K-B", "LINHA_01", "A", "PENDENTE", "Ambíguo", "RN09"],
      ["LG-2026-00106", "AC18-SPLIT", "LINHA_02", "B", "REPROVADO", "Divergência", "RN07, RN10"],
      ["LG-2026-00107", "TV43-FHD", "LINHA_01", "A", "STATUS_INVALIDO", "Erro de Entrada", "RN04"],
      ["LG-2026-00108", "TV55-4K-B", "LINHA_01", "A", "OK", "Válido", "RN06"],
      ["LG-2026-00109", "MON32-4K", "LINHA_03", "B", "EM_AJUSTE", "Ambíguo", "RN09"],
      ["LG-2026-00110", "AC12-SPLIT", "LINHA_02", "C", "APROVADO", "Válido", "Nenhuma"]
    ],
    "Válidos": [
      ["Lote ID", "Produto", "Linha", "Turno", "Status Final", "Responsável", "Data"],
      ["LG-2026-00101", "TV55-4K-B", "LINHA_01", "A", "APROVADO", "Carlos Silva", "15/06/2026"],
      ["LG-2026-00102", "AC12-SPLIT", "LINHA_02", "B", "APROVADO", "Carlos Silva", "15/06/2026"],
      ["LG-2026-00104", "MON27-QHD", "LINHA_03", "C", "APROVADO", "Carlos Silva", "15/06/2026"],
      ["LG-2026-00108", "TV55-4K-B", "LINHA_01", "A", "APROVADO", "Carlos Silva", "15/06/2026"],
      ["LG-2026-00110", "AC12-SPLIT", "LINHA_02", "C", "APROVADO", "Carlos Silva", "15/06/2026"]
    ],
    "Divergências": [
      ["Lote ID", "Produto", "Linha", "Status", "Regra", "Causa Provável ML", "Confiança ML"],
      ["LG-2026-00103", "TV65-OLED", "LINHA_01", "REPROVADO", "RN07", "QTD_FISICA_DIVERGENTE", "97.4%"],
      ["LG-2026-00106", "AC18-SPLIT", "LINHA_02", "REPROVADO", "RN07", "FALHA_TESTE_ELETRICO", "94.8%"],
      ["LG-2026-00115", "TV50-4K-B", "LINHA_01", "REPROVADO", "RN05", "DIVERGENCIA_CADASTRO", "89.2%"],
      ["LG-2026-00122", "MON27-QHD", "LINHA_03", "REPROVADO", "RN07", "AVARIA_TRANSPORTE", "96.1%"]
    ],
    "Ambíguos": [
      ["Lote ID", "Status Raw", "Turno", "Obs Preenchida", "Predição ML", "Probabilidade", "Ação Decidida"],
      ["LG-2026-00105", "PENDENTE", "A", "Não", "revisar", "72.4%", "REVISAR"],
      ["LG-2026-00109", "EM AJUSTE", "B", "Sim", "revisar", "68.9%", "REVISAR"],
      ["LG-2026-00118", "AGUARDANDO REINSPEÇÃO", "C", "Não", "recusar_automatico", "87.3%", "RECUSAR_AUTOMATICO"],
      ["LG-2026-00124", "ESPECIFICAÇÃO EM REVISÃO", "A", "Sim", "revisar", "64.1%", "REVISAO_PRIORITARIA"]
    ],
    "Erros de Entrada": [
      ["Lote ID", "Linha Origem", "Campo Inválido", "Regra Violada", "Destino"],
      ["LG-2026-00107", "Linha 7", "Status não pertence ao domínio", "RN04", "Dead Letter Queue"],
      ["LG-2026-00133", "Linha 33", "Lote ID vazio ou nulo", "RN01", "Dead Letter Queue"],
      ["LG-2026-00145", "Linha 45", "Data fora da referência diária", "RN12", "Dead Letter Queue"]
    ],
    "Ranking de Regras": [
      ["Código", "Descrição da Regra de Negócio", "Ocorrências", "Percentual Total", "Severidade"],
      ["RN06", "Normalização de OK para APROVADO", "108", "10.8%", "Info"],
      ["RN05", "Divergência de Status Cadastral em Teste", "84", "8.4%", "Alta"],
      ["RN07", "Saldo Físico Divergente de Pedido", "65", "6.5%", "Crítica"],
      ["RN01", "Inconsistência de Data / Lote Vazio", "42", "4.2%", "Média"],
      ["RN02", "Produto Descontinuado / Não Encontrado", "28", "2.8%", "Alta"],
      ["RN03", "Turno Inválido ou Fora de Grade", "16", "1.6%", "Baixa"]
    ],
    "Dicionário": [
      ["Coluna", "Tipo de Dado", "Domínio Permitido", "Descrição"],
      ["lote_id", "Texto (String)", "LG-AAAA-XXXXX", "Identificador único do lote"],
      ["produto", "Texto (String)", "Catálogo oficial", "Modelo do eletroeletrônico"],
      ["linha", "Texto (String)", "LINHA_01, LINHA_02, LINHA_03", "Linha de montagem fabril"],
      ["turno", "Texto (String)", "A, B, C", "Turno operacional de inspeção"],
      ["status", "Texto (String)", "APROVADO, REPROVADO, PENDENTE", "Decisão de conformidade"],
      ["origem_decisao", "Texto (String)", "Regras, ML, Fallback", "Camada que atribuiu a causa"],
      ["confianca_ml", "Percentual", "0.0% a 100.0%", "Probabilidade calibrada da inferência"]
    ],
    "Decisões de ML": [
      ["Lote ID", "Status Raw", "Turno", "Probabilidade", "Latência (ms)", "Circuit Breaker", "Ação Final"],
      ["LG-2026-00105", "PENDENTE", "A", "72.40%", "28.4 ms", "CLOSED", "REVISAR"],
      ["LG-2026-00109", "EM AJUSTE", "B", "68.90%", "31.2 ms", "CLOSED", "REVISAR"],
      ["LG-2026-00118", "AGUARDANDO REINSPEÇÃO", "C", "87.30%", "26.8 ms", "CLOSED", "RECUSAR_AUTOMATICO"],
      ["LG-2026-00124", "ESPECIFICAÇÃO EM REVISÃO", "A", "64.10%", "29.5 ms", "CLOSED", "REVISAO_PRIORITARIA"]
    ]
  }
};

let cachedExcelData = null;
let currentActiveSheet = "Resumo";

function setupReportModal() {
  const modal = document.getElementById("modal-relatorios");
  if (!modal) return;

  const btnOpenHeader = document.getElementById("btn-open-report-modal");
  const btnOpenTab4 = document.getElementById("btn-open-all-reports");
  const reportCards = document.querySelectorAll("[data-open-report]");
  const btnClose = document.getElementById("btn-close-report-modal");
  const btnCloseFooter = document.getElementById("btn-close-report-modal-footer");
  const tabButtons = modal.querySelectorAll(".report-tab-btn");

  function openModal(targetTab = "rep-excel") {
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    switchReportTab(targetTab);
  }

  function closeModal() {
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  function switchReportTab(tabId) {
    tabButtons.forEach(btn => {
      const match = btn.getAttribute("data-report-tab") === tabId;
      btn.classList.toggle("active", match);
      btn.setAttribute("aria-selected", match ? "true" : "false");
    });
    modal.querySelectorAll(".report-pane").forEach(pane => {
      pane.classList.toggle("active", pane.id === tabId);
    });

    if (tabId === "rep-excel") loadAndRenderExcelPreview();
    else if (tabId === "rep-resumo") loadAndRenderMarkdownSummary();
    else if (tabId === "rep-pdf") renderPdfLetterheadPreview();
    else if (tabId === "rep-rastreabilidade") loadAndRenderTraceabilityJson();
  }

  if (btnOpenHeader) btnOpenHeader.addEventListener("click", () => openModal("rep-excel"));
  if (btnOpenTab4) btnOpenTab4.addEventListener("click", () => openModal("rep-excel"));

  reportCards.forEach(card => {
    card.addEventListener("click", () => {
      const reportType = card.getAttribute("data-open-report");
      const tabTarget = reportType === "excel" ? "rep-excel" : reportType === "resumo" ? "rep-resumo" : "rep-pdf";
      openModal(tabTarget);
    });
  });

  if (btnClose) btnClose.addEventListener("click", closeModal);
  if (btnCloseFooter) btnCloseFooter.addEventListener("click", closeModal);

  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal.classList.contains("open")) {
      closeModal();
    }
  });

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-report-tab");
      switchReportTab(target);
    });
  });
}

async function loadAndRenderExcelPreview() {
  const containerSheets = document.getElementById("excel-sheets-container");
  if (!containerSheets) return;

  if (!cachedExcelData) {
    try {
      const res = await fetch("/api/reports/excel-preview");
      if (res.ok) {
        const json = await res.json();
        if (json.sheet_names && json.sheet_names.length > 0) {
          cachedExcelData = json;
        }
      }
    } catch {}
  }

  const data = cachedExcelData || EXCEL_PREVIEW_FALLBACK;
  const sheetNames = data.sheet_names || Object.keys(data.sheets || {});

  containerSheets.innerHTML = sheetNames.map((name, idx) => `
    <button type="button" class="sheet-pill ${name === currentActiveSheet ? 'active' : ''}" data-sheet-name="${name}">
      ${idx + 1}. ${name}
    </button>
  `).join("");

  containerSheets.querySelectorAll(".sheet-pill").forEach(btn => {
    btn.addEventListener("click", () => {
      currentActiveSheet = btn.getAttribute("data-sheet-name");
      TABLE_PAGINATION.excel.page = 1;
      containerSheets.querySelectorAll(".sheet-pill").forEach(p => {
        p.classList.toggle("active", p.getAttribute("data-sheet-name") === currentActiveSheet);
      });
      renderSheetTable(currentActiveSheet, data);
    });
  });

  renderSheetTable(currentActiveSheet, data);
}

function renderSheetTable(sheetName, data) {
  const content = document.getElementById("excel-sheet-content");
  if (!content) return;

  const sheets = data.sheets || {};
  const rows = sheets[sheetName] || [];

  if (rows.length === 0) {
    content.innerHTML = `<div style="padding: 2rem; text-align: center; color: var(--text-dim);">Aba vazia ou não processada.</div>`;
    return;
  }

  const headers = rows[0] || [];
  const bodyRows = rows.slice(1);

  const { page, pageSize } = TABLE_PAGINATION.excel;
  const totalPages = Math.ceil(bodyRows.length / pageSize) || 1;
  const safePage = Math.min(Math.max(1, page), totalPages);
  TABLE_PAGINATION.excel.page = safePage;

  const pageRows = bodyRows.slice((safePage - 1) * pageSize, safePage * pageSize);

  const theadHtml = `
    <thead>
      <tr>
        ${headers.map(h => `<th>${h}</th>`).join("")}
      </tr>
    </thead>
  `;

  const tbodyHtml = `
    <tbody>
      ${pageRows.map(row => `
        <tr>
          ${row.map(cell => {
            let cellContent = cell;
            if (cell === "APROVADO" || cell === "OK" || cell === "Válido") {
              cellContent = `<span class="badge badge-success">${cell}</span>`;
            } else if (cell === "REPROVADO" || cell === "NOK" || cell === "Divergência") {
              cellContent = `<span class="badge badge-danger">${cell}</span>`;
            } else if (cell === "PENDENTE" || cell === "Ambíguo") {
              cellContent = `<span class="badge badge-warning">${cell}</span>`;
            } else if (cell === "Erro de Entrada" || cell === "Dead Letter Queue") {
              cellContent = `<span class="badge badge-neutral">${cell}</span>`;
            }
            return `<td>${cellContent}</td>`;
          }).join("")}
        </tr>
      `).join("")}
    </tbody>
  `;

  content.innerHTML = `
    <div class="table-responsive">
      <table class="rep-table">${theadHtml}${tbodyHtml}</table>
    </div>
    <div id="pagination-excel" class="table-pagination"></div>
  `;

  renderPaginationBar("pagination-excel", bodyRows.length, safePage, pageSize, (newPage) => {
    TABLE_PAGINATION.excel.page = newPage;
    renderSheetTable(sheetName, data);
  });
}

async function loadAndRenderMarkdownSummary() {
  const container = document.getElementById("md-preview-content");
  if (!container) return;

  let rawMd = "";
  try {
    const res = await fetch("/api/reports/markdown");
    if (res.ok) {
      const json = await res.json();
      rawMd = json.content || "";
    }
  } catch {}

  const kpis = SMART_OFFICE_STATE.executiveData;
  const total = kpis.total || 1000;
  const validos = kpis.validos || 624;
  const divergencias = kpis.divergencias || 204;
  const ambiguos = kpis.ambiguos || 76;
  const erros = kpis.erros || 96;

  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
      <div>
        <h2 style="font-size: 1.25rem; font-weight: 700; color: var(--text-pure); margin: 0;">Resumo Executivo — Conferência de Lotes</h2>
        <span style="font-size: 0.8rem; color: var(--text-dim);">Dossiê gerencial consolidado do período de 10 dias de inspeção fabril</span>
      </div>
      <span class="badge badge-success" style="font-weight: 700;">Auditado &middot; The DX Way</span>
    </div>

    <div class="md-kpi-summary">
      <div class="md-kpi-box">
        <div class="md-kpi-box-title">Total Processado</div>
        <div class="md-kpi-box-val">${total} lotes</div>
      </div>
      <div class="md-kpi-box">
        <div class="md-kpi-box-title">Registros Válidos</div>
        <div class="md-kpi-box-val" style="color: #34d399;">${validos} (${((validos/total)*100).toFixed(1)}%)</div>
      </div>
      <div class="md-kpi-box">
        <div class="md-kpi-box-title">Divergências</div>
        <div class="md-kpi-box-val" style="color: #f87171;">${divergencias} (${((divergencias/total)*100).toFixed(1)}%)</div>
      </div>
      <div class="md-kpi-box">
        <div class="md-kpi-box-title">Ambíguos (Revisão)</div>
        <div class="md-kpi-box-val" style="color: #fbbf24;">${ambiguos} (${((ambiguos/total)*100).toFixed(1)}%)</div>
      </div>
      <div class="md-kpi-box">
        <div class="md-kpi-box-title">Erros de Entrada</div>
        <div class="md-kpi-box-val" style="color: #9ca3af;">${erros} (${((erros/total)*100).toFixed(1)}%)</div>
      </div>
    </div>

    <div style="background: #1a1a1a; padding: 1.25rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color); margin-bottom: 1.25rem;">
      <h3 style="font-size: 0.95rem; margin: 0 0 0.5rem 0; color: var(--text-pure);">Destaque de Produtividade & Regras:</h3>
      <p style="margin: 0; color: var(--text-muted); font-size: 0.85rem; line-height: 1.6;">
        A regra mais acionada foi a <strong>RN06 — Normalização de OK para APROVADO</strong> com <strong>108 ocorrências (10.8%)</strong>, 
        padronizada de forma determinística sem exigir retrabalho humano. A camada secundária de <strong>Machine Learning (RPA04)</strong> 
        enriqueceu 204 itens divergentes sugerindo a causa-raiz provável sob supervisão de <strong>Circuit Breaker</strong>.
      </p>
    </div>

    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 260px; background: #1a1a1a; padding: 1rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
        <h4 style="margin: 0 0 0.5rem 0; font-size: 0.85rem; color: #a7f3d0;">Ganhos de Tempo Estimados (FTE):</h4>
        <ul style="margin: 0; padding-left: 1.2rem; font-size: 0.8rem; color: var(--text-muted); line-height: 1.6;">
          <li>Tempo manual estimado: <strong>2,00 min / registro</strong></li>
          <li>Tempo automatizado bot: <strong>0,25 min / registro</strong></li>
          <li>Economia total: <strong>1.750 minutos (~29h 10m)</strong></li>
        </ul>
      </div>
      <div style="flex: 1; min-width: 260px; background: #1a1a1a; padding: 1rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
        <h4 style="margin: 0 0 0.5rem 0; font-size: 0.85rem; color: #a7f3d0;">Índices de Qualidade Operacional:</h4>
        <ul style="margin: 0; padding-left: 1.2rem; font-size: 0.8rem; color: var(--text-muted); line-height: 1.6;">
          <li>Taxa de qualidade de entrada: <strong>90.4%</strong> (Meta > 80.0% &middot; <span style="color:#34d399;">Conforme</span>)</li>
          <li>Taxa de revisão humana: <strong>7.6%</strong> (Meta < 15.0% &middot; <span style="color:#34d399;">Conforme</span>)</li>
          <li>Taxa de retrabalho: <strong>20.4%</strong> (Meta < 6.0% &middot; <span style="color:#f87171;">Atenção</span>)</li>
        </ul>
      </div>
    </div>
  `;
}

function renderPdfLetterheadPreview() {
  const container = document.getElementById("pdf-preview-content");
  if (!container) return;

  const kpis = SMART_OFFICE_STATE.executiveData;
  const total = kpis.total || 1000;
  const validos = kpis.validos || 624;
  const divergencias = kpis.divergencias || 204;
  const ambiguos = kpis.ambiguos || 76;
  const erros = kpis.erros || 96;

  container.innerHTML = `
    <div class="pdf-header">
      <div>
        <div class="pdf-brand-logo">LG Electronics do Brasil</div>
        <div class="pdf-brand-sub">Fábrica de Manaus &middot; SCM & Controle de Qualidade Fabril &middot; AX Academy</div>
      </div>
      <div class="pdf-stamp">HOMOLOGADO / DX WAY</div>
    </div>

    <div style="margin-bottom: 1.25rem;">
      <h3 style="font-size: 1.15rem; color: #0f172a; margin: 0 0 0.25rem 0; font-weight: 800;">
        RELATÓRIO CONSOLIDADO DE INSPEÇÃO E AUDITORIA DE LOTES
      </h3>
      <div style="font-size: 0.8rem; color: #64748b;">
        Processo Oficial: <strong>RPA01–RPA06</strong> &middot; Período de Avaliação: <strong>10 Dias Fabris</strong> &middot; Emissão: <strong>${new Date().toLocaleDateString('pt-BR')}</strong>
      </div>
    </div>

    <table class="pdf-table">
      <thead>
        <tr>
          <th>Indicador de Qualidade</th>
          <th>Volume</th>
          <th>Percentual</th>
          <th>Status / Meta</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Total de Lotes Auditados</strong></td>
          <td>${total}</td>
          <td>100.0%</td>
          <td><span style="color: #c084fc; font-weight: 700;">Amostragem Completa</span></td>
        </tr>
        <tr>
          <td><strong>Registros Conformes (Válidos)</strong></td>
          <td>${validos}</td>
          <td>${((validos/total)*100).toFixed(1)}%</td>
          <td><span style="color: #16a34a; font-weight: 700;">Conforme (Liberado)</span></td>
        </tr>
        <tr>
          <td><strong>Divergências Operacionais (ML)</strong></td>
          <td>${divergencias}</td>
          <td>${((divergencias/total)*100).toFixed(1)}%</td>
          <td><span style="color: #dc2626; font-weight: 700;">Tratamento Heurístico</span></td>
        </tr>
        <tr>
          <td><strong>Registros em Quarentena / Erro</strong></td>
          <td>${erros}</td>
          <td>${((erros/total)*100).toFixed(1)}%</td>
          <td><span style="color: #475569; font-weight: 700;">Dead Letter Queue</span></td>
        </tr>
        <tr>
          <td><strong>Ganho de Produtividade Estimado</strong></td>
          <td colspan="2"><strong>1.750 minutos (~29h 10m)</strong></td>
          <td><span style="color: #16a34a; font-weight: 700;">Economia Comprovada</span></td>
        </tr>
      </tbody>
    </table>

    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 1rem; margin-top: 1rem; font-size: 0.8rem; color: #334155; line-height: 1.5;">
      <strong>Parecer Técnico:</strong> A solução automatizada atende integralmente aos critérios de governança The DX Way, 
      com isolamento rigoroso por Circuit Breaker na camada de inteligência artificial e proteção mútua de sessão gráfica (CoexistenceGuard).
    </div>

    <div class="pdf-footer-signatures">
      <div class="pdf-sig-block">
        <div class="pdf-sig-line"></div>
        <div class="pdf-sig-name">Engenharia de Automação</div>
        <div class="pdf-sig-role">Smart Office Orchestrator</div>
      </div>
      <div class="pdf-sig-block">
        <div class="pdf-sig-line"></div>
        <div class="pdf-sig-name">Gerência de Qualidade</div>
        <div class="pdf-sig-role">LG Electronics do Brasil</div>
      </div>
    </div>
  `;
}

async function loadAndRenderTraceabilityJson() {
  const container = document.getElementById("json-traceability-content");
  if (!container) return;

  try {
    const res = await fetch("/api/reports/traceability");
    if (res.ok) {
      const json = await res.json();
      if (Object.keys(json).length > 0) {
        container.querySelector("code").textContent = JSON.stringify(json, null, 2);
        return;
      }
    }
  } catch {}

  const sampleTrace = {
    batch_id: "LOTE-DEMO-CAPSTONE-2026",
    executado_em: new Date().toISOString(),
    total_bots_executados: 6,
    sucesso_global: true,
    cadeia_orquestracao: SMART_OFFICE_STATE.tasks.map(t => ({
      task_id: t.id,
      automation: t.automation,
      runner: t.runner,
      prioridade: t.priority,
      status: t.status,
      duracao: t.duration
    }))
  };

  container.querySelector("code").textContent = JSON.stringify(sampleTrace, null, 2);
}
