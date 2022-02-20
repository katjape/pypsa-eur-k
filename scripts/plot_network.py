import pypsa

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from matplotlib.legend_handler import HandlerPatch
from matplotlib.patches import Circle, Patch
from pypsa.plot import projected_area_factor

from make_summary import assign_carriers
from plot_summary import rename_techs, preferred_order
from helper import override_component_attrs

plt.style.use(['ggplot', "matplotlibrc"])


def rename_techs_tyndp(tech):
    tech = rename_techs(tech)
    if "heat pump" in tech or "resistive heater" in tech:
        return "power-to-heat"
    elif tech in ["H2 Electrolysis", "methanation", "helmeth", "H2 liquefaction"]:
        return "power-to-gas"
    elif tech == "H2":
        return "H2 storage"
    elif tech in ["OCGT", "CHP", "gas boiler", "H2 Fuel Cell"]:
        return "gas-to-power/heat"
    # elif "solar" in tech:
    #     return "solar"
    elif tech == "Fischer-Tropsch":
        return "power-to-liquid"
    elif "offshore wind" in tech:
        return "offshore wind"
    elif "CC" in tech or "sequestration" in tech:
        return "CCS"
    else:
        return tech

class HandlerCircle(HandlerPatch):
    """
    Legend Handler used to create circles for legend entries. 
    
    This handler resizes the circles in order to match the same dimensional 
    scaling as in the applied axis.
    """
    def create_artists(
        self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans
    ):
        fig = legend.get_figure()
        ax = legend.axes

        unit = np.diff(ax.transData.transform([(0, 0), (1, 1)]), axis=0)[0][1]
        radius = orig_handle.get_radius() * unit * (72 / fig.dpi)
        center = 5 - xdescent, 3 - ydescent
        p = plt.Circle(center, radius)
        self.update_prop(p, orig_handle, legend)
        p.set_transform(trans)
        return [p]


def add_legend_circles(ax, sizes, labels, scale=1, srid=None, patch_kw={}, legend_kw={}):
    
    if srid is not None:
        area_correction = projected_area_factor(ax, n.srid)**2 
        print(area_correction)
        sizes = [s * area_correction for s in sizes]
    
    handles = make_legend_circles_for(sizes, scale, **patch_kw)
    
    legend = ax.legend(
        handles, labels,
        handler_map={Circle: HandlerCircle()},
        **legend_kw
    )

    ax.add_artist(legend)
    

def add_legend_lines(ax, sizes, labels, scale=1, patch_kw={}, legend_kw={}):
    
    handles = [plt.Line2D([0], [0], linewidth=s/scale, **patch_kw) for s in sizes]
    
    legend = ax.legend(
        handles, labels,
        **legend_kw
    )
    
    ax.add_artist(legend)


def add_legend_patches(ax, colors, labels, patch_kw={}, legend_kw={}):
    
    handles = [Patch(facecolor=c, **patch_kw) for c in colors]
    
    legend = ax.legend(handles, labels, **legend_kw)

    ax.add_artist(legend)


def make_legend_circles_for(sizes, scale=1.0, **kw):
    return [Circle((0, 0), radius=(s / scale)**0.5, **kw) for s in sizes]


def assign_location(n):
    for c in n.iterate_components(n.one_port_components | n.branch_components):
        ifind = pd.Series(c.df.index.str.find(" ", start=4), c.df.index)
        for i in ifind.value_counts().index:
            # these have already been assigned defaults
            if i == -1: continue
            names = ifind.index[ifind == i]
            c.df.loc[names, 'location'] = names.str[:i]


