import copy
from itertools import compress
import numpy as np
import scipy as sp
import scipy.stats

#plotting
import plotly.offline as pyo
import plotly.graph_objs as go
import plotly as py
import colorlover as cl
import plotly.figure_factory as ff

# internal files
from plotly_scientific_plots.plotly_misc import in_notebook, plotOut, _massageData, _getCols, _extend_range
from plotly_scientific_plots.misc_computational_tools import removeOutliers, removeNaN, norm_mat
from plotly_scientific_plots.plot_subcomponents import *


###Scientific Plots
def plotHist(data,              # 1D list/np vector of data
            maxData=1000,       #  max # of points to plot above histogram (if too high, it will be slow)
            plot=True,          #1/0. If 0, returns plotly json object, but doesnt plot
            title='Distribution', # plot title
            xlbl='',            # plot label
            bins=40,            # number of histogram bins
            rm_outliers = False, #1/0 whether to remove outliers or not
            density = True,		# whether to plot PDF or count
            boxplot = True,     # 1/0 whether to do upper boxplot
            scatter = True,     # 1/0 add upper scatterplot
            diff_tst = 0):        # 1/0. If 1 assumes we checking for a signif difference from 0
    """
    Plots a 1D histogram using plotly.
    Does the binning w/ numpy to make it go way faster than plotly's inherent histogram function

    Usage:
    x = np.random.normal(0,1,(100))
    plotHist(x, title='Normal Distribution', xlbl='values', diff_tst=1)

    :return: NA
    """

    data = np.array(data)

    # remove NaNs/Infs
    try:
        data = data[~np.isnan(data)]
        data = data[np.isfinite(data)]
    except:
        print('Failed to do NaN removal')

    N = len(data)

    adj, corr_data, outliers, rng, stats = removeOutliers(data, stdbnd=6, percclip=[5, 95], rmv=rm_outliers)

    hy, hx = np.histogram(data, bins=bins, density=density, range=rng)
    top = np.max(hy)*1.1
    jitter = .02

    traces = []
    hist = go.Bar(x=hx, y=hy, name='Hist', opacity=.5,
                       marker=dict(color='red',
                                   line=dict(color='black', width=2)))
    traces += [hist]

    # if data too large only plot a subset
    if scatter:
        if N>maxData:
            Np = maxData
            dataToPlot = np.random.choice(data, Np, replace=False)
        else:
            dataToPlot, Np = data, N
        dataPlot = go.Scatter(x=dataToPlot, y=top+np.random.normal(size=Np)*top*jitter, name='data', mode = 'markers',
                         marker = dict(color='black', size = 2), hoverinfo='x+name')
        traces += [dataPlot]

    #boxplot
    if boxplot:
        bp = boxPlot(stats['med'], np.percentile(data, [25, 75]), rng, mean=stats['mean'],
                      horiz=True, offset=top * 1.2, plot=False, col='red', showleg=True)
        traces += bp

    if diff_tst:
        vertline = go.Scatter(x=[0,0], y=[0,top*1.1], name='x=0', showlegend=1, line=dict(color='black', width=2, dash='dot'))
        traces += [vertline]
        _, Pt = sp.stats.ttest_1samp(data, 0)
        _, Pw = sp.stats.wilcoxon(data)
        title += ' P_t=%.2f. P_w=%.2f' % (Pt, Pw)

    ylbl = 'Probability Density' if density else 'Count'

    fig = go.Figure(data=traces,
                   layout={'title':title,
                            'yaxis':{'title': ylbl},
                            'xaxis':{'title': xlbl, 'range': [rng[0]*.9,rng[1]*1.1]},
                            'bargap':0,
                            'hovermode': 'closest',
                           }
                    )

    return plotOut(fig, plot)


def plot2Hists(x1,              # data of 1st histogram
               x2,              # data of 2nd histogram
               names=['A','B'], # legend names of x1, x2 (ex: ['A','B']
               xlbl='',
               maxData=500,     # max # of points to plot above histogram (if too high, it will be slow)
               normHist=True,   # 1/0. if 1, norms the histogram to a PDF
               samebins=True,   # whether both hists should have same edges
               numbins=40,      # # bins in histogram
               title='Data Distribution', # title of plot
               rm_outliers = False, #1/0 whether to remove outliers or not
               KS=False,        # whether to do 2 sample KS test for different distributions
               MW=False,        # whether to display the Mann-Whitney/Ranksum test for difference of distributions in title
               T=False,         # as MW, but for ttest
               alt='two-sided', # one-sided or two-sided hypothesis testing. See scipy for options
               bp=True,         # whether to add barplot above histograms
               plot=True):      # 1/0. If 0, returns plotly json object, but doesnt plot
    """
    Plots two 1D histograms using plotly.
    Does the binning w/ numpy to make it go way faster than plotly's inherent histogram function

    Usage:

 
    """

    x1=np.array(x1)
    x2=np.array(x2)
    N1, N2 = len(x1), len(x2)

    # Remove NaNs
    x1 = x1[~np.isnan(x1)]
    x2 = x2[~np.isnan(x2)]

    # remove outliers & get basic stats
    adj1, corr_data1, outliers1, rng1, stats1 = removeOutliers(x1, stdbnd=6, percclip=[5, 95], rmv=rm_outliers)
    adj2, corr_data2, outliers2, rng2, stats2 = removeOutliers(x2, stdbnd=6, percclip=[5, 95], rmv=rm_outliers)

    if samebins:
        jointrng = _extend_range(min(rng1[0], rng2[0]), max(rng1[1], rng2[1]), .05)
        bins=np.linspace(jointrng[0], jointrng[1], numbins)
    else:
        bins=numbins

    hy1, hx1 = np.histogram(x1, bins=bins, density=normHist, range=rng1)
    hy2, hx2 = np.histogram(x2, bins=bins, density=normHist, range=rng2)

    top = np.max(np.hstack((hy1,hy2))) * 1.1

    # hist plots
    traces=[]
    hist1 = go.Bar(x=hx1, y=hy1, name=names[0], legendgroup = names[0], opacity=.5,
                    marker=dict(color='red',
                              line=dict(color='black', width=2)))
    hist2 = go.Bar(x=hx2, y=hy2, name=names[1], legendgroup = names[1], opacity=.5,
                  marker=dict(color='blue',
                              line=dict(color='black', width=2)))
    traces += [hist1, hist2]

    # data plots
    if N1 > maxData:    # if data too large only plot a subset
        Np = maxData
        dataToPlot = np.random.choice(x1, Np, replace=False)
    else:
        dataToPlot, Np = x1, N1
    dataPlot1 = go.Scatter(x=dataToPlot, y=top*1.2 + np.random.normal(size=Np)*top*.03, mode='markers',
                            marker=dict(size=2, color = 'red'), hoverinfo='x+name',
                            name=names[0], legendgroup=names[0], showlegend=False)
    if N2 > maxData:    # if data too large only plot a subset
        Np = maxData
        dataToPlot = np.random.choice(x2, Np, replace=False)
    else:
        dataToPlot, Np = x2, N1
    dataPlot2 = go.Scatter(x=dataToPlot, y=top + np.random.normal(size=Np)*top*.03, mode='markers',
                            marker=dict(size=2, color = 'blue'), hoverinfo='x+name',
                            name=names[1], legendgroup=names[1], showlegend=False)
    traces += [dataPlot1, dataPlot2]

    # Boxplots
    if bp:
        bp1 = boxPlot(stats1['med'], np.percentile(x1, [25,75]), rng1, mean=stats1['mean'],
                    name=names[0], horiz=True, offset=top*1.3, legendGroup=names[0], plot=False, col='red')
        bp2 = boxPlot(stats2['med'], np.percentile(x2, [25, 75]), rng2, mean=stats2['mean'],
                      name=names[1], horiz=True, offset=top * 1.1, legendGroup=names[1], plot=False, col='blue')
        traces = traces + bp1 + bp2

    # Stat testing
    if MW:
        stat, p_MW = sp.stats.mannwhitneyu(x1, x2, alternative=alt)
        title += ' P_MW=%.3f' % (p_MW)
    if T:
        stat, p_T = sp.stats.ttest_ind(x1, x2, equal_var=True, nan_policy='omit')
        title += ' P_T=%.3f' % (p_T)
    if KS:
        stat, p_KS = sp.stats.ks_2samp(x1, x2)
        title += ' P_KS=%.3f' % (p_KS)

    plotrng = _extend_range(min(rng1[0], rng2[0]), max(rng1[1], rng2[1]), .05)
    ylbl = 'Denisty' if normHist else 'Count'
    fig = go.Figure(data=traces,
                    layout={'title': title,
                            'yaxis': {'title': ylbl},
                            'xaxis': {'range': plotrng, 'title': xlbl},
                            'barmode': 'overlay',
                            'bargap': 0,
                            'hovermode': 'closest',
                            }
                    )

    return plotOut(fig, plot)


