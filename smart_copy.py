import os
import shutil
import re
import threading
import json
from tkinter import messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText

CONFIG_FILE = "smart_copy_config.json"

class SmartCopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("智能文件拷贝专家----by liugngg@sohu.com")
        self.root.geometry("800x600")
        
        # 1. 设置主题和全局样式
        self.style = ttk.Style(theme="cosmo") 
        self.set_custom_styles()

        # 2. 变量初始化
        self.src_path = ttk.StringVar()
        self.dst_path = ttk.StringVar()
        self.is_recursive = ttk.BooleanVar(value=True)
        self.copy_empty_dir = ttk.BooleanVar(value=True)
        self.folder_regex = ttk.StringVar()
        self.file_exts = ttk.StringVar(value=".txt .docx .pdf")
        self.min_size = ttk.StringVar(value="0")
        self.max_size = ttk.StringVar(value="1024")

        self.create_widgets()
        
        # 3. 加载上次保存的配置
        self.load_config()

    def set_custom_styles(self):
        """定义全局字体和颜色"""
        default_font = ("微软雅黑", 10)
        self.style.configure(".", font=default_font)
        # 深蓝色标签样式
        self.style.configure("DeepBlue.TLabel", foreground="#003366", font=("微软雅黑", 10, "bold"))
        self.style.configure("TLabelframe.Label", foreground="blue", font=("微软雅黑", 10, "bold"))

    def create_widgets(self):
        main_container = ttk.Frame(self.root, padding=15)
        main_container.pack(fill=BOTH, expand=YES)

        # --- 路径设置区 ---
        path_frame = ttk.LabelFrame(main_container, text=" 路径设置 ", padding=15)
        path_frame.pack(fill=X, pady=5)

        # 源路径
        ttk.Label(path_frame, text="源文件夹(支持拖曳):", style="DeepBlue.TLabel").grid(row=0, column=0, sticky=E, pady=5)
        src_entry = ttk.Entry(path_frame, textvariable=self.src_path)
        src_entry.grid(row=0, column=1, sticky=EW, padx=10, pady=5)
        src_entry.drop_target_register(DND_FILES)
        src_entry.dnd_bind('<<Drop>>', lambda e: self.src_path.set(self._clean_path(e.data)))
        ttk.Button(path_frame, text="浏览", command=self.browse_src, bootstyle=(PRIMARY, OUTLINE), width=8).grid(row=0, column=2, pady=5)

        # 目标路径
        ttk.Label(path_frame, text="目标文件夹(支持拖曳):", style="DeepBlue.TLabel").grid(row=1, column=0, sticky=W, pady=5)
        dst_entry = ttk.Entry(path_frame, textvariable=self.dst_path)
        dst_entry.grid(row=1, column=1, sticky=EW, padx=10)
        dst_entry.drop_target_register(DND_FILES)
        dst_entry.dnd_bind('<<Drop>>', lambda e: self.dst_path.set(self._clean_path(e.data)))
        ttk.Button(path_frame, text="浏览", command=self.browse_dst, bootstyle=(PRIMARY, OUTLINE), width=8).grid(row=1, column=2)
        path_frame.columnconfigure(1, weight=1)

        # --- 过滤条件区 ---
        filter_frame = ttk.LabelFrame(main_container, text=" 过滤参数 ", padding=15)
        filter_frame.pack(fill=X, pady=10)

        # 第一行：开关选项 (使用标准样式的勾选框)
        check_frame = ttk.Frame(filter_frame)
        check_frame.pack(fill=X, pady=5)
        ttk.Checkbutton(check_frame, text="包含子文件夹", variable=self.is_recursive, bootstyle="primary").pack(side=LEFT, padx=10)
        ttk.Checkbutton(check_frame, text="拷贝空文件夹", variable=self.copy_empty_dir, bootstyle="warning").pack(side=LEFT, padx=10)

        # 第二行：目录名称(支持正则)
        row2 = ttk.Frame(filter_frame)
        row2.pack(fill=X, pady=8)
        ttk.Label(row2, text="目录名称(支持正则):", style="DeepBlue.TLabel").pack(side=LEFT)
        ttk.Entry(row2, textvariable=self.folder_regex).pack(side=LEFT, fill=X, expand=YES, padx=(5, 5))

        # 第三行：后缀和文件大小
        row3 = ttk.Frame(filter_frame)
        row3.pack(fill=X, pady=8)
        ttk.Label(row3, text="文件后缀(空格分割):", style="DeepBlue.TLabel").pack(side=LEFT)
        ttk.Entry(row3, textvariable=self.file_exts).pack(side=LEFT, fill=X, expand=YES, padx=(5,10))

        ttk.Label(row3, text="文件大小 (MB):", style="DeepBlue.TLabel").pack(side=LEFT,padx=(20,0))
        ttk.Entry(row3, textvariable=self.min_size, width=8).pack(side=LEFT, padx=5)
        ttk.Label(row3, text="至").pack(side=LEFT)
        ttk.Entry(row3, textvariable=self.max_size, width=8).pack(side=LEFT, padx=5)

        # --- 进度条 ---
        self.progress = ttk.Progressbar(main_container, mode='determinate', bootstyle=SUCCESS)
        self.progress.pack(fill=X, pady=(10, 5))

        # --- 底部按钮区 (合并一排) ---
        btn_row = ttk.Frame(main_container)
        btn_row.pack(fill=X, pady=(10,0))

        # 缩小尺寸的辅助按钮
        ttk.Button(btn_row, text="🗑️ 清空日志", command=self.clear_log, bootstyle="warning-link", width=12).pack(side=LEFT)

        # 核心开始按钮 (占据中间主要空间)
        self.start_btn = ttk.Button(
            btn_row, text="▶ 开始智能拷贝", command=self.start_copy_task, bootstyle=SUCCESS
        )
        self.start_btn.pack(side=RIGHT, padx=10)

        # 缩小尺寸的辅助按钮
        ttk.Button(btn_row, text="💾 保存配置", command=self.save_config, bootstyle=INFO, width=12).pack(side=RIGHT, padx=2)
        


        # --- 日志显示区 ---
        log_label_frame = ttk.LabelFrame(main_container, text=" 执行日志 ", padding=5, bootstyle="secondary")
        log_label_frame.pack(fill=BOTH, expand=YES)
        self.log_text = ScrolledText(log_label_frame, height=8, autohide=True)
        self.log_text.pack(fill=BOTH, expand=YES)

    # --- 逻辑功能 ---

    def _clean_path(self, path):
        return path.strip('{}').strip('"')

    def browse_src(self):
        path = filedialog.askdirectory()
        if path: self.src_path.set(path)

    def browse_dst(self):
        path = filedialog.askdirectory()
        if path: self.dst_path.set(path)

    def clear_log(self):
        self.log_text.delete('1.0', END)

    def log(self, message, level="INFO"):
        self.log_text.insert(END, f"[{level}] {message}\n")
        self.log_text.see(END)

    def validate_inputs(self):
        """异常处理：校验文件大小输入"""
        try:
            m_s = self.min_size.get().strip() or "0"
            x_s = self.max_size.get().strip() or "999999"
            min_v = float(m_s)
            max_v = float(x_s)
            if min_v < 0 or max_v < 0:
                raise ValueError("数值不能为负数")
            if min_v > max_v:
                raise ValueError("最小值不能大于最大值")
            return min_v * 1024 * 1024, max_v * 1024 * 1024
        except ValueError as e:
            messagebox.showerror("输入错误", f"大小范围填写不正确：\n{e}")
            return None

    def save_config(self):
        config = {
            "src_path": self.src_path.get(), "dst_path": self.dst_path.get(),
            "is_recursive": self.is_recursive.get(), "copy_empty_dir": self.copy_empty_dir.get(),
            "folder_regex": self.folder_regex.get(), "file_exts": self.file_exts.get(),
            "min_size": self.min_size.get(), "max_size": self.max_size.get()
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.log("配置已存档", "SUCCESS")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    c = json.load(f)
                self.src_path.set(c.get("src_path", ""))
                self.dst_path.set(c.get("dst_path", ""))
                self.is_recursive.set(c.get("is_recursive", True))
                self.copy_empty_dir.set(c.get("copy_empty_dir", False))
                self.folder_regex.set(c.get("folder_regex", ""))
                self.file_exts.set(c.get("file_exts", ""))
                self.min_size.set(c.get("min_size", "0"))
                self.max_size.set(c.get("max_size", "1024"))
                self.log("历史配置加载完成", "INFO")
            except: pass

    def start_copy_task(self):
        size_range = self.validate_inputs()
        if not size_range: return
        
        src, dst = self.src_path.get(), self.dst_path.get()
        if not os.path.exists(src) or not dst:
            messagebox.showerror("错误", "请检查源路径和目标路径是否有效！")
            return

        self.start_btn.config(state=DISABLED)
        self.progress['value'] = 0
        threading.Thread(target=self.run_copy, args=(size_range,), daemon=True).start()

    def run_copy(self, size_range):
            src_root, dst_root = self.src_path.get(), self.dst_path.get()
            min_b, max_b = size_range
            exts_lst = re.split("[,;|，；\s]", self.file_exts.get())
            exts = [e.strip().lower() for e in exts_lst if e.strip()]
            
            reg = None
            if self.folder_regex.get().strip():
                try: 
                    reg = re.compile(self.folder_regex.get().strip())
                except re.error as e:
                    err = str(e)
                    self.root.after(0, lambda m=err: messagebox.showerror("正则错误", f"无效的正则表达式: {m}"))
                    self.root.after(0, lambda: self.start_btn.config(state=NORMAL))
                    return

            copied_count = 0
            try:
                for root, dirs, files in os.walk(src_root, topdown=True):
                    # --- 1. 递归深度控制 ---
                    # 如果用户关闭了“包含子文件夹”，则只处理根目录，清空 dirs 以停止深入
                    if not self.is_recursive.get() and root != src_root:
                        dirs[:] = []
                        continue

                    # --- 2. 文件夹匹配判定 ---
                    # 如果没有设置正则，默认全部匹配
                    # 如果设置了正则，判断当前文件夹【名称】是否符合要求
                    folder_name = os.path.basename(root)
                    
                    is_folder_matched = True
                    if reg:
                        # 如果是源根目录本身，我们通常允许它继续向下查找，但不直接匹配它里面的文件（除非根目录名也符合正则）
                        if root == src_root:
                            is_folder_matched = False 
                        else:
                            is_folder_matched = bool(reg.search(folder_name))

                    # --- 3. 执行拷贝逻辑 ---
                    if is_folder_matched:
                        rel_path = os.path.relpath(root, src_root)
                        target_dir = os.path.join(dst_root, rel_path)

                        # 检查是否需要创建空文件夹
                        if self.copy_empty_dir.get() and not os.path.exists(target_dir):
                            os.makedirs(target_dir, exist_ok=True)
                            
                        # 处理当前匹配文件夹下的文件
                        for f in files:
                            # 检查后缀
                            if exts and not any(f.lower().endswith(e if e.startswith('.') else f'.{e}') for e in exts):
                                continue
                            
                            f_path = os.path.join(root, f)
                            try:
                                f_size = os.path.getsize(f_path)
                                if not (min_b <= f_size <= max_b): 
                                    continue
                                
                                # 确保目标文件夹存在（如果不是空文件夹模式，在有文件拷贝时才创建）
                                if not os.path.exists(target_dir):
                                    os.makedirs(target_dir, exist_ok=True)
                                    
                                d_file = os.path.join(target_dir, f)
                                shutil.copy2(f_path, d_file)
                                copied_count += 1
                                
                                self.root.after(0, lambda n=f: self.log(f"已拷贝: {n}"))
                            except Exception:
                                continue
                    
                    # 注意：这里不再修改 dirs[:]，这样 os.walk 就会继续走向更深层的子目录

                self.root.after(0, lambda c=copied_count: messagebox.showinfo("完成", f"任务结束！共拷贝 {c} 个文件。"))
                
            except Exception as e:
                error_val = str(e)
                self.root.after(0, lambda msg=error_val: self.log(f"运行错误: {msg}", "ERROR"))
            finally:
                self.root.after(0, lambda: self.start_btn.config(state=NORMAL))
                self.root.after(0, lambda: self.progress.configure(value=100))

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = SmartCopyApp(root)
    root.mainloop()
