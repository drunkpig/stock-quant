## Ta-Lib安装

Ta-Lib网站 http://ta-lib.org/



### windows上安装步骤

windows上如果直接执行pip install Ta-Lib是不会成功的，还要求你有VS的编译环境。

因此wind上安装一般直接下载别人编译好的，在这里 https://www.lfd.uci.edu/~gohlke/pythonlibs/

我是win10 64位, python3.6,那么就下载  TA_Lib‑0.4.17‑cp36‑cp36m‑win_amd64.whl。

下载之后用pip安装：`$pip install Ta_Lib-xxxx.whl`

-----
遇到错
```python3
>>> import talib
Traceback (most recent call last):
  File "__init__.pxd", line 998, in numpy.import_array
RuntimeError: module compiled against API version 0xb but this version of numpy is 0xa

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "E:\dev\Python\Python35\lib\site-packages\talib\__init__.py", line 43, in <module>
    from ._ta_lib import (
  File "_func.pxi", line 15, in init talib._ta_lib
  File "__init__.pxd", line 1000, in numpy.import_array
ImportError: numpy.core.multiarray failed to import
```
说明numpy版本不兼容，需要升级一下： `$pip install -U numpy`。其他问题类似解决。


### linxu上安装步骤

1. 下载源码 http://ta-lib.org/hdr_dw.html  选unix/linux版本的，就是表中最后一个
2. 解压后进入源码目录执行    `$./configure`
3. 执行 `$make`
4. 执行 `$sudo make install`
5. 编辑 /etc/ld.so.conf ， 在末尾加入 `/usr/local/lib` 这个目录也就是make install安装的Ta-Lib的库文件的目录
6. 执行 `$sudo ldconfig`
7. 安装python的 ta-lib 包装  `$pip install Ta-Lib`

