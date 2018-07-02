# pdalOctreeSplitPointCloud
The point cloud is split using the `pdal` `octree`


## 创建 pdal python 运行的 虚拟环境   这里使用conda 创建
```
$ conda create -n pdalenv -c conda-forge python-pdal pdal=1.7.2 python=3.6
$ activate pdalenv
$ pdal --version
$ echo %PDAL_DRIVER_PATH%
```

## 运行 octree.py  可以八叉树分割点云
```
$ git clone https://github.com/jiawenquan/pdalOctreeSplitPointCloud.git
$ cd pdalOctreeSplitPointCloud
$ python octree.py
```
