import numpy as np
import pandas as pd

from api.models.common import DecimalLabelledSeries
from api.routes.utils.money import format_dollar_value


def make_histogram(
    series: pd.Series,
) -> list[DecimalLabelledSeries]:
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    non_outliers = series[(series >= lower_bound) & (series <= upper_bound)]
    bins = list(
        np.linspace(non_outliers.min(), non_outliers.max(), 9).tolist()
    )
    bins.append(series.max())

    counts, bins = np.histogram(series, bins=bins)

    labels_dict: dict[str, int] = {}
    for left, right, count in zip(bins[:-1], bins[1:], counts):
        label = f"{format_dollar_value(left)} - {format_dollar_value(right)}"
        labels_dict[label] = count

    return [
        DecimalLabelledSeries(label=k, value=v) for k, v in labels_dict.items()
    ]