def plot_map(network, components=["links", "stores", "storage_units", "generators"],
             bus_size_factor=1.7e10, transmission=False):

    tech_colors = snakemake.config['plotting']['tech_colors']

    n = network.copy()
    assign_location(n)
    # Drop non-electric buses so they don't clutter the plot
    n.buses.drop(n.buses.index[n.buses.carrier != "AC"], inplace=True)

    costs = pd.DataFrame(index=n.buses.index)

    for comp in components:
        df_c = getattr(n, comp)
        df_c["nice_group"] = df_c.carrier.map(rename_techs_tyndp)

        attr = "e_nom_opt" if comp == "stores" else "p_nom_opt"

        costs_c = ((df_c.capital_cost * df_c[attr])
                   .groupby([df_c.location, df_c.nice_group]).sum()
                   .unstack().fillna(0.))
        costs = pd.concat([costs, costs_c], axis=1)

        print(comp, costs)

    costs = costs.groupby(costs.columns, axis=1).sum()

    costs.drop(list(costs.columns[(costs == 0.).all()]), axis=1, inplace=True)

    new_columns = (preferred_order.intersection(costs.columns)
                   .append(costs.columns.difference(preferred_order)))
    costs = costs[new_columns]

    for item in new_columns:
        if item not in tech_colors:
            print("Warning!",item,"not in config/plotting/tech_colors")

    costs = costs.stack()  # .sort_index()

    # hack because impossible to drop buses...
    n.buses.loc["EU gas", ["x", "y"]] = n.buses.loc["DE0 0", ["x", "y"]]

    n.links.drop(n.links.index[(n.links.carrier != "DC") & (
        n.links.carrier != "B2B")], inplace=True)

    # drop non-bus
    to_drop = costs.index.levels[0].symmetric_difference(n.buses.index)
    if len(to_drop) != 0:
        print("dropping non-buses", to_drop)
        costs.drop(to_drop, level=0, inplace=True, axis=0, errors="ignore")

    # make sure they are removed from index
    costs.index = pd.MultiIndex.from_tuples(costs.index.values)

    threshold = 100e6 # 100 mEUR/a
    carriers = costs.sum(level=1)
    carriers = carriers.where(carriers > threshold).dropna()
    carriers = list(carriers.index)

    # PDF has minimum width, so set these to zero
    line_lower_threshold = 500.
    line_upper_threshold = 1e4
    linewidth_factor = 2e3
    ac_color = "gray"
    dc_color = "m"

    if snakemake.wildcards["lv"] == "1.0":
        # should be zero
        line_widths = n.lines.s_nom_opt - n.lines.s_nom
        link_widths = n.links.p_nom_opt - n.links.p_nom
        title = "Added grid"

        if transmission:
            line_widths = n.lines.s_nom_opt
            link_widths = n.links.p_nom_opt
            linewidth_factor = 2e3
            line_lower_threshold = 0.
            title = "Today's grid"
    else:
        line_widths = n.lines.s_nom_opt - n.lines.s_nom_min
        link_widths = n.links.p_nom_opt - n.links.p_nom_min
        title = "Added grid"

        if transmission:
            line_widths = n.lines.s_nom_opt
            link_widths = n.links.p_nom_opt
            title = "Total grid"

    line_widths[line_widths < line_lower_threshold] = 0.
    link_widths[link_widths < line_lower_threshold] = 0.

    line_widths[line_widths > line_upper_threshold] = line_upper_threshold
    link_widths[link_widths > line_upper_threshold] = line_upper_threshold

    fig, ax = plt.subplots(subplot_kw={"projection": ccrs.EqualEarth()})
    fig.set_size_inches(7, 6)

    n.plot(
        bus_sizes=costs / bus_size_factor,
        bus_colors=tech_colors,
        line_colors=ac_color,
        link_colors=dc_color,
        line_widths=line_widths / linewidth_factor,
        link_widths=link_widths / linewidth_factor,
        ax=ax,  **map_opts
    )

    sizes = [20, 10, 5]
    labels = [f"{s} bEUR/a" for s in sizes]

    legend_kw = dict(
        loc="upper left",
        bbox_to_anchor=(0.01, 1.06),
        labelspacing=0.8,
        frameon=False,
        handletextpad=0,
        title='System cost',
    )

    add_legend_circles(
        ax,
        sizes,
        labels,
        scale=bus_size_factor/1e9,
        srid=n.srid,
        patch_kw=dict(facecolor="lightgrey"),
        legend_kw=legend_kw
    )

    sizes = [10, 5]
    labels = [f"{s} GW" for s in sizes]

    legend_kw = dict(
        loc="upper left",
        bbox_to_anchor=(0.27, 1.06),
        frameon=False,
        labelspacing=0.8,
        handletextpad=1,
        title=title
    )

    add_legend_lines(
        ax,
        sizes,
        labels,
        scale=linewidth_factor/1e3,
        patch_kw=dict(color='lightgrey'),
        legend_kw=legend_kw
    )
    
    legend_kw = dict(
        bbox_to_anchor=(1.52, 1.04),
        frameon=False,
    )

    colors = [tech_colors[c] for c in carriers] + [ac_color, dc_color]
    labels = carriers + ["HVAC line", "HVDC link"]

    add_legend_patches(
        ax,
        colors,
        labels,
        legend_kw=legend_kw,
    )

    fig.savefig(
        snakemake.output.map,
        transparent=True,
        bbox_inches="tight"
    )


