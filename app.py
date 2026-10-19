"""
Dashboard de Vendas 2020 - Plotly Express + Dash
Disciplina: Visualização de Dados (IFSudesteMG)
"""
import os
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Input, Output

# ----------------------------------------------------------------------------
# 1) CARGA E PREPARAÇÃO DOS DADOS
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_excel(os.path.join(BASE_DIR, "Base_Vendas.xlsx"))

# remove a coluna vazia ("Unnamed: 9") gerada pela planilha
df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

# Valor da venda = quantidade x preço unitário
df["Total Vendas"] = df["Qtd Vendida"] * df["Preço Unitário"]

# Mês (número e nome, para ordenar corretamente)
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
df["Mês Nº"] = df["Data"].dt.month
df["Mês"] = df["Mês Nº"].map(lambda m: MESES[m - 1])

# A coluna "Loja" vem no formato "Cidade - UF"
df[["Cidade", "Estado"]] = df["Loja"].str.rsplit(" - ", n=1, expand=True)

# Regional (macro-região do IBGE a partir do Estado)
REGIONAL = {"SP": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "ES": "Sudeste",
            "BA": "Nordeste", "PE": "Nordeste", "GO": "Centro-Oeste",
            "RS": "Sul", "PR": "Sul", "SC": "Sul"}
df["Regional"] = df["Estado"].map(REGIONAL)

# Cliente (nome completo)
df["Cliente"] = df["Nome"].str.strip() + " " + df["Sobrenome"].str.strip()

# Representante: a base não tem essa coluna; usamos a Loja como unidade
# representante. Se tiver outra regra, basta alterar esta linha.
df["Representante"] = df["Loja"]

FMT_BRL = lambda v: f"R$ {v:,.0f}".replace(",", ".")
TICK_BRL = dict(tickprefix="R$ ", separatethousands=True)

# ----------------------------------------------------------------------------
# 2) FUNÇÕES AUXILIARES
# ----------------------------------------------------------------------------
def opcoes(coluna):
    return [{"label": str(v), "value": v} for v in sorted(df[coluna].unique())]


def estilo(fig, titulo):
    fig.update_layout(title=titulo, template="plotly_white",
                      margin=dict(l=40, r=20, t=60, b=40),
                      legend_title_text="")
    return fig


def figura_vazia(msg="Sem dados para o filtro selecionado"):
    fig = px.scatter()
    fig.update_layout(template="plotly_white",
                      xaxis=dict(visible=False), yaxis=dict(visible=False),
                      annotations=[dict(text=msg, showarrow=False,
                                        font=dict(size=16))])
    return fig


# ----------------------------------------------------------------------------
# 3) GRÁFICOS FIXOS (item 1 do roteiro)
# ----------------------------------------------------------------------------
# Total por mês - gráfico de linhas
vm = (df.groupby(["Mês Nº", "Mês"], as_index=False)["Total Vendas"].sum()
        .sort_values("Mês Nº"))
fig_mes = px.line(vm, x="Mês", y="Total Vendas", markers=True)
fig_mes.update_yaxes(**TICK_BRL, title="")
fig_mes.update_xaxes(title="")
estilo(fig_mes, "Total de Vendas por Mês")

# Total por representante - gráfico de barras
vr = (df.groupby("Representante", as_index=False)["Total Vendas"].sum()
        .sort_values("Total Vendas", ascending=False))
fig_rep = px.bar(vr, x="Representante", y="Total Vendas", text_auto=".3s",
                 color="Total Vendas", color_continuous_scale="Blues")
fig_rep.update_yaxes(**TICK_BRL, title="")
fig_rep.update_xaxes(title="")
fig_rep.update_coloraxes(showscale=False)
estilo(fig_rep, "Total de Vendas por Representante")

# Total por produto - tabela
vp = (df.groupby("Produto", as_index=False)
        .agg(**{"Qtd Vendida": ("Qtd Vendida", "sum"),
                "Total Vendas": ("Total Vendas", "sum")})
        .sort_values("Total Vendas", ascending=False))
vp["Total Vendas"] = vp["Total Vendas"].map(FMT_BRL)
vp["Qtd Vendida"] = vp["Qtd Vendida"].map(lambda v: f"{v:,}".replace(",", "."))

# Total por regional - gráfico de pizza
vg = df.groupby("Regional", as_index=False)["Total Vendas"].sum()
fig_reg = px.pie(vg, names="Regional", values="Total Vendas", hole=0.3)
fig_reg.update_traces(textinfo="percent+label")
estilo(fig_reg, "Total de Vendas por Regional")

