"""Otimizacao de rota de entrega em um grid com obstaculos.

Execute com ``python Aps.py`` para abrir a interface grafica. A biblioteca
``aigyminsper`` e usada para encontrar a solucao de menor custo por busca de
custo uniforme.
"""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Iterable

from aigyminsper.search.graph import Node, State
from aigyminsper.search.search_algorithms import BuscaCustoUniforme

Posicao = tuple[int, int]
_NAO_INFORMADO = object()


class EntregaGrid(State):
    """Estado formado pela posicao do agente e pela situacao do pacote."""

    LINHAS = 4
    COLUNAS = 4
    OBSTACULOS = frozenset({(0, 1), (2, 2)})
    PEDAGIOS = frozenset({(1, 0)})
    DESTINO = (3, 3)
    POSICAO_INICIAL_AGENTE = (0, 0)
    POSICAO_INICIAL_PACOTE = (1, 2)

    MOVIMENTOS = (
        ("cima", (-1, 0)),
        ("baixo", (1, 0)),
        ("esquerda", (0, -1)),
        ("direita", (0, 1)),
    )

    def __init__(
        self,
        op: str,
        agente: Posicao = POSICAO_INICIAL_AGENTE,
        pacote: Posicao | None | object = _NAO_INFORMADO,
        custo_acao: int = 0,
        *,
        tamanho: int = 4,
        obstaculos: Iterable[Posicao] = OBSTACULOS,
        destino: Posicao = DESTINO,
        posicao_inicial_pacote: Posicao = POSICAO_INICIAL_PACOTE,
        pedagios: Iterable[Posicao] = PEDAGIOS,
    ) -> None:
        super().__init__(op)
        self.tamanho = tamanho
        self.agente = agente
        self.pacote = (
            posicao_inicial_pacote if pacote is _NAO_INFORMADO else pacote
        )
        self.obstaculos = frozenset(obstaculos)
        self.destino = destino
        self.pedagios = frozenset(pedagios)
        self.custo_acao = custo_acao
        self.posicao_inicial_pacote = posicao_inicial_pacote

    def _novo_estado(
        self,
        op: str,
        agente: Posicao,
        pacote: Posicao | None,
        custo: int,
    ) -> "EntregaGrid":
        return EntregaGrid(
            op,
            agente=agente,
            pacote=pacote,
            custo_acao=custo,
            tamanho=self.tamanho,
            obstaculos=self.obstaculos,
            destino=self.destino,
            posicao_inicial_pacote=self.posicao_inicial_pacote,
            pedagios=self.pedagios,
        )

    def _custo_da_acao(self) -> int:
        return 1 + (2 if self.agente in self.pedagios else 0)

    def successors(self) -> list["EntregaGrid"]:
        sucessores: list[EntregaGrid] = []
        custo = self._custo_da_acao()

        for nome, (delta_linha, delta_coluna) in self.MOVIMENTOS:
            nova_posicao = (
                self.agente[0] + delta_linha,
                self.agente[1] + delta_coluna,
            )
            dentro_do_grid = all(0 <= coordenada < self.tamanho for coordenada in nova_posicao)
            if dentro_do_grid and nova_posicao not in self.obstaculos:
                sucessores.append(
                    self._novo_estado(nome, nova_posicao, self.pacote, custo)
                )

        if self.pacote is not None and self.agente == self.pacote:
            sucessores.append(
                self._novo_estado("pegar pacote", self.agente, None, custo)
            )

        if self.pacote is None and self.agente == self.destino:
            sucessores.append(
                self._novo_estado(
                    "entregar pacote", self.agente, self.destino, custo
                )
            )

        return sucessores

    def is_goal(self) -> bool:
        return self.pacote == self.destino

    def description(self) -> str:
        return "Entregar um pacote no destino em um grid com obstaculos."

    def cost(self) -> int:
        return self.custo_acao

    def env(self) -> tuple[Posicao, Posicao | None]:
        return self.agente, self.pacote


def gerar_instancia(tamanho: int, rng: random.Random | None = None) -> EntregaGrid:
    """Cria uma instancia aleatoria valida, que pode ou nao ser solucionavel."""
    if tamanho < 2:
        raise ValueError("A dimensao deve ser um numero inteiro maior ou igual a 2.")

    rng = rng or random.Random()
    celulas = [(linha, coluna) for linha in range(tamanho) for coluna in range(tamanho)]
    agente, pacote, destino = rng.sample(celulas, 3)
    disponiveis = [celula for celula in celulas if celula not in {agente, pacote, destino}]
    quantidade_obstaculos = rng.randint(0, len(disponiveis))
    obstaculos = rng.sample(disponiveis, quantidade_obstaculos)
    return EntregaGrid(
        "inicio",
        agente=agente,
        posicao_inicial_pacote=pacote,
        tamanho=tamanho,
        obstaculos=obstaculos,
        destino=destino,
    )


