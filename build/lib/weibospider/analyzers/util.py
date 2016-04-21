# _*_coding:utf-8 _*_

def get_times_fromdb(fetchsize,totalsize):
    """获取需要从数据库中以fetchsize获取的次数"""
    if totalsize % fetchsize == 0:
        return totalsize / fetchsize
    else:
        return totalsize / fetchsize + 1

if __name__ == "__main__":
    print get_times_fromdb(5,13)
