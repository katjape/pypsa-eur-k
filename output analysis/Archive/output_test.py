import pypsa

# Load the network file
network = pypsa.Network("/Users/katjapelzer/Thesis/MA_Git/pypsa-eur-k/resources/base.nc")


def plot_energy():
    energy_df = pd.read_csv(
        snakemake.input.energy, index_col=list(range(2)), header=list(range(n_header))
    )

    df = energy_df.groupby(energy_df.index.get_level_values(1)).sum()

    # convert MWh to TWh
    df = df / 1e6

    df = df.groupby(df.index.map(rename_techs)).sum()

    to_drop = df.index[
        df.abs().max(axis=1) < snakemake.params.plotting["energy_threshold"]
    ]

    logger.info(
        f"Dropping all technology with energy consumption or production below {snakemake.params['plotting']['energy_threshold']} TWh/a"
    )
    logger.debug(df.loc[to_drop])

    df = df.drop(to_drop)

    logger.info(f"Total energy of {round(df.sum().iloc[0])} TWh/a")

    if df.empty:
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.savefig(snakemake.output.energy, bbox_inches="tight")
        return

    new_index = preferred_order.intersection(df.index).append(
        df.index.difference(preferred_order)
    )

    # new_columns = df.columns.sort_values()

    fig, ax = plt.subplots(figsize=(12, 8))

    logger.debug(df.loc[new_index])

    df.loc[new_index].T.plot(
        kind="bar",
        ax=ax,
        stacked=True,
        color=[snakemake.params.plotting["tech_colors"][i] for i in new_index],
    )

    handles, labels = ax.get_legend_handles_labels()

    handles.reverse()
    labels.reverse()

    ax.set_ylim(
        [
            snakemake.params.plotting["energy_min"],
            snakemake.params.plotting["energy_max"],
        ]
    )

    ax.set_ylabel("Energy [TWh/a]")

    ax.set_xlabel("")

    ax.grid(axis="x")

    ax.legend(
        handles, labels, ncol=1, loc="upper left", bbox_to_anchor=[1, 1], frameon=False
    )

    fig.savefig(snakemake.output.energy, bbox_inches="tight")

plot (energy)