def plot_h2_map(network):

    tech_colors = snakemake.config['plotting']['tech_colors']

    n = network.copy()
    if "H2 pipeline" not in n.links.carrier.unique():
        return

    assign_location(n)

    bus_size_factor = 1e5
    linewidth_factor = 1e4
    # MW below which not drawn
    line_lower_threshold = 1e3

    # Drop non-electric buses so they don't clutter the plot
    n.buses.drop(n.buses.index[n.buses.carrier != "AC"], inplace=True)

    carriers = ["H2 Electrolysis", "H2 Fuel Cell"]

    elec = n.links[n.links.carrier.isin(carriers)].index

    bus_sizes = n.links.loc[elec,"p_nom_opt"].groupby([n.links["bus0"], n.links.carrier]).sum() / bus_size_factor

    # make a fake MultiIndex so that area is correct for legend
    bus_sizes.rename(index=lambda x: x.replace(" H2", ""), level=0, inplace=True)

    n.links.drop(n.links.index[~n.links.carrier.str.contains("H2 pipeline")], inplace=True)

    h2_new = n.links.loc[n.links.carrier=="H2 pipeline"]

    h2_retro = n.links.loc[n.links.carrier=='H2 pipeline retrofitted']

    if not h2_retro.empty:

        positive_order = h2_retro.bus0 < h2_retro.bus1
        h2_retro_p = h2_retro[positive_order]
        swap_buses = {"bus0": "bus1", "bus1": "bus0"}
        h2_retro_n = h2_retro[~positive_order].rename(columns=swap_buses)
        h2_retro = pd.concat([h2_retro_p, h2_retro_n])

        h2_retro["index_orig"] = h2_retro.index
        h2_retro.index = h2_retro.apply(
            lambda x: f"H2 pipeline {x.bus0.replace(' H2', '')} -> {x.bus1.replace(' H2', '')}",
            axis=1
        )

        retro_w_new_i = h2_retro.index.intersection(h2_new.index)
        h2_retro_w_new = h2_retro.loc[retro_w_new_i]

        retro_wo_new_i = h2_retro.index.difference(h2_new.index)
        h2_retro_wo_new = h2_retro.loc[retro_wo_new_i]
        h2_retro_wo_new.index = h2_retro_wo_new.index_orig

        to_concat = [h2_new, h2_retro_w_new, h2_retro_wo_new]
        h2_total = pd.concat(to_concat).p_nom_opt.groupby(level=0).sum()

    else:

        h2_total = h2_new

    link_widths_total = h2_total / linewidth_factor
    link_widths_total = link_widths_total.reindex(n.links.index).fillna(0.)
    link_widths_total[n.links.p_nom_opt < line_lower_threshold] = 0.

    retro = n.links.p_nom_opt.where(n.links.carrier=='H2 pipeline retrofitted', other=0.)
    link_widths_retro = retro / linewidth_factor
    link_widths_retro[n.links.p_nom_opt < line_lower_threshold] = 0.

    n.links.bus0 = n.links.bus0.str.replace(" H2", "")
    n.links.bus1 = n.links.bus1.str.replace(" H2", "")

    fig, ax = plt.subplots(
        figsize=(7, 6),
        subplot_kw={"projection": ccrs.EqualEarth()}
    )

    color_h2_pipe = '#b3f3f4'
    color_retrofit = '#54cacd'
    
    bus_colors = {
        "H2 Electrolysis": "#ff29d9",
        "H2 Fuel Cell": "#6b3161",
    }

    n.plot(
        geomap=True,
        bus_sizes=bus_sizes,
        bus_colors=bus_colors,
        link_colors=color_h2_pipe,
        link_widths=link_widths_total,
        branch_components=["Link"],
        ax=ax,
        **map_opts
    )

    n.plot(
        geomap=True,
        bus_sizes=0,
        link_colors=color_retrofit,
        link_widths=link_widths_retro,
        branch_components=["Link"],
        ax=ax,
        color_geomap=False,
        boundaries=map_opts["boundaries"]
    )

    sizes = [50, 10]
    labels = [f"{s} GW" for s in sizes]

    legend_kw = dict(
        loc="upper left",
        bbox_to_anchor=(0, 1),
        labelspacing=0.8,
        handletextpad=0,
        frameon=False,
    )

    add_legend_circles(ax, sizes, labels,
        scale=bus_size_factor/1e3,
        srid=n.srid,
        patch_kw=dict(facecolor='lightgrey'),
        legend_kw=legend_kw
    )

    sizes = [50, 10]
    labels = [f"{s} GW" for s in sizes]

    legend_kw = dict(
        loc="upper left",
        bbox_to_anchor=(0.23, 1),
        frameon=False,
        labelspacing=0.8,
        handletextpad=1,
    )

    add_legend_lines(
        ax,
        sizes,
        labels,
        scale=linewidth_factor/1e3,
        patch_kw=dict(color='lightgrey'),
        legend_kw=legend_kw,
    )

    colors = [bus_colors[c] for c in carriers] + [color_h2_pipe, color_retrofit]
    labels = carriers + ["H2 pipeline (total)", "H2 pipeline (repurposed)"]

    legend_kw = dict(
        loc="upper left",
        bbox_to_anchor=(0, 1.13),
        ncol=2,
        frameon=False,
    )

    add_legend_patches(
        ax,
        colors,
        labels,
        legend_kw=legend_kw
    )

    fig.savefig(
        snakemake.output.map.replace("-costs-all","-h2_network"),
        bbox_inches="tight"
    )


