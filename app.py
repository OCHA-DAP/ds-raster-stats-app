import dash
import dash_bootstrap_components as dbc
import dash_auth
from constants import uid, pwd


from callbacks.callbacks import register_callbacks
from layout.layout import create_layout


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Raster Stats Viz"
server = app.server
auth = dash_auth.BasicAuth(
    app,
    {uid:pwd}
)


app.layout = create_layout()

register_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=True)