def plotPolar(data,         # N-d list/numpy array
              names=None,   # names of cols in data (ex:['A', 'B']
              scatter= True, # whether to do polar scatter plot. Only works if N=1
              maxData=1000, # max # of points to plot above histogram (if too high, it will be slow)
              hist = True,  # 1/0 whether to plot histogram of points
              numbins=40,   # bins in histogram
              normHist=True,# whether to normalize histogram
              title='Polar Distribution',   # title of plot
              plot=True):   # 1/0. If 0, returns plotly json object, but doesnt plot
    """
    This plots a polar plot of data in plotly
    
    Usage:
    x1 = np.random.uniform(-np.pi, np.pi, (100))
    x2 = np.random.uniform(-np.pi, np.pi, (200))
    plotPolar([x1,x2], names=['A', 'B'], numbins=50)
    """

    ## Basic formatting
    if type(data) != np.ndarray:  data = np.array(data)

    if np.issubdtype(data.dtype, np.number):   #given an np array
        data = np.atleast_2d(data)
        N, Lx = data.shape
        Lx = np.matlib.repmat(Lx, 1, N)
    else: #given a data array
        N = len(data)
        Lx = [len(l) for l in data]

    if names is None:
        names = [str(i + 1) for i in range(N)]

    # make sure all data in radians
    [print('All data must be within +-pi') for col in data if (np.min(col)<-np.pi) or (np.max(col)>np.pi)]

    if N>1:
        lg = names
        showleg = True
        cols = cl.scales[str(N+1)]['qual']['Set1']
    else:
        lg=[None]
        showleg = False
        cols=['blue']

    # scale markersize
    Lxp = np.min([max(Lx), maxData])
    if Lxp > 5000:
        markersize = 1
    elif Lxp > 2000:
        markersize = 2
    elif Lxp > 1000:
        markersize = 3
    elif Lxp > 200:
        markersize = 4
    elif Lxp > 80:
        markersize = 5
    elif Lxp > 25:
        markersize = 7
    else:
        markersize = 9

    traces = []

    ## Histogram
    if hist:
        hy, hx = zip(*[np.histogram(col, bins=numbins, density=normHist, range=[-np.pi, np.pi]) for col in data])
        hx = np.array(hx)
        hy = np.array(hy)

        # add first element to last to complete the circle
        hx = np.hstack((hx, hx[:,0:1]))
        hy = np.hstack((hy, hy[:,0:1]))

        # t=theta, r=radius
        traces += [go.Scatter(t=hx[n]/np.pi*180, r=hy[n], name=names[n], mode='lines',
                              line={'width': 3, 'color':cols[n]}, hovertext=names[n], hoverinfo='name+r+t')
                    for n in range(N)]
        top = np.max(hy.flatten()) * 1.2
    else:
        top = 1

    ## Scatter
    if scatter and N==1:
        jitter = .05
        # if data too large only plot a subset
        if Lx[0,0] > maxData:
            Np = maxData
            dataToPlot = np.random.choice(data[0], Np, replace=False)
        else:
            dataToPlot, Np = data[0], Lx[0,0]
        traces += [go.Scatter(r = top+np.random.normal(size=Np)*top*jitter, t = data[0]/np.pi*180,
                        mode='markers', name=names[0] + ' scatter', marker={'size': markersize, 'color':cols[0]})]

    ## make fig
    layout = go.Layout(
        title=title,
        showlegend = showleg
    )
    fig = go.Figure(data=traces, layout=layout)
    #pyo.plot(fig)

    return plotOut(fig, plot)


