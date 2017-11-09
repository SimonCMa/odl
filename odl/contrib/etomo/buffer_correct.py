import numpy as np

__all__ = ('buffer_correction',)


def buffer_correction(data, coords=[[0, 0.25], [0, 0.25]]):

    dim_t, dim_x, dim_y = data.shape
    data_asarray = data.asarray()
    bg = data_asarray[:, round(dim_x*coords[0][0]):round(dim_x*coords[0][1]),
                      round(dim_y*coords[1][0]):round(dim_y*coords[1][1])]
    print(bg.shape)
    bg_mean = np.mean(bg, (1, 2))

    return data.space.element(data_asarray * (1.0/bg_mean.reshape(dim_t,
                                                                  1, 1)))