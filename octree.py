# encoding: utf-8
__author__ = 'jiawenquan'
__date__ = '2018/6/15 0015 14:06'
import os
import pdal
import sys
import datetime, time
import json
import numpy as np


# import gdal
# gdal.SetConfigOption("GDAL_DATA", "D:\OSGeo4W64\share\gdal");  # 设置 gdal路径

def getMetadata(file_path):
    """
    用来获取点云的 max and min  xyz value
    :param file_path:  las点云文件的路径
    :return:  返回一个  dict   {'maxx'：value , 'maxy':value, 'maxz':value, 'minx':value, 'miny':value, 'minz':value}
    """

    '''获取最低点、最高点的字典'''
    data_json = """
            {
                "pipeline": [
                    \"""" + file_path + """\",
                    {
                        "type": "filters.stats"
                    }
                ]
            }"""
    # print(data_json)
    pipeline = pdal.Pipeline(data_json)

    pipeline.validate()  # 检查我们的JSON和选项是否良好
    pipeline.loglevel = 8  # really noisy 输入日志相关 未知
    count = pipeline.execute()  # 执行通道

    # arrays = pipeline.arrays
    # print("arrays:", arrays)

    metadata = pipeline.metadata  # 获取通道的 所有详情信息
    metadata_dict = eval(str(json.loads(metadata)))  # 把字符串 信息转成 字典
    bbox_dict = metadata_dict["metadata"]["filters.stats"][1]["bbox"]["native"]["bbox"]  # 获取到 详情信息包含 最小点最大点的
    # print(metadata_dict)

    subkey = ['maxx', 'maxy', 'maxz', 'minx', 'miny', 'minz']
    box_dict = dict([(key, bbox_dict[key]) for key in subkey])  # 获取到最大点、最小点的字典
    return box_dict


def getCenter(file_path):
    """
    用来获取点云的中心点
    :param file_path:  las 点云文件的路径
    :return: 中心点的坐标 [x,y,z]
    """
    box_dict = getMetadata(file_path)
    xyzcenter = [(box_dict["maxx"] + box_dict["minx"]) / 2, (box_dict["maxy"] + box_dict["miny"]) / 2,
                 (box_dict["maxz"] + box_dict["minz"]) / 2]

    return xyzcenter


def dilutionSampling(input_path, out_path_dir=None, out_name=None, points=100000):  # , out_path_dir=None, out_name=None
    """
    用来实现 抽稀 点云
    :param input_path:   要抽稀点云文件的路径
    :param out_path_dir: 抽吸后的点云文件保存路径目录 默认为None(使用输入点云的文件路径目录)
    :param out_name:     抽吸后的点云文件保存文件名、不包含后缀名 默认为None(使用输入点云的的文件名前面 加"dilution_")
    :param points:       要抽取的点数
    :return:   out_path  成功抽稀点云并保存 返回抽稀点云的文件路径
    """

    # 提取文件后缀名
    input_file_suffix = os.path.splitext(input_path)[1]

    # 提取文件的目录  与文件名字(包含后缀)
    input_file_dir, input_file_name_and_suffix = os.path.split(input_path)
    # print(input_file_dir, input_file_name_and_suffix)


    # 只包含名字 没有后缀
    # input_file_name = input_file_name_and_suffix.split('.')[0]
    input_file_name = os.path.splitext(input_file_name_and_suffix)[0]
    # print(input_file_name)

    # 如果输出路径为空那么 提取点云的文件的路径 为输出路径
    if out_path_dir == None:
        out_path_dir = input_file_dir
    # 如果输出文件名字为空 那么默认"dilution_" + 输入点云的文件名
    if out_name == None:
        out_name = "dilution_" + input_file_name

    # 抽稀后的点云 储存的路径
    out_path = os.path.join(out_path_dir, out_name + input_file_suffix).replace("\\", "/")

    data_json = """
            {
                "pipeline": [
                    \"""" + input_path + """\",
                    {
                        "type": "filters.stats"
                    },
                    {
                      "type":"filters.randomize"
                    },
                    {
                      "type":"filters.head",
                      "count":""" + str(points) + """
                    },
                    {
                     "type": "writers.las",
                     "filename": \"""" + out_path + """\"
                    }
                ]
            }"""
    # print(data_json)
    pipeline = pdal.Pipeline(data_json)
    pipeline.validate()  # 检查我们的JSON和选项是否良好
    pipeline.loglevel = 8  # really noisy 输入日志相关 未知
    count = pipeline.execute()  # 执行通道
    print("抽稀完成")
    print("count:", count)
    return out_path


