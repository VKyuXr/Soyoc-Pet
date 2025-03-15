import pyaudio, wave, librosa, threading, time, math, logging
import numpy as np

class AudioAnalyzer:
    """音频分析类"""
    def __init__(self, loudness_threshold=-70):
        self._audio_lock = threading.Lock()             # 线程锁
        self.period = 0.0                               # 存储检测到的节拍周期
        self.is_accent = False                          # 重音触发标志
        self._recording_thread = None                   # 录音及节拍分析线程初始化
        self._monitoring_thread = None                  # 节拍检测线程初始化
        self.loudness_flag = False                      # 显式初始化响度标志位
        self.loudness_threshold = loudness_threshold    # 响度阈值
        self.pa = pyaudio.PyAudio()
        self.stream = None
        self._stop_event = threading.Event()

        # 响度检测线程启动
        self._loudness_thread = threading.Thread(target=self._loudness_monitor, daemon=True)
        self._loudness_thread.start()

    def __del__(self):
        self._stop_event.set()
        if self.stream:
            self.stream.close()
        self.pa.terminate()

    def _loudness_monitor(self):
        """实时响度检测线程（每秒检测一次）"""
        device_index = self.find_stereo_mix_device()
        self.stream = self.pa.open(             # 打开音频流
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=44100             # 1秒缓冲区
        )
        
        logging.info("响度检测线程已启动")
        while not self._stop_event.is_set():
            try:
                # 读取1秒音频数据
                data = self.stream.read(44100, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # 计算RMS（均方根）声压级
                rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
                db = 20 * math.log10(rms / 32768) if rms != 0 else 0  # 16bit PCM归一化
                
                # 转换为线性比例比较
                if not self.loudness_flag and db > self.loudness_threshold: # 如果上一时刻响度低于阈值，这一时刻高于阈值
                    self.loudness_flag = True                               # 响度标志置 True
                elif self.loudness_flag and db < self.loudness_threshold:   # 如果上一时刻响度高于阈值，这一时刻低于阈值
                    self.loudness_flag = False                              # 响度标志置 False
                
            except Exception as e:
                logging.warning(f"响度检测异常: {e}")
                time.sleep(1)

    def find_stereo_mix_device(self):
        """查找桌面音频录音设备"""
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        for i in range(device_count):
            device_info = p.get_device_info_by_index(i)
            if "立体声混音" in device_info["name"] and device_info["hostApi"] == 0:
                logging.info(f"找到立体声混音设备: {device_info['name']} (索引: {i})")
                p.terminate()
                return i
        p.terminate()
        raise Exception("未找到立体声混音设备，请检查设备是否启用")

    def record_and_analyze(self, duration=3):
        """录音并分析节拍周期"""
        output_file = "./temp/beats_check_record.wav"
        format = pyaudio.paInt16
        channels = 2
        rate = 44100
        chunk = 1024
        stream = None  # 显式初始化流变量

        try:
            # 添加设备获取异常处理
            try:
                device_index = self.find_stereo_mix_device()
            except Exception as e:
                logging.error(f"设备获取失败: {e}")
                return

            p = pyaudio.PyAudio()
            stream = p.open(
                format=format,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk
            )

            logging.info("开始录制...")
            frames = []
            for _ in range(0, int(rate / chunk * duration)):
                data = stream.read(chunk, exception_on_overflow=False)
                frames.append(data)
            logging.info("录制完成")

            # 保存并分析音频
            with wave.open(output_file, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(format))
                wf.setframerate(rate)
                wf.writeframes(b''.join(frames))

            self.period = self.analyze_beats(output_file, rate)
            logging.info(f"节拍周期已更新为: {self.period:.2f}秒")

        except Exception as e:
            logging.error(f"录制异常: {str(e)}")  # 捕获所有异常
        finally:
            if stream:
                try:
                    stream.close()  # 直接关闭流
                except OSError:
                    pass
            p.terminate()
    
    def period_reset(self):
        """重置周期变量"""
        self.period = 0.0

    def analyze_beats(self, audio_file, sample_rate):
        """分析音频文件的节拍周期"""
        y, sr = librosa.load(audio_file, sr=sample_rate, mono=True)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beats, sr=sr)
        intervals = np.diff(beat_times)
        return np.mean(intervals) if len(intervals) > 0 else 0.0

    def start_detection(self):
        """启动检测流程"""
        self._stop_event.clear()

        # 启动录音及节拍分析线程
        self._recording_thread = threading.Thread(target=self.record_and_analyze)
        self._recording_thread.start()

        # 启动重音检测线程
        self._monitoring_thread = threading.Thread(target=self._monitor_accent)
        self._monitoring_thread.start()
        
    
    def record_and_analyze_is_alive(self):
        """录音及分析线程运行标志"""
        if self._recording_thread is not None:          # 如果录音及分析线程已经启动
            return self._recording_thread.is_alive()
        return False

    def _monitor_accent(self):
        """实时监测重音"""
        stream = None
        retry_count = 0
        with self._audio_lock:  # 使用线程锁保护设备访问
            try:
                device_index = self.find_stereo_mix_device()
                stream = self.pa.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=512  # 减小缓冲区降低资源占用
                )
                logging.info("开始实时监测重音...")

                while not self._stop_event.is_set() and retry_count < 3:
                    try:
                        data = stream.read(512, exception_on_overflow=False)
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        
                        # 动态音量阈值检测
                        if np.max(audio_data) > 10000 and self.period > 0:
                            logging.info(f"当前音量：{np.max(audio_data)}")
                            self.is_accent = True
                            logging.info("检测到重音！")
                            self._stop_event.set()
                            break  # 检测到重音后立即退出
                        else:
                            self.is_accent = False
                        
                        retry_count = 0  # 重置重试计数器
                        time.sleep(0.05)  # 降低CPU占用
                        
                    except OSError as e:
                        retry_count += 1
                        logging.warning(f"音频流读取异常，重试次数: {retry_count}/3")
                        time.sleep(0.1)
                        if retry_count >= 3:
                            self._stop_event.set()
                            raise e

            except Exception as e:
                logging.warning(f"监测线程异常: {str(e)}")
                self._stop_event.set()
            finally:
                if stream:
                    try:
                        stream.close()  # 直接关闭流，无需stop_stream()
                    except OSError:
                        pass
                logging.info("监测线程已终止")

    def stop(self):
        self._stop_event.set()
        if self._recording_thread:
            self._recording_thread.join()
        if self._monitoring_thread:
            self._monitoring_thread.join()