from multiprocessing import Process
import numpy as np
import io
from base64 import b64encode
import dash
from dash import dcc, html, callback, Output, Input, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import json
import pickle
from plotly_scientific_plots.plotly_misc import jsonify


def create_html_download_button(figs, file_name="plotly_graph", button_name="Download as HTML"):
    """
    Creates an improved download button using dcc.Download component
    """
    # Convert from dict to Plotly figs as needed
    plotly_figs = []
    for fig in figs:
        if isinstance(fig, dict):
            plotly_figs.append(go.Figure(fig))
        else:
            plotly_figs.append(fig)
    figs = plotly_figs

    # Create a button with download functionality
    download_button = html.Button(
        button_name,
        id="download-button",
        style={
            'background-color': '#4CAF50',
            'border': 'none',
            'color': 'white',
            'padding': '10px 20px',
            'text-align': 'center',
            'text-decoration': 'none',
            'display': 'inline-block',
            'font-size': '16px',
            'margin': '4px 2px',
            'cursor': 'pointer',
            'border-radius': '4px'
        }
    )
    
    # Store the figures data in a dcc.Store component (more reliable than hidden div)
    fig_store = dcc.Store(id="fig-data-store", data=[fig.to_dict() if hasattr(fig, 'to_dict') else fig for fig in figs])
    filename_store = dcc.Store(id="filename-store", data=file_name)
    
    # JavaScript component for download functionality
    download_script = dcc.Download(id="download-html")
    
    return html.Div([download_button, fig_store, filename_store, download_script])