def calibrationCenterAndColor(input_path, out_path_dir=None, out_name=None, point_cloud_type=None):
    """
    用来校准点云的中心点 然后保存为一个新的点云
    :param input_path:          要校准点云的路径
    :param out_path_dir:        校准后的点云存储路径目录  默认为None(使用输入点云的文件路径目录)
    :param out_name:            校准后的点云存储路文件名、不包含后缀 默认为None(使用输入点云的的文件名 前面加"calibration_")
    :param point_cloud_type:    点云的格式 用来判断是否也要缩放颜色取值范围 None(不对颜色进行缩放) 、".las" （从 0-65280 缩放到 0-255）
    :return:                    out_path 校准成功 返回校准后的点云存储路径
    """
    # 提取文件后缀名
    input_file_suffix = os.path.splitext(input_path)[1]
    print("input_file_suffix:", input_file_suffix)

    # 提取文件的目录  与文件名字(包含后缀)
    input_file_dir, input_file_name_and_suffix = os.path.split(input_path)
    # print(input_file_dir, input_file_name_and_suffix)


    # 只包含名字 没有后缀
    input_file_name = os.path.splitext(input_file_name_and_suffix)[0]
    # print(input_file_name)

    # 如果输出路径为空那么 提取点云的文件的路径 为输出路径
    if out_path_dir == None:
        out_path_dir = input_file_dir
    # 如果输出文件名字为空 那么默认"calibration_" + 输入点云的文件名
    if out_name == None:
        out_name = "calibration_" + input_file_name

    # 校准后的点云存储路径
    out_path = os.path.join(out_path_dir, (out_name + input_file_suffix)).replace("\\", "/")

    center = getCenter(input_path)  # 得到点云的中心点

    #
    las_json = """
    {
      "pipeline":[
        \"""" + input_path + """\",
        {
            "type": "filters.python",
            "module": "anything",
            "function": "fff",
            "source": "import numpy as np\ndef fff(ins, outs):\n\tX = ins['X']\n\tY = ins['Y']\n\tZ = ins['Z']\n\tRed = ins['Red']\n\tGreen = ins['Green']\n\tBlue = ins['Blue']\n\tRed = Red>>8\n\tGreen = Green>>8\n\tBlue = Blue>>8\n\touts['Red'] = Red\n\touts['Green'] = Green\n\touts['Blue'] = Blue\n\touts['X'] = X - """ + str(
        center[0]) + """\n\touts['Y'] = Y - """ + str(center[1]) + """\n\touts['Z'] = Z - """ + str(center[2]) + """\n\treturn True"
        },
        {
             "type": "writers.las",
             "filename": \"""" + out_path + """\"
         }
      ]
    }"""

    data_json = """
    {
      "pipeline":[
        \"""" + input_path + """\",
        {
            "type": "filters.python",
            "module": "anything",
            "function": "fff",
            "source": "import numpy as np\ndef fff(ins, outs):\n\tX = ins['X']\n\tY = ins['Y']\n\tZ = ins['Z']\n\touts['X'] = X - """ + str(
        center[0]) + """\n\touts['Y'] = Y - """ + str(center[1]) + """\n\touts['Z'] = Z - """ + str(center[2]) + """\n\treturn True"
        },
        {
             "type": "writers.las",
             "filename": \"""" + out_path + """\"
         }
      ]
    }"""
    # print(data_json)

    if point_cloud_type == None:
        pipeline = pdal.Pipeline(data_json)
    elif point_cloud_type == ".las":
        pipeline = pdal.Pipeline(las_json)
    else:
        pipeline = pdal.Pipeline(data_json)
    pipeline.validate()  # 检查我们的JSON和选项是否良好
    pipeline.loglevel = 8  # really noisy 输入日志相关 未知
    count = pipeline.execute()  # 执行通道

    # arrays = pipeline.arrays
    # print("centerArrays:", arrays)
    # print("count:", count)
    # print("count:", count)
    return out_path


octree_list = []