def corrPlot(x,                 # 1D data vector or list of 1D data vectors
             y,                 # 1D data vector or list of 1D data vectors
             z=None,            # optional colors for the lines
             names=None,        # names of x, y (ex:['A', 'B']
             maxdata=2000,      # max # of points to plot above histogram (if too high, it will be slow)
             addCorr=True,      # whether to add correlation statistics into plot (R2, spearmanR2, Pvals, & y=mx+b)
             addCorrLine=True,     # whether to plot correlation line
             addXYline=False,      # whether to plot y=x line
             text=None,         # whether to add additional text to each point
             plot=True,         # if false, just returns plotly json object
             title='Correlation', # title of plot
             xlbl='',           #
             ylbl='',
             markersize=None,   # either None or #. If None, will automatically determine best
            ):
    """
    Plots x , y data and their trendline using plotly

    EX: plot diff between two series
        corrPlot(x, y, xlbl='A', ylbl='B', addCorr=False, addCorrLine=False, addXYline=True)
    """
    #TODO: remove outliers

    # 1st convert t ndarray
    y, x, z, names, info = _massageData(y, x=x, z=z, names=names, txt=text)
    if text is not None:
        text = np.array(text)

    # assert info['x_info']['shared'], 'All x & y vectors must be same length!!!'

    N = info['n_sigs']
    Lx = np.array([info['n_bins']] * N) if np.isscalar(info['n_bins']) else np.array(info['n_bins'])
    assert len(np.unique(Lx)) == 1, 'All x & y vectors must be same length!!!'

    # if data has too many points, remove some for speed
    Iplot = np.array([np.arange(Lx[n]) if Lx[n] < maxdata else np.random.choice(Lx[n], size=maxdata, replace=False)
             for n in range(N)]).astype(int)

    traces = []

    # determine scatterpoint colors
    if info['z_info']['provided'] is True:
        assert N == 1, 'So far coloring only works w/ 1 data series'
        cols = z
        showleg = False
        showscale = True
        line_col = ['black']
        lg = [None]
        scattertext = ['z=%d' % (i) for i in range(Lx[0])] if text is None else text
    else:
        if N > 1:
            lg = names
            showleg = False
            cols = cl.scales[str(max(3, N))]['qual']['Set1']
        else:
            lg=[None]
            showleg = True
            cols=['blue']
        line_col = cols
        showscale = False
        if text is not None:  # scattertext should be same shape as x!
            scattertext = np.atleast_2d(text)
            if scattertext.shape[0] == 1 and N > 1:
                scattertext = np.tile(scattertext, (N, 1))

    # (2) remove NaNs
    tmpx, tmpy, tmp_ip, tmp_st = [], [], [], []
    for n in range(N):
        bad = np.atleast_2d(np.isnan(x[n]) | np.isnan(y[n]))
        tmpx += [x[n][~bad[0]]]
        tmpy += [y[n][~bad[0]]]
        tmp_ip += [Iplot[n][Iplot[n] < tmpx[-1].size]]
        if text is not None:
            tmp_st += [scattertext[n][~bad[0]]]
    x = np.array(tmpx)
    y = np.array(tmpy)
    scattertext = np.array(tmp_st)
    Iplot = np.array(tmp_ip)

    # scale markersize
    Lxp = np.min([max(Lx),maxdata])
    if markersize is None:
        if Lxp > 5000:
            markersize=1
        elif Lxp >2000:
            markersize=2
        elif Lxp > 1000:
            markersize = 3
        elif Lxp > 200:
            markersize = 4
        elif Lxp > 80:
            markersize = 5
        elif Lxp > 25:
            markersize = 7
        else:
            markersize = 9

    scatPlot = [go.Scatter(x=x[n][Iplot[n]], y=y[n][Iplot[n]], name=names[n], legendgroup=lg[n], mode='markers',
                           opacity=.5,
                           text=scattertext[n][Iplot[n]] if text is not None else '',
                           marker={'size': markersize, 'color':cols[n], 'showscale':showscale, 'colorscale':'Portland'})
                for n in range(N)]
    traces += scatPlot

    annots = []
    if addCorr:
        for n in range(N):
            try:
                slope, intercept, R2, p_val, std_err = sp.stats.linregress(x[n], y[n])
                R2sp, p_val_sp = sp.stats.spearmanr(x[n], y[n])
                corrtext = 'Pearson [R2, P]=[%.2f,%.2f] <br> ' \
                           'Spearman [R2, P]=[%.2f,%.2f] <br> ' \
                           'y=%.2fx+%.2f. N=%d' \
                           % (R2, p_val, R2sp, p_val_sp, slope, intercept, Lx[n])
                #if only 1 data record print stats on graph
                annots += [dict(
                    x=0.05,
                    y=0.95 - .1 * n,
                    showarrow=False,
                    text=corrtext,
                    xref='paper',
                    yref='paper'
                )]
                if addCorrLine:
                    x_rng = [np.min(x[0]), np.max(x[0])]
                    dx_rng = x_rng[1] - x_rng[0]
                    shift = .03 # shift from edges
                    xc = np.array([x_rng[0]+dx_rng*shift, x_rng[1]-dx_rng*shift])
                    yc = slope*xc + intercept
                    corrline = [go.Scatter(x=xc, y=yc, name=names[n]+' corr', legendgroup=lg[n], showlegend=showleg,
                                mode='lines', line={'color':line_col[n]}, hovertext=corrtext, hoverinfo='name+text')]
                    traces += corrline
            except:
                pass

    if addXYline:
        x_rng = [np.min(x[0]), np.max(x[0])]
        dx_rng = x_rng[1] - x_rng[0]
        shift = .03  # shift from edges
        xc = np.array([x_rng[0] + dx_rng * shift, x_rng[1] - dx_rng * shift])
        xyline = [go.Scatter(x=xc, y=xc, name='X=Y', showlegend=True,
                               mode='lines', line={'color': 'black'})]
        traces += xyline

    showleg = False if N==1 else True

    layout = go.Layout(title=title,
                       annotations=annots,
                       xaxis={'title': xlbl},
                       yaxis={'title': ylbl},
                       hovermode='closest',
                       showlegend = showleg,
                       )
    fig = go.Figure(data=traces, layout=layout)

    return plotOut(fig, plot)


def scatterHistoPlot(x,
                     y,
                     title='2D Density Plot',
                     xlbl='',
                     ylbl='',
                     do_contour=True,
                     dot_size=2,
                     nbins=0,
                     xy_line=False,
                     plot=True
                     ):
    """
    This creates a scatter plot above a contour plots for the data
    """

    data = []
    scatter_plot = go.Scatter(
        x=x, y=y, mode='markers', name='points',
        marker=dict(color='rgb(102,0,0)', size=dot_size, opacity=0.4)
    )
    data += [scatter_plot]
    if do_contour:
        contour_plot = go.Histogram2dContour(
            x=x, y=y, name='density', ncontours=20,
            colorscale='Hot', reversescale=True, showscale=False
        )
        data += [contour_plot]
    x_density = go.Histogram(
        x=x, name='x density',
        marker=dict(color='rgb(102,0,0)'),
        yaxis='y2', nbinsx=nbins
    )
    y_density = go.Histogram(
        y=y, name='y density', marker=dict(color='rgb(102,0,0)'),
        xaxis='x2', nbinsy=nbins
    )
    data += [x_density, y_density]

    if xy_line:
        x_rng = [max(np.min(x), np.min(y)), min(np.max(x), np.max(y))]
        dx_rng = x_rng[1] - x_rng[0]
        shift = .03  # shift from edges
        xc = np.array([x_rng[0] + dx_rng * shift, x_rng[1] - dx_rng * shift])
        yc = np.array([x_rng[0] + dx_rng * shift, x_rng[1] - dx_rng * shift])
        xyline = [go.Scatter(x=xc, y=xc, name='X=Y', showlegend=True,
                             mode='lines', line={'color': 'black'})]
        data += xyline

    scatterplot_ratio = .85    # ratio of figure to be taken by scatterplot vs histograms
    layout = go.Layout(
        title=title,
        showlegend=False,
        autosize=False,
        width=600,
        height=550,
        xaxis=dict(
            title=xlbl,
            domain=[0, scatterplot_ratio],
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            title=ylbl,
            domain=[0, scatterplot_ratio],
            showgrid=False,
            zeroline=False
        ),
        margin=dict(
            t=50
        ),
        hovermode='closest',
        bargap=0,
        xaxis2=dict(
            domain=[scatterplot_ratio, 1],
            showgrid=False,
            zeroline=False
        ),
        yaxis2=dict(
            domain=[scatterplot_ratio, 1],
            showgrid=False,
            zeroline=False
        )
    )

    fig = go.Figure(data=data, layout=layout)

    return plotOut(fig, plot)