def buscar_solucao(estado_inicial: EntregaGrid) -> Node | None:
    """Retorna o no objetivo de menor custo ou None quando nao ha solucao."""
    return BuscaCustoUniforme().search(estado_inicial, pruning="general")


class Aplicacao:
    def __init__(self, janela: tk.Tk) -> None:
        self.janela = janela
        self.janela.title("Entrega otimizada em grid")
        self.janela.minsize(700, 500)
        self.instancia: EntregaGrid | None = None
        self.solucao: Node | None = None
        self.canvas = tk.Canvas(janela, background="white", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=12)

        painel = ttk.Frame(janela, padding=12)
        painel.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Label(painel, text="Dimensao do grid:").pack(anchor=tk.W)
        self.dimensao = tk.IntVar(value=8)
        ttk.Spinbox(painel, from_=2, to=30, textvariable=self.dimensao, width=8).pack(
            anchor=tk.W, pady=(4, 12)
        )
        ttk.Button(painel, text="Gerar e resolver", command=self.gerar_e_resolver).pack(
            fill=tk.X
        )
        self.status = tk.StringVar(value="Defina a dimensao e gere um mapa.")
        ttk.Label(
            painel, textvariable=self.status, wraplength=220, justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(16, 8))
        self.instrucoes = tk.StringVar()
        ttk.Label(
            painel, textvariable=self.instrucoes, wraplength=220, justify=tk.LEFT
        ).pack(anchor=tk.W)

    def gerar_e_resolver(self) -> None:
        try:
            tamanho = self.dimensao.get()
            self.instancia = gerar_instancia(tamanho)
        except (tk.TclError, ValueError) as erro:
            messagebox.showerror("Dimensao invalida", str(erro))
            return

        self.solucao = buscar_solucao(self.instancia)
        if self.solucao is None:
            self.status.set("Nao existe solucao para o estado gerado.")
            self.instrucoes.set("Tente gerar outro mapa.")
        else:
            self.status.set(f"Solucao otima encontrada (custo: {self.solucao.g}).")
            self.instrucoes.set(self.solucao.show_path())
        self.desenhar()

    def desenhar(self) -> None:
        if self.instancia is None:
            return
        self.canvas.delete("all")
        tamanho = self.instancia.tamanho
        lado = min(max(self.canvas.winfo_width(), 300), max(self.canvas.winfo_height(), 300))
        celula = max(18, lado // tamanho)
        rota: set[Posicao] = set()
        if self.solucao is not None:
            no: Node | None = self.solucao
            while no is not None:
                rota.add(no.state.agente)  # type: ignore[attr-defined]
                no = no.father_node

        cores = {
            "livre": "#ffffff",
            "obstaculo": "#343a40",
            "rota": "#bde0fe",
            "agente": "#ffb703",
            "pacote": "#90be6d",
            "destino": "#f94144",
        }
        for linha in range(tamanho):
            for coluna in range(tamanho):
                posicao = (linha, coluna)
                tipo = "livre"
                if posicao in rota:
                    tipo = "rota"
                if posicao in self.instancia.obstaculos:
                    tipo = "obstaculo"
                if posicao == self.instancia.destino:
                    tipo = "destino"
                if posicao == self.instancia.pacote:
                    tipo = "pacote"
                if posicao == self.instancia.agente:
                    tipo = "agente"
                x1, y1 = coluna * celula, linha * celula
                self.canvas.create_rectangle(
                    x1, y1, x1 + celula, y1 + celula,
                    fill=cores[tipo], outline="#adb5bd",
                )
                if tipo != "livre":
                    rotulo = {"agente": "A", "pacote": "P", "destino": "D"}.get(tipo, "")
                    if rotulo:
                        self.canvas.create_text(
                            x1 + celula / 2, y1 + celula / 2, text=rotulo,
                            font=("Arial", max(9, celula // 3), "bold"),
                        )

    def iniciar(self) -> None:
        self.janela.bind("<Configure>", lambda _evento: self.desenhar())
        self.gerar_e_resolver()
        self.janela.mainloop()


def main() -> None:
    Aplicacao(tk.Tk()).iniciar()


if __name__ == "__main__":
    main()