def octree(input_path, out_path_dir=None, center=None, points=100000):
    """
    八叉树开始分割点云 并保存
    :param input_path:  要分割点云文件的路径
    :param out_path_dir:    分割后的点云文件名  不需要写后缀名, (outpath_1.las,outpath_2.las ... outpath_8.las)
    :param center:     八叉树分割的 中心点list [x,y,z]  默认 None  需要计算得出center   center传入了 则不需要重新计算
    :param points:     用来判断 分割后的点数要不要继续分割
    :return:           是否成功分割 True and False
    """

    # 提取文件后缀名
    input_file_suffix = os.path.splitext(input_path)[1]

    # 提取文件的目录  与文件名字(包含后缀)
    input_file_dir, input_file_name_and_suffix = os.path.split(input_path)
    # print(input_file_dir, input_file_name_and_suffix)


    # 只包含名字 没有后缀
    input_file_name = os.path.splitext(input_file_name_and_suffix)[0]
    # print(input_file_name)

    if out_path_dir == None:
        out_path_dir = input_file_dir

    # 如果没有传入中心点 则计算出一个中心点
    if center == None:
        center = getCenter(input_path)
    # 八叉树分割点云的八个 json  pipeline  会存入下面的 list中

    out_path_01 = os.path.join(out_path_dir, input_file_name + "_1.las").replace('\\', '/')
    out_path_02 = os.path.join(out_path_dir, input_file_name + "_2.las").replace('\\', '/')
    out_path_03 = os.path.join(out_path_dir, input_file_name + "_3.las").replace('\\', '/')
    out_path_04 = os.path.join(out_path_dir, input_file_name + "_4.las").replace('\\', '/')
    out_path_05 = os.path.join(out_path_dir, input_file_name + "_5.las").replace('\\', '/')
    out_path_06 = os.path.join(out_path_dir, input_file_name + "_6.las").replace('\\', '/')
    out_path_07 = os.path.join(out_path_dir, input_file_name + "_7.las").replace('\\', '/')
    out_path_08 = os.path.join(out_path_dir, input_file_name + "_8.las").replace('\\', '/')

    octree_json01 = """
    {
      "pipeline":[
        \"""" + input_path + """\",
        {
            "type": "filters.range",
            "limits": "X[""" + "" + ":" + str(center[0]) + """],Y[""" + "" + ":" + str(
        center[1]) + """],Z[""" + "" + ":" + str(center[2]) + """]"
        },
        {
           "type": "writers.las",
           "filename": \"""" + out_path_01 + """\"
        }
      ]
    }"""

    octree_json02 = """
    {
      "pipeline":[
        \"""" + input_path + """\",
        {
            "type": "filters.range",
            "limits": "X[""" + "" + ":" + str(center[0]) + """],Y[""" + str(
        center[1]) + ":" + "" + """],Z[""" + "" + ":" + str(center[2]) + """]"
        },
        {
           "type": "writers.las",
           "filename": \"""" + out_path_02 + """\"
        }
      ]
    }"""

    octree_json03 = """
    {
      "pipeline":[
        \"""" + input_path + """\",
        {
            "type": "filters.range",
            "limits": "X[""" + str(center[0]) + ":" + "" + """],Y[""" + str(
        center[1]) + ":" + "" + """],Z[""" + "" + ":" + str(center[2]) + """]"
        },
        {
           "type": "writers.las",
           "filename": \"""" + out_path_03 + """\"
        }
      ]
    }"""

    octree_json04 = """
    {
      "pipeline":[
        \"""" + input_path + """\",
        {
            "type": "filters.range",
            "limits": "X[""" + str(center[0]) + ":" + "" + """],Y[""" + "" + ":" + str(
        center[1]) + """],Z[""" + "" + ":" + str(center[2]) + """]"
        },
        {
           "type": "writers.las",
           "filename": \"""" + out_path_04 + """\"
        }
      ]
    }"""

    octree_json05 = """
    {
      "pipeline":[
        \"""" + input_path + """\",
        {
            "type": "filters.range",
            "limits": "X[""" + "" + ":" + str(center[0]) + """],Y[""" + str(center[1]) + ":" + "" + """],Z[""" + str(
        center[2]) + ":" + "" + """]"
        },
        {
           "type": "writers.las",
           "filename": \"""" + out_path_05 + """\"
        }
      ]
    }"""

    octree_json06 = """
    {
      "pipeline":[
        \"""" + input_path + """\",
        {
            "type": "filters.range",
            "limits": "X[""" + str(center[0]) + ":" + "" + """],Y[""" + str(center[1]) + ":" + "" + """],Z[""" + str(
        center[2]) + ":" + "" + """]"
        },
        {
           "type": "writers.las",
           "filename": \"""" + out_path_06 + """\"
        }
      ]
    }"""

    octree_json07 = """
    {
      "pipeline":[
        \"""" + input_path + """\",
        {
            "type": "filters.range",
            "limits": "X[""" + "" + ":" + str(center[0]) + """],Y[""" + "" + ":" + str(center[1]) + """],Z[""" + str(
        center[2]) + ":" + "" + """]"
        },
        {
           "type": "writers.las",
           "filename": \"""" + out_path_07 + """\"
        }
      ]
    }"""

    octree_json08 = """
    {
      "pipeline":[
        \"""" + input_path + """\",
        {
            "type": "filters.range",
            "limits": "X[""" + str(center[0]) + ":" + "" + """],Y[""" + "" + ":" + str(center[1]) + """],Z[""" + str(
        center[2]) + ":" + "" + """]"
        },
        {
           "type": "writers.las",
           "filename": \"""" + out_path_08 + """\"
        }
      ]
    }"""

    # 储存八个 "filters.python" pipeline  每个 都会保存一个 八叉树分割出来的点云
    octree_json_list = [[octree_json01, out_path_01], [octree_json02, out_path_02], [octree_json03, out_path_03],
                        [octree_json04, out_path_04], [octree_json05, out_path_05], [octree_json06, out_path_06],
                        [octree_json07, out_path_07], [octree_json08, out_path_08]]
    octree_list = []
    num = 0
    for octree in octree_json_list:
        """这里可以开启多线程作为优化 暂时未实现"""
        pipeline = pdal.Pipeline(octree[0])
        pipeline.validate()  # 检查我们的JSON和选项是否良好
        pipeline.loglevel = 8  # really noisy 输入日志相关 未知
        count = pipeline.execute()  # 执行通道
        # arrays = pipeline.arrays
        # print("arrays:", arrays)


        num += 1
        nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在
        print("成功分割出第" + str(num) + "块", nowTime)

        # 如果大于  points 的点数 继续分割
        if count > points:
            dilutionSampling(octree[1], points=points)  # 抽稀点云
            octree_list.append(octree[1])
        else:
            filepath, tempfilename = os.path.split(octree[1]);

            if tempfilename == "1.2-with-color_1.las":
                print(tempfilename)
            os.rename(octree[1], os.path.join(filepath, "over_" + tempfilename))

    return octree_list