def basicBarPlot(data,          # See docstring
                 x=None,        # xtick labels. Can be numeric or str
                 names=None,    # series labels
                 title='',
                 ylbl='',
                 xlbl='',
                 error=None,
                 text=None,     # list of txt vals or 'numb' for numbers
                 sort=False,     # if True, sorts from greatest to least
                 line=None,     # add line perpendicular to bars (eg to show mean)
                 color=None,  # barplot internal color
                 width=None,    # plot width. If None, autoscales
                 plot=True):
    """
    Makes a basic bar plot where data is either:
        1. [Lx, 1] list of values.
        2. nested list of values e.g. [[1,2,3], [3,4,5]]
        3. [Lx, N] np array

    No averaging/etc... For that see barPlot or propBarPlot

    EX: psp.basicBarPlot([1,2,3,2])
    """

    data, x, z, names, info = _massageData(data, x=x, names=names)
    n_sigs = info['n_sigs']
    uniquex = not info['x_info']['shared']

    if color is None and n_sigs == 1:
        color = 'rgb(8,48,107)'

    if text == 'numb':
        text = [[f'{x:.3f}' for x in sig] for sig in data]
    elif text is None:
        text = [None] * n_sigs
    if not isinstance(text[0], list) and text[0] is not None:
        text = [text]

    if sort:
        assert n_sigs == 1, 'Sort only works w/ a single signal'
        ord = np.argsort(data)[::-1]
        data = data[0, ord]
        text = np.array(text)[0, ord]
        if x is not None:
            x = x[0, ord]

    traces = []
    for i in range(n_sigs):
        traces += [go.Bar(x=x[i*uniquex], y=data[i], text=text[i], textposition='auto', name=names[i],
                        marker=dict(
                            color=color,
                            line=dict(
                                color=color,
                                width=width),
                        ),
                        opacity=0.6)
                  ]

    layout = go.Layout(
            title=title,
            yaxis={'title': ylbl},
            xaxis={'title': xlbl},
            hovermode='closest',
            width = width,
    )
    if line:
        if not isinstance(line, list):
            line = [line]
        layout.shapes = [hline(l) for l in line]

    fig = go.Figure(data=traces, layout=layout)

    return plotOut(fig, plot)


def barPlot(data,           # list of 1D data vectors
            names=None,     # names of data vectors
            maxData=500,    # max # of points to plot above histogram (if too high, it will be slow)
            title=' ',      # title of plot
            ylbl='Mean',    # y-label
            xlbl='',
            bar=True,       # 1/0. If 0, makes boxplot instead of barplot
            stats=[],       # which stat tests to run, including [ttest, MW, ANOVA, KW] (kruchsal-wallis)
            plot=True):     # 1/0. If 0, just returns fig object
    """
    Makes a custom plotly barplot w/ data on side

    Ex: barPlot(data, names, title='Plot Title', ylbl='Metric')
    """
    # TODO: add outlier removal

    data = np.array(data)

    # remove NaNs
    data = [removeNaN(col) for col in data]

    # remove any empty data columns
    empty_cols = [len(d) > 0 for d in data]
    data = list(compress(data, empty_cols))

    N = len(data)
    Lx = [len(col) for col in data]

    if names is None:
        names = [str(i + 1) for i in range(N)]
    else:
        names = list(compress(names, empty_cols))

    if N<3:
        cols = cl.scales[str(3)]['qual']['Set1'][0:N]
    elif N<=12:
        cols = cl.scales[str(N)]['qual']['Set3']
    else:
        cols = ['blue'] * N

    jitter = .03

    means = np.array([np.mean(col) for col in data])
    meds = np.array([np.median(col) for col in data])
    std = np.array([np.std(col) for col in data])

    traces = []
    if bar:
        bars = [go.Bar(
            x=list(range(N)),
            y=means,
            marker=dict(
                color=cols),
            text=['median= %.4f' % (m) for m in meds],
            name='BAR',
            error_y=dict(
                type='data',
                array=std,
                visible=True
            ),
            showlegend=False
        )]
        traces += bars
    else:
        #implement boxplot
        boxwidth = 50
        quartiles = np.array([np.percentile(data[n], [25, 75]) for n in range(N)])
        minmax=np.array([np.percentile(data[n],[5,95]) for n in range(N)])
        boxs = [boxPlot(meds[n], quartiles[n], minmax[n], mean=means[n], outliers=None, name=names[n], horiz=0, offset=n,
                legendGroup='boxplot', showleg=False, plot=False, col=cols[n], width=boxwidth) for n in range(N)]
        traces += sum(boxs,[])

    # scale markersize
    Lxp = min(maxData, np.max(Lx))
    if Lxp > 5000:
        markersize = 1
    elif Lxp > 2000:
        markersize = 2
    elif Lxp > 1000:
        markersize = 3
    elif Lxp > 200:
        markersize = 4
    elif Lxp > 80:
        markersize = 5
    else:
        markersize = 7

    # reduce length of data for plotting
    data_to_plot = [np.random.choice(col, maxData, replace=False) if len(col) > maxData else col for col in data]

    dataPlot = [go.Scatter(x=i + .5 + np.random.normal(size=len(data_to_plot[i])) * jitter,
                           y=data_to_plot[i],
                           mode='markers',
                           marker=dict(size=markersize, color=cols[i]),
                           name=names[i])
                for i in range(N)]
    traces += dataPlot

    xaxis = go.layout.XAxis(
        title=xlbl,
        showgrid=True,
        showline=True,
        ticks="",
        showticklabels=True,
        linewidth=2,
        ticktext=names,
        tickvals=list(range(N)),
        tickfont=dict(size=18)
    )

    # if data has huge outliers, manually bring axes closer to look better
    auto_rng = np.max([np.max(col) for col in data_to_plot]) < 2*np.max(means+std)

    # stats
    statvals = []
    if 'MW' in stats and N==2:
        try:
            stat, pval = sp.stats.mannwhitneyu(data[0], data[1], alternative='two-sided')
            statvals += [['MW', pval]]
        except:
            print('Could not process MW stats')
    if 'ttest' in stats and N==2:
        stat, pval = sp.stats.ttest_ind(data[0], data[1])
        statvals += [['T-test', pval]]
    if 'ANOVA' in stats:
        print('ANOVA not yet implemented')
    if 'KW' in stats:
        print('Kruskal–Wallis test not yet implemented')
    if len(statvals) > 0:
        stat_str = '. '.join(['P(%s)=%.3f' % (x[0], x[1]) for x in statvals])
        title = title + '. ' + stat_str

    y_min = min(0, np.min(means-std)*2)
    layout = go.Layout(
        title=title,
        xaxis=xaxis,
        yaxis={'title': ylbl, 'range': [y_min, np.max(means+std)*2], 'autorange': auto_rng},
        bargap=.5,
        hovermode='closest',
        showlegend = False,
    )

    fig = go.Figure(data=traces, layout=layout)

    return plotOut(fig, plot)


