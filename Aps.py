"""Problema de entrega em um grid usando a biblioteca aigyminsper.

Instalacao: python -m pip install aigyminsper
Execucao:   python entrega_grid.py

Coordenadas (linha, coluna), conforme o mapa 4x4 da prova:
  agente=(0, 0), pacote=(1, 2), destino=(3, 3)
  obstaculos={(0, 1), (2, 2)}, pedagio={(1, 0)}
"""

from aigyminsper.search.graph import State
from aigyminsper.search.search_algorithms import BuscaCustoUniforme

_NAO_INFORMADO = object()


class EntregaGrid(State):
    """Um estado guarda a posicao do agente e do pacote.

    pacote=None significa que o pacote esta com o agente; caso contrario,
    pacote e a coordenada da celula onde ele esta.
    """

    LINHAS = 4
    COLUNAS = 4
    OBSTACULOS = frozenset({(0, 1), (2, 2)})
    PEDAGIOS = frozenset({(1, 0)})
    DESTINO = (3, 3)
    POSICAO_INICIAL_AGENTE = (0, 0)
    POSICAO_INICIAL_PACOTE = (1, 2)

    # Movimento: nome da acao e deslocamento (linha, coluna).
    MOVIMENTOS = (
        ("cima", (-1, 0)),
        ("baixo", (1, 0)),
        ("esquerda", (0, -1)),
        ("direita", (0, 1)),
    )

    def __init__(
        self, op, agente=None, pacote=_NAO_INFORMADO, custo_acao=0
    ):
        super().__init__(op)
        self.agente = agente if agente is not None else self.POSICAO_INICIAL_AGENTE
        self.pacote = (
            self.POSICAO_INICIAL_PACOTE
            if pacote is _NAO_INFORMADO
            else pacote
        )
        # A biblioteca consulta cost() no estado sucessor. Guardamos o custo
        # da acao que levou ate este estado.
        self.custo_acao = custo_acao

    def _custo_da_acao(self):
        """Toda acao custa 1; agir estando no pedagio adiciona 2."""
        return 1 + (2 if self.agente in self.PEDAGIOS else 0)

    def successors(self):
        sucessores = []
        custo = self._custo_da_acao()

        # Movimentos para celulas dentro do grid e sem obstaculos.
        for nome, (delta_linha, delta_coluna) in self.MOVIMENTOS:
            nova_posicao = (
                self.agente[0] + delta_linha,
                self.agente[1] + delta_coluna,
            )
            dentro_do_grid = (
                0 <= nova_posicao[0] < self.LINHAS
                and 0 <= nova_posicao[1] < self.COLUNAS
            )
            if dentro_do_grid and nova_posicao not in self.OBSTACULOS:
                sucessores.append(
                    EntregaGrid(
                        nome,
                        agente=nova_posicao,
                        pacote=self.pacote,
                        custo_acao=custo,
                    )
                )

        # Pegar so e permitido quando agente e pacote ocupam a mesma celula.
        if self.pacote is not None and self.agente == self.pacote:
            sucessores.append(
                EntregaGrid(
                    "pegar pacote",
                    agente=self.agente,
                    pacote=None,
                    custo_acao=custo,
                )
            )

        # Entregar coloca o pacote na celula atual do agente.
        if self.pacote is None:
            sucessores.append(
                EntregaGrid(
                    "entregar pacote",
                    agente=self.agente,
                    pacote=self.agente,
                    custo_acao=custo,
                )
            )

        return sucessores

    def is_goal(self):
        return self.pacote == self.DESTINO

    def description(self):
        return "Entregar um pacote no destino em um grid com obstaculos e pedagio."

    def cost(self):
        return self.custo_acao

    def env(self):
        # Inclui tudo que pode alterar as acoes futuras. O mapa e fixo.
        return self.agente, self.pacote


def main():
    estado_inicial = EntregaGrid("inicio")
    busca = BuscaCustoUniforme()
    solucao = busca.search(estado_inicial, pruning="general")

    if solucao is None:
        print("Nao existe solucao.")
    else:
        print("Plano otimo encontrado:")
        print(solucao.show_path())
        print("Custo otimo neste mapa: 10")


if __name__ == "__main__":
    main()
