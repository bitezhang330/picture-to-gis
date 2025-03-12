import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QComboBox, QSpinBox, 
                            QTabWidget, QProgressBar, QSlider, QMessageBox, QSplitter, 
                            QGroupBox, QRadioButton, QLineEdit, QFormLayout, QDoubleSpinBox,
                            QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont
import glob
import re
from PIL import Image
from moviepy.editor import VideoFileClip, ImageSequenceClip
import numpy as np
import tempfile
import shutil


class VideoToGifWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, video_path, output_path, fps, speed_factor, resize=None):
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path
        self.fps = fps
        self.speed_factor = speed_factor
        self.resize = resize  # 添加尺寸参数
        self.temp_dir = None
    
    def run(self):
        try:
            # 创建临时文件夹
            self.temp_dir = tempfile.mkdtemp()
            
            # 加载视频
            video_clip = VideoFileClip(self.video_path)
            
            # 调整尺寸（如果需要）
            if self.resize and self.resize[0] > 0 and self.resize[1] > 0:
                video_clip = video_clip.resize(newsize=self.resize)
            
            # 计算要捕获的时间点
            video_duration = video_clip.duration
            frame_interval = 1.0 / self.fps
            time_points = np.arange(0, video_duration, frame_interval)
            total_frames = len(time_points)
            
            # 捕获帧
            frame_paths = []
            for i, time_point in enumerate(time_points):
                frame = video_clip.get_frame(time_point)
                frame_image = Image.fromarray(np.uint8(frame))
                frame_path = os.path.join(self.temp_dir, f'frame_{i:05d}.png')
                frame_image.save(frame_path)
                frame_paths.append(frame_path)
                
                # 更新进度
                progress_value = int((i + 1) / total_frames * 100)
                self.progress.emit(progress_value)
            
            # 创建GIF
            adjusted_fps = self.fps * self.speed_factor
            gif_clip = ImageSequenceClip(frame_paths, fps=adjusted_fps)
            gif_clip.write_gif(self.output_path, program='ffmpeg')
            
            # 完成
            self.finished.emit(self.output_path)
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            # 清理临时文件
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)


class ImagesToGifWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, image_paths, output_path, duration_ms, loop_count, resize=None):
        super().__init__()
        self.image_paths = image_paths
        self.output_path = output_path
        self.duration_ms = duration_ms
        self.loop_count = loop_count
        self.resize = resize  # 添加尺寸参数
    
    def run(self):
        try:
            total_images = len(self.image_paths)
            frames = []
            
            for i, img_path in enumerate(self.image_paths):
                img = Image.open(img_path)
                
                # 调整尺寸（如果需要）
                if self.resize and self.resize[0] > 0 and self.resize[1] > 0:
                    img = img.resize(self.resize, Image.LANCZOS)
                
                frames.append(img)
                
                # 更新进度
                progress_value = int((i + 1) / total_images * 100)
                self.progress.emit(progress_value)
            
            # 保存为GIF
            if frames:
                frames[0].save(
                    self.output_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=self.duration_ms,
                    loop=self.loop_count
                )
            
            # 完成
            self.finished.emit(self.output_path)
            
        except Exception as e:
            self.error.emit(str(e))


class GifConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF转换器")
        self.setMinimumSize(800, 600)
        
        # 设置应用图标
        self.setWindowIcon(QIcon("app_icon.svg"))
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        # 创建主窗口部件
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # 创建标签
        title_label = QLabel("GIF转换器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        main_layout.addWidget(title_label)
        
        # 创建标签页
        tabs = QTabWidget()
        
        # 视频转GIF标签页
        video_tab = QWidget()
        video_layout = QVBoxLayout(video_tab)
        
        # 视频选择部分
        video_file_group = QGroupBox("视频文件")
        video_file_layout = QFormLayout()
        
        self.video_path_edit = QLineEdit()
        self.video_path_edit.setReadOnly(True)
        self.video_browse_btn = QPushButton("浏览...")
        self.video_browse_btn.clicked.connect(self.browse_video)
        
        video_path_layout = QHBoxLayout()
        video_path_layout.addWidget(self.video_path_edit)
        video_path_layout.addWidget(self.video_browse_btn)
        
        video_file_layout.addRow("选择视频:", video_path_layout)
        video_file_group.setLayout(video_file_layout)
        video_layout.addWidget(video_file_group)
        
        # 视频转换设置
        video_settings_group = QGroupBox("转换设置")
        video_settings_layout = QFormLayout()
        
        self.video_fps_spin = QSpinBox()
        self.video_fps_spin.setRange(1, 30)
        self.video_fps_spin.setValue(10)
        video_settings_layout.addRow("帧率 (FPS):", self.video_fps_spin)
        
        self.video_speed_spin = QDoubleSpinBox()
        self.video_speed_spin.setRange(0.1, 10.0)
        self.video_speed_spin.setValue(1.0)
        self.video_speed_spin.setSingleStep(0.1)
        video_settings_layout.addRow("速度倍数:", self.video_speed_spin)
        
        # 添加尺寸设置
        size_layout = QHBoxLayout()
        
        self.video_resize_check = QCheckBox("调整尺寸")
        self.video_resize_check.setChecked(False)
        size_layout.addWidget(self.video_resize_check)
        
        self.video_width_spin = QSpinBox()
        self.video_width_spin.setRange(10, 3840)
        self.video_width_spin.setValue(640)
        self.video_width_spin.setEnabled(False)
        size_layout.addWidget(QLabel("宽:"))
        size_layout.addWidget(self.video_width_spin)
        
        self.video_height_spin = QSpinBox()
        self.video_height_spin.setRange(10, 2160)
        self.video_height_spin.setValue(480)
        self.video_height_spin.setEnabled(False)
        size_layout.addWidget(QLabel("高:"))
        size_layout.addWidget(self.video_height_spin)
        
        # 连接复选框事件
        self.video_resize_check.toggled.connect(self.video_width_spin.setEnabled)
        self.video_resize_check.toggled.connect(self.video_height_spin.setEnabled)
        
        video_settings_layout.addRow("尺寸设置:", size_layout)
        
        video_settings_group.setLayout(video_settings_layout)
        video_layout.addWidget(video_settings_group)
        
        # 视频输出设置
        video_output_group = QGroupBox("输出设置")
        video_output_layout = QFormLayout()
        
        self.video_output_edit = QLineEdit()
        self.video_output_edit.setReadOnly(True)
        self.video_output_btn = QPushButton("浏览...")
        self.video_output_btn.clicked.connect(self.browse_video_output)
        
        video_output_path_layout = QHBoxLayout()
        video_output_path_layout.addWidget(self.video_output_edit)
        video_output_path_layout.addWidget(self.video_output_btn)
        
        video_output_layout.addRow("输出GIF:", video_output_path_layout)
        video_output_group.setLayout(video_output_layout)
        video_layout.addWidget(video_output_group)
        
        # 视频转换按钮和进度条
        self.video_progress = QProgressBar()
        video_layout.addWidget(self.video_progress)
        
        self.video_convert_btn = QPushButton("开始转换")
        self.video_convert_btn.clicked.connect(self.convert_video_to_gif)
        video_layout.addWidget(self.video_convert_btn)
        
        # 图片转GIF标签页
        image_tab = QWidget()
        image_layout = QVBoxLayout(image_tab)
        
        # 图片选择部分
        image_file_group = QGroupBox("图片文件")
        image_file_layout = QVBoxLayout()
        
        self.image_dir_edit = QLineEdit()
        self.image_dir_edit.setReadOnly(True)
        self.image_dir_btn = QPushButton("选择文件夹...")
        self.image_dir_btn.clicked.connect(self.browse_image_dir)
        
        self.image_files_btn = QPushButton("选择多个文件...")
        self.image_files_btn.clicked.connect(self.browse_image_files)
        
        image_path_layout = QHBoxLayout()
        image_path_layout.addWidget(self.image_dir_edit)
        image_path_layout.addWidget(self.image_dir_btn)
        image_path_layout.addWidget(self.image_files_btn)
        
        image_file_layout.addLayout(image_path_layout)
        
        self.image_count_label = QLabel("已选择 0 个图片文件")
        image_file_layout.addWidget(self.image_count_label)
        
        image_file_group.setLayout(image_file_layout)
        image_layout.addWidget(image_file_group)
        
        # 图片转换设置
        image_settings_group = QGroupBox("转换设置")
        image_settings_layout = QFormLayout()
        
        self.image_duration_spin = QSpinBox()
        self.image_duration_spin.setRange(50, 5000)
        self.image_duration_spin.setValue(500)
        self.image_duration_spin.setSingleStep(50)
        image_settings_layout.addRow("每帧持续时间 (毫秒):", self.image_duration_spin)
        
        self.image_loop_spin = QSpinBox()
        self.image_loop_spin.setRange(0, 100)
        self.image_loop_spin.setValue(0)
        self.image_loop_spin.setSpecialValueText("无限循环")
        image_settings_layout.addRow("循环次数:", self.image_loop_spin)
        
        # 添加尺寸设置
        img_size_layout = QHBoxLayout()
        
        self.image_resize_check = QCheckBox("调整尺寸")
        self.image_resize_check.setChecked(False)
        img_size_layout.addWidget(self.image_resize_check)
        
        self.image_width_spin = QSpinBox()
        self.image_width_spin.setRange(10, 3840)
        self.image_width_spin.setValue(800)
        self.image_width_spin.setEnabled(False)
        img_size_layout.addWidget(QLabel("宽:"))
        img_size_layout.addWidget(self.image_width_spin)
        
        self.image_height_spin = QSpinBox()
        self.image_height_spin.setRange(10, 2160)
        self.image_height_spin.setValue(600)
        self.image_height_spin.setEnabled(False)
        img_size_layout.addWidget(QLabel("高:"))
        img_size_layout.addWidget(self.image_height_spin)
        
        # 连接复选框事件
        self.image_resize_check.toggled.connect(self.image_width_spin.setEnabled)
        self.image_resize_check.toggled.connect(self.image_height_spin.setEnabled)
        
        image_settings_layout.addRow("尺寸设置:", img_size_layout)
        
        image_settings_group.setLayout(image_settings_layout)
        image_layout.addWidget(image_settings_group)
        
        # 图片输出设置
        image_output_group = QGroupBox("输出设置")
        image_output_layout = QFormLayout()
        
        self.image_output_edit = QLineEdit()
        self.image_output_edit.setReadOnly(True)
        self.image_output_btn = QPushButton("浏览...")
        self.image_output_btn.clicked.connect(self.browse_image_output)
        
        image_output_path_layout = QHBoxLayout()
        image_output_path_layout.addWidget(self.image_output_edit)
        image_output_path_layout.addWidget(self.image_output_btn)
        
        image_output_layout.addRow("输出GIF:", image_output_path_layout)
        image_output_group.setLayout(image_output_layout)
        image_layout.addWidget(image_output_group)
        
        # 图片转换按钮和进度条
        self.image_progress = QProgressBar()
        image_layout.addWidget(self.image_progress)
        
        self.image_convert_btn = QPushButton("开始转换")
        self.image_convert_btn.clicked.connect(self.convert_images_to_gif)
        image_layout.addWidget(self.image_convert_btn)
        
        # 添加标签页
        tabs.addTab(video_tab, "视频转GIF")
        tabs.addTab(image_tab, "图片转GIF")
        main_layout.addWidget(tabs)
        
        # 设置主窗口
        self.setCentralWidget(main_widget)
        
        # 初始化变量
        self.selected_image_paths = []
        self.video_worker = None
        self.image_worker = None
    
    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*)"
        )
        if file_path:
            self.video_path_edit.setText(file_path)
            
            # 自动设置输出路径
            output_path = os.path.splitext(file_path)[0] + ".gif"
            self.video_output_edit.setText(output_path)
            
            # 获取视频原始尺寸并设置到尺寸控件中
            try:
                video = VideoFileClip(file_path)
                width, height = video.size
                self.video_width_spin.setValue(width)
                self.video_height_spin.setValue(height)
                video.close()
            except:
                pass
    
    def browse_video_output(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存GIF", "", "GIF文件 (*.gif);;所有文件 (*)"
        )
        if file_path:
            if not file_path.lower().endswith('.gif'):
                file_path += '.gif'
            self.video_output_edit.setText(file_path)
    
    def browse_image_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if dir_path:
            self.image_dir_edit.setText(dir_path)
            
            # 获取文件夹中的所有图片文件
            image_files = glob.glob(os.path.join(dir_path, '*.jpg'))
            image_files += glob.glob(os.path.join(dir_path, '*.jpeg'))
            image_files += glob.glob(os.path.join(dir_path, '*.png'))
            
            # 自然排序
            self.selected_image_paths = sorted(image_files, key=self.natural_sort_key)
            self.image_count_label.setText(f"已选择 {len(self.selected_image_paths)} 个图片文件")
            
            # 自动设置输出路径
            if self.selected_image_paths:
                output_dir = os.path.dirname(self.selected_image_paths[0])
                output_path = os.path.join(output_dir, "output.gif")
                self.image_output_edit.setText(output_path)
                
                # 获取第一张图片尺寸并设置到尺寸控件
                try:
                    img = Image.open(self.selected_image_paths[0])
                    width, height = img.size
                    self.image_width_spin.setValue(width)
                    self.image_height_spin.setValue(height)
                    img.close()
                except:
                    pass
    
    def browse_image_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "", "图片文件 (*.jpg *.jpeg *.png);;所有文件 (*)"
        )
        if file_paths:
            # 设置第一个文件的目录作为显示路径
            if file_paths:
                self.image_dir_edit.setText(os.path.dirname(file_paths[0]) + "/ (多个文件)")
            
            # 自然排序
            self.selected_image_paths = sorted(file_paths, key=self.natural_sort_key)
            self.image_count_label.setText(f"已选择 {len(self.selected_image_paths)} 个图片文件")
            
            # 自动设置输出路径
            if self.selected_image_paths:
                output_dir = os.path.dirname(self.selected_image_paths[0])
                output_path = os.path.join(output_dir, "output.gif")
                self.image_output_edit.setText(output_path)
                
                # 获取第一张图片尺寸并设置到尺寸控件
                try:
                    img = Image.open(self.selected_image_paths[0])
                    width, height = img.size
                    self.image_width_spin.setValue(width)
                    self.image_height_spin.setValue(height)
                    img.close()
                except:
                    pass
    
    def browse_image_output(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存GIF", "", "GIF文件 (*.gif);;所有文件 (*)"
        )
        if file_path:
            if not file_path.lower().endswith('.gif'):
                file_path += '.gif'
            self.image_output_edit.setText(file_path)
    
    def convert_video_to_gif(self):
        video_path = self.video_path_edit.text()
        output_path = self.video_output_edit.text()
        
        if not video_path or not output_path:
            QMessageBox.warning(self, "错误", "请选择视频文件和输出路径")
            return
        
        # 获取设置
        fps = self.video_fps_spin.value()
        speed_factor = self.video_speed_spin.value()
        
        # 获取尺寸设置
        resize = None
        if self.video_resize_check.isChecked():
            width = self.video_width_spin.value()
            height = self.video_height_spin.value()
            resize = (width, height)
        
        # 禁用按钮
        self.video_convert_btn.setEnabled(False)
        
        # 创建并启动工作线程
        self.video_worker = VideoToGifWorker(video_path, output_path, fps, speed_factor, resize)
        self.video_worker.progress.connect(self.update_video_progress)
        self.video_worker.finished.connect(self.on_video_conversion_finished)
        self.video_worker.error.connect(self.on_conversion_error)
        self.video_worker.start()
    
    def convert_images_to_gif(self):
        if not self.selected_image_paths:
            QMessageBox.warning(self, "错误", "请选择图片文件")
            return
        
        output_path = self.image_output_edit.text()
        if not output_path:
            QMessageBox.warning(self, "错误", "请选择输出路径")
            return
        
        # 获取设置
        duration_ms = self.image_duration_spin.value()
        loop_count = self.image_loop_spin.value()
        
        # 获取尺寸设置
        resize = None
        if self.image_resize_check.isChecked():
            width = self.image_width_spin.value()
            height = self.image_height_spin.value()
            resize = (width, height)
        
        # 禁用按钮
        self.image_convert_btn.setEnabled(False)
        
        # 创建并启动工作线程
        self.image_worker = ImagesToGifWorker(self.selected_image_paths, output_path, duration_ms, loop_count, resize)
        self.image_worker.progress.connect(self.update_image_progress)
        self.image_worker.finished.connect(self.on_image_conversion_finished)
        self.image_worker.error.connect(self.on_conversion_error)
        self.image_worker.start()
    
    def update_video_progress(self, value):
        self.video_progress.setValue(value)
    
    def update_image_progress(self, value):
        self.image_progress.setValue(value)
    
    def on_video_conversion_finished(self, output_path):
        # 启用按钮
        self.video_convert_btn.setEnabled(True)
        QMessageBox.information(self, "完成", f"视频已成功转换为GIF：\n{output_path}")
        
        # 重置进度条
        self.video_progress.setValue(0)
    
    def on_image_conversion_finished(self, output_path):
        # 启用按钮
        self.image_convert_btn.setEnabled(True)
        QMessageBox.information(self, "完成", f"图片已成功转换为GIF：\n{output_path}")
        
        # 重置进度条
        self.image_progress.setValue(0)
    
    def on_conversion_error(self, error_msg):
        # 启用按钮
        self.video_convert_btn.setEnabled(True)
        self.image_convert_btn.setEnabled(True)
        
        # 显示错误消息
        QMessageBox.critical(self, "错误", f"转换过程中出错：\n{error_msg}")
        
        # 重置进度条
        self.video_progress.setValue(0)
        self.image_progress.setValue(0)
    
    @staticmethod
    def natural_sort_key(s):
        """自然排序函数"""
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GifConverterApp()
    window.show()
    sys.exit(app.exec_()) 