def propBarPlot(data,           # list of 1D boolean data vectors
            names=None,     # names of data vectors
            title=' ',      # title of plot
            ylbl='Proportion',    # y-label\
            plot=True):
    """
    Makes a custom plotly proportion barplot

    Ex:
    propBarPlot(data, names=None, title='Proportion ...',  ylbl='Proportion')

    """
    data = np.array(data)
    N = len(data)
    Lx = [len(col) for col in data]

    if names is None:
        names = [str(i + 1) for i in range(N)]
    if N >= 3:
        cols = cl.scales[str(N)]['qual']['Set3']
    else:
        cols = cl.scales[str(3)]['qual']['Set3'][0:N]
    jitter = .03

    means = [np.mean(col) for col in data]
    std = [(means[n]*(1-means[n])/Lx[n])**.5 for n in range(N)]

    traces = []
    bars = [go.Bar(
        x=list(range(N)),
        y=means,
        marker=dict(
            color=cols),
        text=['N = %d' % (l) for l in Lx],
        name='BAR',
        error_y=dict(
            type='data',
            array=std,
            visible=True
        ),
        showlegend=False
    )]
    traces += bars

    xaxis = go.XAxis(
        # title="",
        showgrid=True,
        showline=True,
        ticks="",
        showticklabels=True,
        linewidth=2,
        ticktext=names,
        tickvals=list(range(N)),
        tickfont=dict(size=18)
    )

    layout = go.Layout(
        title=title,
        xaxis=xaxis,
        yaxis={'title': ylbl},
        bargap=.5,
        hovermode='closest',
        showlegend=False,
    )

    fig = go.Figure(data=traces, layout=layout)

    return plotOut(fig, plot)


def multiLine(data,         # [N,Lx] numpy array or list, where rows are each line
              x=None,       # optional x-data
              z=None,       # optional z (color) data
              txt=None,     # optional txt over points
              lines=True,   # 1/0 whether we want to plot each of the individual lines
              mean=False,    # True/False where want mean+std line
              names=None,   # names of each data list
              plot=True,    # if false, just returns plotly json object
              title='',     # title of plot
              ylbl='',      #
              xlbl='',      #
              norm=None,    # input to norm_mat function if want to norm the data
              line_mode='lines' # 'lines'/'markers'/'lines+markers'
              ):
    """
    Plots bunch of lines + mean in plotly

    Ex: psp.multiLine(data, x=x, names=[], xlbl='', ylbl='', title='')
    """

    data, x, z, names, info = _massageData(data, x=x, z=z, names=names)
    N, Lx = info['n_sigs'], info['n_bins']
    uniquex = not info['x_info']['shared']

    if norm is not None:
        data = norm_mat(data, method=norm)

    if info['z_info']['provided']:
        assert N==1, 'So far coloring only works w/ 1 data series'
        cols = z
        showleg = False
        showscale = True
        line_mode = 'lines+markers'
        markersize = 2
        scattertext = ['z=%d' % (i) for i in range(Lx)] if txt is None else txt
    else:
        if N>1:
            showleg = False
            cols = _getCols(N)
        else:
            showleg = True
            cols=['blue']
        showscale = False
        markersize = 6
        if txt is None:
            scattertext = ''
        else:
            scattertext = txt

    traces = []
    if lines:
        for i in range(N):
            traces += [go.Scatter(y=data[i], x=x[i*uniquex], name=names[i], line={'width': 1},
                                  mode=line_mode, text=scattertext,
                                  marker={'size': markersize, 'color': cols[i], 'showscale': showscale,
                                          'colorscale': 'Portland'}
                                  )]


    if mean and not uniquex:
        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        plotmean = go.Scatter(x=x[0], y=mean, name='Mean', legendgroup='mean', line={'width': 6})
        ploterror_top = go.Scatter(
            x=x[0],
            y=mean + std,
            fill='none',
            fillcolor='rgba(0,100,80,0.2)',
            mode='lines',
            marker=dict(color='rgba(20,100,80,0)'),
            line=dict(width=0),
            showlegend=False,
            legendgroup='mean',
            name = 'upper bound',
            opacity = .7,
        )
        ploterror_bottom = go.Scatter(
            x=x[0],
            y=mean - std,
            fill='tonexty',
            fillcolor='rgba(0,100,80,0.2)',
            mode='lines',
            marker=dict(color="444"),
            line=dict(width=0),
            showlegend=False,
            legendgroup='mean',
            name='lower bound',
            opacity=.7,
        )
        traces = [plotmean, ploterror_top, ploterror_bottom] + traces

    if info['x_info']['provided'] and isinstance(x[0][0], str):
        xaxis = {   'title': xlbl,
                    'showgrid': True,
                    'showticklabels': True,
                    'tickvals': x[0],
                    'tickfont': dict(size=18)
                 }
    else:
        xaxis = {'title': xlbl}

    layout = go.Layout(title=title,
                       xaxis=xaxis,
                       yaxis={'title': ylbl},
                       )
    fig = go.Figure(data=traces, layout=layout)

    return plotOut(fig, plot)


def multiMean(data,
              x=None,
              plot_std=True,
              names=None,
              plot=True,
              title='',
              ylbl='',
              xlbl='',
              norm=None,
              indiv=False,
              indivnames=None):
    """
    Plots means of multiple data matrices
    :param data: list of data matrices
    :param x: optional x-data
    :param plot_std: 1/0. If 1 plots shaded std deviation around mean
    :param names: names of data
    :param plot: if false, just returns plotly json object
    :param title: title of plot
    :param ylbl:
    :param xlbl:
    :param norm: nput to norm_mat function if want to norm the data
    :param indiv: 1/0 whether we want to plot each of the individual lines
    :param indivnames: names of individual line traces
    :return:
    """
    data = [np.atleast_2d(np.array(d)) for d in data]
    N = len(data)
    Ncol, Lx = zip(*[d.shape for d in data])
    if len(np.unique(Lx)) != 1: raise ValueError('Input data sources must be of the same length (Lx)')
    Lx = Lx[0]

    if norm is not None:
        data = [norm_mat(d, method=norm) for d in data]
    if names is None: names = ['#%d' % (i) for i in range(N)]
    if x is None: x = np.array(range(Lx))
    x = np.atleast_2d(x)

    traces = []
    cols = cl.scales[str(max(3, N))]['qual']['Set1']
    tcols = ['rgba' + c[3:-1] + ',.2)' for c in cols]
    for n in range(N):
        mean = np.mean(data[n], axis=0)
        std = np.std(data[n], axis=0)
        plotmean = go.Scatter(x=x[0], y=mean, name=names[n], legendgroup=names[n], line={'width': 4, 'color': cols[n]})
        traces += [plotmean]
        if plot_std:
            ploterror_top = go.Scatter(
                x=x[0],
                y=mean + std,
                fill='none',
                fillcolor=tcols[n],
                mode='lines',
                marker=dict(color=tcols[n]),
                line=dict(width=0),
                showlegend=False,
                legendgroup=names[n],
                name=names[n] + ' UB',
                opacity=.7,
            )
            ploterror_bottom = go.Scatter(
                x=x[0],
                y=mean - std,
                fill='tonexty',
                fillcolor=tcols[n],
                mode='lines',
                marker=dict(color=tcols[n]),
                line=dict(width=0),
                showlegend=False,
                legendgroup=names[n],
                name=names[n] + ' LB',
                opacity=.7,
            )
            traces += [ploterror_top, ploterror_bottom]
        if indiv and Ncol[n]>1:
            inames = ['']*Ncol[n] if indivnames is None else indivnames
            indivlines = [go.Scatter(x=x[0], y=l, showlegend=c==0, name=names[n] + ' |', legendgroup=names[n] + ' |',
                                     hovertext=inames[c], hoverinfo='text', opacity=.3,
                                     line={'width': 1, 'color': cols[n], 'dash': 'dot'})
            for c, l in enumerate(data[n])]
            traces += indivlines

    layout = go.Layout(title=title,
                       xaxis={'title': xlbl},
                       yaxis={'title': ylbl},
                       hovermode='closest',
                       )
    fig = go.Figure(data=traces, layout=layout)

    return plotOut(fig, plot)


