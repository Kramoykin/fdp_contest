from scipy.spatial import cKDTree
import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline
import os
from lasio import LASFile

def parse_traj_data(file_path: str) -> pd.DataFrame:
    with open(file_path, 'r') as file:
        lines = file.readlines()
        data_start = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('#====='):
                data_start = i + 1
                break
            
        column_names = lines[data_start].split()
        df = pd.DataFrame([x.split() for x in lines[data_start + 2:]], columns=column_names)
        df = df.apply(pd.to_numeric, errors='ignore')

    return df


def find_closest_indices_xyz(coords: np.ndarray, target_coords: np.ndarray) -> np.ndarray:
    tree = cKDTree(coords)
    distances, indices = tree.query(target_coords)
    return indices

def interpolate_well_trajectory(df, new_step):
    md = df['MD'].values
    x = df['X'].values
    y = df['Y'].values
    z = df['Z'].values

    spline_x = CubicSpline(md, x)
    spline_y = CubicSpline(md, y)
    spline_z = CubicSpline(md, z)

    md_new = np.arange(md.min(), md.max(), new_step)

    x_new = spline_x(md_new)
    y_new = spline_y(md_new)
    z_new = spline_z(md_new)

    df_new = pd.DataFrame({'MD': md_new,
                           'X': x_new,
                           'Y': y_new,
                           'Z': z_new
                          })
    return df_new

def get_trajectory_df(file_path: str) -> pd.DataFrame:
    traj_df = parse_traj_data(file_path)
    traj_df.Z = traj_df.Z.to_numpy() * -1
    traj_df = interpolate_well_trajectory(traj_df, new_step=0.1)

    return traj_df

def write_file_full_path(file_path: str, data: bytes) -> None:
    """ 
    Записывает data, переданную в байтах в файл по пути file_path. 
    Если файл не существует, то создает его вместе со всеми 
    поддиректориями, переданными в пути
    """

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb+") as file_object:
        file_object.write(data)

def write_or_append_las(file_path: str, las_file: LASFile) -> None:
    """
    Создаёт файл с каротажем, или дописывает новые данные в файл 
    существующего каротажа. Поддиректории, указанные в 
    file_path создаются при создании файла
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # with open(file_path, "a") as fobj:
    if (os.stat(file_path).st_size == 0):
        with open(file_path, "w+") as fobj:
            las_file.write(fobj, version=2.0)
    else:
        with open(file_path, "r") as fobj:
            old_las = LASFile(file_path)
        with open(file_path, "w+") as fobj:
            old_data = old_las.data
            data = las_file.data
            data = np.concatenate((np.array(data), np.array(old_data)), axis=0)
            las_file.data = data
            las_file.write(fobj, version=2.0)
            # np.savetxt(fobj, data, fmt=' %-12.5f')