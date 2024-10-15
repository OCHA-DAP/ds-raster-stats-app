import dash
import dash_bootstrap_components as dbc

from callbacks.callbacks import register_callbacks
from layout.layout import create_layout

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Raster Stats Viz"

app.layout = create_layout()

register_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=True)