def plot_ch4_map(network):

    n = network.copy()

    if "gas pipeline" not in n.links.carrier.unique():
        return

    assign_location(n)

    bus_size_factor = 8e7
    linewidth_factor = 1e4
    # MW below which not drawn
    line_lower_threshold = 500

    # Drop non-electric buses so they don't clutter the plot
    n.buses.drop(n.buses.index[n.buses.carrier != "AC"], inplace=True)

    fossil_gas_i = n.generators[n.generators.carrier=="gas"].index   
    fossil_gas = n.generators_t.p.loc[:,fossil_gas_i].mul(n.snapshot_weightings.generators, axis=0).sum().groupby(n.generators.loc[fossil_gas_i,"bus"]).sum() / bus_size_factor
    fossil_gas.rename(index=lambda x: x.replace(" gas", ""), inplace=True)
    fossil_gas = fossil_gas.reindex(n.buses.index).fillna(0)
    # make a fake MultiIndex so that area is correct for legend
    fossil_gas.index = pd.MultiIndex.from_product([fossil_gas.index, ["fossil gas"]])

    methanation_i = n.links[n.links.carrier.isin(["helmeth", "Sabatier"])].index
    methanation = abs(n.links_t.p1.loc[:,methanation_i].mul(n.snapshot_weightings.generators, axis=0)).sum().groupby(n.links.loc[methanation_i,"bus1"]).sum() / bus_size_factor
    methanation = methanation.groupby(methanation.index).sum().rename(index=lambda x: x.replace(" gas", ""))
    # make a fake MultiIndex so that area is correct for legend
    methanation.index = pd.MultiIndex.from_product([methanation.index, ["methanation"]])

    biogas_i = n.stores[n.stores.carrier=="biogas"].index
    biogas = n.stores_t.p.loc[:,biogas_i].mul(n.snapshot_weightings.generators, axis=0).sum().groupby(n.stores.loc[biogas_i,"bus"]).sum() / bus_size_factor
    biogas = biogas.groupby(biogas.index).sum().rename(index=lambda x: x.replace(" biogas", ""))
    # make a fake MultiIndex so that area is correct for legend
    biogas.index = pd.MultiIndex.from_product([biogas.index, ["biogas"]])

    bus_sizes = pd.concat([fossil_gas, methanation, biogas])
    bus_sizes.sort_index(inplace=True)

    to_remove = n.links.index[~n.links.carrier.str.contains("gas pipeline")]
    n.links.drop(to_remove, inplace=True)

    link_widths_rem = n.links.p_nom_opt / linewidth_factor  
    link_widths_rem[n.links.p_nom_opt < line_lower_threshold] = 0.

    link_widths_orig = n.links.p_nom / linewidth_factor  
    link_widths_orig[n.links.p_nom < line_lower_threshold] = 0.

    max_usage = n.links_t.p0.abs().max(axis=0)
    link_widths_used =  max_usage / linewidth_factor
    link_widths_used[max_usage < line_lower_threshold] = 0.

    tech_colors = snakemake.config['plotting']['tech_colors']

    pipe_colors = {
        "gas pipeline": "#f08080",
        "gas pipeline new": "#c46868",
        "gas pipeline (2020)": 'lightgrey',
        "gas pipeline (available)": '#e8d1d1',
    }

    link_color_used = n.links.carrier.map(pipe_colors)

    n.links.bus0 = n.links.bus0.str.replace(" gas", "")
    n.links.bus1 = n.links.bus1.str.replace(" gas", "")

    bus_colors = {
        "fossil gas": tech_colors["fossil gas"],
        "methanation": tech_colors["methanation"],
        "biogas": "seagreen"
    }

    fig, ax = plt.subplots(figsize=(7,6), subplot_kw={"projection": ccrs.EqualEarth()})

    n.plot(
        bus_sizes=bus_sizes,
        bus_colors=bus_colors,
        link_colors=pipe_colors['gas pipeline (2020)'],
        link_widths=link_widths_orig,
        branch_components=["Link"],
        ax=ax, 
        geomap=True,
        **map_opts
    )

    n.plot(
        geomap=True,
        ax=ax,
        bus_sizes=0.,
        link_colors=pipe_colors['gas pipeline (available)'],
        link_widths=link_widths_rem,
        branch_components=["Link"],
        color_geomap=False,
        boundaries=map_opts["boundaries"]
    )

    n.plot(
        geomap=True,
        ax=ax,
        bus_sizes=0.,
        link_colors=link_color_used,
        link_widths=link_widths_used,
        branch_components=["Link"],
        color_geomap=False,
        boundaries=map_opts["boundaries"]
    )

    sizes = [100, 10]
    labels = [f"{s} TWh" for s in sizes]
    
    legend_kw = dict(
        loc="upper left",
        bbox_to_anchor=(0, 1.03),
        labelspacing=0.8,
        frameon=False,
        handletextpad=1,
        title='Gas Sources',
    )
    
    add_legend_circles(
        ax,
        sizes,
        labels,
        scale=bus_size_factor/1e6,
        srid=n.srid,
        patch_kw=dict(facecolor='lightgrey'),
        legend_kw=legend_kw,
    )

    sizes = [50, 10]
    labels = [f"{s} GW" for s in sizes]
    
    legend_kw = dict(
        loc="upper left",
        bbox_to_anchor=(0.25, 1.03),
        frameon=False,
        labelspacing=0.8,
        handletextpad=1,
        title='Gas Pipeline'
    )
    
    add_legend_lines(
        ax,
        sizes,
        labels,
        scale=linewidth_factor/1e3,
        patch_kw=dict(color='lightgrey'),
        legend_kw=legend_kw,
    )

    colors = list(pipe_colors.values()) + list(bus_colors.values())
    labels = list(pipe_colors.keys()) + list(bus_colors.keys())
  
    # legend on the side
    # legend_kw = dict(
    #     bbox_to_anchor=(1.47, 1.04),
    #     frameon=False,
    # )

    legend_kw = dict(
        loc='upper left',
        bbox_to_anchor=(0, 1.24),
        ncol=2,
        frameon=False,
    )

    add_legend_patches(
        ax,
        colors,
        labels,
        legend_kw=legend_kw,
    )

    fig.savefig(
        snakemake.output.map.replace("-costs-all","-ch4_network"),
        bbox_inches="tight"
    )