# Total por estado - gráfico de barras
ve = (df.groupby("Estado", as_index=False)["Total Vendas"].sum()
        .sort_values("Total Vendas", ascending=False))
fig_est = px.bar(ve, x="Estado", y="Total Vendas", text_auto=".3s",
                 color="Estado")
fig_est.update_yaxes(**TICK_BRL, title="")
fig_est.update_layout(showlegend=False)
estilo(fig_est, "Total de Vendas por Estado")
fig_est.update_layout(showlegend=False)

# ----------------------------------------------------------------------------
# 4) LAYOUT DO DASHBOARD
# ----------------------------------------------------------------------------
CARD = {"background": "white", "borderRadius": "10px", "padding": "12px",
        "boxShadow": "0 1px 4px rgba(0,0,0,.15)", "flex": "1", "minWidth": "380px"}
ROW = {"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "16px"}
H2 = {"color": "#1f3b63", "margin": "24px 0 10px"}
LBL = {"fontWeight": "bold", "marginBottom": "4px", "display": "block"}

total_geral = df["Total Vendas"].sum()

app = Dash(__name__, title="Dashboard de Vendas 2020")
server = app.server  # usado pelo gunicorn na hospedagem

app.layout = html.Div(
    style={"fontFamily": "Segoe UI, Arial, sans-serif", "background": "#eef2f7",
           "padding": "20px", "maxWidth": "1400px", "margin": "0 auto"},
    children=[
        html.H1("Dashboard de Vendas - 2020", style={"color": "#1f3b63", "marginBottom": 0}),
        html.P(f"Faturamento total: {FMT_BRL(total_geral)}  |  "
               f"{len(df):,} vendas  |  {df['Qtd Vendida'].sum():,} unidades".replace(",", "."),
               style={"color": "#555"}),

        # ---------------- Item 1 ----------------
        html.H2("1) Visão geral das vendas", style=H2),
        html.Div(style=ROW, children=[
            html.Div(dcc.Graph(figure=fig_mes), style=CARD),
            html.Div(dcc.Graph(figure=fig_rep), style=CARD),
        ]),
        html.Div(style=ROW, children=[
            html.Div([
                html.H4("Total de Vendas por Produto", style={"marginTop": 0}),
                dash_table.DataTable(
                    data=vp.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in vp.columns],
                    style_header={"backgroundColor": "#1f3b63", "color": "white",
                                  "fontWeight": "bold"},
                    style_cell={"padding": "8px", "textAlign": "left"},
                    style_data_conditional=[{"if": {"row_index": "odd"},
                                             "backgroundColor": "#f5f8fc"}],
                ),
            ], style=CARD),
            html.Div(dcc.Graph(figure=fig_reg), style=CARD),
        ]),
        html.Div(style=ROW, children=[html.Div(dcc.Graph(figure=fig_est), style=CARD)]),

        # ---------------- Item 2 ----------------
        html.H2("2) Gráficos dinâmicos com filtros", style=H2),
        html.Div(style=ROW, children=[
            # Gráfico A: filtro Produto
            html.Div([
                html.Label("Filtro: Nome do Produto", style=LBL),
                dcc.Dropdown(id="f-produto", options=opcoes("Produto"),
                             placeholder="Todos os produtos", clearable=True),
                dcc.Graph(id="g-produto-mes"),
            ], style=CARD),
            # Gráfico B: filtro Regional
            html.Div([
                html.Label("Filtro: Regional", style=LBL),
                dcc.Dropdown(id="f-regional", options=opcoes("Regional"),
                             placeholder="Todas as regionais", clearable=True),
                dcc.Graph(id="g-regional-rep"),
            ], style=CARD),
        ]),
        html.Div(style=ROW, children=[
            # Gráfico C: filtro Mês
            html.Div([
                html.Label("Filtro: Mês", style=LBL),
                dcc.Dropdown(id="f-mes",
                             options=[{"label": m, "value": m} for m in MESES],
                             placeholder="Ano inteiro", clearable=True),
                dcc.Graph(id="g-mes-clientes"),
            ], style=CARD),
        ]),

        # ---------------- Item 3 ----------------
        html.H2("3) Filtros dependentes: Estado → Cidade", style=H2),
        html.Div(style=ROW, children=[
            html.Div([
                html.Div(style={"display": "flex", "gap": "16px", "flexWrap": "wrap"},
                         children=[
                    html.Div([html.Label("Estado do Cliente", style=LBL),
                              dcc.Dropdown(id="f-estado", options=opcoes("Estado"),
                                           placeholder="Selecione o Estado",
                                           clearable=True)],
                             style={"flex": "1", "minWidth": "220px"}),
                    html.Div([html.Label("Cidade do Cliente", style=LBL),
                              dcc.Dropdown(id="f-cidade", options=[],
                                           placeholder="Selecione o Estado primeiro",
                                           clearable=True)],
                             style={"flex": "1", "minWidth": "220px"}),
                ]),
                dcc.Graph(id="g-estado-cidade"),
            ], style=CARD),
        ]),
    ],
)


