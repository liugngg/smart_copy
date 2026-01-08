# 智能拷贝工具

## 1.主要功能：

1. 将源文件夹的内容拷贝到目标文件夹中，需要根据下述内容筛选：
   
   - 是否递归子文件夹
   - 文件夹的名称（可以为正则表达式）
   - 文件类型（后缀名，可以手工输入多个）
   - 文件大小（可以指定范围）
   - 空文件夹时是否拷贝

2. 源文件夹、目标文件夹支持拖曳选择。

## 2. 打包命令

- 生成单文件格式
  `pyinstaller -i liug.ico -F -w smart_copy.py --clean -n 智能拷贝工具`

- 生成单文件格式（Nuitka --onefile自动压缩）
  
  `python -m nuitka --mingw64 --onefile --lto=yes --show-progress --output-dir=dist --remove-output --plugin-enable=tk-inter --windows-console-mode=disable --windows-icon-from-ico=liug.ico smart_copy.py`

- 生成单文件格式（Nuitka --使用upx 压缩）
  
  `python -m nuitka --mingw64 --onefile --onefile-no-compression --plugin-enable=upx --lto=yes --show-progress --output-dir=dist --remove-output --plugin-enable=tk-inter --windows-console-mode=disable --windows-icon-from-ico=liug.ico smart_copy.py`

## 3. 作者

- [liugngg (GitHub地址)](https://github.com/liugngg)