def plot_map_without(network):

    n = network.copy()
    assign_location(n)

    # Drop non-electric buses so they don't clutter the plot
    n.buses.drop(n.buses.index[n.buses.carrier != "AC"], inplace=True)

    fig, ax = plt.subplots(
        figsize=(7, 6),
        subplot_kw={"projection": ccrs.EqualEarth()}
    )

    # PDF has minimum width, so set these to zero
    line_lower_threshold = 200.
    line_upper_threshold = 1e4
    linewidth_factor = 3e3
    ac_color = "gray"
    dc_color = "m"

    # hack because impossible to drop buses...
    if "EU gas" in n.buses.index:
        n.buses.loc["EU gas", ["x", "y"]] = n.buses.loc["DE0 0", ["x", "y"]]

    to_drop = n.links.index[(n.links.carrier != "DC") & (n.links.carrier != "B2B")]
    n.links.drop(to_drop, inplace=True)

    if snakemake.wildcards["lv"] == "1.0":
        line_widths = n.lines.s_nom
        link_widths = n.links.p_nom
    else:
        line_widths = n.lines.s_nom_min
        link_widths = n.links.p_nom_min

    line_widths[line_widths < line_lower_threshold] = 0.
    link_widths[link_widths < line_lower_threshold] = 0.

    line_widths[line_widths > line_upper_threshold] = line_upper_threshold
    link_widths[link_widths > line_upper_threshold] = line_upper_threshold

    n.plot(
        bus_colors="k",
        line_colors=ac_color,
        link_colors=dc_color,
        line_widths=line_widths / linewidth_factor,
        link_widths=link_widths / linewidth_factor,
        ax=ax, **map_opts
    )

    handles = []
    labels = []

    for s in (10, 5):
        handles.append(plt.Line2D([0], [0], color=ac_color,
                                  linewidth=s * 1e3 / linewidth_factor))
        labels.append("{} GW".format(s))
    l1_1 = ax.legend(handles, labels,
                     loc="upper left", bbox_to_anchor=(0.05, 1.01),
                     frameon=False,
                     labelspacing=0.8, handletextpad=1.5,
                     title='Today\'s transmission')
    ax.add_artist(l1_1)

    fig.savefig(
        snakemake.output.today,
        transparent=True,
        bbox_inches="tight"
    )


