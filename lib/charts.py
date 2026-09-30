"""Graphiques Altair à la charte du projet : barres fines, étiquettes de valeur, axes discrets."""
import altair as alt
import pandas as pd

BRAND, GREY, ACCENT = "#1d5e43", "#b9c1bb", "#d9892b"
LEVELS = {"Faible": "#0ca30c", "Modérée": "#eda100", "Élevée": "#d03b3b"}


def _fmt(pct: bool) -> str:
    return ".0%" if pct else ",d"


def hbar(df: pd.DataFrame, value: str = "part", label: str = "libelle", pct: bool = True, sort=None,
         color: str = BRAND, highlight: str | None = None, height: int | None = None) -> alt.Chart:
    """Barres horizontales triées, valeur affichée au bout de chaque barre."""
    sort = sort if sort is not None else "-x"
    fill = (alt.condition(alt.datum[label] == highlight, alt.value(color), alt.value(GREY)) if highlight else alt.value(color))
    base = alt.Chart(df).encode(
        y=alt.Y(f"{label}:N", sort=sort, title=None, axis=alt.Axis(labelLimit=240, ticks=False, domain=False)),
        x=alt.X(f"{value}:Q", title=None, axis=None, scale=alt.Scale(domainMin=0)),
        tooltip=[alt.Tooltip(f"{label}:N", title="Catégorie"), alt.Tooltip(f"{value}:Q", title="Valeur", format=_fmt(pct))]
        + ([alt.Tooltip("menages:Q", title="Ménages", format=",d")] if "menages" in df and value != "menages" else []),
    )
    bars = base.mark_bar(cornerRadiusEnd=4, size=18).encode(color=fill)
    text = base.mark_text(align="left", dx=4, fontSize=12).encode(text=alt.Text(f"{value}:Q", format=_fmt(pct)))
    return (bars + text).properties(height=height or max(120, 30 * len(df)))


def columns(df: pd.DataFrame, value: str, label: str, order: list, colors: dict | None = None, pct: bool = False,
            color_field: str | None = None, legend: bool = False) -> alt.Chart:
    """Colonnes verticales dans un ordre imposé (classes d'âge, score, niveaux)."""
    color = (alt.Color(f"{color_field or label}:N", title=None, scale=alt.Scale(domain=list(colors), range=list(colors.values())),
                       legend=alt.Legend(orient="bottom") if legend else None)
             if colors else alt.value(BRAND))
    base = alt.Chart(df).encode(
        x=alt.X(f"{label}:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, ticks=False)),
        y=alt.Y(f"{value}:Q", title=None, axis=None),
        tooltip=[alt.Tooltip(f"{label}:N", title="Catégorie"), alt.Tooltip(f"{value}:Q", title="Valeur", format=_fmt(pct))],
    )
    return (base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=38).encode(color=color)
            + base.mark_text(dy=-8, fontSize=12).encode(text=alt.Text(f"{value}:Q", format=_fmt(pct)))).properties(height=240)


def stacked(df: pd.DataFrame, row: str, cat: str, order: list, colors: list) -> alt.Chart:
    """Barres empilées à 100 % : une ligne par groupe, segments dans l'ordre donné."""
    df = df.copy()
    df["part"] = df["menages"] / df.groupby(row)["menages"].transform("sum")
    df["ordre"] = df[cat].map({c: i for i, c in enumerate(order)})
    return alt.Chart(df).mark_bar(size=22).encode(
        y=alt.Y(f"{row}:N", title=None, axis=alt.Axis(ticks=False, domain=False, labelLimit=200)),
        x=alt.X("part:Q", stack="normalize", title=None, axis=alt.Axis(format="%", grid=False)),
        color=alt.Color(f"{cat}:N", scale=alt.Scale(domain=order, range=colors), legend=alt.Legend(orient="bottom", title=None, labelLimit=0, columns=2)),
        order=alt.Order("ordre:Q"),
        tooltip=[alt.Tooltip(f"{row}:N", title="Groupe"), alt.Tooltip(f"{cat}:N", title="Catégorie"),
                 alt.Tooltip("part:Q", title="Part", format=".1%"), alt.Tooltip("menages:Q", title="Ménages")],
    ).properties(height=80 + 55 * df[row].nunique())


def paired(df: pd.DataFrame, label: str, a: str, b: str, la: str, lb: str) -> alt.Chart:
    """Deux séries par catégorie (ex. pratiquée / jugée rentable, femmes / hommes)."""
    long = df.melt(id_vars=[label], value_vars=[a, b], var_name="serie", value_name="part")
    long["serie"] = long["serie"].map({a: la, b: lb})
    base = alt.Chart(long).encode(
        y=alt.Y(f"{label}:N", title=None, sort=list(df[label]), axis=alt.Axis(ticks=False, domain=False, labelLimit=220)),
        yOffset=alt.YOffset("serie:N", sort=[la, lb]),
        x=alt.X("part:Q", title=None, axis=None, scale=alt.Scale(domain=[0, 1.12])),
        tooltip=[alt.Tooltip(f"{label}:N", title="Catégorie"), alt.Tooltip("serie:N", title="Série"), alt.Tooltip("part:Q", title="Part", format=".1%")],
    )
    bars = base.mark_bar(cornerRadiusEnd=3, size=12).encode(
        color=alt.Color("serie:N", scale=alt.Scale(domain=[la, lb], range=[GREY, ACCENT] if "rentable" in lb else [BRAND, ACCENT]),
                        legend=alt.Legend(orient="bottom", title=None, labelLimit=0)))
    text = base.mark_text(align="left", dx=3, fontSize=11).encode(text=alt.Text("part:Q", format=".0%"))
    return (bars + text).properties(height=62 * len(df))