# Add this callback to your Dash app
@callback(
    Output("download-html", "data"),
    Input("download-button", "n_clicks"),
    [State("fig-data-store", "data"),
     State("filename-store", "data")],
    prevent_initial_call=True
)
def download_html(n_clicks, fig_data_list, filename):
    if n_clicks is None:
        raise PreventUpdate
    
    try:
        # Reconstruct figures from stored data
        figs = []
        for fig_data in fig_data_list:
            if isinstance(fig_data, dict):
                figs.append(go.Figure(fig_data))
            else:
                figs.append(fig_data)
        
        # Generate HTML content
        if len(figs) > 1:
            # Multiple figures
            html_parts = []
            
            # Write first figure with full HTML structure
            buffer = io.StringIO()
            figs[0].write_html(buffer, full_html=True, include_plotlyjs='cdn')
            html_parts.append(buffer.getvalue())
            
            # For remaining figures, extract just the plot div and script
            for i, fig in enumerate(figs[1:], 1):
                buffer = io.StringIO()
                fig.write_html(buffer, full_html=False, include_plotlyjs=False, div_id=f"plotly-div-{i}")
                plot_html = buffer.getvalue()
                
                # Insert the additional plot into the main HTML before closing body tag
                if i == 1:  # First additional plot
                    # Find the closing body tag and insert before it
                    main_html = html_parts[0]
                    insert_pos = main_html.rfind('</body>')
                    if insert_pos != -1:
                        html_parts[0] = main_html[:insert_pos] + plot_html + main_html[insert_pos:]
                    else:
                        html_parts.append(plot_html)
                else:
                    # For subsequent plots, find the last closing body tag and insert before it
                    main_html = html_parts[0]
                    insert_pos = main_html.rfind('</body>')
                    if insert_pos != -1:
                        html_parts[0] = main_html[:insert_pos] + plot_html + main_html[insert_pos:]
            
            html_content = html_parts[0]
        else:
            # Single figure
            buffer = io.StringIO()
            figs[0].write_html(buffer, include_plotlyjs='cdn')
            html_content = buffer.getvalue()
        
        # Check content size (basic validation)
        if len(html_content) == 0:
            raise Exception("Generated HTML content is empty")
        
        return dict(content=html_content, filename=f"{filename}.html")
        
    except Exception as e:
        print(f"Download error: {str(e)}")
        # Return a simple error page instead of failing
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Download Error</title></head>
        <body>
        <h1>Download Error</h1>
        <p>An error occurred while generating the dashboard: {str(e)}</p>
        <p>Please try again or contact support.</p>
        </body>
        </html>
        """
        return dict(content=error_html, filename=f"{filename}_error.html")

###Dash wrappers
def dashSubplot(plots,
                min_width=18,  # min width of column (in %). If more columns, scrolling is enabled
                max_width=50,  # max width of column (in %).
                indiv_widths=None,  # can specify list of individual column widths
                title=''        # str or list of strs
                ):

    if isinstance(title, str):
        title = [title]

    # remove empty elements of list
    plots = [[plt for plt in col if plt != []] for col in plots]    # remove empty plots from each column
    for i in range(len(plots)-1, -1, -1):   # remove empty columns
        if plots[i] == []:
            plots.pop(i)
            if indiv_widths is not None:
                indiv_widths.pop(i)

    Ncol = len(plots)  # number of columns

    if indiv_widths is None:
        col_width = [min(max_width, max(int(100/Ncol-2), min_width) )] * Ncol
    else:
        col_width = indiv_widths

    title = sum([[i, html.Br()] for i in title], [])[:-1]

    col_style = [{'width': str(col_width[i]) + '%',
             'display': 'inline-block',
             'vertical-align': 'top',
             'margin-right': '25px'} for i in range(Ncol)]

    plot_divs = html.Div([html.Div(plots[i], style=col_style[i]) for i in range(Ncol)])
    title_div = html.H3(title)
    layout = html.Div(html.Div([title_div, plot_divs]),
                      style={'margin-right': '0px', 'position': 'absolute', 'width': '100%'})

    return layout


def horizontlDiv(dashlist,
                 id='L',    # either single element or list. If single, id of html divs will be this + # (ie 'L1', 'L2', etc..
                 width=50): #either total width or list of indiv widths
    ''' Creates a horizontal Div line '''
    N = len(dashlist)
    if type(width) == int:
        indiv_width = [str(int(width/N))+'%'] * N
    elif type(width) == list:
        indiv_width = [int(w)+'%' for w in width]
    else:
        print('ERROR: width must either be int or list of ints!')

    horiz_div = [html.Div(i, id=id+str(c),
                          style={'width': indiv_width[c],
                                 'display': 'inline-block',
                                 'vertical-align': 'middle'})
                 for c, i in enumerate(dashlist)]
    return horiz_div


def dashSubplot_from_figs(figs):
    n_r = int(np.ceil(np.sqrt(len(figs))))
    i_r = 0
    i_c = 0
    d_plot = [[] for i in range(n_r)]

    for fig in figs:
        i_c += 1
        if i_c >= n_r:
            i_r += 1
            i_c = 0
        da = dcc.Graph(figure=fig, id=' ')
        d_plot[i_r].append(da)
        i_c += 1
        if i_c >= n_r:
            i_r += 1
            i_c = 0

    layout = dashSubplot(d_plot)
    return layout


def startDashboardSerial(figs,
                        min_width = 18,  # min width of column (in %). If more columns, scrolling is enabled
                        max_width = 50,  # max width of column (in %).
                        indiv_widths = None,
                        host=None,    # set to '0.0.0.0' to run as a server. Default val is None (localhost)
                        title='',
                        port=8050,
                        add_download_button=True,
                        download_filename="plotly_dashboard",
                        run=True,
                  ):
    """
    This starts the dash layout
    :param figs: a nested list of plotly figure objects. Each outer list is a column in the dashboard, and each
                        element within the outer list is a row within that column.
    :return:
    """

    # convert plotly fig objects to dash graph objects
    graphs = []
    for c_num, col in enumerate(figs):
        g_col = []
        for r_num, f in enumerate(col):
            if f == []:
                g_col += [[]]
            elif isinstance(f, dash.development.base_component.Component):
                g_col += [f]
            else:
                if 'meta' in f['layout'] and f['layout']['meta'] is not None:
                    id = f['layout']['meta']
                else:
                    id = ['row_%d_col_%d' % (r_num, c_num)]
                g_col += [dcc.Graph(figure=f, id=id[0])]
        graphs += [g_col]

    app = dash.Dash()

    # Create layout with optional download button
    dashboard_layout = dashSubplot(graphs, min_width, max_width, indiv_widths, title)

    if add_download_button:
        # Extract the original figures before conversion to dash components
        original_figs = []
        for col in figs:
            for fig in col:
                if fig != [] and not isinstance(fig, dash.development.base_component.Component):
                    original_figs.append(fig)

        # Create the download button for all figures
        download_button = create_html_download_button(
            original_figs,
            file_name=download_filename,
            button_name="Download Dashboard as HTML"
        )

        # Add download button to layout
        app.layout = html.Div([
            html.Div(download_button, style={'margin': '10px'}),
            dashboard_layout
        ])
    else:
        app.layout = dashboard_layout

    if run:
        app.run_server(port=port, debug=False, host=host)

    return app


def startDashboard(figs,
                   parr=False,  # T/F. If True, will spin seperate python process for Dash webserver
                   save=None,  # either None or save_path
                   **kwargs    # additional optional params for startDashboardSerial (e.g. min_width)
                  ):

    # First convert to json format to allow pkling for multiprocessing
    figs_dictform = jsonify(figs)

    # save if nessesary (currently only saves in pkl format)
    if save is not None and not False:
        # Note, can also use _dump_json, but its about 3x bigger filesize
        _dump_pkl(figs_dictform, save)

    if parr:
        p = Process(target=startDashboardSerial, args=(figs_dictform,), kwargs=kwargs)
        p.start()
        return p
    else:
        startDashboardSerial(figs_dictform, **kwargs)
        return None



def _dump_pkl(obj, file_path):
    ''' Saves a pkl file '''
    with open(file_path, 'wb') as dfile:
        pickle.dump(obj, dfile, protocol = 2)


def _dump_json(obj, file_path):
    ''' Saves a json file '''
    with open(file_path, 'w') as dfile:
        json.dump(obj, dfile, indent = 4)