def plot_series(network, carrier="AC", name="test"):

    n = network.copy()
    assign_location(n)
    assign_carriers(n)

    buses = n.buses.index[n.buses.carrier.str.contains(carrier)]

    supply = pd.DataFrame(index=n.snapshots)
    for c in n.iterate_components(n.branch_components):
        n_port = 4 if c.name=='Link' else 2
        for i in range(n_port):
            supply = pd.concat((supply,
                                (-1) * c.pnl["p" + str(i)].loc[:,
                                                               c.df.index[c.df["bus" + str(i)].isin(buses)]].groupby(c.df.carrier,
                                                                                                                     axis=1).sum()),
                               axis=1)

    for c in n.iterate_components(n.one_port_components):
        comps = c.df.index[c.df.bus.isin(buses)]
        supply = pd.concat((supply, ((c.pnl["p"].loc[:, comps]).multiply(
            c.df.loc[comps, "sign"])).groupby(c.df.carrier, axis=1).sum()), axis=1)

    supply = supply.groupby(rename_techs_tyndp, axis=1).sum()

    both = supply.columns[(supply < 0.).any() & (supply > 0.).any()]

    positive_supply = supply[both]
    negative_supply = supply[both]

    positive_supply[positive_supply < 0.] = 0.
    negative_supply[negative_supply > 0.] = 0.

    supply[both] = positive_supply

    suffix = " charging"

    negative_supply.columns = negative_supply.columns + suffix

    supply = pd.concat((supply, negative_supply), axis=1)

    # 14-21.2 for flaute
    # 19-26.1 for flaute

    start = "2013-02-19"
    stop = "2013-02-26"

    threshold = 10e3

    to_drop = supply.columns[(abs(supply) < threshold).all()]

    if len(to_drop) != 0:
        print("dropping", to_drop)
        supply.drop(columns=to_drop, inplace=True)

    supply.index.name = None

    supply = supply / 1e3

    supply.rename(columns={"electricity": "electric demand",
                           "heat": "heat demand"},
                  inplace=True)
    supply.columns = supply.columns.str.replace("residential ", "")
    supply.columns = supply.columns.str.replace("services ", "")
    supply.columns = supply.columns.str.replace("urban decentral ", "decentral ")

    preferred_order = pd.Index(["electric demand",
                                "transmission lines",
                                "hydroelectricity",
                                "hydro reservoir",
                                "run of river",
                                "pumped hydro storage",
                                "CHP",
                                "onshore wind",
                                "offshore wind",
                                "solar PV",
                                "solar thermal",
                                "building retrofitting",
                                "ground heat pump",
                                "air heat pump",
                                "resistive heater",
                                "OCGT",
                                "gas boiler",
                                "gas",
                                "natural gas",
                                "methanation",
                                "hydrogen storage",
                                "battery storage",
                                "hot water storage"])

    new_columns = (preferred_order.intersection(supply.columns)
                   .append(supply.columns.difference(preferred_order)))

    supply =  supply.groupby(supply.columns, axis=1).sum()
    fig, ax = plt.subplots()
    fig.set_size_inches((8, 5))

    (supply.loc[start:stop, new_columns]
     .plot(ax=ax, kind="area", stacked=True, linewidth=0.,
           color=[snakemake.config['plotting']['tech_colors'][i.replace(suffix, "")]
                  for i in new_columns]))

    handles, labels = ax.get_legend_handles_labels()

    handles.reverse()
    labels.reverse()

    new_handles = []
    new_labels = []

    for i, item in enumerate(labels):
        if "charging" not in item:
            new_handles.append(handles[i])
            new_labels.append(labels[i])

    ax.legend(new_handles, new_labels, ncol=3, loc="upper left", frameon=False)
    ax.set_xlim([start, stop])
    ax.set_ylim([-1300, 1900])
    ax.grid(True)
    ax.set_ylabel("Power [GW]")
    fig.tight_layout()

    fig.savefig("{}{}/maps/series-{}-{}-{}-{}-{}.pdf".format(
        snakemake.config['results_dir'], snakemake.config['run'],
        snakemake.wildcards["lv"],
        carrier, start, stop, name),
        transparent=True)


if __name__ == "__main__":
    if 'snakemake' not in globals():
        from helper import mock_snakemake
        snakemake = mock_snakemake(
            'plot_network',
            simpl='',
            clusters=45,
            lv=1.5,
            opts='',
            sector_opts='Co2L0-168H-T-H-B-I-solar+p3-dist1',
            planning_horizons=2030,
        )

    overrides = override_component_attrs(snakemake.input.overrides)
    n = pypsa.Network(snakemake.input.network, override_component_attrs=overrides)

    map_opts = snakemake.config['plotting']['map']

    plot_map(n,
        components=["generators", "links", "stores", "storage_units"],
        bus_size_factor=2e10,
        transmission=False
    )

    plot_h2_map(n)
    plot_ch4_map(n)
    plot_map_without(n)

    #plot_series(n, carrier="AC", name=suffix)
    #plot_series(n, carrier="heat", name=suffix)