def loop_octree(octree_list=[], points=100000):
    """
    用来递归循环执行八叉树分割点云
    :param octree_list:   要分割点云的 路径集合  list[input_path,input_path]
    :param points:        分割点云每块点的最大数（默认 points=100000）
    :return:  True        返回是否分割成功
    """
    for path in octree_list:
        octreelist = octree(path, points=points)
        loop_octree(octreelist, points=points)
    return True


def octree_process(input_path, out_file_dir=None, out_file_name=None, point_cloud_type=None, points=100000):
    """
    用来控制第一次进入八叉树分割的流程
    先重置 点云的中心点颜色取值范围
    然后开始进入八叉树分割
    :param input_path:          要分割点云的路径
    :param out_file_dir:        分割后保存点云的路径目录 （默认为）
    :param out_file_name:       保存点云的的名字(默认为None,从input_path获取到文件名)
    :param point_cloud_type:    点云的格式 （默认为None,从input_path 中提取后缀名字）
    :param points:              要分割点云每块的最大点数,也用来作为抽稀点云的 点数（默认 points=100000 ）
    :return:
    """

    # 提取文件后缀名
    input_file_suffix = os.path.splitext(input_path)[1]

    if point_cloud_type == None:
        point_cloud_type = input_file_suffix  # 赋值点云类型
    # 提取文件的目录  与文件名字(包含后缀)
    input_file_dir, input_file_name_and_suffix = os.path.split(input_path)
    # print(input_file_dir, input_file_name_and_suffix)


    input_file_name = os.path.splitext(input_file_name_and_suffix)[0]

    # print(input_file_name)

    if out_file_dir == None:
        out_file_dir = input_file_dir
    if out_file_name == None:
        out_file_name = input_file_name

    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在
    print("开始重置中心点", nowTime)

    # 重置中心点与校准颜色
    out_calibration_path = calibrationCenterAndColor(input_path=input_path, out_path_dir=out_file_dir,
                                                     out_name=out_file_name, point_cloud_type=point_cloud_type)
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在
    print("重置中心点与缩放颜色取值范围成功:", nowTime)

    # 开始抽吸点云
    # 抽稀点云的储存路径
    out_dilutionSampling_path = dilutionSampling(input_path=out_calibration_path, out_path_dir=out_file_dir,
                                                 points=points)

    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("抽吸点云成功:", nowTime)

    print("开始八叉树分割")
    octreelist = octree(out_calibration_path, out_path_dir=out_file_dir, center=[0, 0, 0], points=points)
    loop_octree(octreelist, points=points)
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在
    print("八叉树分割完成")


nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在
print("开始时间：", nowTime)
time_start = time.time()  # 开始计时

# 执行这一个
octree_process(input_path="Model.las", point_cloud_type=".las", points=100000)

nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在
print("结束时间：", nowTime)
time_end = time.time()  # 结束计时
print('time cost', time_end - time_start, 's')

if __name__ == '__main__':
    try:
        sys.exit(octree_process(sys.argv[1]))
    except:
        print('Program is dead.')
    finally:
        print('clean-up')


# import numpy as np\ndef fff(ins, outs):\n\tX = ins['X']\n\tY = ins['Y']\n\tZ = ins['Z']\n\touts['X'] = X - 10\n\touts['Y'] = Y - 10\n\touts['Z'] = Z - 10\n\treturn True