def plotHist2D(x,           # 1D vector
               y,           # 1D vector
               bins=[15, 30],   # # of bins in histogram
               xlbl='',
               ylbl='',
               title='',
               log=False,   # whether to log the histogram counts
               mean=False,  # whether to overlay mean + std dhading onto heatmap
               plot=True
               ):
    """
    plots 2D heatmap. Does the binning in np as its faster than plotly 2D hist
    """
    x = np.array(x)
    y = np.array(y)
    maxstd = 8  # if max above this many stddevs from mean, it is clipped
    percclip = [5, 95]  # percentile above which it is clipped
    meanx, stdx, minx, maxx = np.mean(x), np.std(x), np.min(x), np.max(x)
    xbins = np.linspace(*np.percentile(x, percclip),
                        bins[0]) if meanx + maxstd * stdx < maxx or meanx - maxstd * stdx > minx else bins[0]
    meany, stdy, miny, maxy = np.mean(y), np.std(y), np.min(y), np.max(y)
    ybins = np.linspace(*np.percentile(y, percclip),
                        bins[1]) if meany + maxstd * stdy < maxy or meany - maxstd * stdy > miny else bins[1]

    H, xedges, yedges = np.histogram2d(x, y, bins=[xbins, ybins], normed=False)
    H = H.T  # extremely important!!!!!

    if log:
        H[H == 0] = np.nan
        H = np.log10(H);
        zlbl = 'log(Count)'
    else:
        zlbl = 'Count'

    hist = go.Heatmap(
        x=xedges,  # sample to be binned on the x-axis
        y=yedges,  # sample to be binned on of the y-axis
        z=H,
        name='Heatmap',
        zsmooth='best',  # (!) apply smoothing to contours
        colorscale='Portland',  # choose a pre-defined color scale
        colorbar={'titleside': 'right',  # put title right of colorbar
                    'ticks': 'outside',  # put ticks outside colorbar
                    'title': zlbl}
        )

    plots=[hist]

    # plotting trendline
    if mean:
        Hnorm = copy.deepcopy(H)
        Hnorm[np.isnan(Hnorm)]=0
        Hnorm = Hnorm / np.sum(Hnorm, axis=0)
        Px_given_y = np.atleast_2d(yedges[:-1]) @ Hnorm
        dx = xedges[1]-xedges[0]
        meanLine = [go.Scatter(x=xedges+dx/2, y=Px_given_y[0], name='Trendline', showlegend=True)]
        plots = meanLine + plots

    layout = go.Layout(title=title,
                       xaxis={'title': xlbl},
                       yaxis={'title': ylbl},
                       showlegend=True,
                       )

    fig = go.Figure(data=plots, layout=layout)

    return plotOut(fig, plot)


def boxPlot(med, quartiles, minmax, mean=None, outliers=None, name='boxplot', horiz=True, offset=0,
            legendGroup='boxplot', showleg=False, plot=False, col='blue', width=8):
    """
    Makes very light plotly boxplot. Unlike theirs, this can take externally calc'd values rather than just data to make it go much faster.
    :param med:
    :param quartiles:
    :param minmax:
    :param mean:
    :param name:
    :param horiz:
    :param offset:
    :param legendGroup:
    :param plot:
    :param col:
    :return:
    """
    show_indiv_leg=False    #set to true for debug mode
    if horiz:
        wideaxis='x'
        offsetaxis='y'
    else:
        wideaxis = 'y'
        offsetaxis = 'x'

    if mean:
        text='Median=%.3e <br> Mean=%.3e <br> [Q1,Q2]=[%.3e,%.3e] <br> [min, max]=[%.3e,%.3e]' % \
             (med,mean, *quartiles, *minmax)
    else:
        text = 'Median=%.3e <br> [Q1,Q2]=[%.3e,%.3e] <br> [min, max]=[%.2f,%.2f]' \
               % (med, *quartiles, *minmax)

    thickLine = [{wideaxis:quartiles, offsetaxis:[offset]*2,
                    'name':name, 'showlegend':showleg, 'legendgroup':legendGroup, 'type': 'scatter',
                    'line':{'color': col, 'width': width}, 'opacity':.4, 'hovertext':text, 'hoverinfo':'name+text',
                  }]
    thinLine = [{wideaxis:minmax, offsetaxis:[offset]*2,
                    'name':name, 'showlegend':show_indiv_leg, 'legendgroup':legendGroup, 'type': 'scatter',
                    'line': {'color': col, 'width': 2}, 'opacity':.4, 'hovertext':text, 'hoverinfo':'name+text'}]
    medPoint = [{wideaxis:[med], offsetaxis:[offset], 'hovertext':text, 'hoverinfo':'name+text',
                    'name':name, 'showlegend':show_indiv_leg, 'legendgroup':legendGroup, 'mode': 'markers',
                    'marker':{'color':'black', 'symbol':'square', 'size':8}, 'opacity':1}]
    boxPlots = thickLine + thinLine + medPoint
    if mean is not None:
        meanPoint = [{wideaxis: [mean], offsetaxis: [offset], 'hovertext':text, 'hoverinfo':'name+text',
                     'name': name, 'showlegend': show_indiv_leg, 'legendgroup': legendGroup,
                     'mode': 'markers',
                     'marker': {'color': 'white', 'symbol': 'diamond', 'size': 8,
                                'line': {'color':'black', 'width':1}
                               },
                     'opacity': 1,
                     'line': {'color':'black'}}]
        boxPlots += meanPoint
    if outliers is not None:
        outlierplot = [{wideaxis:outliers, offsetaxis:[offset]*len(outliers), 'name':name, 'legendgroup':legendGroup,
                        'mode':'markers', 'marker':dict(size = 2, color=col), 'hoverinfo': wideaxis+'+name'}]
        boxPlots += outlierplot
    fig = go.Figure(data=boxPlots)

    # as boxPlot is used primarily as a subcomponent in other plots, its output is not simply plotOut(fig, plot)
    if plot:
        fig = go.Figure(data=boxPlots)
        plotfunc = pyo.iplot if in_notebook() else pyo.plot
        plotfunc(fig)
    else:
        return boxPlots


