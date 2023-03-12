import numpy as np
import pandas as pd
import lmfit


def gaussian_fit_2d_mesh(
    x: pd.Series, y: pd.Series, z: pd.Series
) -> (np.ndarray, np.ndarray, np.ndarray):
    z_plus = z - z.min()
    X, Y = np.meshgrid(
        np.linspace(x.min(), x.max(), int(x.max() - x.min()) * 10),
        np.linspace(y.min(), y.max(), int(y.max() - y.min()) * 10),
    )
    model = lmfit.models.Gaussian2dModel()
    params = model.guess(z_plus, x, y)
    result = model.fit(z_plus, x=x, y=y, params=params)
    Z_fit = model.func(X, Y, **result.best_values) + z.min()
    return X, Y, Z_fit


def gaussian_fit_2d_max_pos(x: pd.Series, y: pd.Series, z: pd.Series) -> (float, float):
    X, Y, Z = gaussian_fit_2d_mesh(x, y, z)
    max_pos_y, max_pos_x = divmod(Z.argmax(), Z.shape[0])
    x_span = x.max() - x.min()
    y_span = y.max() - y.min()
    x_pos = (max_pos_x / Z.shape[0]) * x_span + x.min()
    y_pos = (max_pos_y / Z.shape[1]) * y_span + y.min()
    return x_pos, y_pos