# ----------------------------------------------------------------------------
# 5) CALLBACKS
# ----------------------------------------------------------------------------
@app.callback(Output("g-produto-mes", "figure"), Input("f-produto", "value"))
def grafico_produto_mes(produto):
    d = df if produto is None else df[df["Produto"] == produto]
    g = (d.groupby(["Mês Nº", "Mês"], as_index=False)["Total Vendas"].sum()
          .sort_values("Mês Nº"))
    fig = px.area(g, x="Mês", y="Total Vendas", markers=True)
    fig.update_yaxes(**TICK_BRL, title="")
    fig.update_xaxes(title="")
    return estilo(fig, f"Vendas por Mês - {produto or 'Todos os produtos'}")


@app.callback(Output("g-regional-rep", "figure"), Input("f-regional", "value"))
def grafico_regional_rep(regional):
    d = df if regional is None else df[df["Regional"] == regional]
    g = (d.groupby("Representante", as_index=False)["Total Vendas"].sum()
          .sort_values("Total Vendas", ascending=True))
    fig = px.bar(g, x="Total Vendas", y="Representante", orientation="h",
                 text_auto=".3s", color="Total Vendas",
                 color_continuous_scale="Teal")
    fig.update_xaxes(**TICK_BRL, title="")
    fig.update_yaxes(title="")
    fig.update_coloraxes(showscale=False)
    return estilo(fig, f"Vendas por Representante - {regional or 'Todas as regionais'}")


@app.callback(Output("g-mes-clientes", "figure"), Input("f-mes", "value"))
def grafico_mes_clientes(mes):
    d = df if mes is None else df[df["Mês"] == mes]
    g = (d.groupby("Cliente", as_index=False)["Total Vendas"].sum()
          .nlargest(10, "Total Vendas").sort_values("Total Vendas"))
    fig = px.bar(g, x="Total Vendas", y="Cliente", orientation="h",
                 text_auto=".3s", color="Total Vendas",
                 color_continuous_scale="Oranges")
    fig.update_xaxes(**TICK_BRL, title="")
    fig.update_yaxes(title="")
    fig.update_coloraxes(showscale=False)
    return estilo(fig, f"Top 10 Clientes - {mes or 'Ano inteiro'}")


# Estado -> preenche o DropDown de cidades
@app.callback(Output("f-cidade", "options"), Output("f-cidade", "value"),
              Input("f-estado", "value"))
def atualiza_cidades(estado):
    if estado is None:
        return [], None
    cidades = sorted(df.loc[df["Estado"] == estado, "Cidade"].unique())
    return [{"label": c, "value": c} for c in cidades], None


@app.callback(Output("g-estado-cidade", "figure"),
              Input("f-estado", "value"), Input("f-cidade", "value"))
def grafico_estado_cidade(estado, cidade):
    d = df
    titulo = "Vendas por Produto - Brasil"
    if estado is not None:
        d = d[d["Estado"] == estado]
        titulo = f"Vendas por Produto - {estado}"
    if cidade is not None:
        d = d[d["Cidade"] == cidade]
        titulo = f"Vendas por Produto - {cidade}/{estado}"
    if d.empty:
        return figura_vazia()
    g = (d.groupby("Produto", as_index=False)["Total Vendas"].sum()
          .sort_values("Total Vendas", ascending=False))
    fig = px.bar(g, x="Produto", y="Total Vendas", text_auto=".3s", color="Produto")
    fig.update_yaxes(**TICK_BRL, title="")
    fig.update_xaxes(title="")
    fig.update_layout(showlegend=False)
    return estilo(fig, titulo)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=False, host="0.0.0.0", port=port)