def scatterMatrix(df,
                  title='Scatterplot Matrix',
                  plot=True):  # if false, just returns plotly json object
    """
    This makes a scattermatrix for data
    """

    cols = df.columns
    N = len(cols)

    fig = py.tools.make_subplots(rows=N, cols=N)

    for n1 in range(1,N+1):
        for n2 in range(1,n1+1):
            #print('n1:%d, n2:%d' %(n1,n2))
            if n1==n2:
                #plot hist
                ff = plotHist(df[cols[n1-1]],  # 1D list/np vector of data
                         maxData=500,  # max # of points to plot above histogram (if too high, it will be slow)
                         plot=False,  # 1/0. If 0, returns plotly json object, but doesnt plot
                         rm_outliers=True,  # 1/0 whether to remove outliers or not
                         density=True,  # whether to plot PDF or count
                         boxplot = 0,
                         scatter = 0,
                         diff_tst=0)
                [fig.append_trace(d, n1, n2) for d in ff.data]
            if n2 < n1:
                # plot scatter
                ff = corrPlot(df[cols[n1-1]],                 # 1D data vector or list of 1D dsata vectors
                     df[cols[n2-1]],                 # 1D data vector or list of 1D dsata vectors
                     maxdata=500,      # max # of points to plot above histogram (if too high, it will be slow)
                     addCorr=False,      # whether to add correlation statistics into plot (R2, spearmanR2, Pvals, & y=mx+b)
                     addCorrLine=False,     # whether to plot correlation line
                     addXYline=False,      # whether to plot y=x line
                     plot=False,         # if false, just returns plotly json object
                )
                [fig.append_trace(d, n1, n2) for d in ff.data]

    fig['layout'].update(title=title)
    fig['layout'].update(showlegend=False)
    [fig['layout']['yaxis' + str((n-1)*N+1)].update(title=cols[n-1]) for n in range(1,N+1)]

    return plotOut(fig, plot)

def tornadoPlot(vals,   # in Nx3 array, where columns are[low_val, orig_val, high_val]
                names,  # parameter names (list of str)
                title,
                width=40,
                xlbl = 'Output node probability',
                plot=True
                ):
    """ Makes a tornado plot in plotly """

    n_pars = len(names)
    traces = []

    # positive change lines
    traces += [go.Scatter(x=row[1:], y=[names[i]] * 2, name=names[i], legendgroup='pos_change',
                          line={'color': 'green', 'width': width})
               for i, row in enumerate(vals)]
    traces += [go.Scatter(x=row[:2], y=[names[i]] * 2, name=names[i], legendgroup='neg_change',
                          line={'color': 'red', 'width': width})
               for i, row in enumerate(vals)]

    layout = go.Layout(title=title,
                       xaxis={'title': xlbl},
                       yaxis={'position': .5, 'autorange': 'reversed'},
                       # yaxis={'title': ylbl},
                       hovermode='closest',
                       showlegend=False,
                       )
    fig = go.Figure(data=traces, layout=layout)

    return plotOut(fig, plot)


def plotTable2(data, col_headers, row_headers=None, width=None, plot=True, title=None, sig_figs=3):
    '''
    Modified wrapper for Plotly table function to handle statistics with bounds.
    :return: Plotly figure or table depending on 'plot' parameter
    '''
    colors = ['#7D7F80', '#a1c3d1', '#EDFAFF']  # Example color scheme

    def truncate(n, decimals=0):
        multiplier = 10 ** decimals
        return int(n * multiplier) / multiplier

    # Prepare data, skip rounding if data is a string (contains bounds)
    processed_data = []
    for row in data:
        processed_row = []
        for item in row:
            if isinstance(item, str) or sig_figs is None:
                processed_row.append(item)
            else:
                try:
                    processed_row.append(np.round(item, sig_figs))
                except Exception as e:
                    print(f'failed to round {item} w/ sigfigs {sig_figs} due to {e}')
                    try:
                        processed_row.append(truncate(item, sig_figs))
                    except Exception as ee:
                        print(f'failed to truncate {item} w/ sigfigs {sig_figs} due to {ee}')
                        processed_row.append(item)
        processed_data.append(processed_row)

    if row_headers is not None:
        processed_data = [row_headers] + processed_data
        col_headers = [''] + col_headers

    # Define the table trace
    trace = go.Table(
        header=dict(values=col_headers,
                    fill=dict(color=colors[1]),
                    align='left',
                    font=dict(color='white', size=12)),
        cells=dict(values=processed_data,
                   fill=dict(color=colors[2]),
                   align='left'),
    )

    # Define the layout
    layout = go.Layout(
        width=width,
        title=title
    )

    # Create the figure
    fig = go.Figure(data=[trace], layout=layout)

    return plotOut(fig, plot)


def plotTable(data,
              top_headers=None, # only required if data is list/nparray, not for pandas df
              width=None,
              plot=True,
              title=None,
              ):
    '''
    Wrapper for plotly table function
    :return:
    '''
    import pandas as pd

    if type(data)==pd.core.frame.DataFrame:
        top_headers = data.columns
        tbl_data = data.values
    else:
        tbl_data = data

    n_rows, n_cols = tbl_data.shape

    # Shorten floats to reasonable length
    def format_func(x):
        try:
            return '%.3f' % float(x)
        except:
            return x
    vfunc = np.vectorize(format_func)
    tbl_data = vfunc(tbl_data)

    inp_data = np.vstack((top_headers, tbl_data))

    fig = ff.create_table(inp_data, hoverinfo='skip')

    fig.layout.width = width
    fig.layout.title = title
    fig.layout.margin = {'b': 80, 'r': 80}

    return plotOut(fig, plot)


def basicLinePlot(y,         # [n_sigs, n_bins] array (each signal is 1 row)
             x=None,        # either [n_bins] array-like signal, or [n_sigs, n_bins] signal
             title='',
             xlbl='',
             ylbl='',
             names=None,    # list of legend entries
             show_leg=True,   # whether to show leg
             plot=True
             ):
    ''' Plots a basic line. No frills (yet)'''

    y = np.atleast_2d(y)
    [n_sigs, n_bins] = y.shape

    if names is None:
        names = ['S_%d' % (n+1) for n in range(n_sigs)]

    traces = []
    for n, sig in enumerate(y):
        traces += [go.Scatter(y=sig, x=x, name=names[n], opacity=.8)]

    layout = go.Layout(title=title,
                       xaxis={'title': xlbl},
                       yaxis={'title': ylbl},
                       # yaxis={'title': ylbl},
                       hovermode='closest',
                       showlegend=show_leg,
                       )
    fig = go.Figure(data=traces, layout=layout)

    return plotOut(fig, plot)


def basicHeatmap(z,
                 x=[],
                 y=[],
                 title='',
                 xlbl='',
                 ylbl='',
                 plot=True):
    ''' Plots a basic heatmap'''
    traces = [go.Heatmap(z=z, x=x, y=y)]

    layout = go.Layout(title=title,
                       xaxis={'title': xlbl},
                       yaxis={'title': ylbl},
                       )
    fig = go.Figure(data=traces, layout=layout)

    return plotOut(fig, plot)



