"""Simulador do Sistema Interno de Controle de Estoque (Cliente Desktop Legado).

Atende às Seções 2, 4.1, 6 (Cenário 1) do Enunciado do Capstone:
- Sistema desktop interno simulado em Tkinter / Python (sem API REST/Web).
- Representa o cliente Windows legado de estoque que necessita de sessão gráfica dedicada.
- Suporta operação gráfica interativa e modo headless para validação em pipelines de CI/CD.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Base de dados simulada de posições de estoque interno
DADOS_ESTOQUE_PADRAO = {
    "LOTE-001": {"produto": "TV 55 OLED", "saldo_fisico": 150, "localizacao": "DOCA-01", "status": "LIBERADO", "turno": "A"},
    "LOTE-002": {"produto": "LAVADORA 12KG", "saldo_fisico": 80, "localizacao": "DOCA-02", "status": "LIBERADO", "turno": "B"},
    "LOTE-003": {"produto": "GELADEIRA FROST", "saldo_fisico": 45, "localizacao": "DOCA-01", "status": "INSPECAO", "turno": "A"},
    "LOTE-004": {"produto": "AR CONDICIONADO", "saldo_fisico": 200, "localizacao": "DOCA-03", "status": "LIBERADO", "turno": "C"},
    "LOTE-005": {"produto": "MICROONDAS 30L", "saldo_fisico": 0, "localizacao": "DOCA-02", "status": "ESGOTADO", "turno": "B"},
    "LOTE-006": {"produto": "SOUNDBAR LG", "saldo_fisico": 95, "localizacao": "DOCA-01", "status": "LIBERADO", "turno": "A"},
    "LOTE-007": {"produto": "MONITOR ULTRA", "saldo_fisico": 120, "localizacao": "DOCA-04", "status": "LIBERADO", "turno": "C"},
    "LOTE-SAB-01": {"produto": "TV 55 OLED", "saldo_fisico": 100, "localizacao": "DOCA-01", "status": "LIBERADO", "turno": "A"},
    "LOTE-SAB-02": {"produto": "LAVADORA 12KG", "saldo_fisico": 40, "localizacao": "DOCA-02", "status": "AVARIADO", "turno": "B"},
    "LOTE-SAB-03": {"produto": "GELADEIRA FROST", "saldo_fisico": 60, "localizacao": "DOCA-01", "status": "LIBERADO", "turno": "A"},
}


class SistemaEstoqueDesktop:
    """Motor de controle do Sistema Desktop de Estoque."""

    def __init__(self, db_file: Optional[Path] = None) -> None:
        self.db_file = db_file or Path("data/datapool/sistema_estoque_db.json")
        self._carregar_base()

    def _carregar_base(self) -> None:
        if self.db_file.exists():
            try:
                self.estoque = json.loads(self.db_file.read_text(encoding="utf-8"))
                return
            except Exception:
                pass
        self.estoque = dict(DADOS_ESTOQUE_PADRAO)
        self.salvar_base()

    def salvar_base(self) -> None:
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self.db_file.write_text(json.dumps(self.estoque, indent=2, ensure_ascii=False), encoding="utf-8")

    def consultar_posicao(self, lote_id: str) -> Optional[Dict[str, Any]]:
        """Consulta posição física e saldo do lote no sistema legado."""
        return self.estoque.get(lote_id)

    def listar_todos(self) -> Dict[str, Dict[str, Any]]:
        return dict(self.estoque)


def iniciar_interface_grafica() -> None:
    """Inicia a interface gráfica Tkinter para demonstração ao vivo."""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError:
        logger.warning("Tkinter não disponível neste ambiente.")
        return

    app = SistemaEstoqueDesktop()
    root = tk.Tk()
    root.title("LG Electronics — Sistema Interno de Controle de Estoque (v3.2.0 - Legado)")
    root.geometry("640x480")
    root.resizable(False, False)

    # Estilo
    style = ttk.Style()
    style.theme_use("clam")

    header = ttk.Label(
        root,
        text="SISTEMA INTERNO DE ESTOQUE — LG ELECTRONICS",
        font=("Arial", 12, "bold"),
        foreground="#A50034",
    )
    header.pack(pady=10)

    frame_busca = ttk.LabelFrame(root, text="Consulta de Lote / Posição")
    frame_busca.pack(padx=20, pady=10, fill="x")

    lbl_lote = ttk.Label(frame_busca, text="Código do Lote:")
    lbl_lote.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    ent_lote = ttk.Entry(frame_busca, width=20)
    ent_lote.grid(row=0, column=1, padx=5, pady=5)

    lbl_resultado = ttk.Label(frame_busca, text="", font=("Arial", 10, "italic"))
    lbl_resultado.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

    def buscar():
        codigo = ent_lote.get().strip().upper()
        info = app.consultar_posicao(codigo)
        if info:
            lbl_resultado.config(
                text=f"Produto: {info['produto']} | Saldo: {info['saldo_fisico']} un | "
                f"Local: {info['localizacao']} | Status: {info['status']}",
                foreground="green",
            )
        else:
            lbl_resultado.config(text="LOTE NÃO ENCONTRADO NA BASE DE ESTOQUE.", foreground="red")

    btn_buscar = ttk.Button(frame_busca, text="Consultar Físico (F2)", command=buscar)
    btn_buscar.grid(row=0, column=2, padx=5, pady=5)

    # Tabela de lotes
    frame_tabela = ttk.LabelFrame(root, text="Posições Físicas em Aberto")
    frame_tabela.pack(padx=20, pady=10, fill="both", expand=True)

    colunas = ("Lote", "Produto", "Saldo", "Doca", "Status", "Turno")
    tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=8)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=95, anchor="center")

    for lote, dados in app.listar_todos().items():
        tree.insert("", "end", values=(lote, dados["produto"], dados["saldo_fisico"], dados["localizacao"], dados["status"], dados["turno"]))

    tree.pack(fill="both", expand=True, padx=5, pady=5)

    status_bar = ttk.Label(root, text="Sessão Gráfica Dedicada: RUNNER_DESKTOP_01 | Status: ONLINE", relief="sunken", anchor="w")
    status_bar.pack(side="bottom", fill="x")

    root.mainloop()


if __name__ == "__main__":
    iniciar_interface_grafica()