def plot_2d_table(matrix = None,  # optional mode to directly provide confusion matrix
                  title = None,
                  x = None,  # list of labels for each class
                  y=None,
                  ylbl='',
                  xlbl='',
                  add_totals = True,  # whether to add an extra row for class totals
                  plot = True,  # 1/0. If 0, returns plotly json object, but doesnt plot
                  fontsize=18,  # axis font
                  summary_func=None,
                  summary_str='Avg'
                  ):
    """
    Plots either a full or binarized confusion matrix

    EX: plotConfusionMatrix(y_true, y_pred, labels)
    """

    n_rows, n_cols = matrix.shape

    if x is None:
        x = ['C%d' % n for n in range(1, n_cols + 1)]

    if y is None:
        y = ['C%d' % n for n in range(1, n_rows + 1)]

    x = [str(x) for x in x]   # convert to str
    x = ['[' + x + ']' if len(x) == 1 else x for x in x]    #needed for stupid plotly bug
    y = [str(x) for x in y]   # convert to str
    y = ['[' + x + ']' if len(x) == 1 else x for x in y]    #needed for stupid plotly bug

    summary_func = summary_func or np.mean

    # adds an extra row for matrix totals
    matrix_tots =  copy.deepcopy(matrix)
    if add_totals:
        pred_tots = summary_func(matrix, 0).astype(int)
        matrix_tots = np.vstack((matrix, pred_tots))
        true_tots = summary_func(matrix_tots, 1).astype(int)
        matrix_tots = np.hstack((matrix_tots, np.atleast_2d(true_tots).T))
        x = x + [summary_str]
        y = y + [summary_str]
    xlbls_short = [x[:10] if type(x) == str else x for x in x]
    ylbls_short = [x[:10] if type(x) == str else x for x in y]

    # numeric labels
    num_xlbls = list(range(len(x)))
    num_ylbls = list(range(len(y)))

    # normalize matrix
    color_mat = copy.deepcopy(matrix_tots)
    norm_conf_matrix = matrix
    color_mat = color_mat.astype(float)
    color_mat[:norm_conf_matrix.shape[0],:norm_conf_matrix.shape[1]] = norm_conf_matrix

    # Adjust Total rows
    if add_totals:
        totals_row_shading = .0    # range 0 to 1. 0=darkest, 1=lightest
        tot_val = np.min(norm_conf_matrix) + (np.max(norm_conf_matrix) - np.min(norm_conf_matrix))*totals_row_shading
        color_mat[-1, :] = tot_val
        color_mat[:, -1] = tot_val


    fig = ff.create_annotated_heatmap(color_mat, x=num_xlbls, y=num_ylbls,
                                      colorscale='Greys', annotation_text=matrix_tots)

    fig.layout.yaxis.title = ylbl
    fig.layout.xaxis.title = xlbl
    fig.layout.xaxis.titlefont.size = fontsize
    fig.layout.yaxis.titlefont.size = fontsize
    fig.layout.xaxis.tickfont.size = fontsize - 2
    fig.layout.yaxis.tickfont.size = fontsize - 2
    fig.layout.showlegend = False
    # Add label text to axis values
    fig.layout.xaxis.tickmode = 'array'
    fig.layout.xaxis.range = [-.5, n_cols + .5]
    fig.layout.xaxis.tickvals = num_xlbls
    fig.layout.xaxis.ticktext = xlbls_short
    fig.data[0].hoverlabel.bgcolor = 'rgb(188,202,225)'
    if title is not None:
        fig.layout.title = title

    # fig.layout.yaxis.autorange = 'reversed'
    fig.layout.yaxis.tickmode = 'array'
    fig.layout.yaxis.range = [n_rows + .5, -.5]
    fig.layout.yaxis.tickvals = num_ylbls
    fig.layout.yaxis.ticktext = ylbls_short
    fig.layout.margin.l = 120   # adjust left margin to avoid ylbl overlaying tick str's

    fig['data'][0]['xgap'] = 1
    fig['data'][0]['ygap'] = 1
    ## Change annotation font (& text)
    for i in range(len(fig.layout.annotations)):
        fig.layout.annotations[i].font.size = fontsize-3

    ### Adjust totals fontstyle
    if add_totals:
        # get totals indxs
        last_column_indxs = [(n_cols + 1) * x - 1 for x in range(1, n_cols + 1)]
        last_row_indxs = list(range((n_rows + 1) * (n_rows), (n_rows + 1) ** 2))
        totals_annot_indxs = last_row_indxs + last_column_indxs
        # adjust totals font size & color
        # for i in totals_annot_indxs:
        #     fig['layout']['annotations'][i]['font'] = dict(size=fontsize, color='#000099')

        # Add border lines for total row/col
        data = list(fig['data'])
        data += [go.Scatter(x=[n_cols - .5, n_cols - .5], y=[-.5, n_rows + .5], showlegend=False,  # vert line
                            hoverinfo='none', line=dict(color='red', width=4, dash='solid'))]
        data += [go.Scatter(y=[n_rows - .5, n_rows - .5], x=[-.5, n_cols + .5], showlegend=False,  # horiz line
                            hoverinfo='none', line=dict(color='red', width=4, dash='solid'))]
        fig = go.Figure(data=data, layout=fig['layout'])

    return plotOut(fig, plot)


def combine_multiple_bar_plots(plots, prefixes, title=None, ylbl=None, xlbl=None, plot=True):
    """
    Combines an arbitrary number of Plotly bar plots into a single figure,
    applying a unique prefix to the x-axis labels of each input plot to
    distinguish between them. This version supports plots with multiple
    data series (columns).

    Parameters:
    - plots (list of plotly.graph_objs.Figure objects): A list of Plotly Figure objects,
      each containing one or more bar plots to be combined.
    - prefixes (list of str): A list of prefixes corresponding to each plot, used to
      prepend to the x-axis labels of that plot for differentiation in the combined figure.

    Returns:
    - plotly.graph_objs.Figure: A new Plotly Figure object containing the combined bar plots
      with updated x-axis labels to reflect their source plot as indicated by the prefixes.

    Note:
    - This function assumes all input plots have the same number of data series and
      they are in the order they should be combined. If plots have a different number of
      series or a different structure, adjustments to the function may be necessary.
    """
    combined_data = []
    num_columns = len(plots[0]['data'])  # Assuming all plots have the same number of columns

    # Iterate over each column
    for i in range(num_columns):
        for pp, prefix in zip(plots, prefixes):
            data_series = pp['data'][i]
            x = [f"{prefix}{label}" for label in data_series.x]  # Apply prefix to x-axis labels
            y = data_series.y
            text = data_series.text if hasattr(data_series, 'text') else [''] * len(x)
            # Create a new Bar object for this data series
            new_bar = go.Bar(name=f"{prefix.rstrip('_')}_{data_series.name}", x=x, y=y, text=text,
                             textposition='auto', marker=data_series.marker,
                             opacity=0.6)
            combined_data.append(new_bar)

    # Define the layout
    title = title or plots[0].layout.title
    xlbl = xlbl or plots[0].layout.xaxis.title
    ylbl = ylbl or plots[0].layout.yaxis.title
    layout = go.Layout(
        title=title,
        hovermode='closest',
        xaxis=dict(title=xlbl),
        yaxis=dict(title=ylbl),
        barmode='group'
    )

    # Create a new figure with the combined data and layout
    fig = go.Figure(data=combined_data, layout=layout)
    return plotOut(fig, plot)


if __name__ == '__main__':
    # this code is purely for debugging
    data_source_1 = np.random.randn(800)
    plotHist(data_source_1, title='Dataset 1', diff_tst=1)
